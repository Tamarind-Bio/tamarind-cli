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

from collections.abc import Callable
from typing import Any


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

    def __init__(self, message: str, *, status_code: int, detail: object | None = None):
        super().__init__(message, detail=detail)
        self.status_code = status_code


class CustomToolError(TamarindError):
    """Base class for Custom Tools SDK failures."""


class CustomToolValidationError(ValidationError, CustomToolError):
    """The server rejected a Custom Tool state or source contract."""


class CustomToolNotFoundError(NotFoundError, CustomToolError):
    """The Custom Tool does not exist or is not visible to the caller."""


class CustomToolExistsError(CustomToolValidationError):
    """A Custom Tool already owns the requested organization-scoped name."""


class CustomToolNotDeployableError(CustomToolValidationError):
    """The Custom Tool cannot be built or published from its current state."""


class StaleCustomToolError(CustomToolError):
    """A selected Tool generation or source revision is no longer current."""


class CustomToolUploadError(CustomToolError):
    """Packaging or direct source upload failed."""


class CustomToolBuildFailedError(CustomToolError):
    """A Custom Tool Version reached an unsuccessful terminal state."""

    exit_code = ExitCode.JOB_FAILED


class CustomToolBuildNotInProgressError(CustomToolError):
    """Cancellation was requested for a Version without an active build."""


class CustomToolBuildInProgressError(CustomToolError):
    """A new build was requested while this Tool already has an active build."""


class CustomToolBuildTimeoutError(CustomToolError):
    """Local monitoring timed out without cancelling the remote build."""

    exit_code = ExitCode.TIMEOUT


class CustomToolGitHubConnectionFailedError(CustomToolError):
    """A GitHub source connection reached a failed or disconnected state."""


class CustomToolGitHubConnectionTimeoutError(CustomToolError):
    """Local GitHub connection monitoring timed out without cancelling remote work."""

    exit_code = ExitCode.TIMEOUT


class CustomToolGitHubAuthorizationRequiredError(CustomToolError):
    """The GitHub App needs one browser authorization before the request can resume."""

    def __init__(
        self,
        message: str,
        *,
        authorization_url: str,
        resume_token: str,
        expires_at: str,
        detail: object | None = None,
        resume: Callable[[], Any] | None = None,
    ):
        super().__init__(message, detail=detail)
        self.authorization_url = authorization_url
        self.resume_token = resume_token
        self.expires_at = expires_at
        self._resume = resume

    def bind_resume(
        self, resume: Callable[[], Any]
    ) -> "CustomToolGitHubAuthorizationRequiredError":
        """Return this authorization request with its exact retry operation bound."""
        return type(self)(
            self.message,
            authorization_url=self.authorization_url,
            resume_token=self.resume_token,
            expires_at=self.expires_at,
            detail=self.detail,
            resume=resume,
        )

    def resume(self) -> Any:
        """Retry the exact operation that produced this authorization request."""
        if self._resume is None:
            raise TamarindError("GitHub authorization cannot be resumed from this context")
        return self._resume()
