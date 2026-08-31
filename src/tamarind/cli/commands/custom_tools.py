"""``tamarind custom-tools`` — organization Custom Tool lifecycle commands."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any, Optional

import typer

from ...custom_tools.resources import BuildEvent, CustomTool, Version
from ...custom_tools.transport import (
    GpuType,
    MemorySize,
    PublicCustomToolStatus,
    PublicVersionStatus,
)
from ...custom_tools.validation import ValidationProblem, ValidationReport, validate_folder
from ...errors import ExitCode, TamarindError, ValidationError
from .. import output


app = typer.Typer(no_args_is_help=True)


def _value(value: object) -> object:
    return getattr(value, "value", value)


def _problem(problem: ValidationProblem) -> dict[str, str]:
    return {
        "code": problem.code,
        "path": problem.path,
        "message": problem.message,
    }


def _report(report: ValidationReport) -> dict[str, object]:
    return {
        "valid": report.valid,
        "errors": [_problem(item) for item in report.errors],
        "warnings": [_problem(item) for item in report.warnings],
    }


def _tool(tool: CustomTool) -> dict[str, object]:
    return {
        "name": tool.name,
        "generation": tool.generation,
        "displayName": tool.display_name,
        "description": tool.description,
        "functions": list(tool.functions),
        "status": _value(tool.status),
        "gpuType": _value(tool.gpu_type),
        "memory": _value(tool.memory),
        "cpu": tool.cpu,
        "homeDiskGi": tool.home_disk_gi,
        "maxRuntimeSeconds": tool.max_runtime_seconds,
        "hasSource": tool.has_source,
        "sourceDigest": tool.source_digest,
        "published": tool.published,
        "autoPublish": tool.auto_publish,
        "estTime": tool.est_time,
        "paperUrl": tool.paper_url,
        "tags": list(tool.tags),
        "defaultVersion": tool.default_version,
        "createdAt": tool.created_at,
        "updatedAt": tool.updated_at,
        "canEdit": tool.can_edit,
        "canBuild": tool.can_build,
    }


def _version(version: Version) -> dict[str, object]:
    error = None
    if version.error is not None:
        error = {"code": version.error.code, "message": version.error.message}
    return {
        "id": version.id,
        "name": version.name,
        "toolName": version.tool_name,
        "toolGeneration": version.tool_generation,
        "sourceRevision": version.source_revision,
        "sourceDigest": version.source_digest,
        "status": _value(version.status),
        "terminal": version.terminal,
        "origin": version.origin,
        "createdAt": version.created_at,
        "startedAt": version.started_at,
        "completedAt": version.completed_at,
        "error": error,
    }


def _tool_human(tool: CustomTool) -> str:
    published = "published" if tool.published else "unpublished"
    return (
        f"{tool.display_name or tool.name}  [{tool.name}]\n"
        f"status: {tool.status}  {published}\n"
        f"generation: {tool.generation}\n"
        f"default version: {tool.default_version or '(none)'}\n"
        f"resources: {tool.cpu} CPU, {tool.memory}, GPU {tool.gpu_type}"
    )


def _version_human(version: Version) -> str:
    error = f"\nerror: {version.error.message}" if version.error is not None else ""
    return (
        f"{version.tool_name}/{version.name}\n"
        f"id: {version.id}\n"
        f"status: {version.status}\n"
        f"terminal: {'yes' if version.terminal else 'no'}{error}"
    )


def _event_printer(mode: output.OutputMode):
    if mode.json:
        return None

    def show(event: BuildEvent) -> None:
        output.info(event.message, mode)

    return show


def _get_version(client: Any, tool_name: str, version_id: str) -> Version:
    return client.custom_tools.get(tool_name).get_version(version_id)


def _attach_version_context(
    exc: TamarindError, *, version: Version, action: object | None = None
) -> TamarindError:
    """Keep the durable reattachment handle when a local wait fails."""
    detail = dict(exc.detail) if isinstance(exc.detail, dict) else {}
    if exc.detail is not None and not isinstance(exc.detail, dict):
        detail["upstreamDetail"] = exc.detail
    detail.update(
        {
            "toolName": version.tool_name,
            "versionId": version.id,
            "versionName": version.name,
        }
    )
    if action is not None:
        detail["action"] = _value(action)
    exc.detail = detail
    return exc


@app.command("list")
def list_tools(
    ctx: typer.Context,
    status: Optional[PublicCustomToolStatus] = typer.Option(
        None, "--status", help="Filter by Draft, Building, or Deployed."
    ),
    published: Optional[bool] = typer.Option(
        None, "--published/--unpublished", help="Filter by publication state."
    ),
    limit: int = typer.Option(50, "--limit", min=1, max=100),
    cursor: Optional[str] = typer.Option(None, "--cursor", help="Opaque pagination cursor."),
) -> None:
    """List Custom Tools owned by your organization."""
    state = ctx.obj
    with state.sdk_client() as client:
        page = client.custom_tools.list(
            status=status, published=published, limit=limit, cursor=cursor
        )
    result = {
        "items": [_tool(item) for item in page.items],
        "nextCursor": page.next_cursor,
    }
    rows = [
        {
            "name": item.name,
            "status": str(item.status),
            "published": "yes" if item.published else "",
            "defaultVersion": item.default_version or "",
            "updatedAt": item.updated_at,
        }
        for item in page.items
    ]
    human = output.render_table(
        rows, ["name", "status", "published", "defaultVersion", "updatedAt"]
    )
    if page.next_cursor:
        human += f"\n\nMore results: pass --cursor {page.next_cursor}"
    output.emit(result, state.output, human=human)


@app.command()
def get(ctx: typer.Context, name: str = typer.Argument(..., help="Custom Tool name.")) -> None:
    """Inspect one Custom Tool."""
    state = ctx.obj
    with state.sdk_client() as client:
        tool = client.custom_tools.get(name)
    output.emit(_tool(tool), state.output, human=_tool_human(tool))


@app.command()
def create(
    ctx: typer.Context,
    name: str = typer.Argument(..., help="Unique Custom Tool name."),
    display_name: Optional[str] = typer.Option(None, "--display-name"),
    description: Optional[str] = typer.Option(None, "--description"),
    gpu_type: Optional[GpuType] = typer.Option(None, "--gpu-type"),
    memory: Optional[MemorySize] = typer.Option(None, "--memory"),
    cpu: Optional[int] = typer.Option(None, "--cpu", min=1),
) -> None:
    """Create an empty Custom Tool ready for a source build."""
    state = ctx.obj
    kwargs: dict[str, object] = {}
    for key, value in (
        ("display_name", display_name),
        ("description", description),
        ("gpu_type", gpu_type),
        ("memory", memory),
        ("cpu", cpu),
    ):
        if value is not None:
            kwargs[key] = value
    with state.sdk_client() as client:
        tool = client.custom_tools.create(name, **kwargs)
    output.emit(_tool(tool), state.output, human=f"created {tool.name}\n{_tool_human(tool)}")


@app.command()
def update(
    ctx: typer.Context,
    name: str = typer.Argument(..., help="Custom Tool name."),
    display_name: Optional[str] = typer.Option(None, "--display-name"),
    description: Optional[str] = typer.Option(None, "--description"),
    function: Optional[list[str]] = typer.Option(None, "--function", help="Repeatable."),
    gpu_type: Optional[GpuType] = typer.Option(None, "--gpu-type"),
    memory: Optional[MemorySize] = typer.Option(None, "--memory"),
    cpu: Optional[int] = typer.Option(None, "--cpu", min=1),
    home_disk_gi: Optional[int] = typer.Option(None, "--home-disk-gi", min=1),
    auto_publish: Optional[bool] = typer.Option(
        None, "--auto-publish/--no-auto-publish"
    ),
    est_time: Optional[str] = typer.Option(None, "--est-time"),
    paper_url: Optional[str] = typer.Option(None, "--paper-url"),
    tag: Optional[list[str]] = typer.Option(None, "--tag", help="Repeatable."),
) -> None:
    """Update editable Custom Tool metadata and resource settings."""
    state = ctx.obj
    values: dict[str, object] = {
        "display_name": display_name,
        "description": description,
        "functions": function,
        "gpu_type": gpu_type,
        "memory": memory,
        "cpu": cpu,
        "home_disk_gi": home_disk_gi,
        "auto_publish": auto_publish,
        "est_time": est_time,
        "paper_url": paper_url,
        "tags": tag,
    }
    kwargs = {key: value for key, value in values.items() if value is not None}
    if not kwargs:
        raise ValidationError("No updates supplied.")
    with state.sdk_client() as client:
        tool = client.custom_tools.get(name).update(**kwargs)
    output.emit(_tool(tool), state.output, human=f"updated {tool.name}\n{_tool_human(tool)}")


@app.command()
def validate(
    ctx: typer.Context,
    folder: Path = typer.Argument(
        ..., exists=True, file_okay=False, readable=True, resolve_path=True
    ),
) -> None:
    """Validate a local Custom Tool source folder without uploading it."""
    state = ctx.obj
    report = validate_folder(folder)
    result = _report(report)
    rows = [
        {"severity": "error", **_problem(item)} for item in report.errors
    ] + [{"severity": "warning", **_problem(item)} for item in report.warnings]
    human = "valid" if report.valid and not rows else output.render_table(
        rows, ["severity", "code", "path", "message"]
    )
    output.emit(result, state.output, human=human)
    if not report.valid:
        raise typer.Exit(ExitCode.VALIDATION)


@app.command()
def build(
    ctx: typer.Context,
    name: str = typer.Argument(..., help="Custom Tool name."),
    folder: Path = typer.Argument(
        ..., exists=True, file_okay=False, readable=True, resolve_path=True
    ),
    idempotency_key: Optional[str] = typer.Option(
        None, "--idempotency-key", help="Reuse this key when retrying an ambiguous build request."
    ),
    wait: bool = typer.Option(False, "--wait", help="Wait for the build to finish."),
    timeout: float = typer.Option(1800.0, "--timeout", min=0.001),
    poll_interval: float = typer.Option(2.0, "--poll-interval", min=0.001),
) -> None:
    """Validate, package, upload, and build a local source folder."""
    state = ctx.obj
    with state.sdk_client() as client:
        result = client.custom_tools.get(name).build(
            folder, idempotency_key=idempotency_key
        )
        version = result.version
        if wait:
            try:
                version = version.monitor(
                    timeout=timeout,
                    interval=poll_interval,
                    on_event=_event_printer(state.output),
                )
            except TamarindError as exc:
                raise _attach_version_context(
                    exc, version=version, action=result.action
                ) from exc
    payload = {"action": _value(result.action), "version": _version(version)}
    human = f"{_value(result.action)}: {_version_human(version)}"
    if not wait and not version.terminal:
        human += (
            f"\n\nReattach with `tamarind custom-tools version {name} {version.id} --wait`."
        )
    output.emit(payload, state.output, human=human)


@app.command()
def versions(
    ctx: typer.Context,
    name: str = typer.Argument(..., help="Custom Tool name."),
    status: Optional[PublicVersionStatus] = typer.Option(None, "--status"),
    limit: int = typer.Option(50, "--limit", min=1, max=100),
    cursor: Optional[str] = typer.Option(None, "--cursor", help="Opaque pagination cursor."),
) -> None:
    """List a Custom Tool's build versions."""
    state = ctx.obj
    with state.sdk_client() as client:
        page = client.custom_tools.get(name).versions(
            status=status, limit=limit, cursor=cursor
        )
    result = {"items": [_version(item) for item in page.items], "nextCursor": page.next_cursor}
    rows = [
        {
            "id": item.id,
            "name": item.name,
            "status": str(item.status),
            "origin": item.origin,
            "createdAt": item.created_at,
        }
        for item in page.items
    ]
    human = output.render_table(rows, ["id", "name", "status", "origin", "createdAt"])
    if page.next_cursor:
        human += f"\n\nMore results: pass --cursor {page.next_cursor}"
    output.emit(result, state.output, human=human)


