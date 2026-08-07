"""`tamarind ct` — authoring custom tools.

The lifecycle verbs people run constantly (`deploy`, `publish`) are registered at the
top level by :func:`register`; the occasional ones live under `ct`. That split is not
taste — `tamarind tools` already means "search the catalog", so the authoring surface
cannot take that name, and burying `deploy` three tokens deep would be worse.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from ... import customtools as ct
from ...customtools import archive as ct_archive
from ...customtools import flow as ct_flow
from ...errors import TamarindError, ValidationError
from .. import output

app = typer.Typer(no_args_is_help=True)


def _renderer(state) -> "callable":
    """Send progress to STDERR so stdout stays a clean result object.

    This is what makes `tamarind deploy --json | jq` work: build output and the result
    cannot share a stream. Suppressed entirely in quiet/JSON mode.
    """

    def handle(event: ct_flow.BuildEvent) -> None:
        if event.kind == "warning":
            output.info(f"warning: {event.message}", state.output)
        else:
            output.info(event.message, state.output)

    return handle


def _outcome_payload(outcome: ct.DeployOutcome, name: str) -> dict:
    return {
        "tool": name,
        "version": outcome.version_name,
        "path": outcome.path,
        "buildId": outcome.build_id,
        # The field a script branches on. Deliberately NOT re-derived from `path` by
        # the caller — that inference is made once, in plan.reconcile.
        "deployed": outcome.deployed,
        "reason": outcome.reason,
        "detail": outcome.explanation,
    }


# ------------------------------------------------------------- top-level verbs ----


def register(app_root: typer.Typer) -> None:
    """Attach the everyday verbs to the root command."""

    @app_root.command()
    def deploy(
        ctx: typer.Context,
        folder: Path = typer.Argument(
            Path("."), help="Tool folder. Defaults to the current directory."
        ),
        name: Optional[str] = typer.Option(
            None, "--name", help="Tool id. Defaults to the folder name."
        ),
        wait: bool = typer.Option(
            True, "--wait/--no-wait", help="Watch the build until it finishes."
        ),
        publish_after: bool = typer.Option(
            False, "--publish", help="Publish the new version if the build succeeds."
        ),
        fail_on_noop: bool = typer.Option(
            False,
            "--fail-on-noop",
            help="Exit non-zero when there was nothing to deploy (for strict CI).",
        ),
        timeout: float = typer.Option(3600.0, "--timeout", help="Seconds to watch a build."),
    ) -> None:
        """Package a folder, upload it, and deploy it.

        Streams build output as it arrives. When nothing changed this still succeeds —
        `deployed: false` in the JSON says so, and `--fail-on-noop` makes it an error.
        """
        state = ctx.obj
        tool = name or Path(folder).resolve().name
        with state.rest_client() as client:
            outcome = ct.build(
                client,
                name=tool,
                folder=folder,
                wait=wait,
                on_event=_renderer(state),
                timeout=timeout,
            )
            payload = _outcome_payload(outcome, tool)

            if publish_after and outcome.deployed and outcome.version_name:
                _, published = ct.publish(client, name=tool, version_name=outcome.version_name)
                payload["published"] = published

        human = (
            f"{tool} {outcome.version_name}: {outcome.explanation}"
            if outcome.deployed
            else f"{tool}: {outcome.explanation}"
        )
        output.emit(payload, state.output, human=human)
        if fail_on_noop and not outcome.deployed:
            raise typer.Exit(code=1)

    @app_root.command()
    def publish(
        ctx: typer.Context,
        name: Optional[str] = typer.Argument(None, help="Tool id. Defaults to the folder name."),
        version: Optional[str] = typer.Argument(
            None, help="Version. Defaults to the newest complete one."
        ),
    ) -> None:
        """Make a version live for the whole organization.

        Separate from `deploy` on purpose: publishing hands every member of your org the
        viewer role on the tool, so it should not happen as a side effect of building.
        """
        state = ctx.obj
        tool = name or Path.cwd().name
        with state.rest_client() as client:
            _, published = ct.publish(client, name=tool, version_name=version)
        output.emit(
            {"tool": tool, "published": published},
            state.output,
            human=f"published {tool} {published}",
        )

    @app_root.command()
    def check(
        ctx: typer.Context,
        folder: Path = typer.Argument(
            Path("."), help="Tool folder. Defaults to the current directory."
        ),
    ) -> None:
        """Inspect a tool folder before spending a build on it.

        Local only and instant. These same checks run inside `deploy` — a pre-flight
        nobody remembers to run prevents nothing — so this exists for pre-commit hooks
        and CI, where running it alone is the point.
        """
        state = ctx.obj
        spec = ct_archive.plan_archive(folder)
        root = spec.root
        problems: list[str] = []
        warnings: list[str] = []

        if not (root / "Dockerfile").is_file():
            problems.append("No Dockerfile — the build has nothing to build.")
        if not (root / "run.sh").is_file():
            problems.append(
                'No run.sh — the generated Dockerfile ends in `CMD ["bash","run.sh"]`, '
                "so the image builds and then fails to start."
            )
        config = root / "config.json"
        if not config.is_file():
            problems.append("No config.json — the tool has no declared inputs or outputs.")
        else:
            import json

            try:
                json.loads(config.read_text())
            except (OSError, ValueError) as exc:
                problems.append(f"config.json is not valid JSON: {exc}")

        advice = ct.packaging.env_var_advice(spec.secrets)
        if advice:
            warnings.append(advice)
        for weight in spec.weights:
            warnings.append(
                f"{weight} looks like model weights. The runtime container has no "
                f"network, so weights belong in the image via the Dockerfile."
            )

        payload = {
            "folder": str(root),
            "files": len(spec.included),
            "bytes": spec.total_bytes,
            "excludedSecrets": list(spec.secrets),
            "excludedNoise": spec.noise_count,
            "problems": problems,
            "warnings": warnings,
            "ok": not problems,
        }
        for warning in warnings:
            output.info(f"warning: {warning}", state.output)
        human = (
            f"{len(spec.included)} files, {spec.total_bytes / 1024:.0f} KiB — looks deployable"
            if not problems
            else "\n".join(f"- {p}" for p in problems)
        )
        output.emit(payload, state.output, human=human)
        if problems:
            raise typer.Exit(code=5)


# ------------------------------------------------------------------- ct verbs ----


@app.command("list")
def list_tools(ctx: typer.Context) -> None:
    """Your organization's own custom tools (not the runnable catalog)."""
    state = ctx.obj
    with state.rest_client() as client:
        resp = ct.list_tools(client)
    tools = resp.get("tools", resp) if isinstance(resp, dict) else resp
    rows = tools if isinstance(tools, list) else []
    output.emit(
        resp,
        state.output,
        human=output.render_table(
            [
                {
                    "name": t.get("name"),
                    "status": t.get("status"),
                    "published": t.get("published"),
                }
                for t in rows
                if isinstance(t, dict)
            ],
            ["name", "status", "published"],
        ),
    )


