"""Today's commands, on the v1 API.

Each function here is what a command does when v1 is selected: same name, same
flags, the v1 operation behind it, and the v1 fields in ``--json``. Calls go
through :mod:`.sdk`, never raw HTTP. A flag with no v1 meaning is refused with a
pointer to the v1 way, rather than ignored.
"""

from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any

import yaml

from ...errors import (
    ExitCode,
    JobTimeoutError,
    NotFoundError,
    TamarindError,
    UsageError,
    ValidationError,
)
from .. import output
from . import manifest, render, sdk

_ID_PREFIXES = ("job_", "batch_", "run_")
# A v1 id: a kind prefix and a UUID (with or without dashes). Anything else is a name,
# even one that happens to start with `job_`.
_ID = re.compile(r"^(job|batch|run)_[0-9a-fA-F]{8}-?(?:[0-9a-fA-F]{4}-?){3}[0-9a-fA-F]{12}$")
FINAL = {"Complete", "Stopped", "Failed"}


def _emit(body: Any, mode: Any, *, human: str | None = None) -> None:
    """Print a v1 answer with signed links redacted, as today's job output is."""
    output.emit(render.redact(body), mode, human=human)


def op(operation_id: str) -> dict[str, Any]:
    return manifest.operation(operation_id)


def call(client: Any, operation_id: str, *args: Any, **kwargs: Any) -> Any:
    return sdk.invoke(client, op(operation_id), *args, **kwargs)


def failed(job: dict[str, Any]) -> bool:
    """A final job that didn't complete (``Stopped`` or ``Failed``)."""
    return job.get("status") in FINAL and job.get("status") != "Complete"


def status_line(job: dict[str, Any]) -> str:
    text = f"{job.get('name') or job.get('id')}: {job.get('status')}"
    if job.get("lowPriority"):
        text += " (low priority)"
    reason = job.get("stopReason")
    if isinstance(reason, dict) and reason.get("message"):
        text += f" ({reason['message']})"
    return text


def resolve_id(
    client: Any,
    ref: str,
    *,
    kind: str | None = None,
    organization: bool = False,
    email: str | None = None,
) -> str:
    """A ``job_``/``batch_``/``run_`` id as given, or a name looked up with ``listJobs?name=``.

    ``organization``/``email`` look the name up across the organization
    (``scope=org``, ``createdBy``); the server answers where that isn't built yet.
    """
    ref = ref.strip()
    if _ID.match(ref):
        return ref
    query: dict[str, Any] = {"name": ref}
    if kind:
        query["kind"] = kind
    if organization or email:
        query["scope"] = "org"
    if email:
        query["createdBy"] = email
    page = call(client, "listJobs", **query)
    items = page.get("items") if isinstance(page, dict) else None
    if not items:
        what = kind or "job"
        raise NotFoundError(f"No {what} named '{ref}'.", detail={"name": ref})
    return str(items[0]["id"])


def refuse_run_for_one_file(job_id: str, what: str) -> None:
    """getJobFile reads a job's or a batch's file; a pipeline run's is a 404 there."""
    if job_id.startswith("run_"):
        raise UsageError(
            f"{what} reads one job's file; a pipeline run's outputs come as one zip "
            "(`tamarind results ID --download DIR`), or per step with `tamarind pipelines results`."
        )


def resolve_batch_or_run(client: Any, ref: str) -> str:
    """``--batch``: a batch or a pipeline run, by id or by name (today's flag takes both)."""
    ref = ref.strip()
    if _ID.match(ref):
        if ref.startswith("job_"):
            raise UsageError("--batch takes a batch_ or run_ id; cancel one job without --batch.")
        return ref
    # `name=` answers only the newest match, so ask per kind: a newer single job with
    # the same name must not hide the batch or run.
    found = [
        item
        for kind in ("batch", "pipeline")
        for item in (call(client, "listJobs", name=ref, kind=kind).get("items") or [])
    ]
    if not found:
        raise NotFoundError(f"No batch or pipeline run named '{ref}'.", detail={"name": ref})
    return str(max(found, key=lambda item: str(item.get("createdAt") or ""))["id"])


# -- identity ----------------------------------------------------------------


def me(state: Any) -> dict[str, Any]:
    with sdk.make_client(state) as client:
        return call(client, "getMe")


def rejected_key(exc: TamarindError) -> bool:
    """Whether an error means the key itself was refused (exit code 3)."""
    return exc.exit_code == ExitCode.AUTH


