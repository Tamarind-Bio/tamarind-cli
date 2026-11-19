"""Today's commands on the v1 API.

With v1 selected, every command the CLI already had keeps its classic code (its flags,
its human and ``--json`` layout, its exit codes) and its requests go to v1 instead.
:class:`ClassicOverV1` stands in for the classic :class:`~tamarind.http.HTTPClient`,
and :class:`CatalogOverV1` for the catalog client's job logs: each classic request is
answered by the v1 operation behind it, and v1's answer is rebuilt into the layout
classic returns. A field v1 doesn't have is left out; docs/v1-mode.md lists those
differences.

There is no fallback. What v1 refuses is raised as v1's error (a ``ProblemError``,
whose exit code follows the CLI's table), so a run with v1 selected shows what v1
does. The few requests v1 has no form for yet go to classic on purpose
(:class:`OnClassic`): the catalog, another member's jobs (``--organization`` /
``--email``), a list with ``--include-subjobs``, ``results --pdbs-only``, and the logs
of anything but a single job.

A v1 failure with no answer, a 5xx or a 409 ``idempotency_in_progress`` is raised the
way the classic client raises one, so the commands' own "outcome may be ambiguous"
handling applies unchanged.
"""

from __future__ import annotations

import json
import re
import time
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4
from typing import Any, Callable, Iterator

import click

from ...custom_tools.resources import CustomTool, CustomToolTestJob
from ...errors import (
    APIError,
    CustomToolNotDeployableError,
    JobTimeoutError,
    NotFoundError,
    TamarindError,
    ValidationError,
)
from ...http import HTTPClient
from . import sdk

# What submit-job and submit-batch append for a low-priority job (classic's
# `lowPrioritySubmittedSuffix(true)`, src/lib/jobs/lowPriority.js).
LOW_PRIORITY_SUFFIX = (
    " at low priority (20% off, no completion guarantee, and a job not started within "
    "7 days stops with no charge)"
)
FINAL = ("Complete", "Stopped", "Failed")


class OnClassic(Exception):
    """v1 has no form for this request yet: it goes to classic."""


def _classic_error(exc: TamarindError) -> TamarindError:
    """A v1 failure raised the way the classic client raises one.

    A 5xx becomes an :class:`APIError` with its status; a failure with no answer, or a
    409 ``idempotency_in_progress``, a plain :class:`TamarindError`, which is what the
    commands read as "the outcome may be ambiguous". Any other error is v1's own answer
    and keeps its exit code.
    """
    status = getattr(exc, "status", None)
    if getattr(exc, "code", None) == "idempotency_in_progress":
        return TamarindError(exc.message, detail=getattr(exc, "problem", None))
    if isinstance(status, int) and status >= 500:
        return APIError(exc.message, status_code=status, detail=getattr(exc, "problem", None))
    return exc


Route = tuple[Callable[..., Any], tuple[str, ...]]


