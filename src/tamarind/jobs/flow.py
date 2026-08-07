"""Multi-step job orchestration: fetch-one, and poll-until-terminal.

The shell. It calls `api`, decides with `plan`, and owns the clock — which is the
only reason this can't live in `plan`. Progress is reported through the `on_poll`
callback rather than printed, so the same function serves the CLI's live output and
a script that wants silence.
"""

from __future__ import annotations

import time
from typing import Any, Callable

from ..errors import JobTimeoutError, NotFoundError, TamarindError
from ..http import HTTPClient
from . import api, plan


def fetch_job(client: HTTPClient, name: str, *, timeout: float | None = None) -> dict[str, Any]:
    """Fetch a single job by name. Raises NotFoundError if it doesn't exist."""
    resp = api.get_jobs(client, job_name=name, timeout=timeout)
    job = plan.extract_single(resp, name)
    if job is None:
        raise NotFoundError(f"Job '{name}' not found")
    return job


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
    plan.validate_wait_options(poll_interval=poll_interval, timeout=timeout)
    deadline = None if timeout is None else time.monotonic() + max(0.0, timeout)
    last_status: str | None = None
    while True:
        remaining = None if deadline is None else deadline - time.monotonic()
        if remaining is not None and remaining <= 0:
            status_text = f" still {last_status!r}" if last_status is not None else ""
            raise JobTimeoutError(f"Job '{name}'{status_text} after {timeout:.0f}s")
        try:
            job = fetch_job(client, name, timeout=remaining)
        except TamarindError as exc:
            # Only a generic transport timeout is eligible for deadline
            # translation. Preserve typed API failures (auth, budget, rate
            # limit, not-found, validation) even if the clock crossed while
            # the request was in flight.
            if type(exc) is TamarindError and deadline is not None and time.monotonic() >= deadline:
                raise JobTimeoutError(
                    f"Job '{name}' did not return status before the {timeout:.0f}s deadline"
                ) from exc
            raise
        if on_poll is not None:
            on_poll(job)
        last_status = plan.job_status(job)
        if plan.is_terminal(last_status):
            return job
        remaining = None if deadline is None else deadline - time.monotonic()
        if remaining is not None and remaining <= 0:
            raise JobTimeoutError(f"Job '{name}' still {last_status!r} after {timeout:.0f}s")
        sleep_for = poll_interval if remaining is None else min(poll_interval, remaining)
        time.sleep(max(0.0, sleep_for))
