"""Deploying a tool folder, and watching a build. The shell.

`build` is the only genuinely multi-step operation in the package, and the one place
where getting the sequence wrong ships nothing while reporting success. The sequence
and the reason for it:

    read source state  ->  upload  ->  finalize  ->  wait  ->  deploy  ->  reconcile

`finalize` hands extraction to a background task and returns immediately, while
`deploy` builds at whatever the repository currently points to. Those race. The naive
handling — deploy straight after finalize — can build the PREVIOUS source, find an
existing version there, and report "nothing to do" on a run that was supposed to ship
new code.

**What the wait watches matters more than how long it waits.** The obvious signal is
the source ref, and it is the wrong one: an identical re-upload produces no commit at
all (the server skips a commit whose tree matches HEAD), so on the single most common
CI deploy the ref never moves and a ref-watcher waits out its entire timeout before
concluding nothing happened. `lastUpdatedAt` is the right one — the extractor stamps it
on every successful extraction, including the no-commit case — so "the server finished"
and "the content changed" stop being the same question.

The wait still does not GATE the deploy: it is bounded, and on timeout the deploy runs
anyway. What changes is the reporting. A no-op with an unconfirmed extraction is no
longer called `unchanged`, because that claims a success we did not observe.

Progress is reported through `on_event`, never printed. The CLI passes a renderer; a
script passes nothing.
"""

from __future__ import annotations

import json
import tempfile
import time
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Callable, Literal

from ..errors import JobTimeoutError, TamarindError, ValidationError
from ..http import HTTPClient
from ..upload import put_presigned
from . import api, archive, manifest, plan, project, wire

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


@dataclass(frozen=True)
class SourceState:
    """What the server said about the tool's source at one moment.

    Captured BEFORE an upload so the wait afterwards has something to compare against.
    """

    ref: str | None = None
    updated_at: str | None = None


@dataclass(frozen=True)
class ExtractionResult:
    """How the wait for extraction ended.

    ``landed`` is the load-bearing one, and it is deliberately separate from
    ``ref_moved``: extraction completing and the content having changed are different
    facts, and conflating them is what made an unchanged re-upload indistinguishable
    from an upload that had not finished.
    """

    landed: bool = False
    ref: str | None = None
    ref_moved: bool = False


def ensure_usable_destination(destination: Path | str, *, allow_nonempty: bool = False) -> Path:
    """Check a folder a command is about to write into. Returns it.

    ONE guard, because there were two and they drifted: `init` and `clone` each grew
    their own `exists() and any(iterdir())`, and both crashed with a raw
    NotADirectoryError when the path was an existing FILE — user input producing a
    traceback rather than a typed error.

    Three distinct cases, distinguished on purpose:

      * missing            -> fine, the caller creates it
      * an existing file   -> always an error; there is no sense in which this works
      * a non-empty folder -> an error unless the caller explicitly allows it, since
                              extraction overwrites whatever is already there
    """
    target = Path(destination)
    if not target.exists():
        return target
    if not target.is_dir():
        raise ValidationError(
            f"'{target}' is a file, not a folder. Point this at a directory, or remove it."
        )
    if not allow_nonempty and any(target.iterdir()):
        raise ValidationError(
            f"'{target}' is not empty. Writing here overwrites whatever is already "
            f"there, so local edits would be lost. Choose an empty folder."
        )
    return target


def read_source_state(client: HTTPClient, *, name: str) -> SourceState:
    """The source fields a deploy needs to compare against afterwards."""
    tool = api.get_tool(client, name=name)
    return SourceState(ref=tool.current_source_ref, updated_at=tool.last_updated_at)