class _OverV1:
    """A classic client's interface, answering the requests :meth:`_route` names from v1."""

    def __init__(self, state: Any, classic: HTTPClient):
        self._state = state
        self._classic = classic
        self.base_url = classic.base_url
        self.api_key = classic.api_key
        self._v1: Any = None
        self._items: dict[tuple[str, tuple[str, ...]], dict[str, Any]] = {}
        self._names: dict[str, str] = {}
        # When the command began: its --timeout counts from here, across every wait.
        self.started = time.monotonic()

    def close(self) -> None:
        self._classic.close()
        if self._v1 is not None:
            self._v1.__exit__(None, None, None)

    def __enter__(self) -> Any:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def v1(self) -> Any:
        if self._v1 is None:
            self._v1 = sdk.make_client(self._state)
        return self._v1

    def get_json(
        self, path: str, *, params: dict[str, Any] | None = None, timeout: float | None = None
    ) -> Any:
        return self._serve(
            "GET",
            path,
            params,
            lambda: self._classic.get_json(path, params=params, timeout=timeout),
            timeout=timeout,
        )

    def post_json(self, path: str, *, json: Any | None = None) -> Any:
        return self._serve("POST", path, json, lambda: self._classic.post_json(path, json=json))

    def delete_json(
        self, path: str, *, params: dict[str, Any] | None = None, json: Any | None = None
    ) -> Any:
        payload = json if json is not None else params
        return self._serve(
            "DELETE", path, payload, lambda: self._classic.delete_json(path, params=params, json=json)
        )

    def _route(self, method: str, path: str) -> Route | None:
        raise NotImplementedError

    def _serve(
        self,
        method: str,
        path: str,
        payload: Any,
        classic: Callable[[], Any],
        *,
        timeout: float | None = None,
    ) -> Any:
        route = self._route(method, path.strip("/"))
        # No key: classic's client says so, in its words, before sending anything.
        if route is None or not self.api_key:
            return classic()
        handler, args = route
        try:
            with self._bounded(timeout):
                return handler(self, *args, payload if isinstance(payload, dict) else {})
        except OnClassic:
            return classic()
        except TamarindError as exc:
            raise _classic_error(exc) from exc

    @contextmanager
    def _bounded(self, timeout: float | None) -> Iterator[None]:
        """A request its caller bounds (a wait's remaining deadline) is sent the way
        classic's client sends it: one try of at most ``timeout`` seconds, not the SDK's
        retries, which could run past the deadline."""
        if timeout is None:
            yield
            return
        saved = self._v1
        self._v1 = sdk.make_client(self._state, timeout=max(float(timeout), 0.001), max_retries=0)
        try:
            yield
        finally:
            self._v1.__exit__(None, None, None)
            self._v1 = saved

    # -- lookups -----------------------------------------------------------

    def find(self, name: Any, kinds: tuple[str, ...] = ()) -> dict[str, Any] | None:
        """The caller's own job, batch or run named ``name`` (classic looks names up among
        the caller's own jobs), of one of ``kinds`` if given; None when there is none.
        Remembered for this client's life, so a wait doesn't look it up on every poll."""
        if not isinstance(name, str) or not name:
            return None
        key = (name, kinds)
        if key not in self._items:
            found: list[dict[str, Any]] = []
            for kind in kinds or (None,):
                query = {"name": name, **({"kind": kind} if kind else {})}
                page = sdk.plain(self.v1().jobs.list(**query))
                found.extend((page or {}).get("items") or [])
            if not found:
                return None
            self._items[key] = max(found, key=lambda item: str(item.get("createdAt") or ""))
        return self._items[key]

    def name_of(self, item_id: str) -> str | None:
        """A batch's (or run's) name, from its id."""
        if item_id not in self._names:
            self._names[item_id] = str(sdk.plain(self.v1().jobs.get(item_id)).get("name") or "")
        return self._names[item_id] or None


# -- job rows -------------------------------------------------------------------------


def stamp(value: Any) -> str | None:
    """v1's RFC 3339 time as classic writes it: ``2026-11-19 05:27:02``."""
    if not isinstance(value, str) or not value:
        return None
    text = value.replace("T", " ")
    return re.split(r"[.Z+]", text, maxsplit=1)[0] if len(text) >= 19 else text


def job_row(item: dict[str, Any], *, batch_name: str | None = None) -> dict[str, Any]:
    """A v1 job, batch or run as classic's job row (``legacy_jobs.summary``'s fields, in
    its order). v1 has no ``TamarindSchemaVersion``, ``StorageFolder``, ``User`` or a
    batch's ``resultUrl``, so those are left out; ``Settings`` is there when v1 sent the
    settings (a single job's read, not a list)."""
    kind = item.get("kind")
    row: dict[str, Any] = {
        "JobName": item.get("name"),
        "JobStatus": item.get("status"),
        "Created": stamp(item.get("createdAt")),
        "Type": "batch" if kind == "batch" else (item.get("tool") if kind == "job" else kind),
    }
    if kind == "batch":
        if item.get("tool"):
            row["Settings"] = item["tool"]  # classic's batch row carries the tool name there
    elif item.get("settings") is not None:
        row["Settings"] = json.dumps(item["settings"], separators=(",", ":"))
    if item.get("scores") is not None:
        row["Score"] = json.dumps(item["scores"])
    for source, wire in (("startedAt", "Started"), ("completedAt", "Completed")):
        if item.get(source):
            row[wire] = stamp(item[source])
    if batch_name:
        row["Batch"] = batch_name
    if isinstance(item.get("weightedHours"), (int, float)):
        row["WeightedHours"] = round(item["weightedHours"], 2)
    if kind == "batch":
        row["batchStatus"] = item.get("status")
    if item.get("lowPriority"):
        row["LowPriority"] = True
        reason = item.get("stopReason")
        if isinstance(reason, dict) and reason.get("message"):
            row["StoppedReasonUserFacing"] = reason["message"]
    return row


