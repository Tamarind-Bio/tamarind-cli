"""A service account's OAuth client credentials, traded for one-hour access tokens.

A service account made OAuth-only has a client ID (the account's ID) and a client secret
that works in one place: the token endpoint on the website host,
``POST <api base>/oauth/token`` with ``grant_type=client_credentials``. The same endpoint
serves the classic API and the v1 API. It answers with an access token good for an hour,
sent like an API key (``x-api-key``) wherever one goes.

One :class:`ClientCredentials` keeps one token in memory and hands it to every request. It
fetches the first token when a request needs one, renews it a minute before it runs out
(keeping it for that minute if the renewal fails), and renews it once more when a request
sent with it is refused with 401. Clients made in
one process with the same ID and secret share one (:func:`shared`), so any number of
clients and threads in a process need one token an hour. Nothing is written to disk, and
neither the secret nor a token is ever logged, shown or put in an error.

The token endpoint allows 600 tokens an hour per account and 300 requests in 10 minutes
per network. Past either it answers 429 with ``Retry-After``. A wait of up to two minutes
is slept through. A longer one raises :class:`~tamarind.errors.RateLimitError`, and no
token is asked for again until the wait is over.
"""

from __future__ import annotations

import base64
import hashlib
import math
import threading
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Any
from urllib.parse import quote

import httpx

from .attribution import client_headers
from .errors import APIError, AuthError, RateLimitError, TamarindError, UsageError

TOKEN_PATH = "oauth/token"
DEFAULT_TIMEOUT = 30.0
MAX_RETRIES = 3
# A token is renewed this long before it runs out, and a 401 renews it at most this often.
RENEW_BEFORE = 60.0
# Waits longer than this are not slept through; the error is raised instead.
MAX_WAIT = 120.0
# A token this close to running out is not sent; an early renewal that failed is tried
# again after RETRY_EARLY_RENEWAL seconds.
EXPIRY_SLACK = 5.0
RETRY_EARLY_RENEWAL = 10.0
# The lifetime assumed when an answer doesn't give one (ours always does: an hour).
_ASSUMED_LIFETIME = 300.0
_LOOPBACK = {"localhost", "127.0.0.1", "::1"}


def token_url_for(api_base: str) -> str:
    """The token endpoint for a classic API base (``https://app.tamarind.bio/api/``)."""
    return api_base.rstrip("/") + "/" + TOKEN_PATH


