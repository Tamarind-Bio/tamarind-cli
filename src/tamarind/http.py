"""Thin HTTP transport shared by the REST and catalog clients.

Wraps ``httpx.Client`` with the ``x-api-key`` header the Tamarind API expects,
and maps non-2xx responses onto the typed errors in :mod:`tamarind.errors` so
callers (and the CLI's exit codes) get consistent behaviour.
"""

from __future__ import annotations

from typing import Any

import httpx

from .errors import (
    APIError,
    AuthError,
    NotFoundError,
    RateLimitError,
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
        headers = {
            "Accept": "application/json",
            # Brotli is still decoded transparently by httpx; we just don't want
            # surprises from upstream content-encoding negotiation.
            "Accept-Encoding": "identity",
            "User-Agent": f"{USER_AGENT}/{_version()}",
        }
        if api_key:
            headers["x-api-key"] = api_key
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
        json: Any | None = None,
        timeout: float | None = None,
    ) -> httpx.Response:
        if not self.api_key:
            raise AuthError(
                "No API key configured. Set TAMARIND_API_KEY, pass --api-key, "
                "or run `tamarind auth login`."
            )
        # Drop None-valued query params so we don't send `?x=None`.
        clean_params = (
            {k: v for k, v in params.items() if v is not None} if params else None
        )
        try:
            resp = self._client.request(
                method,
                path.lstrip("/"),
                params=clean_params,
                json=json,
                timeout=timeout if timeout is not None else httpx.USE_CLIENT_DEFAULT,
            )
        except httpx.HTTPError as exc:
            raise TamarindError(f"Network error talking to {self.base_url}: {exc}") from exc

        if resp.is_success:
            return resp
        raise _map_error(resp)

    def get_json(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        return _parse_json(self.request("GET", path, params=params))

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


def _extract_message(resp: httpx.Response) -> str:
    try:
        body = resp.json()
    except ValueError:
        return resp.text.strip() or resp.reason_phrase or f"HTTP {resp.status_code}"
    if isinstance(body, dict):
        for key in ("error", "message", "detail"):
            if body.get(key):
                return str(body[key])
    if isinstance(body, str):
        return body
    return resp.reason_phrase or f"HTTP {resp.status_code}"


def _map_error(resp: httpx.Response) -> TamarindError:
    msg = _extract_message(resp)
    code = resp.status_code
    ml = msg.lower()
    auth_ish = "api key" in ml or "api-key" in ml or "apikey" in ml or "unauthorized" in ml
    notfound_ish = "not found" in ml or "does not exist" in ml or "no such" in ml
    if code == 401:
        return AuthError(f"Unauthorized: {msg}")
    if code == 403:
        return AuthError(f"Access denied: {msg}")
    if code == 404:
        return NotFoundError(msg)
    if code == 400:
        # The API uses 400 for several distinct failures; classify by message so
        # exit codes are consistent: bad/missing key -> auth (3), missing job/file
        # -> not-found (4), otherwise a genuine validation error (5).
        if auth_ish:
            return AuthError(f"Unauthorized: {msg}")
        if notfound_ish:
            return NotFoundError(msg)
        return ValidationError(msg)
    if code == 429:
        return RateLimitError(f"Rate limited: {msg}")
    return APIError(msg, status_code=code)


def _version() -> str:
    from . import __version__

    return __version__