def statuses(rows: list[dict[str, Any]]) -> dict[str, int]:
    """Classic's per-answer counts: always these four keys."""
    keys = ("Complete", "In Queue", "Running", "Stopped")
    return {key: sum(1 for row in rows if row.get("JobStatus") == key) for key in keys}


def get_jobs(client: _OverV1, params: dict[str, Any]) -> dict[str, Any]:
    """GET /jobs: one job by name (getJob), or a page (listJobs)."""
    if params.get("organization") or params.get("jobEmail") or params.get("includeSubjobs"):
        raise OnClassic  # another member's jobs (website#7795); subjobs mixed into the list
    name = params.get("jobName")
    if name:
        found = client.find(name)
        if found is None:
            raise NotFoundError(f"Job {name} not found")
        job = sdk.plain(client.v1().jobs.get(found["id"]))
        batch = client.name_of(job["batchId"]) if job.get("batchId") else None
        row = job_row(job, batch_name=batch)
        return {**row, "statuses": statuses([row])}
    query: dict[str, Any] = {"limit": params.get("limit")}
    if params.get("startKey"):
        query["cursor"] = params["startKey"]
    batch_name = None
    if params.get("batch"):
        parent = client.find(params["batch"], kinds=("batch", "pipeline"))
        if parent is None:
            return {"jobs": [], "statuses": statuses([])}
        key = "pipeline_run_id" if parent.get("kind") == "pipeline" else "batch_id"
        query[key], batch_name = parent["id"], parent.get("name")
    page = sdk.plain(client.v1().jobs.list(**{k: v for k, v in query.items() if v is not None}))
    rows = [job_row(item, batch_name=batch_name) for item in page.get("items") or []]
    out: dict[str, Any] = {"jobs": rows}
    if page.get("nextCursor"):
        out["startKey"] = page["nextCursor"]
    out["statuses"] = statuses(rows)
    return out


# -- validate -----------------------------------------------------------------------


def _field(pointer: Any, *, row: bool = False) -> str | None:
    """The setting a v1 pointer names: ``/settings/x`` → ``x``; a batch row's
    ``/settings/17/x`` → ``x`` too."""
    parts = [p for p in str(pointer or "").split("/") if p]
    if parts[:1] == ["settings"]:
        parts = parts[1:]
        if row and parts[:1] and parts[0].isdigit():
            parts = parts[1:]
    return ".".join(parts) or None


def _classic_errors(errors: list[Any], *, row: bool = False) -> dict[str, Any]:
    """v1's ``errors[]`` as classic's ``error``, ``errors[{rule, field, message}]``,
    ``unrecognized_settings`` and ``missing_fields`` (of one batch row with ``row``)."""
    items = [e for e in errors if isinstance(e, dict)]
    out: dict[str, Any] = {
        "error": "; ".join(str(e.get("detail") or e.get("code")) for e in items) or "Settings invalid",
        "errors": [
            {
                "rule": e.get("code"),
                "field": _field(e.get("pointer"), row=row),
                "message": e.get("detail"),
                **({"suggestion": e["suggestion"]} if e.get("suggestion") else {}),
            }
            for e in items
        ],
    }
    unknown = [_field(e.get("pointer"), row=row) for e in items if e.get("code") == "unknown_field"]
    if unknown:
        out["unrecognized_settings"] = unknown
    missing = [_field(e.get("pointer"), row=row) for e in items if e.get("code") in ("missing_field", "required")]
    if missing:
        out["missing_fields"] = [{"name": name} for name in missing]
    return out


