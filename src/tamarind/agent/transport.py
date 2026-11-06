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
import threading
import time
from typing import Any
from urllib.parse import quote
import uuid

import httpx

from tamarind.errors import (
    APIError,
    ArgumentError,
    BudgetError,
    JobTimeoutError,
    RateLimitError,
    TamarindError,
)
from tamarind.http import HTTPClient, map_error

from ._contract import API_VERSION, OPERATIONS, VERSION_HEADER, Operation

_monotonic = time.monotonic  # the bounded attempt's clock
DEFAULT_MAX_RETRIES = 3
DEFAULT_MAX_RATE_LIMIT_WAIT = 60.0
_RETRYABLE_STATUS = frozenset({500, 502, 503, 504})
# The operations whose answer is a 302 to a presigned URL. Any other redirect (a 307 to a
# proxy's login page, say) is an error:
# it is not followed (it would carry the API key) and not returned as a success.
REDIRECTING = frozenset({"downloadChatFile", "getCandidateStructure"})


def build_path(template: str, path_params: Mapping[str, str]) -> str:
    """Fill ``{name}`` segments, each percent-encoded whole (an id is never a path)."""
    path = template
    for name, value in path_params.items():
        if not isinstance(value, str) or not value:
            raise ArgumentError(f"{name} must be a non-empty string")
        path = path.replace("{" + name + "}", quote(value, safe=""))
    if "{" in path:
        raise ArgumentError(f"missing path parameter for {template}")
    return path


def wait_seconds(resp: httpx.Response) -> float | None:
    """How long the server asked us to wait: ``Retry-After``, else, on a 429 only,
    ``x-ratelimit-reset``. That header rides on every counted send (a retryable 500
    included) and says when the hourly count resets, not when to retry."""
    names = ("Retry-After", "x-ratelimit-reset") if resp.status_code == 429 else ("Retry-After",)
    for name in names:
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