def key_works(state: Any, api_key: str) -> bool:
    if not api_key.strip():
        return False
    try:
        with sdk.make_client(state, api_key=api_key) as client:
            call(client, "getMe")
        return True
    except TamarindError as exc:
        if rejected_key(exc):
            return False
        raise


# -- tools ---------------------------------------------------------------------


def tools_list(
    state: Any,
    *,
    modality: str | None,
    function: str | None,
    search: str | None,
    custom: bool | None,
    finetune: bool | None = None,
    pipeline_tools: bool | None = None,
    limit: int | None = None,
    cursor: str | None = None,
) -> None:
    query = {
        "modality": modality,
        "function": function,
        "search": search,
        "custom": custom,
        "finetune": finetune,
        "pipelineTools": pipeline_tools,
    }
    query = {k: v for k, v in query.items() if v is not None}
    with sdk.make_client(state) as client:
        if limit is None and cursor is None:
            # Today's `tools` lists the whole catalog; keep that.
            page = sdk.collect(client, op("listTools"), **query)
        else:
            page = call(client, "listTools", limit=limit, cursor=cursor, **query)
    human = render.table(page["items"], ["name", "displayName", "modalities"])
    human += f"\n\n{len(page['items'])} tools. Use `tamarind schema <name>` for parameters."
    if page.get("nextCursor"):
        human += "\nMore results: pass --cursor with the nextCursor in --json."
    _emit(page, state.output, human=human)


def facets(state: Any, part: str) -> None:
    with sdk.make_client(state) as client:
        body = call(client, "getToolFacets")
    rows = body.get(part) or []
    _emit(body, state.output, human=render.table(rows))


def schema(state: Any, tool: str, *, example: bool) -> None:
    with sdk.make_client(state) as client:
        body = call(client, "getToolSchema", tool)
    if example:
        settings = body.get("example")
        # A tool with no settings has `{}` as its example, which is a runnable one.
        if not isinstance(settings, dict):
            raise NotFoundError(
                f"No runnable example is available for '{tool}'. "
                f"Run `tamarind schema {tool}` to see its settings."
            )
        _emit(
            {"tool": tool, "settings": settings},
            state.output,
            human=yaml.safe_dump(settings, sort_keys=False).rstrip(),
        )
        return
    props = ((body.get("schema") or {}).get("properties") or {}) if isinstance(body, dict) else {}
    required = set(((body.get("schema") or {}).get("required") or []))
    rows = [
        {
            "name": name,
            "type": spec.get("type") if isinstance(spec, dict) else None,
            "required": "yes" if name in required else "",
            "default": spec.get("default") if isinstance(spec, dict) else None,
            "description": (spec.get("description") or spec.get("title") or "")
            if isinstance(spec, dict)
            else "",
        }
        for name, spec in props.items()
    ]
    human = (
        f"{tool} (version {body.get('version')})\n\n"
        + output.render_table(rows, ["name", "type", "required", "default", "description"])
        + f"\n\nRun `tamarind schema {tool} --example` for example settings."
    )
    _emit(body, state.output, human=human)


# -- jobs ----------------------------------------------------------------------


