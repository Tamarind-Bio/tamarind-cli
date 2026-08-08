"""Jobs: submit, inspect, and wait.

Split into the package's standard three layers — `api` (one function per endpoint),
`plan` (pure decisions), `flow` (orchestration that owns the clock). Callers don't
need to know which is which: the public surface is re-exported here, so
``from tamarind import jobs`` keeps working exactly as it did when this was a single
module.

What the split buys is testability, not a lighter import: `plan` performs no I/O and
owns no clock, so its behaviour can be exercised as a table of inputs and outputs with
no server and no fixtures. (Importing `tamarind.jobs.plan` still executes this
`__init__` and therefore still loads the transport — httpx is a hard dependency of the
package regardless, so there is nothing to save there.)
"""

from __future__ import annotations

# Re-exported so a test or caller can patch the clock via `jobs.time`, as before.
import time

from ..errors import JobTimeoutError, NotFoundError
from .api import (
    JOB_SOURCE,
    cancel_batch,
    cancel_job,
    delete_job,
    get_jobs,
    get_result,
    submit_batch,
    submit_batch_pinned,
    submit_job,
    submit_job_pinned,
    validate_job,
)
from . import api, flow, plan
from .flow import fetch_job, wait_for_job
from .wire import (
    BatchItem,
    BatchSubmission,
    Job,
    find_job,
    parse_batch_submission,
    parse_job,
)
from .plan import (
    MAX_BATCH_ITEMS,
    SUCCESS_STATUSES,
    TERMINAL_STATUSES,
    BatchOutcome,
    BatchSummary,
    extract_single,
    is_success,
    is_terminal,
    job_name,
    job_status,
    summarize_batch,
    validate_batch_size,
    validate_wait_options,
)

# Pre-split name. Kept so the migration doesn't churn callers that reached for the
# private helper; `extract_single` is the name to use.
_extract_single = extract_single

__all__ = [
    "BatchItem",
    "BatchOutcome",
    "BatchSubmission",
    "BatchSummary",
    "MAX_BATCH_ITEMS",
    "parse_batch_submission",
    "summarize_batch",
    "validate_batch_size",
    "parse_job",
    "find_job",
    "Job",
    "JOB_SOURCE",
    "api",
    "flow",
    "plan",
    "JobTimeoutError",
    "NotFoundError",
    "SUCCESS_STATUSES",
    "TERMINAL_STATUSES",
    "cancel_batch",
    "cancel_job",
    "delete_job",
    "extract_single",
    "fetch_job",
    "get_jobs",
    "get_result",
    "is_success",
    "is_terminal",
    "job_name",
    "job_status",
    "submit_batch",
    "submit_batch_pinned",
    "submit_job",
    "submit_job_pinned",
    "time",
    "validate_job",
    "validate_wait_options",
    "wait_for_job",
]
