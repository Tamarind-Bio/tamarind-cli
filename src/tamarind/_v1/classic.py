"""Today's classic requests, answered by the v1 API.

When the server says a key uses v1 (``tamarind._v1.switch``), every classic request
v1 has a form for is answered by the v1 operation behind it, and v1's answer is
rebuilt into the layout classic returns. :class:`~tamarind.http.HTTPClient` does
this for every caller, so ``tamarind.rest``, ``tamarind.Tamarind`` and the CLI's
commands keep their signatures, layouts and exit codes. A field v1 doesn't have is
left out; docs/v1-mode.md lists those differences.

There is no fallback. What v1 refuses is raised as v1's error, a ``ProblemError``
that is also the classic error class for its status (``NotFoundError`` for a 404...),
so existing ``except`` clauses still match. The few requests v1 has no form for yet
go to classic on purpose (:class:`OnClassic`): the catalog, another member's jobs
(``organization`` / ``jobEmail``), a list with ``includeSubjobs``, ``pdbsOnly``
results, and the logs of anything but a single job.

A v1 failure with no answer, a 5xx or a 409 ``idempotency_in_progress`` is raised the
way the classic client raises one, so callers' "outcome may be ambiguous" handling
applies unchanged.
"""

from __future__ import annotations

import json
import re
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Iterator, NoReturn

from ..errors import (
    APIError,
    AuthError,
    BudgetError,
    JobTimeoutError,
    NotFoundError,
    RateLimitError,
    TamarindError,
    ValidationError,
)
from .errors import _BUDGET_CODES, ProblemError

# What submit-job and submit-batch append for a low-priority job (classic's
# `lowPrioritySubmittedSuffix(true)`, src/lib/jobs/lowPriority.js).
LOW_PRIORITY_SUFFIX = (
    " at low priority (20% off, no completion guarantee, and a job not started within "
    "7 days stops with no charge)"
)
FINAL = ("Complete", "Stopped", "Failed")


class OnClassic(Exception):
    """v1 has no form for this request yet: it goes to classic."""


def plain(value: Any) -> Any:
    """SDK models → their wire dicts (camelCase), recursively; everything else as is."""
    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        return to_dict()
    if isinstance(value, (list, tuple)):
        return [plain(v) for v in value]
    if isinstance(value, dict):
        return {k: plain(v) for k, v in value.items()}
    return value


# -- errors -------------------------------------------------------------------------


class AuthProblem(ProblemError, AuthError):
    """v1 refused the key or its access (401, or an auth code)."""


class NotFoundProblem(ProblemError, NotFoundError):
    """v1 answered 404."""


class ValidationProblem(ProblemError, ValidationError):
    """v1 answered 400 or 422."""


class RateLimitProblem(ProblemError, RateLimitError):
    """v1 answered 429."""


class BudgetProblem(ProblemError, BudgetError):
    """v1 refused for budget or quota."""


class APIProblem(ProblemError, APIError):
    """Any other v1 refusal; ``status_code`` is its status, as classic's APIError has."""


_AUTH_CODES = {"authentication_required", "invalid_api_key", "agent_trial_expired"}


def _classic_class(error: ProblemError) -> type[ProblemError]:
    if error.code in _BUDGET_CODES:
        return BudgetProblem
    if error.status == 401 or error.code in _AUTH_CODES:
        return AuthProblem
    if error.status == 404:
        return NotFoundProblem
    if error.status in (400, 422):
        return ValidationProblem
    if error.status == 429:
        return RateLimitProblem
    return APIProblem