class ClientCredentials:
    """A client ID and secret, and the access token they were last traded for.

    Thread-safe: requests that need a token while one is being fetched wait for it, so one
    fetch serves them all.
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        *,
        token_url: str,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = MAX_RETRIES,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ):
        if not client_id or not client_secret:
            raise UsageError("Client credentials need both a client ID and a client secret.")
        url = httpx.URL(token_url)
        if url.scheme != "https" and url.host not in _LOOPBACK:
            raise UsageError(
                f"A client secret is only sent over HTTPS, and the token endpoint is {token_url}."
            )
        self.client_id = client_id
        self.token_url = token_url
        self._secret = client_secret
        self._timeout = timeout
        self._max_retries = max_retries
        self._sleep = sleep
        self._clock = clock
        self._lock = threading.Lock()
        self._token: str | None = None
        self._renew_at = 0.0
        self._expires_at = 0.0
        self._renewed_for_401_at: float | None = None
        # Set by a 429 whose Retry-After is too long to sleep through: no token is asked
        # for before then.
        self._not_before = 0.0

    def __repr__(self) -> str:
        return f"ClientCredentials(client_id={self.client_id!r}, token_url={self.token_url!r})"

    @property
    def flag_identity(self) -> str:
        """What the v1 flag cache keys this account's answer on. It is the client ID,
        which stays the same while the tokens change."""
        return f"oauth-client\n{self.client_id}"

    def token(self, *, budget: float | None = None) -> str:
        """The current access token, fetched first or renewed when it is about to run out.

        ``budget`` bounds a request its caller bounds (a wait's remaining deadline): the
        token is had within that many seconds, in one try, or a :class:`TamarindError`
        says it wasn't, as a request that timed out would. An early renewal that fails
        keeps the token, which still works for up to a minute, and is tried again in
        :data:`RETRY_EARLY_RENEWAL` seconds.
        """
        deadline = self._deadline(budget)
        with self._held(deadline):
            now = self._clock()
            if self._token is not None and now < self._renew_at:
                return self._token
            usable = self._token is not None and now < self._expires_at - EXPIRY_SLACK
            try:
                # With a token that still works, one try and no sleeping: it isn't needed yet.
                self._fetch(deadline, patient=not usable)
            except AuthError:
                raise
            except TamarindError:
                if not usable:
                    raise
                self._renew_at = min(now + RETRY_EARLY_RENEWAL, self._expires_at - EXPIRY_SLACK)
            assert self._token is not None
            return self._token

    def renew(self, rejected: str | None, *, budget: float | None = None) -> str | None:
        """A token to send again after a request sent with ``rejected`` was refused (401).

        If another request has already replaced that token, the newer one is returned
        without a fetch. A new token is fetched at most once a minute this way; inside that
        minute the answer is None, and the 401 stands. ``budget`` is as for :meth:`token`.
        """
        deadline = self._deadline(budget)
        with self._held(deadline):
            if self._token is not None and self._token != rejected:
                return self._token
            now = self._clock()
            if self._renewed_for_401_at is not None and now - self._renewed_for_401_at < RENEW_BEFORE:
                return None
            self._renewed_for_401_at = now
            self._token = None
            self._fetch(deadline, patient=True)
            return self._token

    # -- the token endpoint -------------------------------------------------
    def _deadline(self, budget: float | None) -> float | None:
        return None if budget is None else self._clock() + max(0.0, budget)

    @contextmanager
    def _held(self, deadline: float | None) -> Iterator[None]:
        """The lock, waited for no longer than ``deadline`` allows."""
        wait = -1.0 if deadline is None else max(0.0, deadline - self._clock())
        if not self._lock.acquire(timeout=wait):
            raise TamarindError("Timed out waiting for an access token.")
        try:
            yield
        finally:
            self._lock.release()

    def _fetch(self, deadline: float | None, *, patient: bool) -> None:
        """Ask the token endpoint. Patient (no deadline, no token to fall back on): retry
        network errors, 429 and 5xx, sleeping through a Retry-After of up to
        :data:`MAX_WAIT`. Otherwise one try, within the deadline."""
        # Imported here: the v1 package is not loaded until something needs it.
        from ._v1._transport import _backoff, _retry_after
        from .http import detached

        wait = self._not_before - self._clock()
        if wait > 0:
            raise self._rate_limited(wait)
        retries = self._max_retries if patient and deadline is None else 0
        attempt = 0
        while True:
            asked_at = self._clock()
            timeout = self._timeout
            if deadline is not None:
                timeout = min(timeout, deadline - asked_at)
                if timeout <= 0:
                    raise TamarindError("Timed out waiting for an access token.")
            try:
                response = self._post(timeout)
            except httpx.TransportError as exc:
                if attempt < retries:
                    self._sleep(_backoff(attempt))
                    attempt += 1
                    continue
                # Chained without its request, which holds the secret: the type says
                # whether it was a timeout.
                raise TamarindError(
                    f"Network error getting an access token from {self.token_url}: {type(exc).__name__}"
                ) from detached(exc)
            if response.is_success:
                self._keep(response, asked_at)
                return
            retry_after = _retry_after(response.headers.get("retry-after"))
            status = response.status_code
            if status == 429 or status >= 500:
                delay = retry_after if retry_after is not None else _backoff(attempt)
                if attempt < retries and delay <= MAX_WAIT:
                    self._sleep(delay)
                    attempt += 1
                    continue
                if status == 429 and retry_after is not None:
                    self._not_before = self._clock() + retry_after
            raise self._error(response, retry_after)

    def _post(self, timeout: float) -> httpx.Response:
        from . import __version__

        # RFC 6749 section 2.3.1: each half is form-encoded before the pair is base64-encoded.
        pair = f"{quote(self.client_id, safe='')}:{quote(self._secret, safe='')}"
        headers = {
            "Accept": "application/json",
            "User-Agent": f"tamarind-cli/{__version__}",
            **client_headers(),
            "Authorization": "Basic " + base64.b64encode(pair.encode()).decode("ascii"),
        }
        with httpx.Client(timeout=timeout) as client:
            # Never follow a redirect with the secret.
            return client.post(
                self.token_url,
                data={"grant_type": "client_credentials"},
                headers=headers,
                follow_redirects=False,
            )

    def _keep(self, response: httpx.Response, asked_at: float) -> None:
        try:
            body = response.json()
        except ValueError:
            body = None
        token = body.get("access_token") if isinstance(body, dict) else None
        lifetime = body.get("expires_in") if isinstance(body, dict) else None
        if not isinstance(token, str) or not token:
            # The answer itself is never quoted: it may hold a token.
            raise TamarindError("The token endpoint answered without an access token.")
        if isinstance(lifetime, bool) or not isinstance(lifetime, (int, float)) or lifetime <= 0:
            lifetime = _ASSUMED_LIFETIME
        self._token = token
        self._expires_at = asked_at + lifetime
        self._renew_at = self._expires_at - min(RENEW_BEFORE, lifetime / 2)

    def _rate_limited(self, wait: float | None) -> RateLimitError:
        seconds = math.ceil(wait) if wait else None
        later = f"Try again in {seconds} s." if seconds else "Try again later."
        return RateLimitError(
            f"The token endpoint is limiting requests from this client or network. {later}",
            detail={"error": "slow_down", "retryAfter": seconds},
        )

    def _error(self, response: httpx.Response, retry_after: float | None) -> TamarindError:
        status = response.status_code
        detail = _oauth_error(response)
        code = (detail or {}).get("error")
        described = (detail or {}).get("error_description")
        if status == 429:
            return self._rate_limited(retry_after)
        if status == 401:
            return AuthError(
                "The token endpoint refused this client ID and secret (invalid_client).",
                detail=detail,
            )
        if status == 404:
            return AuthError(
                "The token endpoint answered 404: OAuth client credentials aren't enabled for "
                f"this account, or {self.token_url} has no token endpoint.",
                detail=detail,
            )
        if status == 400:
            return AuthError(
                f"The token endpoint refused the request: {described or code or 'HTTP 400'}.",
                detail=detail,
            )
        return APIError(
            f"The token endpoint answered {status}: {described or code or response.reason_phrase}",
            status_code=status,
            detail=detail,
        )


def _oauth_error(response: httpx.Response) -> dict[str, Any] | None:
    """The OAuth error fields of a refusal; nothing else from its body."""
    try:
        body = response.json()
    except ValueError:
        return None
    if not isinstance(body, dict):
        return None
    kept = {k: body[k] for k in ("error", "error_description") if isinstance(body.get(k), str)}
    return kept or None


_SHARED: dict[tuple[str, str, str], ClientCredentials] = {}
_SHARED_LOCK = threading.Lock()


def shared(client_id: str, client_secret: str, *, token_url: str) -> ClientCredentials:
    """The one :class:`ClientCredentials` this process keeps for this ID, secret and token
    endpoint, so every client made with them uses the same token."""
    key = (token_url, client_id, hashlib.sha256(client_secret.encode()).hexdigest())
    with _SHARED_LOCK:
        found = _SHARED.get(key)
        if found is None:
            found = _SHARED[key] = ClientCredentials(client_id, client_secret, token_url=token_url)
        return found


__all__ = ["ClientCredentials", "shared", "token_url_for"]
