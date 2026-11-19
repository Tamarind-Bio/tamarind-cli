"""The one exception type the v1 SDK raises for an API error."""

from __future__ import annotations

from typing import Any

import httpx

from tamarind.errors import ExitCode, TamarindError

_AUTH_CODES = {"authentication_required", "invalid_api_key", "agent_trial_expired"}
_BUDGET_CODES = {"budget_exceeded", "quota_exceeded"}


class ProblemError(TamarindError):
    """An API answer that is not a success, carrying its RFC 9457 problem document.

    ``code`` is the stable, machine-readable reason: switch on it, not on ``title``.
    ``errors`` lists every field-level problem (``pointer``, ``detail``, ``suggestion``...).
    ``problem`` is the whole document, including any extension member such as
    ``existingId`` or ``currentVersion``.
    """

    def __init__(
        self,
        *,
        status: int,
        code: str,
        type: str = "about:blank",
        title: str = "",
        detail: str | None = None,
        errors: list[dict[str, Any]] | None = None,
        retryable: bool | None = None,
        request_id: str | None = None,
        problem: dict[str, Any] | None = None,
        headers: httpx.Headers | None = None,
    ):
        self.status = status
        self.code = code
        self.type = type
        self.title = title
        self.detail = detail
        self.errors = list(errors or [])
        self.retryable = retryable
        self.request_id = request_id
        self.problem = dict(problem or {})
        self.headers = headers if headers is not None else httpx.Headers()
        # TamarindError keeps ``detail`` too: here it is the problem's own ``detail``.
        super().__init__(self._message(), detail=detail)
        self.exit_code = _exit_code(status, code)

    @classmethod
    def from_response(cls, response: httpx.Response) -> "ProblemError":
        body: Any
        try:
            body = response.json()
        except ValueError:
            body = None
        status = response.status_code
        if isinstance(body, dict) and isinstance(body.get("code"), str):
            errors = body.get("errors")
            return cls(
                status=int(body.get("status") or status),
                code=body["code"],
                type=str(body.get("type") or "about:blank"),
                title=str(body.get("title") or ""),
                detail=body.get("detail") if isinstance(body.get("detail"), str) else None,
                errors=[item for item in errors if isinstance(item, dict)]
                if isinstance(errors, list)
                else None,
                retryable=body.get("retryable")
                if isinstance(body.get("retryable"), bool)
                else None,
                request_id=body.get("requestId") or response.headers.get("x-request-id"),
                problem=body,
                headers=response.headers,
            )
        # Not a problem document (a gateway or proxy answered): keep what there is.
        if isinstance(body, dict):
            text = str(body.get("message") or body.get("detail") or body.get("error") or "")
        else:
            text = response.text.strip()[:500]
        return cls(
            status=status,
            code=_status_code_name(status),
            title=response.reason_phrase,
            detail=text or None,
            request_id=response.headers.get("x-request-id"),
            problem=body if isinstance(body, dict) else None,
            headers=response.headers,
        )

    def _message(self) -> str:
        message = f"{self.status} {self.code}"
        if self.detail:
            message += f": {self.detail}"
        for item in self.errors[:5]:
            pointer = item.get("pointer") or ""
            text = item.get("detail") or item.get("code") or ""
            suggestion = item.get("suggestion")
            message += f"\n  {pointer} {text}".rstrip()
            if suggestion:
                message += f" (did you mean {suggestion!r}?)"
        if len(self.errors) > 5:
            message += f"\n  ... and {len(self.errors) - 5} more"
        return message


def _exit_code(status: int, code: str) -> int:
    if status == 401 or code in _AUTH_CODES:
        return ExitCode.AUTH
    if code in _BUDGET_CODES:
        return ExitCode.BUDGET
    if status == 404:
        return ExitCode.NOT_FOUND
    if status in (400, 422):
        return ExitCode.VALIDATION
    if status == 429:
        return ExitCode.RATE_LIMIT
    return ExitCode.ERROR


def _status_code_name(status: int) -> str:
    names = {
        400: "bad_request",
        401: "authentication_required",
        403: "forbidden",
        404: "not_found",
        409: "conflict",
        413: "payload_too_large",
        422: "unprocessable_content",
        429: "rate_limited",
        502: "bad_gateway",
        503: "service_unavailable",
        504: "gateway_timeout",
    }
    return names.get(status, "internal_error" if status >= 500 else f"http_{status}")