def validate_job(client: _OverV1, body: dict[str, Any]) -> dict[str, Any]:
    """POST /validate-job → validateJob, the report rebuilt as classic's verdict."""
    settings, tool = body.get("settings"), body.get("type")
    if isinstance(settings, list):
        request: dict[str, Any] = {"kind": "batch", "tool": tool, "settings": settings}
        if body.get("jobNames") is not None:
            request["names"] = body["jobNames"]
        report = sdk.plain(client.v1().jobs.validate(body=request))
        rows = report.get("results")
        if report.get("errors") or not isinstance(rows, list):
            # A problem with the batch as a whole: classic's {valid: false, error}, no rows.
            return {"valid": False, "error": _classic_errors(report.get("errors") or [])["error"]}
        # v1 lists only the rows with an error or a warning; classic answers for every row.
        # When v1 cut its list short, the rows it left out are unknown, so they get no
        # verdict and the CLI refuses the batch rather than pass rows nobody checked.
        listed = {row.get("index"): row for row in rows if isinstance(row, dict)}
        indexes = sorted(i for i in listed if isinstance(i, int)) if report.get("resultsTruncated") else range(
            int(report.get("count") or len(settings))
        )
        results = []
        for index in indexes:
            row = listed.get(index) or {"valid": True}
            verdict: dict[str, Any] = {"index": index, "valid": bool(row.get("valid"))}
            if not verdict["valid"]:
                verdict.update(_classic_errors(row.get("errors") or [], row=True))
            results.append(verdict)
        return {
            "valid": all(r["valid"] for r in results) and not report.get("errors"),
            "count": len(results),
            "valid_count": sum(1 for r in results if r["valid"]),
            "results": results,
        }
    request = {"kind": "job", "tool": tool, "settings": settings}
    if body.get("jobName"):
        request["name"] = body["jobName"]
    report = sdk.plain(client.v1().jobs.validate(body=request))
    if report.get("valid"):
        out: dict[str, Any] = {"valid": True}
        if report.get("normalized") is not None:
            out["normalized"] = report["normalized"]
        out["job_name"] = report.get("name") or body.get("jobName")
        return out
    return {"valid": False, **_classic_errors(report.get("errors") or [])}


# -- submit -------------------------------------------------------------------------


def _submit(client: _OverV1, request: dict[str, Any], name: str) -> None:
    try:
        client.v1().jobs.submit(body=request)
    except TamarindError as exc:
        if getattr(exc, "code", None) == "job_name_conflict":
            # v1's 409 for a name you already use; classic answers it as a 400 in these words.
            raise ValidationError(f"jobName {name} already exists, please choose a different name") from exc
        raise


def submit_job(client: _OverV1, body: dict[str, Any]) -> str:
    """POST /submit-job → submitJob; classic answers ``<name> submitted to queue.``"""
    name = body.get("jobName")
    request: dict[str, Any] = {"kind": "job", "tool": body.get("type"), "name": name, "settings": body.get("settings")}
    low_priority = body.get("lowPriority") is True
    if low_priority:
        request["lowPriority"] = True
    _submit(client, request, str(name))
    return f"{name} submitted to queue{LOW_PRIORITY_SUFFIX if low_priority else ''}."


def submit_batch(client: _OverV1, body: dict[str, Any]) -> str:
    """POST /submit-batch → submitJob (kind batch); classic answers
    ``<name> batch submitted to queue.``"""
    name = body.get("batchName")
    request: dict[str, Any] = {"kind": "batch", "tool": body.get("type"), "name": name, "settings": body.get("settings")}
    if body.get("jobNames") is not None:
        request["names"] = body["jobNames"]
    if body.get("maxRuntimeSeconds") is not None:
        request["maxRuntimeSeconds"] = body["maxRuntimeSeconds"]
    low_priority = body.get("lowPriority") is True
    if low_priority:
        request["lowPriority"] = True
    _submit(client, request, str(name))
    return f"{name} batch submitted to queue{LOW_PRIORITY_SUFFIX if low_priority else ''}."