def classic_error(exc: TamarindError) -> TamarindError:
    """A v1 failure raised the way the classic client raises one.

    A failure with no answer is already a plain :class:`TamarindError`; a 409
    ``idempotency_in_progress`` (or ``idempotency_order_unavailable``) becomes one too,
    which is what callers read as "the outcome may be ambiguous". Any other v1 answer
    stays a ``ProblemError`` (its problem document, its exit code) and also becomes the
    classic class for its status; a 5xx is an ``APIError`` with ``status_code``.
    """
    if not isinstance(exc, ProblemError):
        return exc
    if exc.code in ("idempotency_in_progress", "idempotency_order_unavailable"):
        return TamarindError(exc.message, detail=exc.problem or None)
    if not isinstance(exc, (AuthError, NotFoundError, ValidationError, RateLimitError, BudgetError, APIError)):
        exc.__class__ = _classic_class(exc)
        if isinstance(exc, APIError):
            exc.status_code = exc.status
    return exc


_WITH_PROBLEM: dict[type[TamarindError], type[ProblemError]] = {}


def same_path_error(response: Any, error: TamarindError) -> TamarindError:
    """A v1 refusal of a request sent at the same path (custom tools, pipeline runs).

    ``error`` is what the classic client makes of the same answer (its class, message,
    exit code: ``CustomToolExistsError`` and the rest), so callers see what they see
    today. It also becomes a ``ProblemError`` carrying v1's problem document (``code``,
    ``errors``, ``problem``). A refusal v1 marks as about the key or the budget by its
    code is the auth or budget error, whatever its status."""
    problem = ProblemError.from_response(response)
    if problem.code in _AUTH_CODES or problem.code in _BUDGET_CODES:
        if not isinstance(error, (AuthError, BudgetError)):
            return classic_error(problem)
    base = type(error)
    if isinstance(error, ProblemError) or not issubclass(base, TamarindError):
        return error
    hybrid = _WITH_PROBLEM.get(base)
    if hybrid is None:
        made = type(base.__name__, (ProblemError, base), {"__module__": base.__module__, "__doc__": base.__doc__})
        hybrid = _WITH_PROBLEM[base] = made
    out = Exception.__new__(hybrid)
    out.__dict__.update(problem.__dict__)
    out.__dict__.update(error.__dict__)  # classic's detail, status_code
    out.args = error.args
    out.exit_code = error.exit_code
    return out


def _raise_classic(exc: TamarindError) -> NoReturn:
    converted = classic_error(exc)
    if converted is exc:
        raise exc
    raise converted from exc


Handler = Callable[..., Any]
Route = tuple[Handler, tuple[str, ...]]


class Router:
    """One classic client's requests on v1: its lookups, remembered for its life, and
    the state a results wait carries."""

    def __init__(self, http: Any):
        self._http = http
        self._bounded_client: Any = None
        self._items: dict[tuple[str, tuple[str, ...]], dict[str, Any]] = {}
        self._names: dict[str, str] = {}
        # (waiting, deadline): set by HTTPClient.results_wait; deadline is monotonic.
        self.results_deadline: tuple[bool, float | None] = (False, None)

    @property
    def api_key(self) -> str | None:
        return self._http.api_key

    def v1(self) -> Any:
        if self._bounded_client is not None:
            return self._bounded_client
        return self._http.v1()

    def serve(self, route: Route, payload: Any, classic: Callable[[], Any], *, timeout: float | None = None) -> Any:
        handler, args = route
        try:
            with self._bounded(timeout):
                return handler(self, *args, payload if isinstance(payload, dict) else {})
        except OnClassic:
            return classic()
        except TamarindError as exc:
            _raise_classic(exc)

    @contextmanager
    def _bounded(self, timeout: float | None) -> Iterator[None]:
        """A request its caller bounds (a wait's remaining deadline) is sent the way
        classic's client sends it: one try of at most ``timeout`` seconds, not the SDK's
        retries, which could run past the deadline."""
        if timeout is None:
            yield
            return
        saved = self._bounded_client
        self._bounded_client = self._http.v1_client(timeout=max(float(timeout), 0.001), max_retries=0)
        try:
            yield
        finally:
            self._bounded_client.close()
            self._bounded_client = saved

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
                page = plain(self.v1().jobs.list(**query))
                found.extend((page or {}).get("items") or [])
            if not found:
                return None
            self._items[key] = max(found, key=lambda item: str(item.get("createdAt") or ""))
        return self._items[key]

    def name_of(self, item_id: str) -> str | None:
        """A batch's (or run's) name, from its id."""
        if item_id not in self._names:
            self._names[item_id] = str(plain(self.v1().jobs.get(item_id)).get("name") or "")
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


