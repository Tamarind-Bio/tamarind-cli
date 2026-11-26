"""Thin HTTP transport shared by the REST and catalog clients.

Wraps ``httpx.Client`` with the ``x-api-key`` header the Tamarind API expects,
and maps non-2xx responses onto the typed errors in :mod:`tamarind.errors` so
callers (and the CLI's exit codes) get consistent behaviour. With a service
account's client credentials (:mod:`tamarind.oauth`) the header carries an access
token instead of a key, renewed once when a request is refused with 401.
"""

from __future__ import annotations

import asyncio
import re
import time
from collections.abc import Iterator
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any

import httpx

from .attribution import client_headers
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

if TYPE_CHECKING:
    from .oauth import ClientCredentials

DEFAULT_TIMEOUT = 120.0
USER_AGENT = "tamarind-cli"
_NO_KEY = (
    "No API key configured. Set TAMARIND_API_KEY (or, for a service account, TAMARIND_CLIENT_ID "
    "and TAMARIND_CLIENT_SECRET), pass --api-key, or run `tamarind auth login`."
)
_DERIVED: Any = object()
# Paths the v1 API serves exactly as here (the custom-tools router wraps this one's).
_SAME_PATH_ON_V1 = re.compile(r"^(?:custom-tools(?:/|$)|pipelines/runs/[^/]+(?:/node-runs/[^/]+/molecules)?$)")