def job_body(
    tool: str,
    settings: Any,
    *,
    name: str | None,
    low_priority: bool,
    kind: str = "job",
    names: list[str] | None = None,
    max_runtime: int | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {"kind": kind, "tool": tool, "settings": settings, **(extra or {})}
    if name:
        body["name"] = name
    if names is not None:
        body["names"] = names
    if max_runtime is not None:
        body["maxRuntimeSeconds"] = max_runtime
    if low_priority:
        body["lowPriority"] = True
    return body


def _validation_message(report: dict[str, Any]) -> str:
    errors = list(report.get("errors") or [])
    # A batch's report puts each row's errors under its result, with the row's index.
    for row in report.get("results") or []:
        if isinstance(row, dict) and not row.get("valid", True):
            for err in row.get("errors") or []:
                if isinstance(err, dict):
                    errors.append({**err, "pointer": f"row {row.get('index')} {err.get('pointer') or ''}".strip()})
    parts = []
    for err in errors[:5]:
        if isinstance(err, dict):
            where = err.get("pointer") or ""
            parts.append(f"{where} {err.get('detail') or err.get('code')}".strip())
    if len(errors) > 5:
        parts.append(f"and {len(errors) - 5} more")
    return "; ".join(parts) or "see --json"


def validate(state: Any, body: dict[str, Any]) -> None:
    with sdk.make_client(state) as client:
        report = call(client, "validateJob", body=body)
    valid = bool(report.get("valid"))
    human = "valid ✓" if valid else f"invalid ✗ {_validation_message(report)}"
    _emit(report, state.output, human=human)
    if not valid:
        import typer

        raise typer.Exit(ValidationError.exit_code)


def _wait(client: Any, job_id: str, state: Any, *, poll_interval: float, timeout: float | None) -> dict:
    return sdk.wait(
        client,
        job_id,
        poll_interval=poll_interval,
        timeout=timeout,
        on_poll=lambda job: output.info(f"  status: {job.get('status')}", state.output),
    )


def _remaining(deadline: float | None) -> float | None:
    return None if deadline is None else max(deadline - time.monotonic(), 0.0)


def _archive(
    client: Any, job_id: str, *, body: dict[str, Any] | None, wait: bool, timeout: float | None
) -> dict[str, Any]:
    """The archive's download link, waiting while it's prepared if asked to.

    A pipeline run's zip comes from ``archivePipelineRun``; ``archiveJob`` is for
    jobs and batches (a ``run_`` id there is 404).
    """
    operation = "archivePipelineRun" if job_id.startswith("run_") else "archiveJob"
    deadline = None if timeout is None else time.monotonic() + timeout
    while True:
        answer = call(client, operation, job_id, body=body or {})
        if not isinstance(answer, dict) or answer.get("status") != "preparing":
            return answer
        retry = max(int(answer.get("retryAfterSeconds") or 5), 1)
        if not wait:
            raise TamarindError(
                f"The archive is still being prepared; ask again in {retry} s, or pass --wait.",
                detail=answer,
            )
        if deadline is not None and time.monotonic() + retry > deadline:
            raise JobTimeoutError("Timed out waiting for the archive.", detail=answer)
        time.sleep(retry)


def _submit(client: Any, body: dict[str, Any], idempotency_key: str | None) -> dict[str, Any]:
    """``submitJob``; an unclear outcome comes back with the key to retry it safely
    (see :func:`.sdk.invoke`)."""
    return call(client, "submitJob", body=body, idempotency_key=idempotency_key)


def submit(
    state: Any,
    body: dict[str, Any],
    *,
    idempotency_key: str | None,
    wait: bool,
    poll_interval: float,
    timeout: float | None,
    download: Path | None,
) -> None:
    import typer

    from ..commands.jobs import _download

    deadline = None if timeout is None else time.monotonic() + timeout
    with sdk.make_client(state) as client:
        submitted = _submit(client, body, idempotency_key)
        if not wait:
            _emit(
                submitted,
                state.output,
                human=f"submitted: {submitted.get('name')} ({submitted.get('id')}, {submitted.get('status')})",
            )
            return
        result: dict[str, Any] = {"submit": submitted}
        output.info("Waiting for completion…", state.output)
        final = _wait(client, submitted["id"], state, poll_interval=poll_interval, timeout=timeout)
        result["final"] = final
        if download and final.get("status") == "Complete":
            link = _archive(client, final["id"], body=None, wait=True, timeout=_remaining(deadline))
            dest = download / Path(f"{final.get('name') or final['id']}.zip").name
            written = _download(link["downloadUrl"], dest)
            result["download"] = {"path": str(dest), "bytes": written}
            output.info(f"  downloaded {written} bytes → {dest}", state.output)
    _emit(result, state.output, human=status_line(final))
    if failed(final):
        raise typer.Exit(ExitCode.JOB_FAILED)


def batch(
    state: Any, body: dict[str, Any], *, prevalidate: bool, idempotency_key: str | None
) -> None:
    with sdk.make_client(state) as client:
        if prevalidate:
            report = call(client, "validateJob", body=body)
            if not report.get("valid"):
                raise ValidationError(
                    f"Batch settings invalid: {_validation_message(report)}", detail=report
                )
        submitted = _submit(client, body, idempotency_key)
    _emit(
        submitted,
        state.output,
        human=(
            f"submitted batch '{submitted.get('name')}' ({submitted.get('id')}, "
            f"{len(body['settings'])} jobs, {submitted.get('status')})"
        ),
    )


def jobs_list(
    state: Any,
    *,
    status: str | None,
    batch: str | None,
    limit: int,
    start_key: str | None,
    all_jobs: bool,
    organization: bool,
    include_subjobs: bool,
    email: str | None,
    filters: dict[str, Any] | None = None,
) -> None:
    if include_subjobs:
        raise UsageError("v1 lists a batch's jobs with --batch NAME_OR_ID, not --include-subjobs.")
    with sdk.make_client(state) as client:
        query: dict[str, Any] = {"limit": limit, **(filters or {})}
        if status:
            query["status"] = [s.strip() for s in status.split(",") if s.strip()]
        if batch:
            query["batchId"] = resolve_id(client, batch, kind="batch")
        if organization or email:
            query["scope"] = "org"
        if email:
            query["createdBy"] = email
        if start_key:
            query["cursor"] = start_key
        if all_jobs:
            page = sdk.collect(client, op("listJobs"), **query)
        else:
            page = call(client, "listJobs", **query)
    human = render.table(page["items"], ["id", "name", "tool", "status", "createdAt"])
    if page.get("nextCursor"):
        human += "\n\nMore results — re-run with --all, or --start-key with the nextCursor in --json."
    _emit(page, state.output, human=human)


def get(state: Any, ref: str, *, organization: bool = False, email: str | None = None) -> None:
    with sdk.make_client(state) as client:
        job = call(client, "getJob", resolve_id(client, ref, organization=organization, email=email))
    _emit(job, state.output, human=status_line(job))


def wait(
    state: Any,
    ref: str,
    *,
    poll_interval: float,
    timeout: float | None,
    organization: bool = False,
    email: str | None = None,
) -> None:
    import typer

    with sdk.make_client(state) as client:
        job_id = resolve_id(client, ref, organization=organization, email=email)
        final = _wait(client, job_id, state, poll_interval=poll_interval, timeout=timeout)
    _emit(final, state.output, human=status_line(final))
    if failed(final):
        raise typer.Exit(ExitCode.JOB_FAILED)


def results(
    state: Any,
    ref: str,
    *,
    download: Path | None,
    file: str | None,
    pdbs_only: bool,
    show_url: bool,
    wait: bool,
    poll_interval: float,
    timeout: float | None,
    organization: bool = False,
    email: str | None = None,
) -> None:
    import typer

    from ..commands.jobs import _download

    if file and pdbs_only:
        raise UsageError("--file and --pdbs-only can't be combined.")
    deadline = None if timeout is None else time.monotonic() + timeout
    with sdk.make_client(state) as client:
        job_id = resolve_id(client, ref, organization=organization, email=email)
        result: dict[str, Any] = {"id": job_id}
        if wait:
            output.info("Waiting for completion…", state.output)
            final = _wait(client, job_id, state, poll_interval=poll_interval, timeout=timeout)
            result["final"] = final
            if failed(final):
                _emit(result, state.output, human=status_line(final))
                raise typer.Exit(ExitCode.JOB_FAILED)
        if file:
            refuse_run_for_one_file(job_id, "--file")
            link = call(client, "getJobFile", job_id, path=file, delivery="url")
            url = link["url"]
            name = Path(file).name
        else:
            # `--pdbs-only` is the archive's `glob`; the server answers 422 `not_supported`
            # until choosing files is built, and honors it from then on.
            link = _archive(
                client,
                job_id,
                body={"glob": "*.pdb"} if pdbs_only else None,
                wait=wait,
                timeout=_remaining(deadline),
            )
            url = link["downloadUrl"]
            name = f"{job_id if _ID.match(ref.strip()) else ref}.zip"
    if download:
        dest = download / Path(name).name
        written = _download(url, dest)
        result["download"] = {"path": str(dest), "bytes": written}
        _emit(result, state.output, human=str(dest))
    else:
        shown = render.redact(result)
        shown["url"] = url  # asked for with --show-url
        output.emit(shown, state.output, human=url)


def logs(
    state: Any, ref: str, *, max_lines: int, max_bytes: int | None = None, cursor: str | None = None
) -> None:
    if max_lines < 1:
        raise UsageError("--max-lines must be at least 1.")
    with sdk.make_client(state) as client:
        chunk = call(client, "getJobLogs", resolve_id(client, ref), maxBytes=max_bytes, cursor=cursor)
    content = chunk.get("content") or ""
    lines = content.splitlines(keepends=True)
    if len(lines) > max_lines:
        # --max-lines keeps the newest lines in both output modes; `omittedLines` says
        # how many of this window's older lines were left out (read them without it).
        chunk = {**chunk, "content": "".join(lines[-max_lines:]), "omittedLines": len(lines) - max_lines}
    text = chunk.get("content") or ""
    _emit(chunk, state.output, human=text.rstrip("\n") or "(no log yet)")


def cancel(state: Any, ref: str | None, batch: str | None, *, reason: str | None = None) -> None:
    with sdk.make_client(state) as client:
        target = resolve_batch_or_run(client, batch) if batch else resolve_id(client, ref or "")
        job = call(client, "cancelJob", target, body={"reason": reason} if reason else {})
    _emit(job, state.output, human=status_line(job))


def delete(state: Any, ref: str) -> None:
    with sdk.make_client(state) as client:
        job_id = resolve_id(client, ref)
        call(client, "deleteJob", job_id)
    _emit({"id": job_id, "deleted": True}, state.output, human=f"deleted {job_id}")


# -- files ---------------------------------------------------------------------


def files_list(
    state: Any,
    *,
    types: str | None,
    search: str | None,
    folder: str | None,
    limit: int,
    offset: int,
    all_dirs: bool,
    cursor: str | None = None,
    all_pages: bool = False,
) -> None:
    if offset:
        raise UsageError("v1 pages files with --cursor (the nextCursor in --json), not --offset.")
    query: dict[str, Any] = {"limit": limit}
    if types:
        query["extension"] = [t.strip() for t in types.split(",") if t.strip()]
    if search:
        query["search"] = search
    if folder:
        query["folder"] = folder
    if all_dirs:
        query["recursive"] = True
    if cursor:
        query["cursor"] = cursor
    with sdk.make_client(state) as client:
        page = sdk.collect(client, op("listFiles"), **query) if all_pages else call(client, "listFiles", **query)
    human = render.table(page["items"], ["path", "type", "sizeBytes", "modifiedAt"])
    if page.get("nextCursor"):
        human += "\n\nMore results: pass --cursor with the nextCursor in --json."
    _emit(page, state.output, human=human)


def files_folders(state: Any, *, limit: int, all_folders: bool, folder: str | None = None) -> None:
    """The folders of a listing. v1 lists files and folders together (at the root,
    uploads first), so this reads pages until it has ``limit`` folders, or all of them."""
    if not all_folders and limit < 1:
        raise UsageError("--limit must be at least 1.")
    query: dict[str, Any] = {"limit": 200}
    if folder:
        query["folder"] = folder
    folders: list[dict[str, Any]] = []
    with sdk.make_client(state) as client:
        for item in client.paginate(sdk.method(client, op("listFiles")["sdk"]), **query):
            if isinstance(item, dict) and item.get("type") == "folder":
                folders.append(item)
                if not all_folders and len(folders) >= limit:
                    break
    out = {"items": folders, "nextCursor": None}
    _emit(out, state.output, human="\n".join(str(f.get("path")) for f in folders) or "(none)")


def files_stats(state: Any, *, folder: str | None) -> None:
    with sdk.make_client(state) as client:
        body = call(client, "getFileStats", folder=folder)
    by_ext = body.get("byExtension") or {}
    rows = (
        [{"extension": k or "(none)", "count": v} for k, v in by_ext.items()]
        if isinstance(by_ext, dict)
        else by_ext
    )
    human = render.table(rows) + f"\n\n{body.get('fileCount')} files total."
    _emit(body, state.output, human=human)


def files_upload(state: Any, path: Path, remote: str) -> None:
    with sdk.make_client(state) as client:
        result = sdk.upload(client, path, remote)
    _emit(result, state.output, human=f"uploaded {remote}")


def files_delete(state: Any, path: str | None, folder: str | None) -> None:
    with sdk.make_client(state) as client:
        call(client, "deleteFile", path=path, folder=folder)
    target = path or folder
    _emit({"deleted": target}, state.output, human=f"deleted {target}")


def download_link(
    state: Any, operation_id: str, *args: str, path: str, dest: Path | None, show_url: bool
) -> None:
    """``files download`` / ``jobs download``: fetch a file's link and save it, or print it."""
    from ..commands.jobs import _download

    with sdk.make_client(state) as client:
        link = call(client, operation_id, *args, path=path, delivery="url")
    if show_url:
        output.emit(link, state.output, human=link["url"])  # asked for with --show-url
        return
    target = dest or Path(".")
    if target.is_dir() or str(target).endswith(("/", "\\")):
        target = target / Path(path).name
    written = _download(link["url"], target)
    _emit({"path": str(target), "bytes": written}, state.output, human=str(target))
