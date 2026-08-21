"""Thin HTTP transport shared by the REST and catalog clients.

Wraps ``httpx.Client`` with the ``x-api-key`` header the Tamarind API expects,
and maps non-2xx responses onto the typed errors in :mod:`tamarind.errors` so
callers (and the CLI's exit codes) get consistent behaviour.
"""

from __future__ import annotations

import re
from typing import Any

import httpx

from .errors import (
    APIError,
    AuthError,
    BudgetError,
    CustomToolBuildInProgressError,
    CustomToolBuildNotInProgressError,
    CustomToolExistsError,
    CustomToolNotFoundError,
    CustomToolNotDeployableError,
    CustomToolUploadError,
    CustomToolValidationError,
    NotFoundError,
    RateLimitError,
    StaleCustomToolError,
    TamarindError,
    ValidationError,
)

DEFAULT_TIMEOUT = 120.0
USER_AGENT = "tamarind-cli"


class HTTPClient:
    """A small wrapper around ``httpx.Client`` keyed by base URL + API key."""

    def __init__(
        self,
        base_url: str,
        api_key: str | None,
        *,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        self.base_url = base_url
        self.api_key = api_key
        self._timeout = timeout
        headers = {
            "Accept": "application/json",
            # Brotli is still decoded transparently by httpx; we just don't want
            # surprises from upstream content-encoding negotiation.
            "Accept-Encoding": "identity",
            "User-Agent": f"{USER_AGENT}/{_version()}",
        }
        if api_key:
            headers["x-api-key"] = api_key
        self._headers = headers
        self._client = httpx.Client(base_url=base_url, headers=headers, timeout=timeout)

    # -- lifecycle ---------------------------------------------------------
    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "HTTPClient":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    # -- requests ----------------------------------------------------------
    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str | None] | None = None,
        json: Any | None = None,
        timeout: float | None = None,
    ) -> httpx.Response:
        if not self.api_key:
            raise AuthError(
                "No API key configured. Set TAMARIND_API_KEY, pass --api-key, "
                "or run `tamarind auth login`."
            )
        clean_params = _without_none_values(params)
        clean_headers = _without_none_values(headers)
        try:
            resp = self._client.request(
                method,
                path.lstrip("/"),
                params=clean_params,
                headers=clean_headers,
                json=json,
                timeout=timeout if timeout is not None else httpx.USE_CLIENT_DEFAULT,
            )
        except httpx.HTTPError as exc:
            raise TamarindError(f"Network error talking to {self.base_url}: {exc}") from exc

        if resp.is_success:
            return resp
        raise _map_error(resp)

    async def request_async(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str | None] | None = None,
        json: Any | None = None,
        timeout: float | None = None,
    ) -> httpx.Response:
        """Perform one cancellable request for a wall-clock-bounded operation.

        The client is scoped to the coroutine so cancellation closes its socket
        before returning. Synchronous calls keep their pooled client above.
        """
        if not self.api_key:
            raise AuthError(
                "No API key configured. Set TAMARIND_API_KEY, pass --api-key, "
                "or run `tamarind auth login`."
            )
        clean_params = _without_none_values(params)
        clean_headers = _without_none_values(headers)
        try:
            async with httpx.AsyncClient(
                base_url=self.base_url,
                headers=self._headers,
                timeout=self._timeout,
            ) as client:
                resp = await client.request(
                    method,
                    path.lstrip("/"),
                    params=clean_params,
                    headers=clean_headers,
                    json=json,
                    timeout=timeout if timeout is not None else httpx.USE_CLIENT_DEFAULT,
                )
        except httpx.HTTPError as exc:
            raise TamarindError(f"Network error talking to {self.base_url}: {exc}") from exc

        if resp.is_success:
            return resp
        raise _map_error(resp)

    def get_json(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> Any:
        return _parse_json(self.request("GET", path, params=params, timeout=timeout))

    def post_json(self, path: str, *, json: Any | None = None) -> Any:
        return _parse_json(self.request("POST", path, json=json))

    def delete_json(
        self, path: str, *, params: dict[str, Any] | None = None, json: Any | None = None
    ) -> Any:
        return _parse_json(self.request("DELETE", path, params=params, json=json))


def _parse_json(resp: httpx.Response) -> Any:
    text = resp.text.strip()
    if not text:
        return None
    try:
        return resp.json()
    except ValueError:
        # Some endpoints (e.g. /result) return a bare presigned URL string.
        return text


def _without_none_values(values: dict[str, Any] | None) -> dict[str, Any] | None:
    """Omit absent optional wire values before handing them to HTTPX."""
    if not values:
        return None
    retained = {key: value for key, value in values.items() if value is not None}
    return retained or None


def _error_body(resp: httpx.Response) -> tuple[object | None, bool]:
    try:
        return resp.json(), True
    except ValueError:
        return None, False


def _extract_message(resp: httpx.Response, body: object | None, *, is_json: bool) -> str:
    if not is_json:
        return resp.text.strip() or resp.reason_phrase or f"HTTP {resp.status_code}"
    if isinstance(body, dict):
        for key in ("error", "message", "detail", "title"):
            if body.get(key):
                return str(body[key])
    if isinstance(body, str):
        return body
    return resp.reason_phrase or f"HTTP {resp.status_code}"


def _map_error(resp: httpx.Response) -> TamarindError:
    body, is_json = _error_body(resp)
    detail = body if is_json else None
    msg = _extract_message(resp, body, is_json=is_json)
    code = resp.status_code
    problem_code = _problem_code(detail)
    path_segments = tuple(segment for segment in resp.request.url.path.split("/") if segment)
    not_found_error = CustomToolNotFoundError if "custom-tools" in path_segments else NotFoundError
    if problem_code == "custom_tool_not_found" or problem_code == "custom_tool_version_not_found":
        return CustomToolNotFoundError(msg, detail=detail)
    if problem_code == "custom_tool_name_taken":
        return CustomToolExistsError(msg, detail=detail)
    if problem_code == "custom_tool_not_deployable":
        return CustomToolNotDeployableError(msg, detail=detail)
    if problem_code == "invalid_custom_tool_config" or problem_code == "invalid_custom_tool_source":
        return CustomToolValidationError(msg, detail=detail)
    if problem_code in {"custom_tool_generation_mismatch", "custom_tool_source_changed"}:
        return StaleCustomToolError(msg, detail=detail)
    if (
        problem_code == "custom_tool_source_digest_mismatch"
        or problem_code == "custom_tool_upload_not_found"
    ):
        return CustomToolUploadError(msg, detail=detail)
    if problem_code == "custom_tool_build_in_progress":
        return CustomToolBuildInProgressError(msg, detail=detail)
    if problem_code == "custom_tool_build_not_cancellable":
        return CustomToolBuildNotInProgressError(msg, detail=detail)
    ml = msg.lower()
    auth_ish = "api key" in ml or "api-key" in ml or "apikey" in ml or "unauthorized" in ml
    resource = (
        r"(?:budget|quota|weighted[-_\s]?hours?|credits?|account balance|funds|"
        r"spend(?:ing)? limit|usage (?:limit|cap))"
    )
    exhausted = (
        r"(?:exceed(?:ed|s)?|exhaust(?:ed|ion)?|deplet(?:ed|ion)?|reached|"
        r"insufficient|empty|zero|out of|not enough|unavailable)"
    )
    # A resource word alone is not enough: policy/admin endpoints can mention
    # "budget", "quota", or "credit" without the account being exhausted.
    budget_ish = bool(
        re.search(rf"\b{resource}\b.{{0,80}}\b{exhausted}\b", ml)
        or re.search(rf"\b{exhausted}\b.{{0,80}}\b{resource}\b", ml)
    )
    notfound_ish = "not found" in ml or "does not exist" in ml or "no such" in ml
    if code == 401:
        return AuthError(f"Unauthorized: {msg}", detail=detail)
    if code == 403:
        if auth_ish:
            return AuthError(f"Access denied: {msg}", detail=detail)
        if budget_ish:
            return BudgetError(f"Budget or quota rejected the request: {msg}", detail=detail)
        return APIError(f"Access denied: {msg}", status_code=code, detail=detail)
    if code == 404:
        return not_found_error(msg, detail=detail)
    if code == 400:
        # The API uses 400 for several distinct failures; classify by message so
        # exit codes are consistent: bad/missing key -> auth (3), missing job/file
        # -> not-found (4), otherwise a genuine validation error (5).
        if auth_ish:
            return AuthError(f"Unauthorized: {msg}", detail=detail)
        if notfound_ish:
            return not_found_error(msg, detail=detail)
        return ValidationError(msg, detail=detail)
    if code == 429:
        return RateLimitError(f"Rate limited: {msg}", detail=detail)
    if code == 422:
        return ValidationError(msg, detail=detail)
    return APIError(msg, status_code=code, detail=detail)


def _problem_code(body: object | None) -> str | None:
    value = body.get("code") if isinstance(body, dict) else None
    return str(value) if value else None


def _version() -> str:
    from . import __version__

    return __version__
