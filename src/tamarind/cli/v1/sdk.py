"""The CLI's one doorway to the v1 SDK.

Every v1 command calls the API through these functions, which call the SDK
(``tamarind.v1``); nothing in the CLI sends v1 HTTP itself, so the CLI and the
SDK can't drift. An operation is called by its ``x-clients.sdk`` name, e.g.
``projects.notes.createEntry`` → ``client.projects.notes.create_entry(...)``.
"""

from __future__ import annotations

import builtins
import keyword
import re
import time
import uuid
from typing import Any, Callable

import httpx

from ...errors import TamarindError, UsageError

# openapi-python-client (pinned) renames a parameter that would shadow a builtin
# or a keyword by adding "_": `from` → `from_`, `filter` → `filter_`.
_RESERVED = (set(dir(builtins)) | {"self", "true", "false", "datetime"}) - {"id"}


def snake(name: str) -> str:
    """``createEntry`` → ``create_entry``; ``serviceAccounts`` → ``service_accounts``."""
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def argument(name: str) -> str:
    """A contract parameter's keyword in the SDK: snake_case, reserved words + ``_``."""
    value = snake(name)
    return value + "_" if value in _RESERVED or keyword.iskeyword(value) else value


def make_client(state: Any, *, api_key: str | None = None) -> Any:
    """The v1 SDK client for this invocation's key (or ``api_key``) and v1 base URL."""
    from tamarind.v1 import Tamarind as V1Client  # the v1 SDK's client

    cfg = state.config()
    key = api_key if api_key is not None else cfg.api_key
    return V1Client(api_key=key, base_url=cfg.v1_api_base.rstrip("/"))