class HTTPClient:
    """A small wrapper around ``httpx.Client`` keyed by base URL + API key (or a service
    account's client credentials, ``credentials``)."""

    def __init__(
        self,
        base_url: str,
        api_key: str | None,
        *,
        timeout: float = DEFAULT_TIMEOUT,
        v1_base: Any = _DERIVED,
        flag_cache: Any = None,
        credentials: ClientCredentials | None = None,
    ):
        from ._v1.switch import Switch, v1_base_for

        if api_key and credentials is not None:
            raise ValueError("Pass an API key or client credentials, not both.")
        self.base_url = base_url
        self.api_key = api_key
        self.credentials = credentials
        self._timeout = timeout
        # Whether this key's requests go to the v1 API: the server says (`GET /me`,
        # asked on the first request v1 can answer). `v1_base` defaults to the v1 API
        # of this base's environment; None means classic only.
        self._switch = Switch(
            api_key,
            v1_base_for(base_url) if v1_base is _DERIVED else v1_base,
            flag_cache,
            credentials=credentials,
        )
        self._v1: Any = None
        self._v1_raw: HTTPClient | None = None
        self._router: Any = None
        # Set on the client that sends same-path requests to v1: its errors are v1's.
        self._answers_for_v1 = False
        headers = {
            "Accept": "application/json",
            # Brotli is still decoded transparently by httpx; we just don't want
            # surprises from upstream content-encoding negotiation.
            "Accept-Encoding": "identity",
            "User-Agent": f"{USER_AGENT}/{_version()}",
            # Channel (cli/sdk) and the AI agent driving us, for usage attribution only.
            **client_headers(),
        }
        if api_key:
            headers["x-api-key"] = api_key
        self._headers = headers
        self._client = httpx.Client(base_url=base_url, headers=headers, timeout=timeout)

    @property
    def has_credentials(self) -> bool:
        """Whether requests carry an API key or a client-credentials token."""
        return bool(self.api_key) or self.credentials is not None

    # -- lifecycle ---------------------------------------------------------
    def close(self) -> None:
        self._client.close()
        if self._v1 is not None:
            self._v1.close()
        if self._v1_raw is not None:
            self._v1_raw.close()

    def __enter__(self) -> "HTTPClient":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    # -- the v1 API --------------------------------------------------------
    @property
    def v1_base(self) -> str | None:
        return self._switch.v1_base

    def uses_v1(self, *, budget: float | None = None) -> bool:
        """Whether this key's requests go to the v1 API (asks the server once, cached).
        ``budget``: the deadline of the request that needs the answer, which bounds
        getting a client-credentials token for the question."""
        return self._switch.on(budget=budget)

    def cached_uses_v1(self) -> bool | None:
        """The last answer kept for this key, however old (what ``--help`` lists v1
        commands by); never the network."""
        return self._switch.last_known()

    def _new_v1(self, **options: Any) -> Any:
        from ._v1.client import Tamarind as V1

        options.setdefault("timeout", self._timeout)
        return V1(
            self.api_key, base_url=self._switch.v1_base, credentials=self.credentials, **options
        )

    def require_v1(self, what: str) -> None:
        """Raise unless v1 is on for this key: no key is classic's AuthError, and a
        key v1 isn't on for is :class:`~tamarind._v1.switch.V1NotEnabledError`."""
        from ._v1.switch import V1NotEnabledError

        if not self.has_credentials:
            raise AuthError(_NO_KEY)
        if not self.uses_v1():
            raise V1NotEnabledError(what)

    def v1(self, what: str = "This operation") -> Any:
        """The v1 client for this key, closed with this client. Raises
        :class:`~tamarind._v1.switch.V1NotEnabledError` when v1 isn't on for it."""
        self.require_v1(what)
        if self._v1 is None:
            self._v1 = self._new_v1()
        return self._v1

    def v1_client(self, what: str = "This operation", **options: Any) -> Any:
        """A new v1 client (``timeout``, ``max_retries``...); the caller closes it."""
        self.require_v1(what)
        return self._new_v1(**options)

    def _routes(self) -> Any:
        if self._router is None:
            from ._v1.classic import Router

            self._router = Router(self)
        return self._router

    @contextmanager
    def results_wait(self, timeout: float | None) -> Iterator[None]:
        """Within this block a results request (``/result``) answered from v1 waits for
        an archive that is still being built, until ``timeout`` seconds from now (no
        limit if None), as classic's results wait does. Outside it, such a request
        says the archive is being prepared."""
        router = self._routes()
        saved = router.results_deadline
        router.results_deadline = (True, None if timeout is None else time.monotonic() + timeout)
        try:
            yield
        finally:
            router.results_deadline = saved

    def _serve(self, method: str, path: str, payload: Any, classic: Any, timeout: float | None = None) -> Any:
        from ._v1 import catalog as catalog_on_v1
        from ._v1 import classic as on_v1

        handler = on_v1.route(method, path.strip("/")) or catalog_on_v1.route(method, path.strip("/"))
        if handler is None or not self.has_credentials or not self.uses_v1(budget=timeout):
            return classic()
        return self._routes().serve(handler, payload, classic, timeout=timeout)

    def _same_path_on_v1(self, path: str, timeout: float | None = None) -> bool:
        """Whether a request the v1 API serves at the same path (custom tools, pipeline
        runs) goes to its base: v1 is on for this key. May ask the server, once."""
        return bool(
            self.has_credentials
            and _SAME_PATH_ON_V1.match(path.lstrip("/"))
            and self.uses_v1(budget=timeout)
        )

    def _v1_same_path_client(self) -> "HTTPClient":
        if self._v1_raw is None:
            self._v1_raw = HTTPClient(
                str(self._switch.v1_base),
                self.api_key,
                timeout=self._timeout,
                v1_base=None,
                credentials=self.credentials,
            )
            self._v1_raw._answers_for_v1 = True
        return self._v1_raw

    def _raw_client(self, path: str, timeout: float | None = None) -> "HTTPClient":
        """The client a raw request goes through: v1's base for the paths it serves alike
        when v1 is on for this key, otherwise this one."""
        return self._v1_same_path_client() if self._same_path_on_v1(path, timeout) else self

    def _error(self, resp: httpx.Response, path: str) -> TamarindError:
        error = _map_error(resp, request_path=path)
        if not self._answers_for_v1:
            return error
        from ._v1 import classic

        return classic.same_path_error(resp, error)

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
        client = self._raw_client(path, timeout)
        if client is self:
            return client._classic_request(
                method, path, params=params, headers=headers, json=json, timeout=timeout
            )
        response = client._classic_request(
            method, _to_v1(path), params=params, headers=headers, json=json, timeout=timeout
        )
        return _from_v1(method, path, response)

    def _classic_request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str | None] | None = None,
        json: Any | None = None,
        timeout: float | None = None,
    ) -> httpx.Response:
        if not self.has_credentials:
            raise AuthError(_NO_KEY)
        clean_params = _without_none_values(params)
        clean_headers = _without_none_values(headers)

        def send(token: str | None) -> httpx.Response:
            return self._client.request(
                method,
                path.lstrip("/"),
                params=clean_params,
                headers=_with_token(clean_headers, token),
                json=json,
                timeout=timeout if timeout is not None else httpx.USE_CLIENT_DEFAULT,
            )

        try:
            # A request its caller bounds (`timeout`) gets its token within the same bound.
            token = self.credentials.token(budget=timeout) if self.credentials is not None else None
            resp = send(token)
            if resp.status_code == 401 and self.credentials is not None:
                # Refused before any work was done, so sending it again is safe.
                renewed = self.credentials.renew(token, budget=timeout)
                if renewed is not None:
                    resp = send(renewed)
        except httpx.HTTPError as exc:
            raise TamarindError(f"Network error talking to {self.base_url}: {exc}") from detached(exc)

        if resp.is_success:
            return resp
        raise self._error(resp, path)

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
        # Asking the server whether v1 is on (once per client) is a blocking request: it
        # runs in a thread, so it never stalls the event loop or delays a cancellation. The
        # thread only decides; the v1 client is made here, so a cancelled request whose
        # thread finishes later leaves nothing open behind it.
        on_v1 = await asyncio.to_thread(self._same_path_on_v1, path, timeout)
        client = self._v1_same_path_client() if on_v1 else self
        if client is self:
            return await client._classic_request_async(
                method, path, params=params, headers=headers, json=json, timeout=timeout
            )
        response = await client._classic_request_async(
            method, _to_v1(path), params=params, headers=headers, json=json, timeout=timeout
        )
        return _from_v1(method, path, response)

    async def _classic_request_async(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str | None] | None = None,
        json: Any | None = None,
        timeout: float | None = None,
    ) -> httpx.Response:
        if not self.has_credentials:
            raise AuthError(_NO_KEY)
        clean_params = _without_none_values(params)
        clean_headers = _without_none_values(headers)
        credentials = self.credentials
        try:
            async with httpx.AsyncClient(
                base_url=self.base_url,
                headers=self._headers,
                timeout=self._timeout,
            ) as client:

                async def send(token: str | None) -> httpx.Response:
                    return await client.request(
                        method,
                        path.lstrip("/"),
                        params=clean_params,
                        headers=_with_token(clean_headers, token),
                        json=json,
                        timeout=timeout if timeout is not None else httpx.USE_CLIENT_DEFAULT,
                    )

                # A token fetch is a blocking request: it runs in a thread, like the v1 question.
                token = (
                    await asyncio.to_thread(credentials.token, budget=timeout)
                    if credentials is not None
                    else None
                )
                resp = await send(token)
                if resp.status_code == 401 and credentials is not None:
                    renewed = await asyncio.to_thread(credentials.renew, token, budget=timeout)
                    if renewed is not None:
                        resp = await send(renewed)
        except httpx.HTTPError as exc:
            raise TamarindError(f"Network error talking to {self.base_url}: {exc}") from detached(exc)

        if resp.is_success:
            return resp
        raise self._error(resp, path)

    # With v1 on for this key, the requests v1 has a form for are answered from it and
    # rebuilt in this API's layout (tamarind._v1.classic); the rest are sent here.
    def get_json(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> Any:
        return self._serve(
            "GET", path, params,
            lambda: self._classic_json("GET", path, params=params, timeout=timeout),
            timeout=timeout,
        )

    def post_json(self, path: str, *, json: Any | None = None) -> Any:
        return self._serve("POST", path, json, lambda: self._classic_json("POST", path, json=json))

    def delete_json(
        self, path: str, *, params: dict[str, Any] | None = None, json: Any | None = None
    ) -> Any:
        return self._serve(
            "DELETE", path, json if json is not None else params,
            lambda: self._classic_json("DELETE", path, params=params, json=json),
        )

    def _classic_json(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any | None = None,
        timeout: float | None = None,
    ) -> Any:
        return _parse_json(
            self._classic_request(method, path, params=params, json=json, timeout=timeout)
        )


def _to_v1(path: str) -> str:
    from ._v1 import classic

    return classic.v1_path(path)


def _from_v1(method: str, path: str, response: httpx.Response) -> httpx.Response:
    from ._v1 import classic

    return classic.rebuild_response(method.upper(), path.split("?", 1)[0].strip("/"), response)


def _parse_json(resp: httpx.Response) -> Any:
    text = resp.text.strip()
    if not text:
        return None
    try:
        return resp.json()
    except ValueError:
        # Some endpoints (e.g. /result) return a bare presigned URL string.
        return text


def detached(exc: httpx.HTTPError) -> httpx.HTTPError:
    """``exc`` without the request httpx attached to it, whose headers hold the API key or
    access token. Chained errors keep their type, which callers read (a network error
    means the outcome is unclear); anything that reports a cause can't reach the key."""
    exc._request = None
    return exc


def _with_token(headers: dict[str, Any] | None, token: str | None) -> dict[str, Any] | None:
    """A request's headers with a client-credentials token in ``x-api-key``; an API key
    is already among the client's headers."""
    if token is None:
        return headers
    return {**(headers or {}), "x-api-key": token}


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


def _map_error(resp: httpx.Response, *, request_path: str) -> TamarindError:
    body, is_json = _error_body(resp)
    detail = body if is_json else None
    msg = _extract_message(resp, body, is_json=is_json)
    code = resp.status_code
    problem_code = _problem_code(detail)
    relative_path = "/" + request_path.lstrip("/")
    not_found_error = (
        CustomToolNotFoundError
        if relative_path == "/custom-tools" or relative_path.startswith("/custom-tools/")
        else NotFoundError
    )
    if problem_code == "custom_tool_not_found" or problem_code == "custom_tool_version_not_found":
        return CustomToolNotFoundError(msg, detail=detail)
    if problem_code == "custom_tool_name_taken":
        return CustomToolExistsError(msg, detail=detail)
    if problem_code == "custom_tool_not_deployable":
        return CustomToolNotDeployableError(msg, detail=detail)
    if problem_code == "invalid_custom_tool_config" or problem_code == "invalid_custom_tool_source":
        return CustomToolValidationError(msg, detail=detail)
    if (
        code == 412
        and (relative_path == "/custom-tools" or relative_path.startswith("/custom-tools/"))
    ) or problem_code in {"custom_tool_generation_mismatch", "custom_tool_source_changed"}:
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