# -- cancel -------------------------------------------------------------------------


def _uuid(item_id: str) -> str:
    return item_id.split("_", 1)[1] if "_" in item_id else item_id


def _cancel_many(client: _OverV1, item: dict[str, Any], *, cascaded: bool) -> dict[str, Any]:
    """Cancel a batch or run: classic's answer, its counts read from v1 just before."""
    before = sdk.plain(client.v1().jobs.get(item["id"]))
    counts = before.get("counts") or {}
    live = int(counts.get("inQueue") or 0) + int(counts.get("running") or 0)
    parent_live = before.get("status") not in FINAL
    after = sdk.plain(client.v1().jobs.cancel(item["id"], body={}))
    name = item.get("name")
    cancelled = live + (1 if parent_live else 0)
    out: dict[str, Any] = {
        "success": True,
        "message": f'Cancelled {cancelled} job{"" if cancelled == 1 else "s"} in batch "{name}"',
        "batchName": name,
    }
    if cascaded:
        out["cascaded"] = True
    out.update(
        {
            "cancelledCount": cancelled,
            "totalChildren": int(counts.get("total") or 0),
            "cancellableChildren": live,
            "parentCancelled": parent_live,
            "status": after.get("status") or "Stopped",
        }
    )
    return out


def cancel_job(client: _OverV1, body: dict[str, Any]) -> dict[str, Any]:
    """POST /cancelJob → cancelJob; a batch or run name cancels all of it, as classic does."""
    name = body.get("jobName")
    if not name:
        raise OnClassic  # by row id: v1 takes its own ids
    item = client.find(name)
    if item is None:
        raise NotFoundError(f"Job {name} not found")
    if item.get("kind") != "job":
        return _cancel_many(client, item, cascaded=True)
    job = sdk.plain(client.v1().jobs.cancel(item["id"], body={}))
    return {
        "success": True,
        "message": "Job cancelled successfully",
        "jobId": _uuid(item["id"]),
        "cancelledJobs": [
            {
                "Id": _uuid(item["id"]),
                "Created": stamp(job.get("createdAt") or item.get("createdAt")),
                "JobName": name,
                "Type": job.get("tool") or item.get("tool"),
                "User": job.get("createdBy") or item.get("createdBy"),
            }
        ],
        "status": job.get("status") or "Stopped",
    }


def cancel_batch(client: _OverV1, body: dict[str, Any]) -> dict[str, Any]:
    """POST /cancelBatch → cancelJob on the batch or run."""
    name = body.get("batchName")
    item = client.find(name, kinds=("batch", "pipeline"))
    if item is None:
        raise NotFoundError(f'No batch or pipeline named "{name}" found for this user')
    return _cancel_many(client, item, cascaded=False)


# -- results, delete --------------------------------------------------------------------


def _not_complete(name: Any, item: dict[str, Any]) -> ValidationError:
    return ValidationError(f"Job {name} is not complete. Status: {item.get('status')}")


def _waiting() -> tuple[bool, float | None]:
    """Whether the command asked to wait (``--wait``), and its ``--timeout``."""
    ctx = click.get_current_context(silent=True)
    params = ctx.params if ctx is not None else {}
    timeout = params.get("timeout")
    return bool(params.get("wait")), float(timeout) if isinstance(timeout, (int, float)) else None


def _retry_after(exc: Exception, default: float) -> float:
    """The seconds an error's ``Retry-After`` asks for (``default`` if it gives none)."""
    headers = getattr(exc, "headers", None)
    try:
        return max(float(headers.get("retry-after")), 1.0) if headers else default
    except (TypeError, ValueError):
        return default


def _archive(client: _OverV1, item: dict[str, Any]) -> dict[str, Any]:
    v1 = client.v1()
    if item.get("kind") == "pipeline":
        return sdk.plain(v1.pipelines.archive_run(item["id"], body={}))
    return sdk.plain(v1.jobs.archive(item["id"], body={}))