# listJobs filters only v1 has (rest.get_jobs checks v1 is on before sending them).
_V1_JOB_FILTERS = ("kind", "status", "tool", "search")


def get_jobs(client: Router, params: dict[str, Any]) -> dict[str, Any]:
    """GET /jobs: one job by name (getJob), or a page (listJobs)."""
    filters = {key: params[key] for key in _V1_JOB_FILTERS if params.get(key) is not None}
    if params.get("organization") or params.get("jobEmail") or params.get("includeSubjobs"):
        if filters:
            raise ValidationError(
                f"{', '.join(filters)} can't be combined with organization, job_email or include_subjobs yet."
            )
        raise OnClassic  # another member's jobs (website#7795); subjobs mixed into the list
    name = params.get("jobName")
    if name and filters:
        raise ValidationError(f"{', '.join(filters)} can't be combined with job_name.")
    if name:
        found = client.find(name)
        if found is None:
            raise NotFoundError(f"Job {name} not found")
        job = plain(client.v1().jobs.get(found["id"]))
        batch = client.name_of(job["batchId"]) if job.get("batchId") else None
        row = job_row(job, batch_name=batch)
        return {**row, "statuses": statuses([row])}
    query: dict[str, Any] = {"limit": params.get("limit"), **filters}
    if params.get("startKey"):
        query["cursor"] = params["startKey"]
    batch_name = None
    if params.get("batch"):
        parent = client.find(params["batch"], kinds=("batch", "pipeline"))
        if parent is None:
            return {"jobs": [], "statuses": statuses([])}
        key = "pipeline_run_id" if parent.get("kind") == "pipeline" else "batch_id"
        query[key], batch_name = parent["id"], parent.get("name")
    page = plain(client.v1().jobs.list(**{k: v for k, v in query.items() if v is not None}))
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


def validate_job(client: Router, body: dict[str, Any]) -> dict[str, Any]:
    """POST /validate-job → validateJob, the report rebuilt as classic's verdict."""
    settings, tool = body.get("settings"), body.get("type")
    if isinstance(settings, list):
        request: dict[str, Any] = {"kind": "batch", "tool": tool, "settings": settings}
        if body.get("jobNames") is not None:
            request["names"] = body["jobNames"]
        report = plain(client.v1().jobs.validate(body=request))
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
    report = plain(client.v1().jobs.validate(body=request))
    if report.get("valid"):
        out: dict[str, Any] = {"valid": True}
        if report.get("normalized") is not None:
            out["normalized"] = report["normalized"]
        out["job_name"] = report.get("name") or body.get("jobName")
        return out
    return {"valid": False, **_classic_errors(report.get("errors") or [])}


# -- submit -------------------------------------------------------------------------


def _submit(client: Router, request: dict[str, Any], name: str) -> None:
    try:
        client.v1().jobs.submit(body=request)
    except TamarindError as exc:
        if getattr(exc, "code", None) == "job_name_conflict":
            # v1's 409 for a name you already use; classic answers it as a 400 in these words.
            raise ValidationError(f"jobName {name} already exists, please choose a different name") from exc
        raise


def submit_job(client: Router, body: dict[str, Any]) -> str:
    """POST /submit-job → submitJob; classic answers ``<name> submitted to queue.``"""
    name = body.get("jobName")
    request: dict[str, Any] = {"kind": "job", "tool": body.get("type"), "name": name, "settings": body.get("settings")}
    low_priority = body.get("lowPriority") is True
    if low_priority:
        request["lowPriority"] = True
    _submit(client, request, str(name))
    return f"{name} submitted to queue{LOW_PRIORITY_SUFFIX if low_priority else ''}."


