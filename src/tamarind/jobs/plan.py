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
from dataclasses import dataclass
from enum import Enum
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


# ── Batch submission ──────────────────────────────────────────────────────────
# The pinned batch route submits N INDEPENDENT jobs and answers 200 even when some
# of them failed. Two consequences shape everything below:
#
#   1. "The request succeeded" does not mean "the work is running". Partial failure
#      is the normal case for a 500-item batch, not an exceptional one.
#   2. There is no batch parent row. Each job stands alone, so the returned names
#      are the ONLY handle a caller has on what it just started — losing them loses
#      the work.

# The server's cap. Enforced client-side too, so an over-cap batch is a clear local
# error naming the limit rather than a 422 the caller has to decode.
MAX_BATCH_ITEMS = 500


class BatchOutcome(str, Enum):
    """What a batch submit actually achieved."""

    SUBMITTED = "submitted"  # every item dispatched
    PARTIAL = "partial"  # some dispatched, some did not
    FAILED = "failed"  # nothing dispatched


@dataclass(frozen=True)
class BatchSummary:
    """The reconciled result of a batch submit.

    ``counts_disagreed`` records that the server's own tallies did not match its
    itemized results. That should never happen; surfacing it is cheaper than
    debugging a silent miscount later, and the item list is what we believe.
    """

    outcome: BatchOutcome
    submitted: tuple[str, ...]
    failures: tuple[tuple[str, str], ...]  # (job name, reason)
    counts_disagreed: bool = False

    @property
    def ok(self) -> bool:
        return self.outcome is BatchOutcome.SUBMITTED


def summarize_batch(submission: wire.BatchSubmission) -> BatchSummary:
    """Reconcile a batch response into what a caller should act on.

    The ITEMS win over the server's counts. They are the itemized truth, they carry
    the names a caller needs in order to retry, and believing a `submitted: 500`
    header over 300 items marked `ok: false` is exactly how a batch failure becomes
    invisible.

    An empty item list with a positive `submitted` count is the one case where the
    counts are all we have; it yields SUBMITTED with no names, which is honest —
    something ran, and we cannot say what.
    """
    if not submission.items:
        reported = submission.submitted or 0
        if reported > 0:
            return BatchSummary(outcome=BatchOutcome.SUBMITTED, submitted=(), failures=())
        return BatchSummary(outcome=BatchOutcome.FAILED, submitted=(), failures=())

    submitted = tuple(i.job_name or "" for i in submission.items if i.ok)
    failures = tuple(
        (i.job_name or "<unnamed>", i.error or "no reason given")
        for i in submission.items
        if not i.ok
    )

    if not failures:
        outcome = BatchOutcome.SUBMITTED
    elif submitted:
        outcome = BatchOutcome.PARTIAL
    else:
        outcome = BatchOutcome.FAILED

    disagreed = (submission.submitted is not None and submission.submitted != len(submitted)) or (
        submission.failed is not None and submission.failed != len(failures)
    )

    return BatchSummary(
        outcome=outcome,
        submitted=submitted,
        failures=failures,
        counts_disagreed=disagreed,
    )


def validate_batch_size(count: int) -> None:
    """Reject a batch the server would reject, with a message that says the limit."""
    if count < 1:
        raise ValidationError("A batch needs at least one job.")
    if count > MAX_BATCH_ITEMS:
        raise ValidationError(
            f"{count} jobs exceeds the {MAX_BATCH_ITEMS}-job batch limit. "
            f"Split it into {math.ceil(count / MAX_BATCH_ITEMS)} batches."
        )
