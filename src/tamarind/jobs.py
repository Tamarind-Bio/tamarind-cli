"""Job-status helpers: normalization and polling.

The REST job objects use capitalized keys (``JobName``, ``JobStatus``, ...),
while batch-parent objects report their lifecycle in ``batchStatus``. The job
status enum is {Complete, In Queue, Running, Stopped, Deleted}; we also treat
Failed/Cancelled/Error and the batch-specific AggregationFailed as terminal.
"""

from __future__ import annotations

import math
import time
from typing import Any, Callable

from . import rest
from .errors import JobTimeoutError, NotFoundError, TamarindError, ValidationError
from .http import HTTPClient

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

    ``batchStatus`` is authoritative when present: a batch parent can retain a
    nonterminal per-job field while its aggregation lifecycle has completed.
    """
    for key in ("batchStatus", "BatchStatus", "JobStatus", "status", "Status"):
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


def fetch_job(
    client: HTTPClient, name: str, *, timeout: float | None = None
) -> dict[str, Any]:
    """Fetch a single job by name. Raises NotFoundError if it doesn't exist."""
    resp = rest.get_jobs(client, job_name=name, timeout=timeout)
    job = _extract_single(resp, name)
    if job is None:
        raise NotFoundError(f"Job '{name}' not found")
    return job


def _extract_single(resp: Any, name: str) -> dict[str, Any] | None:
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


def wait_for_job(
    client: HTTPClient,
    name: str,
    *,
    poll_interval: float = 10.0,
    timeout: float | None = None,
    on_poll: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    """Block until ``name`` reaches a terminal status (or ``timeout`` elapses).

    Returns the final job object. Raises :class:`JobTimeoutError` (exit code 7)
    if a timeout is set and the job is still running when it elapses — a clean,
    stably-coded error rather than a bare builtin ``TimeoutError`` traceback.
    """
    if not math.isfinite(poll_interval) or poll_interval < 0:
        raise ValidationError("Poll interval must be a finite, non-negative number.")
    if timeout is not None and (not math.isfinite(timeout) or timeout < 0):
        raise ValidationError("Wait timeout must be a finite, non-negative number.")
    deadline = None if timeout is None else time.monotonic() + max(0.0, timeout)
    last_status: str | None = None
    while True:
        remaining = None if deadline is None else deadline - time.monotonic()
        if remaining is not None and remaining <= 0:
            status_text = f" still {last_status!r}" if last_status is not None else ""
            raise JobTimeoutError(
                f"Job '{name}'{status_text} after {timeout:.0f}s"
            )
        try:
            job = fetch_job(client, name, timeout=remaining)
        except TamarindError as exc:
            if deadline is not None and time.monotonic() >= deadline:
                raise JobTimeoutError(
                    f"Job '{name}' did not return status before the {timeout:.0f}s deadline"
                ) from exc
            raise
        if on_poll is not None:
            on_poll(job)
        last_status = job_status(job)
        if is_terminal(last_status):
            return job
        remaining = None if deadline is None else deadline - time.monotonic()
        if remaining is not None and remaining <= 0:
            raise JobTimeoutError(
                f"Job '{name}' still {last_status!r} after {timeout:.0f}s"
            )
        sleep_for = poll_interval if remaining is None else min(poll_interval, remaining)
        time.sleep(max(0.0, sleep_for))