def submit_batch(client: Router, body: dict[str, Any]) -> str:
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


def _cancel_many(client: Router, item: dict[str, Any], *, cascaded: bool) -> dict[str, Any]:
    """Cancel a batch or run: classic's answer, its counts read from v1 just before."""
    before = plain(client.v1().jobs.get(item["id"]))
    counts = before.get("counts") or {}
    live = int(counts.get("inQueue") or 0) + int(counts.get("running") or 0)
    parent_live = before.get("status") not in FINAL
    after = plain(client.v1().jobs.cancel(item["id"], body={}))
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


def cancel_job(client: Router, body: dict[str, Any]) -> dict[str, Any]:
    """POST /cancelJob → cancelJob; a batch or run name cancels all of it, as classic does."""
    name = body.get("jobName")
    if not name:
        raise OnClassic  # by row id: v1 takes its own ids
    item = client.find(name)
    if item is None:
        raise NotFoundError(f"Job {name} not found")
    if item.get("kind") != "job":
        return _cancel_many(client, item, cascaded=True)
    job = plain(client.v1().jobs.cancel(item["id"], body={}))
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


def cancel_batch(client: Router, body: dict[str, Any]) -> dict[str, Any]:
    """POST /cancelBatch → cancelJob on the batch or run."""
    name = body.get("batchName")
    item = client.find(name, kinds=("batch", "pipeline"))
    if item is None:
        raise NotFoundError(f'No batch or pipeline named "{name}" found for this user')
    return _cancel_many(client, item, cascaded=False)


# -- results, delete --------------------------------------------------------------------


def _not_complete(name: Any, item: dict[str, Any]) -> ValidationError:
    return ValidationError(f"Job {name} is not complete. Status: {item.get('status')}")


def _retry_after(exc: Exception, default: float) -> float:
    """The seconds an error's ``Retry-After`` asks for (``default`` if it gives none)."""
    headers = getattr(exc, "headers", None)
    try:
        return max(float(headers.get("retry-after")), 1.0) if headers else default
    except (TypeError, ValueError):
        return default


def _archive(client: Router, item: dict[str, Any]) -> dict[str, Any]:
    v1 = client.v1()
    if item.get("kind") == "pipeline":
        return plain(v1.pipelines.archive_run(item["id"], body={}))
    return plain(v1.jobs.archive(item["id"], body={}))


def result(client: Router, body: dict[str, Any]) -> str:
    """POST /result → archiveJob (archivePipelineRun for a run, getJobFile for
    ``fileName``); classic answers the signed link. v1's archive is the stored
    ``result-<folder>.zip`` classic serves, so the bytes are the same (the link itself is
    v1's, signed for the global endpoint).

    v1 can call a batch Complete before its archive is built, where classic's wait covers
    the build. So inside ``HTTPClient.results_wait`` (the CLI's ``--wait``) a Complete item
    whose archive is still preparing is asked again after ``retryAfterSeconds``, until it
    is ready or the wait's deadline passes."""
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
        link = plain(client.v1().jobs.get_file(item["id"], path=file_name, delivery="url"))
        return str(link.get("url"))
    wait, deadline = client.results_deadline
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
                    current = plain(client.v1().jobs.get(item["id"]))
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
            current = plain(client.v1().jobs.get(item["id"]))
        if current.get("status") != "Complete":
            raise _not_complete(name, current)
        delay = max(float(answer.get("retryAfterSeconds") or 5), 1.0)
        if not wait:
            raise TamarindError(
                f"The results archive is still being prepared; try again in {delay:g} s.", detail=answer
            )
        pause(delay, answer)


def delete_job(client: Router, body: dict[str, Any]) -> str:
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


