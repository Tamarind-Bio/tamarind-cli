"""Job-state decisions. Pure — no network, no clock, no I/O.

Everything here is a function of a payload the caller already has, which is what
makes it testable as a table of inputs and outputs with no server and no fixtures.
`plan` may not import `api`, `flow`, or `http`; `tests/test_layering.py` enforces it.

The REST job objects use capitalized keys (``JobName``, ``JobStatus``, ...), while
batch-parent objects report their lifecycle in ``batchStatus``. The job status enum
is {Complete, In Queue, Running, Stopped, Deleted}; Failed/Cancelled/Error and the
batch-specific AggregationFailed are also treated as terminal.
"""

from __future__ import annotations

import math
from typing import Any

from ..errors import ValidationError

# Compared case-insensitively.
TERMINAL_STATUSES = {
    "complete",
    "completed",
    "stopped",
    "deleted",
    "failed",
    "cancelled",
    "error",
    "aggregationfailed",
    "aggregation failed",
}
SUCCESS_STATUSES = {"complete", "completed"}


def job_status(job: dict[str, Any]) -> str | None:
    """Read a job or batch-parent status regardless of API casing.

    ``batchStatus`` is authoritative for an identifiable batch parent, which
    can retain a nonterminal per-job field while aggregation has completed.
    A subjob's own ``JobStatus`` remains authoritative even if a future API
    response also includes parent batch metadata.
    """
    kind = str(job.get("Type") or job.get("type") or "").strip().lower()
    has_batch_name = any(job.get(key) for key in ("batchName", "BatchName"))
    has_job_name = any(job.get(key) for key in ("JobName", "jobName"))
    # Subjob rows may carry their parent's batchName and batchStatus. A row is
    # a parent only when the API identifies its type as batch, or when it uses
    # a batch name without also carrying its own durable job name.
    is_batch_parent = kind == "batch" or (has_batch_name and not has_job_name)
    keys = (
        ("batchStatus", "BatchStatus", "JobStatus", "status", "Status")
        if is_batch_parent
        else ("JobStatus", "status", "Status", "batchStatus", "BatchStatus")
    )
    for key in keys:
        if job.get(key):
            return str(job[key])
    return None


def job_name(job: dict[str, Any]) -> str | None:
    for key in ("JobName", "jobName", "batchName", "BatchName", "name"):
        if job.get(key):
            return str(job[key])
    return None


def is_terminal(status: str | None) -> bool:
    return bool(status) and status.lower() in TERMINAL_STATUSES


def is_success(status: str | None) -> bool:
    return bool(status) and status.lower() in SUCCESS_STATUSES


def extract_single(resp: Any, name: str) -> dict[str, Any] | None:
    """Find one job in any of the three shapes the jobs endpoint returns."""
    if not isinstance(resp, dict):
        return None

    # Shape A: {"jobs": [...]}
    if "jobs" in resp:
        jobs = resp.get("jobs") or []
        for j in jobs:
            if job_name(j) == name:
                return j
        return jobs[0] if jobs else None

    # Shape B: an index-keyed map {"0": {...}, "1": {...}, "statuses": {...}} —
    # what the job API returns for a single-jobName query.
    indexed = [v for k, v in resp.items() if k.isdigit() and isinstance(v, dict)]
    if indexed:
        for j in indexed:
            if job_name(j) == name:
                return j
        return indexed[0]

    # Shape C: a bare JobInfo object.
    if any(
        k in resp
        for k in (
            "JobName",
            "JobStatus",
            "jobName",
            "status",
            "batchName",
            "BatchName",
            "batchStatus",
            "BatchStatus",
        )
    ):
        return resp
    return None


def validate_wait_options(*, poll_interval: float = 10.0, timeout: float | None = None) -> None:
    """Reject invalid local wait timing without making a remote request."""
    if not math.isfinite(poll_interval) or math.copysign(1.0, poll_interval) < 0:
        raise ValidationError("Poll interval must be a finite, non-negative number.")
    if timeout is not None and (not math.isfinite(timeout) or math.copysign(1.0, timeout) < 0):
        raise ValidationError("Wait timeout must be a finite, non-negative number.")
