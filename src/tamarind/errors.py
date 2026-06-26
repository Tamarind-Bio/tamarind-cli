"""Exception types and exit codes for the Tamarind client.

Exit codes are stable so agents and CI can branch on them:

    0  success
    1  generic / unexpected error
    2  usage error (bad arguments) — Typer's default
    3  authentication error (no key, or 401)
    4  not found (404)
    5  validation error (a job's settings failed validate-job, or a 400)
    6  rate limited (429)
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


class TamarindError(Exception):
    """Base class for all client errors. Carries a stable exit code."""

    exit_code: int = ExitCode.ERROR

    def __init__(self, message: str, *, detail: object | None = None):
        super().__init__(message)
        self.message = message
        self.detail = detail


class AuthError(TamarindError):
    exit_code = ExitCode.AUTH


class NotFoundError(TamarindError):
    exit_code = ExitCode.NOT_FOUND


class ValidationError(TamarindError):
    exit_code = ExitCode.VALIDATION


class RateLimitError(TamarindError):
    exit_code = ExitCode.RATE_LIMIT


class APIError(TamarindError):
    """A non-2xx response that doesn't map to a more specific error."""

    def __init__(self, message: str, *, status_code: int, detail: object | None = None):
        super().__init__(message, detail=detail)
        self.status_code = status_code