class DeadlineExceeded(JobTimeoutError):
    """A call did not finish inside its wall-clock deadline (see ``call_within``)."""


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

    def _prepare(self, operation_id: str, path_params: Mapping[str, str] | None,
                 idempotency_key: str | None, op: Operation | None = None,
                 ) -> tuple[Operation, str, dict[str, str | None]]:
        """The operation, its path, and its extra headers, with the Idempotency-Key fixed
        here once: before a thread starts, so every error can name it."""
        op = op or OPERATIONS[operation_id]
        path = build_path(op.path, path_params or {})
        extra: dict[str, str | None] = {}
        if op.idempotency_key:
            if idempotency_key is not None and not idempotency_key.strip():
                # The server refuses a blank key; never swap in a fresh one, or a caller
                # that persisted "" would get a new key, and a new effect, every retry.
                raise ArgumentError("idempotency_key must not be blank")
            extra["Idempotency-Key"] = idempotency_key or str(uuid.uuid4())
        elif idempotency_key is not None:
            raise ArgumentError(f"{operation_id} does not take an Idempotency-Key")
        return op, path, extra

    def _network_error(self, exc: Exception, op: Operation, key: str | None) -> TamarindError:
        message = f"Network error talking to {self.http.base_url}: {exc}."
        if not op.retry_safe:
            message += " The request may have been applied; check before retrying."
        return TamarindError(message + _retry_with(key), detail=_key_detail(key))

    def _refusal(self, operation_id: str, resp: httpx.Response, path: str, key: str | None,
                 ) -> TamarindError | None:
        """The error for a response that is neither a success nor a download's 302; None for
        a response that is fine to return."""
        if resp.is_success or (resp.status_code == 302 and operation_id in REDIRECTING):
            return None
        if resp.is_redirect:
            # Never the body: a proxy's HTML page can echo the URL, presigned or not.
            return APIError(f"The Agent API answered an unexpected redirect (HTTP {resp.status_code}).",
                            status_code=resp.status_code)
        error = agent_error(resp, request_path=path)
        if key and resp.status_code >= 500:
            # Unknown whether it was applied: the same key makes the retry safe.
            error.message = error.message + _retry_with(key)
            error.detail = {**(error.detail if isinstance(error.detail, dict) else {}), **_key_detail(key)}
        return error

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
        max_retries: int | None = None,
    ) -> httpx.Response:
        """Send one logical call, retrying as its operation allows; non-2xx raises.

        ``retry_safe`` narrows the operation's own flag for one call whose body makes a
        repeat unsafe (an approval resolved with options is answered 409 the second time).
        ``max_retries`` overrides the transport's budget for one call (0: a caller that
        runs its own bounded loop).
        """
        budget = self.max_retries if max_retries is None else max_retries
        op = OPERATIONS[operation_id]
        if retry_safe is False:
            op = op._replace(retry_safe=False)
        op, path, extra = self._prepare(operation_id, path_params, idempotency_key, op)
        key = extra.get("Idempotency-Key")
        headers = self.headers(extra)
        attempt = 0
        while True:
            try:
                resp = self.http.send(
                    op.method, path, params=dict(params or {}), headers=headers, json=json,
                    timeout=timeout,
                )
            except httpx.HTTPError as exc:
                if op.retry_safe and attempt < budget:
                    attempt += 1
                    self.sleep(backoff(attempt))
                    continue
                raise self._network_error(exc, op, key) from exc
            error = self._refusal(operation_id, resp, path, key)
            if error is None:
                return resp
            if resp.is_redirect:
                raise error
            delay = self._retry_delay(op, resp, attempt, budget)
            if delay is None:
                raise error
            attempt += 1
            self.sleep(delay)

    def call_within(
        self,
        seconds: float,
        operation_id: str,
        path_params: Mapping[str, str] | None = None,
        *,
        params: Mapping[str, Any] | None = None,
        json: Any | None = None,
        idempotency_key: str | None = None,
    ) -> httpx.Response:
        """One attempt that ends ``seconds`` of wall-clock time after it starts, whatever
        the server does (:class:`DeadlineExceeded`).

        httpx's timeouts are per phase (connect, write, pool) and per chunk (read is
        inactivity), so on their own a slow connect plus a slow answer, or a body trickled a
        byte at a time, runs far past any one number. Three layers, so nothing outlives the
        deadline for long:

        - the attempt runs on a daemon thread and the caller stops waiting at the deadline;
        - the worker streams the answer and checks a monotonic deadline between chunks, then
          closes the response, so a trickling server cannot keep a worker (and a pooled
          connection) alive forever;
        - every httpx phase timeout is capped at ``seconds``, so no single phase outlasts it.

        No retries: a caller bounding by time is its own retry loop. A keyed call's
        Idempotency-Key is fixed before the thread starts and named in
        :class:`DeadlineExceeded`, since the deadline can fire after the write committed.
        """
        op, path, extra = self._prepare(operation_id, path_params, idempotency_key)
        key = extra.get("Idempotency-Key")
        headers = self.headers(extra)
        deadline = _monotonic() + max(seconds, 0.0)

        def expired() -> DeadlineExceeded:
            message = f"{operation_id} did not finish within {seconds:g}s." + _retry_with(key)
            return DeadlineExceeded(message, detail=_key_detail(key))

        outcome: list[tuple[bool, Any]] = []
        done = threading.Event()

        def attempt() -> None:
            try:
                outcome.append((True, self._attempt_streamed(
                    operation_id, op, path, headers, key, params, json, seconds, deadline, expired)))
            except BaseException as exc:  # noqa: BLE001 - handed to the waiting caller
                outcome.append((False, exc))
            finally:
                done.set()

        threading.Thread(target=attempt, name=f"agent-{operation_id}", daemon=True).start()
        if not done.wait(max(seconds, 0.0)):
            raise expired()
        ok, value = outcome[0]
        if ok:
            return value  # type: ignore[no-any-return]
        raise value

    def _attempt_streamed(
        self, operation_id: str, op: Operation, path: str, headers: dict[str, str | None],
        key: str | None, params: Mapping[str, Any] | None, json: Any | None, seconds: float,
        deadline: float, expired: Callable[[], DeadlineExceeded],
    ) -> httpx.Response:
        """The worker: stream one request, giving up at ``deadline`` between chunks."""
        phase = max(min(seconds, deadline - _monotonic()), 0.001)
        try:
            with self.http.stream(op.method, path, params=dict(params or {}), headers=headers,
                                  json=json, timeout=httpx.Timeout(phase)) as streamed:
                if _monotonic() >= deadline:
                    raise expired()
                body = bytearray()
                for chunk in streamed.iter_bytes():
                    body += chunk
                    if _monotonic() >= deadline:
                        raise expired()  # leaving the block closes the response
                resp = httpx.Response(streamed.status_code, headers=streamed.headers,
                                      content=bytes(body), request=streamed.request)
        except httpx.HTTPError as exc:
            raise self._network_error(exc, op, key) from exc
        error = self._refusal(operation_id, resp, path, key)
        if error is not None:
            raise error
        return resp

    def _retry_delay(self, op: Operation, resp: httpx.Response, attempt: int,
                     budget: int) -> float | None:
        """Seconds to wait before retrying ``resp``, or None to raise it now."""
        if attempt >= budget:
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


def _retry_with(key: str | None) -> str:
    """The way back from a lost answer to a keyed call: the same key applies it once."""
    if not key:
        return ""
    return (f" It may have been applied: retry with the same Idempotency-Key {key} "
            f"(CLI: --idempotency-key {key}) so it is applied once.")


def _key_detail(key: str | None) -> dict[str, str]:
    return {"idempotencyKey": key} if key else {}


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
