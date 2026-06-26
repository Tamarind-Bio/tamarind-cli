"""Job-status helpers: normalization and polling.

The REST job objects use capitalized keys (``JobName``, ``JobStatus``, ...).
The status enum is {Complete, In Queue, Running, Stopped, Deleted}; we also
treat Failed/Cancelled/Error as terminal defensively in case the backend grows
new terminal states.
"""

from __future__ import annotations

import time
from typing import Any, Callable

from . import rest
from .errors import NotFoundError
from .http import HTTPClient

# Compared case-insensitively.
TERMINAL_STATUSES = {"complete", "completed", "stopped", "deleted", "failed", "cancelled", "error"}
SUCCESS_STATUSES = {"complete", "completed"}


def job_status(job: dict[str, Any]) -> str | None:
    """Read a job's status regardless of which casing the API used."""
    for key in ("JobStatus", "status", "Status"):
        if job.get(key):
            return str(job[key])
    return None


def job_name(job: dict[str, Any]) -> str | None:
    for key in ("JobName", "jobName", "name"):
        if job.get(key):
            return str(job[key])
    return None


def is_terminal(status: str | None) -> bool:
    return bool(status) and status.lower() in TERMINAL_STATUSES


def is_success(status: str | None) -> bool:
    return bool(status) and status.lower() in SUCCESS_STATUSES


def fetch_job(client: HTTPClient, name: str) -> dict[str, Any]:
    """Fetch a single job by name. Raises NotFoundError if it doesn't exist."""
    resp = rest.get_jobs(client, job_name=name)
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
    if any(k in resp for k in ("JobName", "JobStatus", "jobName", "status")):
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

    Returns the final job object. Raises TimeoutError if a timeout is set and
    the job is still running when it elapses.
    """
    deadline = None if timeout is None else time.monotonic() + timeout
    while True:
        job = fetch_job(client, name)
        if on_poll is not None:
            on_poll(job)
        if is_terminal(job_status(job)):
            return job
        if deadline is not None and time.monotonic() >= deadline:
            raise TimeoutError(
                f"Job '{name}' still {job_status(job)!r} after {timeout:.0f}s"
            )
        time.sleep(poll_interval)
