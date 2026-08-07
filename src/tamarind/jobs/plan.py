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
from . import wire

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

    Delegates to the parser: shape knowledge lives at the boundary (`wire`), and this
    stays as the documented name for it.
    """
    return wire.parse_job(job).status


def job_name(job: dict[str, Any]) -> str | None:
    """The job's name, whichever of the API's five spellings it arrived under."""
    return wire.parse_job(job).name


def is_terminal(status: str | None) -> bool:
    return bool(status) and status.lower() in TERMINAL_STATUSES


def is_success(status: str | None) -> bool:
    return bool(status) and status.lower() in SUCCESS_STATUSES


def extract_single(resp: Any, name: str) -> dict[str, Any] | None:
    """Find one job in any of the shapes the jobs endpoint returns."""
    return wire.find_job(resp, name)


def validate_wait_options(*, poll_interval: float = 10.0, timeout: float | None = None) -> None:
    """Reject invalid local wait timing without making a remote request."""
    if not math.isfinite(poll_interval) or math.copysign(1.0, poll_interval) < 0:
        raise ValidationError("Poll interval must be a finite, non-negative number.")
    if timeout is not None and (not math.isfinite(timeout) or math.copysign(1.0, timeout) < 0):
        raise ValidationError("Wait timeout must be a finite, non-negative number.")
