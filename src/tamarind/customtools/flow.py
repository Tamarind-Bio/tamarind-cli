"""Deploying a tool folder, and watching a build. The shell.

`build` is the only genuinely multi-step operation in the package, and the one place
where getting the sequence wrong ships nothing while reporting success. The sequence
and the reason for it:

    read the source ref  ->  upload  ->  finalize  ->  wait  ->  deploy  ->  reconcile

`finalize` hands extraction to a background task and returns immediately, while
`deploy` builds at whatever the repository currently points to. Those race. The naive
handling — deploy straight after finalize — can build the PREVIOUS source, find an
existing version there, and report "nothing to do" on a run that was supposed to ship
new code.

The wait is deliberately advisory rather than a gate. An identical re-upload produces
no new commit at all (the server skips a commit whose tree matches HEAD), so demanding
that the ref move would turn every unchanged CI re-deploy into a hard timeout. Instead:
wait if we can, deploy regardless, then interpret what came back — which is what
`plan.reconcile` is for.

Progress is reported through `on_event`, never printed. The CLI passes a renderer; a
script passes nothing.
"""

from __future__ import annotations

import json
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Literal

from ..errors import TamarindError, ValidationError
from ..http import HTTPClient
from ..upload import put_presigned
from . import api, archive, plan, project, wire

Phase = Literal["check", "package", "upload", "extract", "deploy", "build"]
Kind = Literal["status", "log", "warning"]

# How long to wait for the server to finish extracting before giving up and deploying
# anyway. Generous, because being slow here is harmless — the reconcile step catches a
# late landing — while being impatient is not.
EXTRACT_TIMEOUT = 300.0
EXTRACT_INTERVAL = 2.0
# Polling the logs endpoint also reconciles build state server-side, so a sane interval
# is useful rather than merely polite.
BUILD_INTERVAL = 5.0
BUILD_TIMEOUT = 3600.0


@dataclass(frozen=True)
class BuildEvent:
    """A progress event. Structured rather than a line of text.

    A string callback would force every consumer to parse prose to find out which phase
    it is in, and widening it later is a breaking change for anyone who took it.
    """

    phase: Phase
    kind: Kind
    message: str
    timestamp: int | None = None


EventHandler = Callable[[BuildEvent], None]


def _emit(
    on_event: EventHandler | None, phase: Phase, kind: Kind, message: str, ts: int | None = None
) -> None:
    if on_event is not None:
        on_event(BuildEvent(phase=phase, kind=kind, message=message, timestamp=ts))


def wait_for_source(
    client: HTTPClient,
    *,
    name: str,
    previous_ref: str | None,
    timeout: float = EXTRACT_TIMEOUT,
    interval: float = EXTRACT_INTERVAL,
) -> str | None:
    """Poll until the source ref differs from ``previous_ref``. Never raises on timeout.

    Returns the new ref, or None if it never moved within ``timeout``. None is NOT an
    error: an identical upload legitimately produces no commit, so the caller deploys
    anyway and lets `reconcile` decide.

    `hasSource` is unusable for this — it is already true on every redeploy — and a null
    ref reads as "not yet" rather than "never", since the field is documented as null
    when the repository is unreachable.
    """
    deadline = time.monotonic() + max(0.0, timeout)
    while True:
        current = api.get_tool(client, name=name).current_source_ref
        if current and current != previous_ref:
            return current
        if time.monotonic() >= deadline:
            return None
        time.sleep(max(0.0, min(interval, deadline - time.monotonic())))


def wait_for_build(
    client: HTTPClient,
    *,
    name: str,
    build_id: str,
    timeout: float = BUILD_TIMEOUT,
    interval: float = BUILD_INTERVAL,
    on_event: EventHandler | None = None,
) -> wire.LogPage:
    """Stream build output until the build reaches a terminal state.

    Raises :class:`TamarindError` on a non-successful terminal state, carrying the
    server's own error message — which is already humanized, so it is surfaced verbatim
    rather than re-derived from the log tail.
    """
    deadline = time.monotonic() + max(0.0, timeout)
    token: str | None = None
    page = wire.LogPage()
    while True:
        page = api.get_logs(client, name=name, build_id=build_id, next_token=token)
        for line in page.lines:
            _emit(on_event, "build", "log", line.message, line.timestamp)
        # Only advance on a real token: reusing the previous one would replay the page.
        token = page.next_token or token
        if plan.is_terminal_build(page.build_status):
            break
        if time.monotonic() >= deadline:
            raise TamarindError(
                f"Build {build_id} was still {page.build_status!r} after {timeout:.0f}s. "
                f"It is still running — `tamarind ct logs {name}` reattaches."
            )
        time.sleep(max(0.0, min(interval, deadline - time.monotonic())))

    if not plan.build_succeeded(page.build_status):
        raise TamarindError(
            page.error_message or f"Build {build_id} ended {page.build_status}.",
            detail={"build_id": build_id, "build_status": page.build_status},
        )
    return page


