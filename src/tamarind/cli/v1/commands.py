"""The hand-written v1 commands: ``jobs download`` and ``files download``.

They save a file to disk, which a command built from the contract can't. Calls go
through :mod:`.sdk`, never raw HTTP. (Today's commands don't come here: with v1
selected they keep their classic code, see :mod:`.classic_routes`.)
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from ...errors import NotFoundError, UsageError
from .. import output
from . import manifest, render, sdk

# A v1 id: a kind prefix and a UUID (with or without dashes). Anything else is a name,
# even one that happens to start with `job_`.
_ID = re.compile(r"^(job|batch|run)_[0-9a-fA-F]{8}-?(?:[0-9a-fA-F]{4}-?){3}[0-9a-fA-F]{12}$")


def _emit(body: Any, mode: Any, *, human: str | None = None) -> None:
    """Print a v1 answer with signed links redacted, as today's job output is."""
    output.emit(render.redact(body), mode, human=human)


def op(operation_id: str) -> dict[str, Any]:
    return manifest.operation(operation_id)


def call(client: Any, operation_id: str, *args: Any, **kwargs: Any) -> Any:
    return sdk.invoke(client, op(operation_id), *args, **kwargs)


_PREFIX_KIND = {"job_": "job", "batch_": "batch", "run_": "pipeline"}
ANY_KIND = ("job", "batch", "pipeline")
_KIND_WORDS = {"job": "a job", "batch": "a batch", "pipeline": "a pipeline run"}


def _kinds_text(kinds: tuple[str, ...], *, article: bool = True) -> str:
    words = [_KIND_WORDS[k] if article else _KIND_WORDS[k].split(" ", 1)[1] for k in kinds]
    return words[0] if len(words) == 1 else ", ".join(words[:-1]) + " or " + words[-1]


def resolve_id(
    client: Any,
    ref: str,
    *,
    kinds: tuple[str, ...] = ANY_KIND,
    what: str = "this command",
) -> str:
    """The id of the job, batch or pipeline run ``ref`` names, limited to ``kinds``.

    An id (``job_``/``batch_``/``run_`` + UUID) is used as given once its kind is one
    ``what`` takes; anything else is a name, looked up with ``listJobs?name=``. That
    answers only the newest match, so with a narrower ``kinds`` each kind is asked
    for and the newest wins: a newer item of another kind can't hide the one meant.
    """
    ref = ref.strip()
    if _ID.match(ref):
        kind = next(k for prefix, k in _PREFIX_KIND.items() if ref.startswith(prefix))
        if kind not in kinds:
            raise UsageError(f"{what} takes {_kinds_text(kinds)}, not {_KIND_WORDS[kind]} ({ref}).")
        return ref
    query: dict[str, Any] = {"name": ref}
    if set(kinds) == set(ANY_KIND):
        found = list(call(client, "listJobs", **query).get("items") or [])
    else:
        found = [
            item
            for kind in kinds
            for item in (call(client, "listJobs", **query, kind=kind).get("items") or [])
        ]
    if not found:
        raise NotFoundError(f"'{ref}' names no {_kinds_text(kinds, article=False)} of yours.", detail={"name": ref})
    return str(max(found, key=lambda item: str(item.get("createdAt") or ""))["id"])


def download_link(
    state: Any, operation_id: str, *args: str, path: str, dest: Path | None, show_url: bool
) -> None:
    """``files download`` / ``jobs download``: fetch a file's link and save it, or print it."""
    from ..commands.jobs import _download

    with sdk.make_client(state) as client:
        link = call(client, operation_id, *args, path=path, delivery="url")
    if show_url:
        output.emit(link, state.output, human=link["url"])  # asked for with --show-url
        return
    target = dest or Path(".")
    if target.is_dir() or str(target).endswith(("/", "\\")):
        target = target / Path(path).name
    written = _download(link["url"], target)
    _emit({"path": str(target), "bytes": written}, state.output, human=str(target))
