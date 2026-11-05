"""The Agent API's HTTP boundary: version header, retries, rate limits, idempotency.

Every request goes through :meth:`AgentTransport.call` with an ``operationId`` from
:data:`~tamarind.agent._contract.OPERATIONS`, which fixes its method, path, whether it
takes an ``Idempotency-Key`` and whether a retry is safe.

- ``Tamarind-Version`` is sent on every request, so a later breaking change never
  reaches code written against this SDK.
- A 429 waits ``Retry-After`` (else ``x-ratelimit-reset``) seconds and tries again, up to
  ``max_rate_limit_wait`` per wait; a longer wait is raised as :class:`RateLimitError`
  rather than slept through (the hourly message limit can be most of an hour away).
- A lost response, 5xx, or a problem marked ``retryable`` is retried with backoff, but
  only for an operation where that cannot apply the request twice.
- An operation that takes ``Idempotency-Key`` gets one per logical call (the caller's, or
  a fresh UUID), reused on every retry of that call: a retried send never starts a second
  reply.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
import random
import time
from typing import Any
from urllib.parse import quote
import uuid

import httpx

from tamarind.errors import BudgetError, RateLimitError, TamarindError
from tamarind.http import HTTPClient, map_error

from ._contract import API_VERSION, OPERATIONS, VERSION_HEADER, Operation

DEFAULT_MAX_RETRIES = 3
DEFAULT_MAX_RATE_LIMIT_WAIT = 60.0
_RETRYABLE_STATUS = frozenset({500, 502, 503, 504})
# The operations whose answer is a 302 to a presigned URL. Any other redirect is an error:
# it is not followed (it would carry the API key) and not returned as a success.
REDIRECTING = frozenset({"downloadChatFile", "getCandidateStructure"})


def build_path(template: str, path_params: Mapping[str, str]) -> str:
    """Fill ``{name}`` segments, each percent-encoded whole (an id is never a path)."""
    path = template
    for name, value in path_params.items():
        if not isinstance(value, str) or not value:
            raise ValueError(f"{name} must be a non-empty string")
        path = path.replace("{" + name + "}", quote(value, safe=""))
    if "{" in path:
        raise ValueError(f"missing path parameter for {template}")
    return path


def wait_seconds(resp: httpx.Response) -> float | None:
    """How long the server asked us to wait: ``Retry-After``, else ``x-ratelimit-reset``."""
    for name in ("Retry-After", "x-ratelimit-reset"):
        raw = resp.headers.get(name)
        if raw is None:
            continue
        try:
            value = float(raw.strip())
        except ValueError:
            continue  # an HTTP-date Retry-After: fall through to the reset header
        if value >= 0:
            return value
    return None


def _problem(resp: httpx.Response) -> Mapping[str, Any]:
    try:
        body = resp.json()
    except ValueError:
        return {}
    return body if isinstance(body, dict) else {}


class AgentTransport:
    """Sends Agent API requests for the resource layer, with the policy above."""

    def __init__(
        self,
        http: HTTPClient,
        *,
        version: str = API_VERSION,
        max_retries: int = DEFAULT_MAX_RETRIES,
        max_rate_limit_wait: float = DEFAULT_MAX_RATE_LIMIT_WAIT,
        sleep: Callable[[float], None] = time.sleep,
    ):
        self.http = http
        self.version = version
        self.max_retries = max_retries
        self.max_rate_limit_wait = max_rate_limit_wait
        self.sleep = sleep

    def headers(self, extra: Mapping[str, str | None] | None = None) -> dict[str, str | None]:
        return {VERSION_HEADER: self.version, **(extra or {})}

    def call(
        self,
        operation_id: str,
        path_params: Mapping[str, str] | None = None,
        *,
        params: Mapping[str, Any] | None = None,
        json: Any | None = None,
        idempotency_key: str | None = None,
        timeout: float | None = None,
        retry_safe: bool | None = None,
    ) -> httpx.Response:
        """Send one logical call, retrying as its operation allows; non-2xx raises.

        ``retry_safe`` narrows the operation's own flag for one call whose body makes a
        repeat unsafe (an approval resolved with options is answered 409 the second time).
        """
        op = OPERATIONS[operation_id]
        if retry_safe is False:
            op = op._replace(retry_safe=False)
        path = build_path(op.path, path_params or {})
        extra: dict[str, str | None] = {}
        if op.idempotency_key:
            if idempotency_key is not None and not idempotency_key.strip():
                # The server refuses a blank key; never swap in a fresh one, or a caller
                # that persisted "" would get a new key, and a new effect, every retry.
                raise ValueError("idempotency_key must not be blank")
            extra["Idempotency-Key"] = idempotency_key or str(uuid.uuid4())
        elif idempotency_key is not None:
            raise ValueError(f"{operation_id} does not take an Idempotency-Key")
        headers = self.headers(extra)
        attempt = 0
        while True:
            try:
                resp = self.http.send(
                    op.method, path, params=dict(params or {}), headers=headers, json=json,
                    timeout=timeout,
                )
            except httpx.HTTPError as exc:
                if op.retry_safe and attempt < self.max_retries:
                    attempt += 1
                    self.sleep(backoff(attempt))
                    continue
                raise TamarindError(
                    f"Network error talking to {self.http.base_url}: {exc}"
                    + ("" if op.retry_safe else " The request may have been applied; check before retrying.")
                ) from exc
            if resp.is_success or (resp.is_redirect and operation_id in REDIRECTING):
                return resp
            delay = self._retry_delay(op, resp, attempt)
            if delay is None:
                raise agent_error(resp, request_path=path)
            attempt += 1
            self.sleep(delay)

    def _retry_delay(self, op: Operation, resp: httpx.Response, attempt: int) -> float | None:
        """Seconds to wait before retrying ``resp``, or None to raise it now."""
        if attempt >= self.max_retries:
            return None
        if resp.status_code == 429:
            # A 429 is a refusal before anything ran, so it is safe to retry for any op.
            asked = wait_seconds(resp)
            delay = asked if asked is not None else backoff(attempt + 1)
            return delay if delay <= self.max_rate_limit_wait else None
        if not op.retry_safe:
            return None
        if resp.status_code in _RETRYABLE_STATUS or _problem(resp).get("retryable") is True:
            asked = wait_seconds(resp)
            if asked is not None:
                return asked if asked <= self.max_rate_limit_wait else None
            return backoff(attempt + 1)
        return None

    @contextmanager
    def open_stream(
        self, path: str, *, params: Mapping[str, Any], last_event_id: str | None
    ) -> Iterator[httpx.Response]:
        """One SSE connection; the caller reconnects. Non-2xx is read and returned as-is."""
        headers = self.headers({"Accept": "text/event-stream", "Last-Event-ID": last_event_id})
        # The server pings every 15 s, so 60 s of silence is a dead connection: the read
        # timeout ends it and the stream reconnects from its cursor.
        timeout = httpx.Timeout(30.0, read=60.0)
        with self.http.stream("GET", path, params=dict(params), headers=headers,
                              timeout=timeout) as resp:
            if not resp.is_success:
                resp.read()
            yield resp


def backoff(attempt: int, *, base: float = 0.5, cap: float = 30.0) -> float:
    """Full-jitter exponential backoff for retry ``attempt`` (1-based)."""
    return random.uniform(0, min(cap, base * (2 ** max(attempt - 1, 0))))


def agent_error(resp: httpx.Response, *, request_path: str) -> TamarindError:
    """The typed error for an Agent API refusal.

    The shared mapping, plus what is specific to this API: 402 is a used-up budget, and a
    429 says how long to wait.
    """
    error = map_error(resp, request_path=request_path)
    if resp.status_code == 402:
        return BudgetError(error.message, detail=error.detail)
    if isinstance(error, RateLimitError):
        asked = wait_seconds(resp)
        if asked is not None:
            error.message = f"{error.message} (retry in {asked:g}s)"
    return error
