"""Send v1 requests built by the generated client: auth, retries, idempotency, errors.

The generated endpoint modules own the wire shape (method, path, query and header
names, body). This module adds what every call shares: the ``x-api-key`` header,
an ``Idempotency-Key`` on the operations that take one, retries with backoff on 429
and 5xx that honor ``Retry-After``, and :class:`ProblemError` for every failure.
"""

from __future__ import annotations

import datetime
import email.utils
import enum
import random
import time
import types
import typing
import uuid
from collections.abc import Callable, Mapping
from typing import Any

import httpx
from dateutil.parser import isoparse

from tamarind.attribution import client_headers
from tamarind.errors import TamarindError
from tamarind.v1._contract import COMMA_JOINED_QUERY
from tamarind.v1._generated.types import UNSET, Unset
from tamarind.v1.errors import ProblemError

DEFAULT_BASE_URL = "https://api.tamarind.bio"
DEFAULT_TIMEOUT = 60.0
DEFAULT_MAX_RETRIES = 3
# Waits longer than this are not slept through; the error is raised instead.
MAX_RETRY_AFTER = 120.0
# Repeating these can't change anything. A DELETE is not here: after a lost answer a
# repeat could delete a file or tool someone just made at the freed path or name.
_SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


class Transport:
    def __init__(
        self,
        *,
        api_key: str | None,
        base_url: str,
        timeout: float,
        max_retries: int,
        version: str | None,
        http_client: httpx.Client | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ):
        headers = {
            "Accept": "application/json",
            "User-Agent": f"tamarind-cli/{_version()}",
            **client_headers(),
        }
        if api_key:
            headers["x-api-key"] = api_key
        self.base_url = base_url.rstrip("/")
        self.max_retries = max_retries
        self.version = version
        self._sleep = sleep
        self._client = http_client or httpx.Client(timeout=timeout)
        self._owns_client = http_client is None
        self._headers = headers
        # Signed storage URLs must never see the API key.
        self._storage_transport = httpx.HTTPTransport()
        self._storage = httpx.Client(transport=self._storage_transport, timeout=timeout)

    def close(self) -> None:
        if self._owns_client:
            self._client.close()
        self._storage.close()

    # -- API calls --------------------------------------------------------
    def call(
        self,
        endpoint: types.ModuleType,
        body: Any = UNSET,
        extra_headers: Mapping[str, str] | None = None,
        repeat_safe: bool = False,
        **arguments: Any,
    ) -> httpx.Response:
        """Build one request with ``endpoint._get_kwargs`` and send it.

        ``repeat_safe`` marks a request the contract says can be repeated (it is also
        implied by GET and by an operation that takes an ``Idempotency-Key``). A failure raised after retries
        carries ``idempotency_key``, so a caller can repeat the same intent safely.
        """
        build = endpoint._get_kwargs
        hints = _hints(build)
        unknown = set(arguments) - set(hints) - {"return", "body"}
        if unknown:
            raise TypeError(f"unexpected argument(s): {', '.join(sorted(unknown))}")
        values = {
            name: _coerce(hints.get(name), value)
            for name, value in arguments.items()
            if value is not None
        }
        if "idempotency_key" in hints and "idempotency_key" not in values:
            values["idempotency_key"] = str(uuid.uuid4())
        if self.version is not None:
            values.setdefault("tamarind_version", self.version)
        json_body = _json_body(body)
        if "body" in hints and json_body is not UNSET:
            values["body"] = _Body(json_body)
        elif json_body is not UNSET:
            raise TypeError(f"{endpoint.__name__.rsplit('.', 1)[-1]} takes no request body")
        request = build(**values)
        if json_body is not UNSET:
            request["json"] = json_body
        params = request.get("params")
        for name in COMMA_JOINED_QUERY.get(endpoint.__name__.rsplit(".", 1)[-1], ()):
            if params and isinstance(params.get(name), list):
                params[name] = ",".join(str(item) for item in params[name])
        headers = httpx.Headers(request.get("headers") or {})
        headers.update(extra_headers or {})
        # Repeatable when the contract says so: an operation that takes an Idempotency-Key
        # (a header added through extra_headers doesn't count), or one marked repeat-safe.
        repeat_safe = repeat_safe or "idempotency_key" in hints
        try:
            return self.send(
                request["method"].upper(),
                self.base_url + request["url"],
                params=request.get("params"),
                headers=headers,
                json=request.get("json"),
                repeat_safe=repeat_safe,
            )
        except TamarindError as error:
            # The key on the wire, so an inconclusive submit can be repeated without duplicating it.
            error.idempotency_key = headers.get("idempotency-key")  # type: ignore[attr-defined]
            raise

    def send(
        self,
        method: str,
        url: str,
        *,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | httpx.Headers | None = None,
        json: Any = None,
        repeat_safe: bool = False,
    ) -> httpx.Response:
        merged = httpx.Headers(self._headers)
        merged.update(headers or {})
        repeat_safe = repeat_safe or method in _SAFE_METHODS
        return self._with_retries(
            # Never follow a redirect with the key, even on a caller's client that would.
            lambda: self._client.request(
                method, url, params=params, headers=merged, json=json, follow_redirects=False
            ),
            repeat_safe=repeat_safe,
            api=True,
        )

    # -- storage (signed URLs) --------------------------------------------
    def require_secure(self, url: object) -> None:
        """Signed query strings are credentials: never send them, or a file, in the clear,
        unless the API itself is plain HTTP (a local development server)."""
        secure = isinstance(url, str) and url.startswith("https://")
        local = isinstance(url, str) and not self.base_url.startswith("https://")
        if not (secure or local):
            raise TamarindError("The upload session named a storage URL that isn't HTTPS.")

    def put_signed(self, url: str, content: Any, headers: Mapping[str, str]) -> httpx.Response:
        """PUT bytes to a signed storage URL, without the API key."""
        self.require_secure(url)
        return self._with_retries(
            lambda: self._put_unlogged(url, content(), headers),
            repeat_safe=True,
            api=False,
        )

    def _put_unlogged(self, url: str, content: Any, headers: Mapping[str, str]) -> httpx.Response:
        """Send a PUT below ``httpx.Client``, whose INFO log line would carry the signed URL
        (a credential) into the application's logs."""
        request = self._storage.build_request("PUT", url, content=content, headers=dict(headers))
        response = self._storage_transport.handle_request(request)
        try:
            response.read()
        finally:
            response.close()
        response.request = request
        return response

    # -- retries ----------------------------------------------------------
    def _with_retries(
        self, send: Callable[[], httpx.Response], *, repeat_safe: bool, api: bool
    ) -> httpx.Response:
        attempt = 0
        while True:
            try:
                response = send()
            except httpx.TransportError as exc:
                # A connection that never opened sent nothing, so any request may retry it.
                never_sent = isinstance(
                    exc, (httpx.ConnectError, httpx.ConnectTimeout, httpx.PoolTimeout)
                )
                if attempt < self.max_retries and (repeat_safe or never_sent):
                    self._sleep(_backoff(attempt))
                    attempt += 1
                    continue
                raise TamarindError(f"Network error: {exc}") from exc
            if response.is_success:
                return response
            error = ProblemError.from_response(response) if api else _storage_error(response)
            delay = _retry_delay(response, error, repeat_safe=repeat_safe, attempt=attempt)
            if delay is None or attempt >= self.max_retries:
                raise error
            self._sleep(delay)
            attempt += 1