@app.command()
def status(ctx: typer.Context, name: str = typer.Argument(..., help="Tool id.")) -> None:
    """What state a tool is in, and whether it has changes that were never deployed."""
    state = ctx.obj
    with state.rest_client() as client:
        tool = ct.get_tool(client, name=name)
        versions = ct.get_versions(client, name=name)

    latest = versions[0] if versions else None
    # The genuinely useful line, and the only derived one: if the source has moved past
    # the newest version's ref, there is work sitting undeployed.
    undeployed = bool(tool.current_source_ref and latest and latest.ref != tool.current_source_ref)
    payload = {
        "name": tool.name,
        "status": tool.status,
        "published": tool.published,
        "latestVersion": latest.name if latest else None,
        "latestVersionStatus": latest.status if latest else None,
        "latestBuildStatus": tool.latest_build_status,
        "sourceRef": tool.current_source_ref,
        "hasUndeployedChanges": undeployed,
        "publishPending": tool.publish_pending_version,
    }
    lines = [f"{tool.name}: {tool.status}" + (" (published)" if tool.published else "")]
    if latest:
        lines.append(f"latest version {latest.name} — {latest.status}")
    if undeployed:
        lines.append("source has changes that have not been deployed")
    output.emit(payload, state.output, human="\n".join(lines))


@app.command()
def versions(ctx: typer.Context, name: str = typer.Argument(..., help="Tool id.")) -> None:
    """Version history, newest first."""
    state = ctx.obj
    with state.rest_client() as client:
        found = ct.get_versions(client, name=name)
    output.emit(
        [v.raw for v in found],
        state.output,
        human=output.render_table(
            [
                {
                    "version": v.name,
                    "status": v.status,
                    "build": v.build_id,
                    "by": v.created_by,
                    "error": v.error_message,
                }
                for v in found
            ],
            ["version", "status", "build", "by", "error"],
        ),
    )


@app.command()
def logs(
    ctx: typer.Context,
    name: str = typer.Argument(..., help="Tool id."),
    build_id: Optional[str] = typer.Option(
        None, "--build-id", help="Defaults to the latest build."
    ),
    follow: bool = typer.Option(
        False, "--follow", "-f", help="Keep streaming until the build ends."
    ),
) -> None:
    """Build output, for reattaching after `--no-wait` or a dropped connection.

    Ctrl-C stops watching. It does NOT cancel the build — use `ct cancel` for that.
    """
    state = ctx.obj
    with state.rest_client() as client:
        target = build_id
        if target is None:
            tool = ct.get_tool(client, name=name)
            target = tool.latest_build_id
            if not target:
                raise ValidationError(f"'{name}' has no build to show logs for.")
        if follow:
            page = ct.wait_for_build(client, name=name, build_id=target, on_event=_renderer(state))
        else:
            page = ct.api.get_logs(client, name=name, build_id=target)
            for line in page.lines:
                output.info(line.message, state.output)
    output.emit(
        {"buildId": target, "buildStatus": page.build_status, "error": page.error_message},
        state.output,
        human=f"build {target}: {page.build_status}",
    )