def result(client: _OverV1, body: dict[str, Any]) -> str:
    """POST /result → archiveJob (archivePipelineRun for a run, getJobFile for
    ``fileName``); classic answers the signed link. v1's archive is the stored
    ``result-<folder>.zip`` classic serves, so the bytes are the same (the link itself is
    v1's, signed for the global endpoint).

    v1 can call a batch Complete before its archive is built, where classic's wait covers
    the build. So under ``--wait`` a Complete item whose archive is still preparing is
    asked again after ``retryAfterSeconds``, until it is ready or ``--timeout`` passes."""
    if body.get("jobEmail") is not None or body.get("pdbsOnly"):
        raise OnClassic  # another member's job (website#7795); best structures (not on v1 yet)
    name = body.get("jobName")
    item = client.find(name)
    if item is None:
        raise NotFoundError(f"Job {name} not found")
    file_name = body.get("fileName")
    if file_name:
        if item.get("kind") == "pipeline":
            raise OnClassic  # getJobFile takes a job or a batch; one file of a run has no v1 form
        link = sdk.plain(client.v1().jobs.get_file(item["id"], path=file_name, delivery="url"))
        return str(link.get("url"))
    wait, timeout = _waiting()
    deadline = None if timeout is None else client.started + timeout
    def remaining() -> float | None:
        """What's left of --timeout under --wait (each request is bounded by it); None if unbounded."""
        if not wait or deadline is None:
            return None
        left = deadline - time.monotonic()
        if left <= 0:
            raise JobTimeoutError(f"The results archive of {name} wasn't ready when --timeout passed.")
        return left

    def pause(delay: float, detail: Any) -> None:
        if deadline is not None and time.monotonic() + delay > deadline:
            raise JobTimeoutError(
                f"The results archive of {name} wasn't ready when --timeout passed.", detail=detail
            )
        time.sleep(delay)

    rebuilds = 0
    while True:
        try:
            with client._bounded(remaining()):
                answer = _archive(client, item)
        except TamarindError as exc:
            code = getattr(exc, "code", None)
            if code == "archive_failed" and item.get("kind") == "pipeline" and wait and rebuilds < 3:
                # archivePipelineRun's archive_failed is retryable: the results service builds
                # the zip of a finished run again after Retry-After (90 s). Asked a few times.
                with client._bounded(remaining()):
                    current = sdk.plain(client.v1().jobs.get(item["id"]))
                if current.get("status") != "Complete":
                    raise _not_complete(name, current) from exc
                rebuilds += 1
                pause(_retry_after(exc, 90.0), None)
                continue
            if code == "archive_failed" and item.get("status") != "Complete":
                raise _not_complete(name, item) from exc  # classic's words for a Stopped/Failed job
            raise
        if not (isinstance(answer, dict) and answer.get("status") == "preparing"):
            return str(answer.get("downloadUrl"))
        with client._bounded(remaining()):
            current = sdk.plain(client.v1().jobs.get(item["id"]))
        if current.get("status") != "Complete":
            raise _not_complete(name, current)
        delay = max(float(answer.get("retryAfterSeconds") or 5), 1.0)
        if not wait:
            raise TamarindError(
                f"The results archive is still being prepared; try again in {delay:g} s.", detail=answer
            )
        pause(delay, answer)


def delete_job(client: _OverV1, body: dict[str, Any]) -> str:
    """DELETE /delete-job → deleteJob; classic answers ``<name> deleted``."""
    name = body.get("jobName")
    item = client.find(name, kinds=("job", "batch"))  # deleteJob takes a job or a batch
    if item is None:
        if client.find(name) is not None:
            raise OnClassic  # only a pipeline run has this name: v1 has no delete for one
        raise NotFoundError(f"{name} does not exist")
    client.v1().jobs.delete(item["id"])
    return f"{name} deleted"


# -- files ----------------------------------------------------------------------------


def _entries(client: _OverV1, **query: Any) -> Any:
    v1 = client.v1()
    return (sdk.plain(entry) for entry in v1.paginate(v1.files.list, limit=200, **query))