def wait_for_source(
    client: HTTPClient,
    *,
    name: str,
    before: SourceState,
    timeout: float = EXTRACT_TIMEOUT,
    interval: float = EXTRACT_INTERVAL,
) -> ExtractionResult:
    """Poll until the server finishes extracting the upload.

    Watches ``lastUpdatedAt``, not the source ref. The extractor stamps that field on
    every successful extraction *including one whose tree matched and produced no
    commit*, so it answers "is the server done with my upload" — which the ref cannot,
    because on an identical re-upload the ref never moves at all. Watching the ref made
    the single most common CI deploy wait out the full timeout every time, and made a
    genuinely-unchanged upload look identical to one still being unpacked.

    Raises if the server recorded an extraction failure: a bad zip or an LFS-pointer
    archive is a real error, and burning the timeout before reporting "unchanged" told
    the user the opposite of what happened.

    ``landed=False`` on timeout is honest rather than fatal — the caller still deploys,
    but must not then claim the source was unchanged.

    NOT correlated with THIS upload: a concurrent upload by someone else stamps the same
    field. Closing that needs a per-upload signal (the source hash), which the API does
    not expose yet; the late-landing recheck in `build` is the partial mitigation.
    """
    deadline = time.monotonic() + max(0.0, timeout)
    while True:
        tool = api.get_tool(client, name=name)
        if tool.connection_error:
            raise TamarindError(
                f"The server could not unpack the upload: {tool.connection_error}",
                detail={"tool": name, "phase": "extract"},
            )
        moved = bool(tool.current_source_ref and tool.current_source_ref != before.ref)
        if tool.last_updated_at and tool.last_updated_at != before.updated_at:
            return ExtractionResult(landed=True, ref=tool.current_source_ref, ref_moved=moved)
        # A server that reports no timestamp at all leaves only the old signal. Treat a
        # moved ref as landed rather than waiting out the clock for a field this
        # deployment may not serve.
        if moved:
            return ExtractionResult(landed=True, ref=tool.current_source_ref, ref_moved=True)
        if time.monotonic() >= deadline:
            return ExtractionResult(landed=False, ref=tool.current_source_ref, ref_moved=False)
        time.sleep(max(0.0, min(interval, deadline - time.monotonic())))