def decode(response: httpx.Response) -> Any:
    """The answer as JSON, ``None`` for an empty answer, or the raw bytes."""
    if response.status_code == 204 or not response.content:
        return None
    media = response.headers.get("content-type", "").split(";")[0].strip().lower()
    if media == "application/json" or media.endswith("+json"):
        return response.json()
    return response.content


class _Body:
    """Hands a plain JSON body to a generated ``_get_kwargs`` (which calls ``to_dict``)."""

    def __init__(self, value: Any):
        self._value = value

    def to_dict(self) -> Any:
        return self._value


def _json_body(body: Any) -> Any:
    if body is UNSET or body is None:
        return UNSET
    to_dict = getattr(body, "to_dict", None)
    return to_dict() if callable(to_dict) else body


def _retry_delay(
    response: httpx.Response, error: ProblemError, *, repeat_safe: bool, attempt: int
) -> float | None:
    if error.retryable is False or response.headers.get("idempotent-replayed") == "true":
        return None
    status = response.status_code
    retry_after = _retry_after(response.headers.get("retry-after"))
    if status == 429 or status == 503 or (status == 409 and retry_after is not None):
        # Refused before any work, or the server asked us to come back.
        pass
    elif status >= 500 and (repeat_safe or error.retryable is True):
        pass
    else:
        return None
    if retry_after is not None:
        return retry_after if retry_after <= MAX_RETRY_AFTER else None
    return _backoff(attempt)


def _retry_after(value: str | None) -> float | None:
    if not value:
        return None
    value = value.strip()
    try:
        return max(0.0, float(value))
    except ValueError:
        pass
    try:
        when = email.utils.parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    if when.tzinfo is None:
        when = when.replace(tzinfo=datetime.timezone.utc)
    return max(0.0, (when - datetime.datetime.now(datetime.timezone.utc)).total_seconds())


def _backoff(attempt: int) -> float:
    return min(8.0, 0.5 * 2**attempt) * (0.5 + random.random() / 2)


def _storage_error(response: httpx.Response) -> ProblemError:
    return ProblemError(
        status=response.status_code,
        code="storage_error",
        title=response.reason_phrase,
        detail=f"signed URL answered {response.status_code}: {response.text.strip()[:300]}",
        headers=response.headers,
    )


_HINTS: dict[Callable[..., Any], dict[str, Any]] = {}


def _hints(function: Callable[..., Any]) -> dict[str, Any]:
    if function not in _HINTS:
        _HINTS[function] = typing.get_type_hints(function)
    return _HINTS[function]


def _coerce(hint: Any, value: Any) -> Any:
    """Turn plain strings into the enums and datetimes a generated signature expects."""
    members = [m for m in _members(hint) if m is not Unset and m is not type(None)]
    if any(typing.get_origin(m) is list for m in members) and not isinstance(value, list):
        value = [value]
    if isinstance(value, list):
        inner = [a for m in members if typing.get_origin(m) is list for a in typing.get_args(m)]
        return [_coerce_scalar(inner, item) for item in value] if inner else value
    return _coerce_scalar(members, value)


def _coerce_scalar(members: list[Any], value: Any) -> Any:
    if isinstance(value, str):
        for member in members:
            if isinstance(member, type) and issubclass(member, enum.Enum):
                try:
                    return member(value)
                except ValueError:
                    allowed = ", ".join(str(item.value) for item in member)
                    raise ValueError(f"{value!r} is not one of: {allowed}") from None
            if member is datetime.datetime:
                return isoparse(value)
            if member is datetime.date:
                return datetime.date.fromisoformat(value)
    return value


def _members(hint: Any) -> list[Any]:
    if hint is None:
        return []
    origin = typing.get_origin(hint)
    if origin is typing.Union or origin is types.UnionType:
        return [m for arg in typing.get_args(hint) for m in _members(arg)]
    return [hint]


def _version() -> str:
    from tamarind import __version__

    return __version__


__all__ = ["DEFAULT_BASE_URL", "Transport", "decode", "UNSET"]
