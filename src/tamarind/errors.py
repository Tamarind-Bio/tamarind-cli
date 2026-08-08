"""Exception types and exit codes for the Tamarind client.

Exit codes are stable so agents and CI can branch on them:

    0  success
    1  generic / unexpected error
    2  usage error (bad arguments) — Typer's default
    3  authentication error (no key, or 401)
    4  not found (404)
    5  validation error (a job's settings failed validate-job, or a 400)
    6  rate limited (429)
    7  timed out (a --wait / --timeout deadline elapsed before a terminal state)
    8  budget/quota exhausted (a 403 that explicitly names usage or credits)
    9  remote job reached an unsuccessful terminal state
"""

from __future__ import annotations


class ExitCode:
    OK = 0
    ERROR = 1
    USAGE = 2
    AUTH = 3
    NOT_FOUND = 4
    VALIDATION = 5
    RATE_LIMIT = 6
    TIMEOUT = 7
    BUDGET = 8
    JOB_FAILED = 9


class TamarindError(Exception):
    """Base class for all client errors. Carries a stable exit code.

    ``status_code`` is the HTTP status this error was mapped FROM, or None when it did
    not come from a response. It lives on the base class because callers legitimately
    branch on it — `deploy --create` treats 400/409 as "already exists" — and it used
    to exist only on `APIError`, so a 400 mapped to `ValidationError` lost it and the
    idempotency check silently stopped working.
    """

    exit_code: int = ExitCode.ERROR

    def __init__(
        self, message: str, *, detail: object | None = None, status_code: int | None = None
    ):
        super().__init__(message)
        self.message = message
        self.detail = detail
        self.status_code = status_code


class AuthError(TamarindError):
    exit_code = ExitCode.AUTH


class NotFoundError(TamarindError):
    exit_code = ExitCode.NOT_FOUND


class ValidationError(TamarindError):
    exit_code = ExitCode.VALIDATION


class RateLimitError(TamarindError):
    exit_code = ExitCode.RATE_LIMIT


class BudgetError(TamarindError):
    """The request was rejected because account usage/credits are exhausted."""

    exit_code = ExitCode.BUDGET


class JobTimeoutError(TamarindError):
    """A `wait`/`--wait` deadline elapsed before the job reached a terminal state.

    Its own exit code so agents can tell "still running when I gave up" apart
    from a real failure. Named to avoid shadowing the builtin ``TimeoutError``.
    """

    exit_code = ExitCode.TIMEOUT


class APIError(TamarindError):
    """A non-2xx response that doesn't map to a more specific error."""

    def __init__(self, message: str, *, status_code: int, detail: object | None = None):  # noqa: D107
        super().__init__(message, detail=detail)
        self.status_code = status_code