@app.command()
def cancel(
    ctx: typer.Context,
    name: str = typer.Argument(..., help="Tool id."),
    build_id: Optional[str] = typer.Option(
        None, "--build-id", help="Defaults to the in-flight build."
    ),
) -> None:
    """Stop a build that is still running."""
    state = ctx.obj
    with state.rest_client() as client:
        target = build_id
        if target is None:
            target = ct.plan.cancellable_build_id(ct.get_versions(client, name=name))
            if not target:
                # Deliberately an error rather than a silent no-op: "cancelled" on a
                # finished build reads as success and hides that nothing happened.
                raise ValidationError(f"'{name}' has no build in progress to cancel.")
        resp = ct.cancel_build(client, name=name, build_id=target)
    output.emit(resp, state.output, human=f"cancelled build {target}")


@app.command()
def config(
    ctx: typer.Context,
    name: str = typer.Argument(..., help="Tool id."),
    gpu_type: Optional[str] = typer.Option(None, "--gpu-type", help="None|T4|L4|L40S|A10|A100."),
    memory: Optional[str] = typer.Option(None, "--memory", help="e.g. 8Gi, 32Gi, 180Gi."),
    cpu: Optional[int] = typer.Option(None, "--cpu", help="1-8."),
    home_disk_gi: Optional[int] = typer.Option(None, "--home-disk-gi", help="1-50."),
    display_name: Optional[str] = typer.Option(None, "--display-name"),
    description: Optional[str] = typer.Option(None, "--description"),
) -> None:
    """Read or change a tool's resources and metadata.

    Never builds and never creates a version — changes apply to the next run. Inputs
    are NOT settable here: config.json in the repo is canonical for those, so changing
    one means editing that file and deploying.
    """
    state = ctx.obj
    changes = {
        "gpuType": gpu_type,
        "memory": memory,
        "cpu": cpu,
        "homeDiskGi": home_disk_gi,
        "displayName": display_name,
        "description": description,
    }
    changes = {k: v for k, v in changes.items() if v is not None}
    with state.rest_client() as client:
        tool = (
            ct.update_tool(client, name=name, **changes)
            if changes
            else ct.get_tool(client, name=name)
        )
    shown = {
        k: tool.raw.get("latest", tool.raw).get(k)
        for k in ("gpuType", "memory", "cpu", "homeDiskGi", "displayName", "description")
    }
    output.emit(
        shown,
        state.output,
        human="\n".join(f"{k}: {v}" for k, v in shown.items() if v is not None),
    )


@app.command()
def clone(
    ctx: typer.Context,
    name: str = typer.Argument(..., help="Tool id."),
    dest: Optional[Path] = typer.Argument(None, help="Destination. Defaults to ./<name>."),
    version: Optional[str] = typer.Option(None, "--version", help="Version to fetch."),
) -> None:
    """Download a tool's source, so you can edit it and deploy it back."""
    import io
    import zipfile

    state = ctx.obj
    target = Path(dest) if dest else Path.cwd() / name
    with state.rest_client() as client:
        ref = None
        if version:
            found = ct.plan.find_version(ct.get_versions(client, name=name), version)
            if found is None:
                raise ValidationError(f"'{name}' has no version {version}.")
            ref = found.ref
        blob = ct.download_archive(client, name=name, ref=ref)

    target.mkdir(parents=True, exist_ok=True)
    try:
        with zipfile.ZipFile(io.BytesIO(blob)) as zf:
            zf.extractall(target)
    except (zipfile.BadZipFile, OSError) as exc:
        raise TamarindError(f"Could not unpack {name}'s source: {exc}") from exc

    pointers = [p.name for p in target.rglob("*") if p.is_file() and _is_lfs_pointer(p)]
    if pointers:
        output.info(
            f"warning: {len(pointers)} file(s) came down as Git-LFS pointers, not "
            f"content ({', '.join(sorted(pointers)[:3])}…). Deploying this folder as-is "
            f"would upload the pointers.",
            state.output,
        )
    output.emit(
        {"tool": name, "path": str(target), "lfsPointers": pointers},
        state.output,
        human=f"cloned {name} to {target}",
    )


def _is_lfs_pointer(path: Path) -> bool:
    """Whether a file is a Git-LFS pointer rather than its content.

    Archives serve LFS-tracked files as pointers, matching GitHub and GitLab, so a
    clone of a tool with large assets is not immediately redeployable — worth saying
    rather than letting the next build fail confusingly.
    """
    try:
        with path.open("rb") as fh:
            return fh.read(45).startswith(b"version https://git-lfs.github.com/spec")
    except OSError:
        return False


@app.command()
def delete(
    ctx: typer.Context,
    name: str = typer.Argument(..., help="Tool id."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip the confirmation."),
) -> None:
    """Permanently delete a tool and its source. There is no recycle bin."""
    state = ctx.obj
    output.confirm_destructive(
        f"delete custom tool '{name}' and all its source", yes=yes, mode=state.output
    )
    with state.rest_client() as client:
        ct.delete_tool(client, name=name)
    output.emit({"tool": name, "deleted": True}, state.output, human=f"deleted {name}")