@app.command("version")
def get_version(
    ctx: typer.Context,
    name: str = typer.Argument(..., help="Custom Tool name."),
    version_id: str = typer.Argument(..., help="Opaque Version ID (not its vN display name)."),
    wait: bool = typer.Option(False, "--wait", help="Wait for this build to finish."),
    timeout: float = typer.Option(1800.0, "--timeout", min=0.001),
    poll_interval: float = typer.Option(2.0, "--poll-interval", min=0.001),
) -> None:
    """Inspect or wait for one exact Version."""
    state = ctx.obj
    with state.sdk_client() as client:
        version = _get_version(client, name, version_id)
        if wait:
            try:
                version = version.monitor(
                    timeout=timeout,
                    interval=poll_interval,
                    on_event=_event_printer(state.output),
                )
            except TamarindError as exc:
                raise _attach_version_context(exc, version=version) from exc
    output.emit(_version(version), state.output, human=_version_human(version))


@app.command()
def logs(
    ctx: typer.Context,
    name: str = typer.Argument(..., help="Custom Tool name."),
    version_id: str = typer.Argument(..., help="Opaque Version ID."),
    cursor: Optional[str] = typer.Option(None, "--cursor", help="Resume from this log cursor."),
) -> None:
    """Read one page of build logs for an exact Version."""
    state = ctx.obj
    with state.sdk_client() as client:
        page = _get_version(client, name, version_id).logs(cursor=cursor)
    result = {
        "items": [asdict(item) for item in page.items],
        "status": _value(page.status),
        "nextCursor": page.next_cursor,
        "error": asdict(page.error) if page.error is not None else None,
    }
    human = "\n".join(item.message for item in page.items) or "(no new logs)"
    if page.next_cursor:
        human += f"\n\nResume with --cursor {page.next_cursor}"
    output.emit(result, state.output, human=human)