def get_files(client: _OverV1, params: dict[str, Any]) -> list[str]:
    """GET /files → listFiles: the folder's files (not folders, not zips) by path, in
    classic's order: the five newest first, then the rest by name."""
    folder = params.get("folder") or None
    files = [
        e
        for e in _entries(client, **({"folder": folder} if folder else {}))
        if e.get("type") == "file" and not str(e.get("path", "")).endswith(".zip")
    ]
    files.sort(key=lambda e: str(e.get("modifiedAt") or ""), reverse=True)
    rest = sorted(files[5:], key=lambda e: (str(e.get("path")).casefold(), str(e.get("path"))))
    return [str(e.get("path")) for e in files[:5] + rest]


def get_folders(client: _OverV1, params: dict[str, Any]) -> dict[str, Any]:
    """GET /getFolders → listFiles' folder entries at the root."""
    limit = None if params.get("loadAll") else int(params.get("limit") or 20)
    folders: list[str] = []
    more = False
    for entry in _entries(client):
        if entry.get("type") != "folder":
            continue
        if limit is not None and len(folders) >= limit:
            more = True
            break
        folders.append(str(entry.get("path")))
    return {"folders": folders, "hasMore": more}


def delete_file(client: _OverV1, params: dict[str, Any]) -> dict[str, str]:
    """DELETE /delete-file → deleteFile; classic answers ``{message}``."""
    path, folder = params.get("filePath"), params.get("folder")
    if path and folder:
        raise OnClassic  # v1 takes exactly one; classic decides, as it does today
    if folder:
        client.v1().files.delete(folder=folder)
        return {"message": "Folder deleted successfully"}
    client.v1().files.delete(path=path)
    return {"message": "File deleted successfully"}


_JOB_API: dict[tuple[str, str], Callable[..., Any]] = {
    ("GET", "jobs"): get_jobs,
    ("POST", "validate-job"): validate_job,
    ("POST", "submit-job"): submit_job,
    ("POST", "submit-batch"): submit_batch,
    ("POST", "cancelJob"): cancel_job,
    ("POST", "cancelBatch"): cancel_batch,
    ("POST", "result"): result,
    ("DELETE", "delete-job"): delete_job,
    ("GET", "files"): get_files,
    ("GET", "getFolders"): get_folders,
    ("DELETE", "delete-file"): delete_file,
}


class ClassicOverV1(_OverV1):
    """The job API (``State.rest_client()``) with v1 selected."""

    def __init__(self, state: Any):
        cfg = state.config()
        super().__init__(state, HTTPClient(cfg.api_base, cfg.api_key))

    def _route(self, method: str, path: str) -> Route | None:
        handler = _JOB_API.get((method, path))
        return (handler, ()) if handler else None


# -- logs (the catalog client) --------------------------------------------------------------

_LOGS = re.compile(r"^catalog/jobs/(?P<name>.+)/logs$")


# The most of a job's log one classic getJobLogs call reads; v1 is asked for the same.
LOG_PAGE_BYTES = 256 * 1024


def job_logs(client: _OverV1, name: str, params: dict[str, Any]) -> dict[str, Any]:
    """The catalog's job logs → getJobLogs, cut the way classic cuts them: the log split
    on newlines (so a final newline ends in an empty line), the last ``maxLines`` of those,
    and their byte offsets. v1 sends the newest output first, so the page always ends at
    the end of the log; when v1 has older output the log's size isn't known, and the
    offsets are null."""
    item = client.find(name)
    if item is None:
        return {"error": f"Job {name} not found"}
    if item.get("kind") != "job":
        raise OnClassic  # v1 reads one job's log; classic decides for a batch or run
    chunk = sdk.plain(client.v1().jobs.logs(item["id"], max_bytes=LOG_PAGE_BYTES))
    raw = str(chunk.get("content") or "").encode()
    whole = not chunk.get("nextCursor")
    lines = raw.split(b"\n")
    max_lines = int(params.get("maxLines", 500))
    kept = lines[-max_lines:] if max_lines > 0 else []
    dropped = lines[: len(lines) - len(kept)]
    first = sum(len(line) + 1 for line in dropped) if kept else len(raw)
    return {
        "jobName": name,
        "logLines": len(kept),
        "truncated": first > 0 or not whole,
        "totalLines": len(lines) if whole else None,
        "totalBytes": len(raw) if whole else None,
        "startByte": first if whole else None,
        "endByte": len(raw) if whole else None,
        "olderBeforeByte": (first or None) if whole else None,
        "log": b"\n".join(kept).decode("utf-8", errors="replace"),
    }