def _entries(client: Router, **query: Any) -> Any:
    v1 = client.v1()
    return (plain(entry) for entry in v1.paginate(v1.files.list, limit=200, **query))


def get_files(client: Router, params: dict[str, Any]) -> list[str]:
    """GET /files → listFiles: the folder's files (not zips) by path, in classic's order:
    the five newest first, then the rest by name. With ``includeFolders`` the folders are
    listed too, as ``path/``, and count as the newest (classic dates them "now"). Classic
    reads no other option (``includeAll``, ``includeMetadata``, paging: pages/api/files.js
    passes only the folder and includeFolders), so neither does this."""
    folder = params.get("folder") or None
    with_folders = str(params.get("includeFolders")).lower() == "true"
    entries = list(_entries(client, **({"folder": folder} if folder else {})))
    files = [e for e in entries if e.get("type") == "file" and not str(e.get("path", "")).endswith(".zip")]
    files.sort(key=lambda e: str(e.get("modifiedAt") or ""), reverse=True)
    paths = [str(e.get("path")) for e in files]
    if with_folders:
        folders = [str(e.get("path")).rstrip("/") + "/" for e in entries if e.get("type") == "folder"]
        paths = folders + paths
    rest = sorted(paths[5:], key=lambda path: (path.casefold(), path))
    return paths[:5] + rest


def get_folders(client: Router, params: dict[str, Any]) -> dict[str, Any]:
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


def delete_file(client: Router, params: dict[str, Any]) -> dict[str, str]:
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


# -- logs (the catalog client) --------------------------------------------------------------

_LOGS = re.compile(r"^catalog/jobs/(?P<name>.+)/logs$")


# The most of a job's log one classic getJobLogs call reads; v1 is asked for the same.
LOG_PAGE_BYTES = 256 * 1024


def job_logs(client: Router, name: str, params: dict[str, Any]) -> dict[str, Any]:
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
    chunk = plain(client.v1().jobs.logs(item["id"], max_bytes=LOG_PAGE_BYTES))
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


# -- custom tool tests -------------------------------------------------------------------


def custom_tool_test(client: Router, body: dict[str, Any]) -> dict[str, Any]:
    """POST /v2/jobs with a test marker (``toolRef``, what ``CustomTool.test`` sends) →
    submitJob pinned to the version (``toolVersion`` and its ``toolLifetimeEtag``).
    v1 has no test marker, so the run isn't in the website's Test history. The answer
    is the receipt classic gives: ``Id``, ``JobName``, ``Type``, ``JobStatus``,
    ``Created``."""
    if not body.get("toolRef"):
        raise OnClassic  # any other v2/jobs request
    name = body.get("jobName")
    request = {
        "kind": "job",
        "tool": body.get("type"),
        "name": name,
        "settings": body.get("settings"),
        "toolVersion": body.get("toolRef"),
        "toolLifetimeEtag": body.get("toolLifetimeEtag"),
    }
    try:
        job = plain(client.v1().jobs.submit(body=request))
    except TamarindError as exc:
        if getattr(exc, "code", None) == "job_name_conflict":
            raise ValidationError(f"jobName {name} already exists, please choose a different name") from exc
        raise
    return {
        "Id": _uuid(str(job.get("id") or "")),
        "JobName": str(job.get("name") or name),
        "Type": str(job.get("tool") or body.get("type")),
        "JobStatus": str(job.get("status") or "In Queue"),
        "Created": stamp(job.get("createdAt")) or "",
    }


# -- the routes ---------------------------------------------------------------------------

_ROUTES: dict[tuple[str, str], Handler] = {
    **_JOB_API,
    ("POST", "v2/jobs"): custom_tool_test,
}


def route(method: str, path: str) -> Route | None:
    """The handler for a classic request v1 has a form for; None for the rest."""
    handler = _ROUTES.get((method, path))
    if handler is not None:
        return handler, ()
    match = _LOGS.match(path)
    if method == "GET" and match:
        return job_logs, (match.group("name"),)
    return None