def build(
    client: HTTPClient,
    *,
    name: str,
    folder: Path | str,
    wait: bool = True,
    on_event: EventHandler | None = None,
    timeout: float = BUILD_TIMEOUT,
    extract_timeout: float = EXTRACT_TIMEOUT,
) -> plan.DeployOutcome:
    """Package a folder, upload it, deploy it, and (by default) watch the build.

    Returns a :class:`plan.DeployOutcome` whose ``deployed`` flag is decided in exactly
    one place. Callers must not re-derive it from ``path``.
    """
    root = Path(folder)

    # 1. Decide what goes up, and say what does not.
    _emit(on_event, "package", "status", f"Packaging {root}")
    spec = archive.plan_archive(root)
    advice = archive.packaging.env_var_advice(spec.secrets)
    if advice:
        _emit(on_event, "package", "warning", advice)
    for weight in spec.weights:
        _emit(
            on_event,
            "package",
            "warning",
            f"{weight} looks like model weights. The runtime container has no network, "
            f"so weights should be baked into the image by the Dockerfile rather than "
            f"uploaded as source.",
        )

    # 2. The ref BEFORE the upload — this is what makes step 4 possible at all.
    previous_ref = api.get_tool(client, name=name).current_source_ref

    # 3. Package and upload.
    with tempfile.TemporaryDirectory() as tmp:
        zip_path = Path(tmp) / f"{name}.zip"
        size = archive.write_archive(spec, zip_path)
        _emit(on_event, "package", "status", f"{len(spec.included)} files, {size / 1024:.0f} KiB")

        ticket = api.init_upload(client, name=name)
        if not ticket.upload_url or not ticket.upload_id:
            raise TamarindError(
                "Upload could not be started — the server returned no destination.",
                detail={"fields": sorted(ticket.raw) if ticket.raw else []},
            )
        _emit(on_event, "upload", "status", "Uploading source")
        put_presigned(
            ticket.upload_url, zip_path, content_type="application/zip", remote=f"{name} source"
        )
        api.finalize_upload(client, name=name, upload_id=ticket.upload_id)

    # 4. Advisory wait. None here is not a failure.
    _emit(on_event, "extract", "status", "Waiting for the server to unpack the upload")
    new_ref = wait_for_source(client, name=name, previous_ref=previous_ref, timeout=extract_timeout)
    ref_moved = new_ref is not None
    if not ref_moved:
        _emit(
            on_event,
            "extract",
            "status",
            "Source is unchanged from what is already stored (an identical upload "
            "produces no new commit)",
        )

    # 5. Deploy regardless, then interpret.
    _emit(on_event, "deploy", "status", "Deploying")
    result = api.deploy(client, name=name)

    if plan.needs_late_landing_recheck(ref_moved=ref_moved, path=result.path):
        # The one ambiguous corner. If the ref has moved by NOW, extraction finished
        # after the deploy read the repository — so that deploy built the OLD source and
        # shipped nothing. Deploying again is the fix; reporting success is the bug this
        # whole sequence exists to avoid.
        settled = api.get_tool(client, name=name).current_source_ref
        if settled and settled != previous_ref:
            _emit(
                on_event,
                "deploy",
                "warning",
                "Upload landed after the deploy started; deploying again",
            )
            result = api.deploy(client, name=name)
            # The ref is now confirmed moved, so the retry's result is reconciled on the
            # normal paths — a second no-op here genuinely means someone else got there.
            ref_moved = True

    outcome = plan.reconcile(ref_moved=ref_moved, result=result)
    _emit(on_event, "deploy", "status", outcome.explanation)

    if outcome.deployed and outcome.build_id and wait:
        wait_for_build(
            client, name=name, build_id=outcome.build_id, timeout=timeout, on_event=on_event
        )
    return outcome


def publish(
    client: HTTPClient, *, name: str, version_name: str | None = None
) -> tuple[wire.Tool, str]:
    """Promote a version live for the org. Returns the tool and the version published.

    Defaults to the newest version that actually built. A failed build leaves its
    version *Stopped*, so publishing "the latest" without checking would promote a
    version that never produced an image.
    """
    versions = api.get_versions(client, name=name)
    if version_name is None:
        chosen = plan.select_publishable(versions)
        if chosen is None or not chosen.name:
            raise ValidationError(
                f"'{name}' has no completed version to publish. "
                f"`tamarind ct versions {name}` shows what exists."
            )
        version_name = chosen.name
    else:
        named = plan.find_version(versions, version_name)
        if named is None:
            raise ValidationError(f"'{name}' has no version {version_name}.")
        if not named.is_complete:
            raise ValidationError(
                f"Version {version_name} is {named.status}, not Complete — it has no "
                f"image to publish." + (f" ({named.error_message})" if named.error_message else "")
            )
    return api.publish_version(client, name=name, version_name=version_name), version_name