def wait(
    client: Any,
    job_id: str,
    *,
    poll_interval: float,
    timeout: float | None,
    on_poll: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    """The SDK's wait helper: poll a job, batch or run until it's final.

    Raises ``JobTimeoutError`` (exit 7) when ``timeout`` passes first.
    """
    final = client.jobs.wait(
        job_id,
        poll_interval=poll_interval,
        timeout=timeout,
        on_update=(lambda job: on_poll(plain(job))) if on_poll else None,
    )
    return plain(final)


def upload(client: Any, local_path: Any, remote_path: str) -> dict[str, Any]:
    """The SDK's one-call upload (``uploadFile``, the PUTs, ``completeFileUpload``)."""
    return plain(client.files.upload(local_path, path=remote_path))


def require_v1(state: Any, command: str) -> None:
    if not state.is_v1:
        raise UsageError(
            f"`tamarind {command}` uses the v1 API (https://api.tamarind.bio). "
            "Select it with TAMARIND_API=v1, or \"api\": \"v1\" in your profile."
        )


def plain(value: Any) -> Any:
    """SDK models → their wire dicts (camelCase), recursively; everything else as is."""
    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        return to_dict()
    if isinstance(value, list):
        return [plain(v) for v in value]
    if isinstance(value, tuple):
        return [plain(v) for v in value]
    if isinstance(value, dict):
        return {k: plain(v) for k, v in value.items()}
    return value


def method(client: Any, sdk_name: str) -> Callable[..., Any]:
    target = client
    for segment in sdk_name.split("."):
        target = getattr(target, snake(segment))
    return target


def check_values(op: dict[str, Any], query: dict[str, Any]) -> None:
    """Values the SDK would have to coerce (an enum member, a date-time) are checked
    against the contract first, so a bad one is a usage error rather than a traceback."""
    from dateutil.parser import isoparse

    for param in op["query"]:
        value = query.get(param["name"])
        if value is None:
            continue
        allowed = param.get("enum")
        for item in value if isinstance(value, (list, tuple)) else [value]:
            if allowed and str(item) not in allowed:
                raise UsageError(
                    f"--{param['option']} {item!r} isn't one of: {', '.join(allowed)}."
                )
            if param.get("format") == "date-time":
                try:
                    isoparse(str(item))
                except ValueError:
                    raise UsageError(
                        f"--{param['option']} {item!r} isn't an RFC 3339 date-time "
                        "(e.g. 2026-11-01T00:00:00Z)."
                    ) from None


def invoke(
    client: Any,
    op: dict[str, Any],
    *path_args: str,
    body: Any = None,
    idempotency_key: str | None = None,
    if_match: str | None = None,
    **query: Any,
) -> Any:
    """Call one operation through its SDK method; returns the plain answer (None for 204).

    An operation that takes an ``Idempotency-Key`` always gets one the CLI knows (the
    caller's, or a new one), so when its outcome is unclear the error can say how to
    retry it without doing the work twice.
    """
    check_values(op, query)
    kwargs: dict[str, Any] = {argument(k): v for k, v in query.items() if v is not None}
    if body is not None:
        kwargs["body"] = body
    retry_safe = "Idempotency-Key" in op["headers"]
    if retry_safe:
        idempotency_key = idempotency_key or str(uuid.uuid4())
    if idempotency_key:
        kwargs["idempotency_key"] = idempotency_key
    if if_match:
        kwargs["if_match"] = if_match
    try:
        return plain(method(client, op["sdk"])(*path_args, **kwargs))
    except TamarindError as exc:
        if retry_safe and idempotency_key and outcome_unclear(exc):
            raise retry_hint(exc, op, idempotency_key) from exc
        raise


def outcome_unclear(exc: TamarindError) -> bool:
    """No answer, a 5xx, or 409 `idempotency_in_progress` (the first attempt may be
    running): the work may have been done. A 4xx refusal means nothing was, and so
    does an error the SDK raises on an answer it got (a replayed key create with no
    secret says so itself)."""
    if getattr(exc, "code", None) == "idempotency_in_progress":
        return True
    status = getattr(exc, "status", None) or getattr(exc, "status_code", None)
    if isinstance(status, int):
        return status >= 500
    # No status: unclear only when no answer came back (the SDK's network error).
    return isinstance(exc.__cause__, httpx.HTTPError)


def retry_hint(exc: TamarindError, op: dict[str, Any], key: str) -> TamarindError:
    err = TamarindError(
        f"{exc.message} `tamarind {op['cli']}` may or may not have gone through; run the "
        f"same command again with --idempotency-key {key} to get the same result, not a second one.",
        detail={
            "idempotencyKey": key,
            "outcomeMayBeAmbiguous": True,
            "problem": getattr(exc, "problem", None) or None,
        },
    )
    err.exit_code = exc.exit_code
    return err


def collect(
    client: Any, op: dict[str, Any], *path_args: str, body: Any = None, **query: Any
) -> dict[str, Any]:
    """All items of a list operation as one page, with a null ``nextCursor``.

    The other fields come from the LAST page: totals (a usage page's ``total``,
    ``metric``, ``asOf``) are the same on every page, and a molecules scan's state
    (``waiting``, ``scanProgress``...) is only current there. The cursor goes in the
    query or, for an operation that pages through its body (``molecules search``), in
    the body; a page still being prepared (``waiting``) is waited for as the SDK's
    own paging does (``retryAfterMs``).
    """
    page = invoke(client, op, *path_args, body=body, **query)
    if not isinstance(page, dict):
        return page
    items = list(page.get("items") or [])
    in_query = any(q["name"] == "cursor" for q in op["query"])
    seen: set[str] = set()
    while page.get("nextCursor") and page["nextCursor"] not in seen:
        cursor = page["nextCursor"]
        seen.add(cursor)
        if page.get("waiting") and isinstance(page.get("retryAfterMs"), (int, float)):
            time.sleep(page["retryAfterMs"] / 1000)
        if in_query:
            page = invoke(client, op, *path_args, body=body, **{**query, "cursor": cursor})
        else:
            page = invoke(client, op, *path_args, body={**(body or {}), "cursor": cursor}, **query)
        items.extend(page.get("items") or [])
    return {**page, "items": items, "nextCursor": None}