class CatalogOverV1(_OverV1):
    """The catalog client (``State.catalog_client()``) with v1 selected: job logs come
    from v1; tools, schemas and facets stay on the catalog until v1 serves them alike."""

    def __init__(self, state: Any):
        cfg = state.config()
        super().__init__(state, HTTPClient(cfg.catalog_base, cfg.api_key))

    def _route(self, method: str, path: str) -> Route | None:
        match = _LOGS.match(path)
        return (job_logs, (match.group("name"),)) if method == "GET" and match else None


# -- outside the classic clients ---------------------------------------------------------


def upload(state: Any, path: Path, remote: str) -> dict[str, Any] | None:
    """``files upload`` on v1 (uploadFile, the PUTs, completeFileUpload); the answer
    classic's upload gives. None without a key: classic's client says so."""
    if not state.config().api_key:
        return None
    try:
        with sdk.make_client(state) as client:
            client.files.upload(path, path=remote)
    except TamarindError as exc:
        raise _classic_error(exc) from exc
    return {"ok": True, "filename": remote, "bytes": path.stat().st_size}


def test_custom_tool(
    state: Any, tool: CustomTool, settings: Any, *, version: str, name: str | None
) -> CustomToolTestJob:
    """``custom-tools test`` on v1: submitJob pinned to the version (``toolVersion`` and
    its ``toolLifetimeEtag``), where classic posts ``v2/jobs`` with a test marker. v1 has
    no test marker, so the run isn't in the website's Test history. The checks before
    and the receipt are the SDK's (``CustomTool.test``)."""
    if not isinstance(settings, dict):
        raise ValidationError("Test settings must be an object")
    if name is not None and (not isinstance(name, str) or not name.strip()):
        raise ValidationError("Test job name must be a non-empty string")
    job_name = name if name is not None else f"{tool.name}-test-{uuid4().hex[:12]}"
    selected = tool.get_version(version)
    if selected.status != "Complete" or selected.error is not None:
        raise CustomToolNotDeployableError(
            f"Version {selected.version} is {selected.status}; test a completed build."
        )
    request = {
        "kind": "job",
        "tool": tool.name,
        "name": job_name,
        "settings": settings,
        "toolVersion": selected.version,
        "toolLifetimeEtag": selected._lifetime_etag,
    }
    try:
        with sdk.make_client(state) as client:
            job = sdk.plain(client.jobs.submit(body=request))
    except TamarindError as exc:
        if not sdk.outcome_unclear(exc):
            raise
        err = _classic_error(exc)
        err.message += f" Query job {job_name!r} before retrying; submission may have succeeded."
        err.detail = {
            **(err.detail if isinstance(err.detail, dict) else {}),
            "jobName": job_name,
            "toolName": tool.name,
            "version": selected.version,
            "submitted": None,
            "outcomeMayBeAmbiguous": True,
        }
        raise err from exc
    return CustomToolTestJob(
        id=_uuid(str(job.get("id") or "")),
        job_name=str(job.get("name") or job_name),
        job_type=str(job.get("tool") or tool.name),
        status=str(job.get("status") or "In Queue"),
        created_at=stamp(job.get("createdAt")) or "",
    )


def key_works(state: Any, api_key: str) -> bool:
    """Whether v1 takes ``api_key`` (getMe); any error but v1 refusing the key is raised."""
    if not api_key.strip():
        return False
    try:
        with sdk.make_client(state, api_key=api_key) as client:
            client.me.get()
    except TamarindError as exc:
        if getattr(exc, "status", None) == 401:
            return False
        raise
    return True