def unpack_source(blob: bytes, destination: Path) -> tuple[Path, tuple[str, ...]]:
    """Extract a downloaded source archive. Returns the folder and any LFS pointers.

    Shared by `init` and `clone` rather than written twice — the LFS detection is the
    kind of detail that gets fixed in one copy and not the other.
    """
    import io
    import zipfile

    target = Path(destination)
    target.mkdir(parents=True, exist_ok=True)
    try:
        with zipfile.ZipFile(io.BytesIO(blob)) as zf:
            zf.extractall(target)
    except (zipfile.BadZipFile, OSError) as exc:
        raise TamarindError(f"Could not unpack the tool's source: {exc}") from exc
    pointers = tuple(
        p.relative_to(target).as_posix()
        for p in sorted(target.rglob("*"))
        if p.is_file() and _is_lfs_pointer(p)
    )
    return target, pointers


def _is_lfs_pointer(path: Path) -> bool:
    """Whether a file is a Git-LFS pointer rather than its content.

    Archives serve LFS-tracked files as pointers, matching GitHub and GitLab, so a
    cloned tool with large assets is not immediately redeployable. Worth saying rather
    than letting the next build fail confusingly.
    """
    try:
        with path.open("rb") as fh:
            return fh.read(45).startswith(b"version https://git-lfs.github.com/spec")
    except OSError:
        return False


def init(
    client: HTTPClient,
    *,
    name: str,
    destination: Path | str,
    display_name: str | None = None,
    on_event: EventHandler | None = None,
) -> tuple[Path, project.Project]:
    """Create a tool and put its starting files on disk.

    The scaffold is generated SERVER-SIDE (`template="scratch"`) and downloaded, rather
    than the CLI carrying its own copies. That matters because the server picks the
    Dockerfile's base image from the tool's declared packages — GPU work gets a CUDA
    base, conda gets miniconda — so local templates would be a fourth copy of that
    logic and would drift the first time a base image moved.
    """
    target = Path(destination)
    if target.exists() and any(target.iterdir()):
        raise ValidationError(
            f"'{target}' already exists and is not empty. Point `init` at a new folder, "
            f"or use `tamarind ct clone {name}` to fetch an existing tool."
        )

    _emit(on_event, "check", "status", f"Creating {name}")
    api.create_tool(client, name=name, display_name=display_name, template="scratch")

    _emit(on_event, "package", "status", "Fetching the starting files")
    blob = api.download_archive(client, name=name)
    folder, pointers = unpack_source(blob, target)
    for pointer in pointers:
        _emit(
            on_event,
            "package",
            "warning",
            f"{pointer} came down as a Git-LFS pointer, not content.",
        )

    marker = project.write(folder, name=name)
    _emit(on_event, "check", "status", f"Recorded the tool id in {marker.name}")
    return folder, project.Project(name=name, path=marker)


def apply_config(
    client: HTTPClient,
    *,
    name: str,
    folder: Path | str,
    target_version: str | None = None,
) -> dict:
    """Push a folder's config.json to the tool WITHOUT building or minting a version.

    This is the input-schema iteration loop. Deploying would also work — an
    inputs-only change does not rebuild, because the rebuild decision hashes the
    environment files rather than config.json — but it mints a version every time and a
    new version is not live until it is published. Fiddling with a label through
    `deploy` produces v7 through v12 differing by a text field.

    ``target_version`` is the capability nothing else reaches: a version's inputs are
    snapshotted when it builds and pinned by its ref, so this is the only way to
    correct a schema on a version that already exists.
    """
    config = Path(folder) / "config.json"
    if not config.is_file():
        raise ValidationError(f"No config.json in '{folder}' — nothing to apply.")
    try:
        text = config.read_text()
        json.loads(text)
    except OSError as exc:
        raise TamarindError(f"Could not read {config}: {exc}") from exc
    except ValueError as exc:
        # Refuse locally rather than letting the server reject it: the message here can
        # name the line, and a round trip proves nothing the parser cannot.
        raise ValidationError(f"{config} is not valid JSON: {exc}") from exc
    return api.save_config(client, name=name, config_json=text, target_version=target_version)