@app.command()
def cancel(
    ctx: typer.Context,
    name: str = typer.Argument(..., help="Custom Tool name."),
    version_id: str = typer.Argument(..., help="Opaque Version ID."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation."),
) -> None:
    """Request cancellation of a queued or running build."""
    state = ctx.obj
    output.confirm_destructive(
        f"cancel Custom Tool build '{name}/{version_id}'", yes=yes, mode=state.output
    )
    with state.sdk_client() as client:
        version = _get_version(client, name, version_id).cancel()
    output.emit(_version(version), state.output, human=f"cancellation requested\n{_version_human(version)}")


@app.command()
def publish(
    ctx: typer.Context,
    name: str = typer.Argument(..., help="Custom Tool name."),
    version_id: str = typer.Argument(..., help="Opaque completed Version ID."),
) -> None:
    """Publish a completed Version as the tool's organization-wide default."""
    state = ctx.obj
    with state.sdk_client() as client:
        tool = _get_version(client, name, version_id).publish()
    output.emit(_tool(tool), state.output, human=f"published {name}/{version_id}\n{_tool_human(tool)}")


@app.command()
def delete(
    ctx: typer.Context,
    name: str = typer.Argument(..., help="Custom Tool name."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation."),
) -> None:
    """Delete a Custom Tool and release its name for reuse."""
    state = ctx.obj
    output.confirm_destructive(
        f"permanently delete Custom Tool '{name}'", yes=yes, mode=state.output
    )
    with state.sdk_client() as client:
        client.custom_tools.get(name).delete()
    output.emit({"ok": True, "name": name}, state.output, human=f"deleted {name}")