def drain_logs(
    client: HTTPClient,
    *,
    name: str,
    build_id: str,
    token: str | None = None,
    on_event: EventHandler | None = None,
) -> tuple[wire.LogPage, str | None, tuple[wire.LogLine, ...]]:
    """Read every page currently available. Returns (last page, next token, lines).

    ONE drain, because there were two and only one of them was right. The non-follow
    path fetched a single page and reported the build summary as though that were the
    whole log; `wait_for_build` stopped the moment a page reported a terminal status,
    which is exactly when the remaining pages matter most — a failed build's error is
    in its tail.

    Never waits for output that does not exist yet: it follows tokens the server has
    already issued and stops when it stops issuing new ones. A repeated token ends the
    loop rather than replaying the page forever.
    """
    seen: set[str] = set()
    lines: list[wire.LogLine] = []
    while True:
        page = api.get_logs(client, name=name, build_id=build_id, next_token=token)
        for line in page.lines:
            _emit(on_event, "build", "log", line.message, line.timestamp)
        lines.extend(page.lines)
        following = page.next_token
        if not following or following in seen:
            # Keep the last real token so a follow-up call resumes rather than replays.
            return page, following or token, tuple(lines)
        seen.add(following)
        token = following


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

    Raises :class:`JobTimeoutError` when the deadline elapses — a typed error with its
    own exit code, so a caller can tell "still building when I stopped watching" (the
    build is fine, and reattachable) from "the build failed". Raises
    :class:`TamarindError` on a non-successful terminal state, carrying the server's own
    message, which is already humanized.
    """
    deadline = time.monotonic() + max(0.0, timeout)
    token: str | None = None
    page = wire.LogPage()
    while True:
        page, token, _ = drain_logs(
            client, name=name, build_id=build_id, token=token, on_event=on_event
        )
        if plan.is_terminal_build(page.build_status):
            break
        if time.monotonic() >= deadline:
            raise JobTimeoutError(
                f"Build {build_id} was still {page.build_status!r} after {timeout:.0f}s. "
                f"It is still running — `tamarind ct logs {name}` reattaches.",
                detail={"build_id": build_id, "build_status": page.build_status},
            )
        time.sleep(max(0.0, min(interval, deadline - time.monotonic())))

    if not plan.build_succeeded(page.build_status):
        raise TamarindError(
            page.error_message or f"Build {build_id} ended {page.build_status}.",
            detail={"build_id": build_id, "build_status": page.build_status},
        )
    return page


def inspect_manifest(folder: Path | str) -> manifest.Findings:
    """Read a folder's config.json and check it. The shell half of `manifest`.

    `manifest.check` is pure and takes parsed data; this is the one place that turns
    a folder into findings, so `deploy`, `check` and any caller script agree about
    what "the manifest" means rather than each reading the file their own way.

    A missing config.json yields no findings rather than an error. The server is the
    authority on whether one is required, and refusing locally would put this client
    between an author and a fix.
    """
    config = Path(folder) / "config.json"
    if not config.is_file():
        return manifest.Findings()
    try:
        data = json.loads(config.read_text())
    except (OSError, ValueError) as exc:
        raise ValidationError(f"config.json is not valid JSON: {exc}") from exc
    return manifest.check(data)


def inspect_folder(folder: Path | str) -> manifest.Findings:
    """Everything decidable about a tool folder without contacting the server.

    The structural files plus the manifest, in ONE function, because `check` and
    `deploy` must not disagree about what a deployable folder is. They did: `check`
    verified the Dockerfile and run.sh while `deploy` verified neither, so a folder
    `check` rejected still got packaged, uploaded, and sent to a remote build that
    could only fail — with `check`'s own docstring promising otherwise.
    """
    root = Path(folder)
    problems: list[str] = []

    # `will_upload`, not `is_file` — the packager drops symlinks, so a linked
    # Dockerfile is a file that exists locally and will NOT be in the archive. Asking
    # the same question the packager asks is what keeps the two from disagreeing.
    def _missing(name: str) -> bool:
        return not archive.will_upload(root / name)

    def _is_link(name: str) -> bool:
        return (root / name).is_symlink()

    if _missing("Dockerfile"):
        problems.append(
            "Dockerfile is a symlink, which is never uploaded — copy the real file in."
            if _is_link("Dockerfile")
            else "No Dockerfile — the build has nothing to build."
        )
    if _missing("run.sh"):
        problems.append(
            "run.sh is a symlink, which is never uploaded — copy the real file in."
            if _is_link("run.sh")
            else 'No run.sh — the generated Dockerfile ends in `CMD ["bash","run.sh"]`, '
            "so the image builds and then fails to start."
        )
    if _missing("config.json"):
        problems.append(
            "config.json is a symlink, which is never uploaded — copy the real file in."
            if _is_link("config.json")
            else "No config.json — the tool has no declared inputs or outputs."
        )

    # Only read the manifest when there IS one that will ship. Parsing a config.json
    # that is a symlink (and therefore excluded from the upload) reports a JSON error
    # about a file the server will never see, burying the actual problem.
    found = manifest.Findings() if _missing("config.json") else inspect_manifest(root)
    return manifest.Findings(
        errors=tuple(problems) + tuple(f"config.json: {e}" for e in found.errors),
        warnings=found.warnings,
        facts=found.facts,
    )


def _preflight(root: Path, on_event: EventHandler | None) -> None:
    """Refuse a deploy that cannot work, before anything is uploaded."""
    findings = inspect_folder(root)
    for warning in findings.warnings:
        _emit(on_event, "package", "warning", warning)
    if findings.errors:
        raise ValidationError(
            "This folder will not deploy:\n" + "\n".join(f"  - {e}" for e in findings.errors),
            detail={"errors": list(findings.errors)},
        )


def build(
    client: HTTPClient,
    *,
    name: str,
    folder: Path | str,
    wait: bool = True,
    on_event: EventHandler | None = None,
    timeout: float = BUILD_TIMEOUT,
    extract_timeout: float = EXTRACT_TIMEOUT,
    preflight: bool = True,
) -> plan.DeployOutcome:
    """Package a folder, upload it, deploy it, and (by default) watch the build.

    Returns a :class:`plan.DeployOutcome` whose ``deployed`` flag is decided in exactly
    one place. Callers must not re-derive it from ``path``.

    The folder is checked FIRST — structural files and the manifest, via the same
    `inspect_folder` that `check` runs — and a fatal finding stops the deploy before
    anything is uploaded. The server would reject most of this too, but only after an
    upload, an extraction and a build; the cost of being told about a missing run.sh
    should not be minutes. Pass ``preflight=False`` to deploy anyway, for the case
    where this client's rules have gone stale against a newer server.
    """
    root = Path(folder)

    # 0. Refuse before spending anything, if the manifest is already wrong.
    if preflight:
        _preflight(root, on_event)

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
    before = read_source_state(client, name=name)

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

    # 4. Wait for the server to finish unpacking. Bounded, and not fatal on timeout.
    _emit(on_event, "extract", "status", "Waiting for the server to unpack the upload")
    extraction = wait_for_source(client, name=name, before=before, timeout=extract_timeout)
    ref_moved = extraction.ref_moved
    if extraction.landed and not ref_moved:
        _emit(
            on_event,
            "extract",
            "status",
            "Unpacked; the source is identical to what is already stored, so there is "
            "no new commit",
        )
    elif not extraction.landed:
        _emit(
            on_event,
            "extract",
            "warning",
            f"The server did not confirm it unpacked the upload within "
            f"{extract_timeout:.0f}s. Deploying anyway, and reporting the result as "
            f"unconfirmed rather than guessing.",
        )

    # 5. Deploy regardless, then interpret.
    _emit(on_event, "deploy", "status", "Deploying")
    result = api.deploy(client, name=name)

    if plan.needs_late_landing_recheck(ref_moved=ref_moved):
        # We never watched our own content land, so this deploy read whatever the
        # repository happened to hold. If the ref has moved by NOW, extraction finished
        # after the deploy started and that deploy was against the OLD source —
        # whatever it reported. Checked for EVERY path, not just `noop`: when the
        # previous head itself needed building, a stale deploy comes back `building`,
        # reports success, and `--publish` then publishes a version built from source
        # the caller never asked to ship.
        settled = api.get_tool(client, name=name).current_source_ref
        if settled and settled != before.ref:
            _emit(
                on_event,
                "deploy",
                "warning",
                "Upload landed after the deploy started, so that deploy used the "
                "previous source. Deploying again.",
            )
            result = api.deploy(client, name=name)
            # The ref is now confirmed moved, so the retry's result is reconciled on the
            # normal paths — a second no-op here genuinely means someone else got there.
            ref_moved = True
            extraction = replace(extraction, landed=True, ref_moved=True)

    outcome = plan.reconcile(
        ref_moved=ref_moved, result=result, extraction_landed=extraction.landed
    )
    _emit(on_event, "deploy", "status", outcome.explanation)

    if outcome.deployed and outcome.path == "building" and not outcome.build_id:
        # `building` promises a build is running. Without an id there is nothing to
        # watch, so honouring `wait=True` is impossible and returning success would
        # exit clean while an untracked build is still going.
        raise TamarindError(
            "The server reported a build started but named no build id, so it cannot "
            "be watched. `tamarind ct status` shows whether it is running.",
            detail={"tool": name, "path": outcome.path, "version": outcome.version_name},
        )
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


def fetch_source(
    client: HTTPClient, *, name: str, destination: Path, ref: str | None = None
) -> tuple[Path, tuple[str, ...]]:
    """Download a tool's source into ``destination``. Returns it and any LFS pointers.

    Shared by `init` and `clone` rather than written twice — the LFS detection and the
    streaming download are both the kind of detail that gets fixed in one copy and not
    the other. The archive goes to a temporary file and is deleted afterwards, so a
    5 GiB source never has to fit in memory.
    """
    with tempfile.TemporaryDirectory() as tmp:
        zip_path = Path(tmp) / "source.zip"
        api.download_archive(client, name=name, ref=ref, destination=zip_path)
        return unpack_source(zip_path, destination)


def _extract_without_following_links(zf, target: Path) -> None:
    """Extract every member, refusing to write THROUGH an existing symlink.

    `extractall` opens each output path for writing, and open() follows a symlink that
    is already sitting there. So a destination containing `config.json -> /etc/thing`
    lets an archive member named `config.json` write outside the destination entirely.
    Only reachable with `clone --force` (an empty destination has no links to follow),
    but --force means "overwrite this folder", not "overwrite anything it points at".

    Links in the destination are removed rather than refused: the caller has already
    said to overwrite, and the file being replaced is the link itself.
    """
    for member in zf.infolist():
        parts = _sanitized_parts(member.filename)
        if not parts:
            continue
        # Walk down from the destination. An INTERMEDIATE component can be a link too —
        # `a/b.txt` writes through `a` if `a` points elsewhere — so every component is
        # checked, not just the leaf.
        current = target
        for part in parts:
            current = current / part
            if current.is_symlink():
                current.unlink()
        extracted = Path(zf.extract(member, target))
        _restore_mode(member, extracted)


def _restore_mode(member, path: Path) -> None:
    """Put back the executable bit the archive recorded.

    `ZipFile.extract` creates files with the process default (usually 0644) and drops
    the Unix mode in `external_attr`, so a cloned `run.sh` or `install.sh` comes back
    non-executable and `RUN ./install.sh` fails on a tree that built fine before.

    Only the executable bits are restored, and only where the archive already grants
    read: setuid/setgid/sticky and world-writable bits from an untrusted archive are
    not something a clone should be able to set.
    """
    import stat

    mode = member.external_attr >> 16
    if not mode or stat.S_ISDIR(mode) or stat.S_ISLNK(mode):
        return
    if not mode & 0o111:
        return
    try:
        current = path.stat().st_mode
        # Grant execute exactly where read is already granted — the umask-respecting
        # idiom. 0644 becomes 0755; a file the extractor made group-unreadable does not
        # silently become group-executable.
        path.chmod(current | ((current & 0o444) >> 2))
    except OSError:
        # A filesystem without executable bits (or a read-only one) is not a reason to
        # fail a clone that has already written every file.
        pass


def _sanitized_parts(filename: str) -> list[str]:
    """The path components `ZipFile.extract` will actually use for a member.

    Mirrors CPython's `_extract_member`: drive letters are dropped and empty, `.` and
    `..` components are removed. Computing the same path is what makes the symlink
    check land on the file that gets written rather than on a name that never exists.
    """
    import os

    name = filename.replace("/", os.path.sep)
    if os.path.altsep:
        name = name.replace(os.path.altsep, os.path.sep)
    name = os.path.splitdrive(name)[1]
    invalid = ("", os.path.curdir, os.path.pardir)
    return [part for part in name.split(os.path.sep) if part not in invalid]


def unpack_source(archive_path: Path, destination: Path) -> tuple[Path, tuple[str, ...]]:
    """Extract a downloaded source archive. Returns the folder and any LFS pointers.

    Takes a PATH, not bytes: the caller has already streamed it to disk, and taking
    bytes here would have forced every caller to hold the whole archive in memory to
    satisfy this signature.
    """
    import zipfile

    target = Path(destination)
    target.mkdir(parents=True, exist_ok=True)
    try:
        with zipfile.ZipFile(archive_path) as zf:
            _extract_without_following_links(zf, target)
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
    target = ensure_usable_destination(destination)

    _emit(on_event, "check", "status", f"Creating {name}")
    api.create_tool(client, name=name, display_name=display_name, template="scratch")

    _emit(on_event, "package", "status", "Fetching the starting files")
    folder, pointers = fetch_source(client, name=name, destination=target)
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
