"""The job boundary: raw API payloads in, frozen types out.

Everything the package knows about the *shape* of a job response lives here and
nowhere else. That is the point of a boundary — the API answers in several shapes
(capitalized keys, a batch parent reporting its lifecycle in ``batchStatus``, an
index-keyed envelope for a single-name query), and absorbing that variance once
means nothing downstream has to re-learn it.

Parse, don't validate: this layer is *tolerant* on the way in and *strict* on the
way out. It does not reject a payload it doesn't recognize — an unknown shape yields
a Job with null fields and the original payload intact on ``raw`` — because refusing
to parse would turn a harmless new server field into a client-side outage. What it
guarantees is that everything past it sees the same typed thing.

Pure: no network, no clock. `tests/test_layering.py` enforces that.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

# Key precedence for reading a status, by whether the row is a batch parent.
_PARENT_STATUS_KEYS = ("batchStatus", "BatchStatus", "JobStatus", "status", "Status")
_JOB_STATUS_KEYS = ("JobStatus", "status", "Status", "batchStatus", "BatchStatus")
_NAME_KEYS = ("JobName", "jobName", "batchName", "BatchName", "name")

# Keys whose presence marks a bare payload as a job object rather than an envelope.
_JOB_MARKER_KEYS = (
    "JobName",
    "JobStatus",
    "jobName",
    "status",
    "batchName",
    "BatchName",
    "batchStatus",
    "BatchStatus",
)


@dataclass(frozen=True)
class Job:
    """A job or batch parent, with the API's shape variance already resolved.

    ``raw`` is the untouched payload. It is deliberately kept: the CLI renders
    fields this type doesn't model, and a caller should never have to choose
    between typed access and the server's full answer.
    """

    name: str | None = None
    status: str | None = None
    type: str | None = None
    is_batch_parent: bool = False
    raw: Mapping[str, Any] = field(default_factory=dict)


def _is_batch_parent(payload: Mapping[str, Any]) -> bool:
    """Whether this row reports a batch's lifecycle rather than a single job's.

    Subjob rows may carry their parent's ``batchName`` and ``batchStatus``. A row is
    a parent only when the API identifies its type as batch, or when it uses a batch
    name without also carrying its own durable job name.
    """
    kind = str(payload.get("Type") or payload.get("type") or "").strip().lower()
    has_batch_name = any(payload.get(k) for k in ("batchName", "BatchName"))
    has_job_name = any(payload.get(k) for k in ("JobName", "jobName"))
    return kind == "batch" or (has_batch_name and not has_job_name)


def _first_present(payload: Mapping[str, Any], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        if payload.get(key):
            return str(payload[key])
    return None


def parse_job(payload: Any) -> Job:
    """Normalize one job payload. Never raises; an unrecognized shape parses to blanks."""
    if not isinstance(payload, Mapping):
        return Job(raw={})
    parent = _is_batch_parent(payload)
    return Job(
        name=_first_present(payload, _NAME_KEYS),
        status=_first_present(payload, _PARENT_STATUS_KEYS if parent else _JOB_STATUS_KEYS),
        type=_first_present(payload, ("Type", "type")),
        is_batch_parent=parent,
        raw=payload,
    )


def find_job(response: Any, name: str) -> Mapping[str, Any] | None:
    """Pull one job's raw payload out of any envelope the jobs endpoint returns.

    Returns the raw mapping rather than a :class:`Job` because the CLI renders the
    server's full answer; call :func:`parse_job` on it for typed access.
    """
    if not isinstance(response, Mapping):
        return None

    # Shape A: {"jobs": [...]}
    if "jobs" in response:
        # Filter to mappings FIRST, as the index-keyed branch below already does. The
        # fallback used to return `jobs[0]` whatever it was, so a scalar entry came back
        # from a function whose contract is Mapping | None. `fetch_job` then treated it
        # as a found job with a null status, and `wait_for_job` with no timeout polled
        # it forever — a hang, not an error.
        jobs = [j for j in (response.get("jobs") or []) if isinstance(j, Mapping)]
        for j in jobs:
            if parse_job(j).name == name:
                return j
        return jobs[0] if jobs else None

    # Shape B: an index-keyed map {"0": {...}, "1": {...}, "statuses": {...}} —
    # what the job API returns for a single-jobName query.
    indexed = [v for k, v in response.items() if k.isdigit() and isinstance(v, Mapping)]
    if indexed:
        for j in indexed:
            if parse_job(j).name == name:
                return j
        return indexed[0]

    # Shape C: a bare job object.
    if any(k in response for k in _JOB_MARKER_KEYS):
        return response
    return None


# ── Batch submission ──────────────────────────────────────────────────────────
# The pinned batch route answers 200 with per-item outcomes rather than failing the
# request, so "the HTTP call worked" and "the jobs were submitted" are different
# facts. Keeping them different types is the point: a caller that conflates them
# reports 500 submissions when 300 silently failed.


@dataclass(frozen=True)
class BatchItem:
    """One job's outcome inside a batch submit."""

    job_name: str | None = None
    job_type: str | None = None
    ok: bool = False
    job_id: str | None = None
    status: str | None = None
    error: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class BatchSubmission:
    """What a batch submit reported.

    ``submitted``/``failed`` are the server's OWN counts, kept separate from
    ``items`` rather than reconciled here — deciding which to believe is a
    judgement, and judgements live in `plan`.
    """

    items: tuple[BatchItem, ...] = ()
    submitted: int | None = None
    failed: int | None = None
    raw: Mapping[str, Any] = field(default_factory=dict)


def parse_batch_item(payload: Any) -> BatchItem:
    """Normalize one per-item batch outcome. Never raises.

    ``ok`` defaults to False for an unrecognized payload: an item we cannot read is
    an item we cannot claim was submitted.
    """
    if not isinstance(payload, Mapping):
        return BatchItem()
    return BatchItem(
        job_name=_first_str(payload, ("JobName", "jobName")),
        job_type=_first_str(payload, ("Type", "type")),
        ok=payload.get("ok") is True,
        job_id=_first_str(payload, ("Id", "id", "jobId")),
        status=_first_str(payload, ("JobStatus", "status")),
        error=_first_str(payload, ("error", "Error", "message")),
        raw=payload,
    )


def parse_batch_submission(payload: Any) -> BatchSubmission:
    """Normalize the batch-submit response. Never raises."""
    if not isinstance(payload, Mapping):
        return BatchSubmission()
    results = payload.get("results")
    items: tuple[BatchItem, ...] = ()
    if isinstance(results, (list, tuple)):
        items = tuple(parse_batch_item(r) for r in results)
    submitted = payload.get("submitted")
    failed = payload.get("failed")
    return BatchSubmission(
        items=items,
        submitted=submitted if isinstance(submitted, int) else None,
        failed=failed if isinstance(failed, int) else None,
        raw=payload,
    )


def _first_str(payload: Mapping[str, Any], keys: tuple[str, ...]) -> str | None:
    """The first key present with a non-empty value, as a string."""
    for key in keys:
        value = payload.get(key)
        if value not in (None, ""):
            return str(value)
    return None