# -- uploads ------------------------------------------------------------------------------


def upload(http: Any, path: Path, remote: str, content_type: str | None = None) -> dict[str, Any] | None:
    """An upload on v1 (uploadFile, the PUTs, completeFileUpload), answered as classic's
    upload is: ``{ok, filename, bytes}``. None when v1 isn't on for this key."""
    if not http.api_key or not http.uses_v1():
        return None
    try:
        http.v1().files.upload(path, path=remote, content_type=content_type)
    except TamarindError as exc:
        _raise_classic(exc)
    return {"ok": True, "filename": remote, "bytes": path.stat().st_size}


# -- responses of the requests v1 serves at the same path --------------------------------

_UPLOAD_SESSION = re.compile(r"^custom-tools/[^/]+/uploads$")
_NODE_RUN_MOLECULES = re.compile(r"^pipelines/runs/[^/]+/node-runs/[^/]+/molecules$")
_RUN = re.compile(r"^pipelines/runs/[^/]+$")
_RUN_ID = re.compile(r"^(/?pipelines/runs/)([^/?]+)(.*)$", re.DOTALL)
_RUN_PREFIX = "run_"


def v1_path(path: str) -> str:
    """A request v1 serves at the same path, as v1 takes it: classic names a pipeline run
    by its bare id, v1 by ``run_<id>``."""
    match = _RUN_ID.match(path)
    if not match or match.group(2).startswith(_RUN_PREFIX):
        return path
    return f"{match.group(1)}{_RUN_PREFIX}{match.group(2)}{match.group(3)}"


def rebuild_response(method: str, path: str, response: Any) -> Any:
    """A v1 answer to a request sent at the same path (custom tools, pipeline runs), in
    the shape the classic contract's parsers read where v1 renamed a field:
    createCustomToolUpload's ``id`` is classic's ``uploadId``, listNodeRunMolecules' page
    of ``items`` (each with ``id``) is classic's ``molecules`` (each ``complexId``), and a
    run's ``run_<id>`` is classic's bare id. Everything else is the same shape (v1 adds
    ``failureReason``), so it is passed through."""
    import httpx

    if method == "POST" and _UPLOAD_SESSION.match(path):
        rebuild = _upload_session
    elif method == "GET" and _NODE_RUN_MOLECULES.match(path):
        rebuild = _node_run_molecules
    elif method == "GET" and _RUN.match(path):
        rebuild = _run
    else:
        return response
    try:
        body = response.json()
    except ValueError:
        return response
    if not isinstance(body, dict):
        return response
    headers = {
        k: v for k, v in response.headers.items()
        if k.lower() not in ("content-length", "content-encoding", "transfer-encoding")
    }
    return httpx.Response(response.status_code, json=rebuild(body), headers=headers, request=response.request)


def _upload_session(body: dict[str, Any]) -> dict[str, Any]:
    if "uploadId" in body or "id" not in body:
        return body
    out = {k: v for k, v in body.items() if k != "id"}
    out["uploadId"] = body["id"]
    return out


def _node_run_molecules(body: dict[str, Any]) -> dict[str, Any]:
    if "molecules" in body or not isinstance(body.get("items"), list):
        return body
    molecules = []
    for item in body["items"]:
        if isinstance(item, dict) and "id" in item and "complexId" not in item:
            item = {"complexId": item["id"], **{k: v for k, v in item.items() if k != "id"}}
        molecules.append(item)
    return {"molecules": molecules, "nextCursor": body.get("nextCursor")}


def _run(body: dict[str, Any]) -> dict[str, Any]:
    run_id = body.get("id")
    if isinstance(run_id, str) and run_id.startswith(_RUN_PREFIX):
        return {**body, "id": run_id[len(_RUN_PREFIX):]}
    return body
