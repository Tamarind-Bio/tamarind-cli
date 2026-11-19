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
from typing import Any, Callable

from ...errors import UsageError

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
            "Select it with TAMARIND_API=v1, `--api v1`, or \"api\": \"v1\" in your profile."
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


def check_enums(op: dict[str, Any], query: dict[str, Any]) -> None:
    """A value the contract doesn't list for a parameter is a usage error, not a traceback."""
    for param in op["query"]:
        allowed = param.get("enum")
        value = query.get(param["name"])
        if not allowed or value is None:
            continue
        for item in value if isinstance(value, (list, tuple)) else [value]:
            if str(item) not in allowed:
                raise UsageError(
                    f"--{param['option']} {item!r} isn't one of: {', '.join(allowed)}."
                )


def invoke(
    client: Any,
    op: dict[str, Any],
    *path_args: str,
    body: Any = None,
    idempotency_key: str | None = None,
    if_match: str | None = None,
    **query: Any,
) -> Any:
    """Call one operation through its SDK method; returns the plain answer (None for 204)."""
    check_enums(op, query)
    kwargs: dict[str, Any] = {argument(k): v for k, v in query.items() if v is not None}
    if body is not None:
        kwargs["body"] = body
    if idempotency_key:
        kwargs["idempotency_key"] = idempotency_key
    if if_match:
        kwargs["if_match"] = if_match
    return plain(method(client, op["sdk"])(*path_args, **kwargs))


def collect(client: Any, op: dict[str, Any], *path_args: str, **query: Any) -> dict[str, Any]:
    """All items of a list operation as one page, ``{items, nextCursor: null}``,
    through the SDK's auto-paging helper."""
    check_enums(op, query)
    kwargs = {argument(k): v for k, v in query.items() if v is not None}
    items = client.paginate(method(client, op["sdk"]), *path_args, **kwargs)
    return {"items": plain(list(items)), "nextCursor": None}
