"""Workspace-file decisions. Pure — no network, no I/O.

`apply_filters` was previously stranded inside `cli/commands/files.py`, which meant a
script could not reach it even though it is the logic that makes a file listing usable.
It is pure and it mirrors a server-side behaviour, so it belongs in the library.
"""

from __future__ import annotations

from typing import Any


def file_name(f: object) -> str:
    """A file entry is usually a bare name string, but be tolerant of dicts."""
    if isinstance(f, str):
        return f
    if isinstance(f, dict):
        return str(f.get("name") or f.get("filename") or f.get("key") or "")
    return str(f)


def apply_filters(
    files: list,
    *,
    types: str | None = None,
    search: str | None = None,
    limit: int | None = None,
    offset: int = 0,
) -> dict[str, Any]:
    """Filter a workspace file list client-side, mirroring the MCP ``getFiles`` tool.

    The ``/files`` REST endpoint returns the full, unfiltered list and ignores the
    ``types``/``search``/``limit``/``offset`` query params, so the client applies them
    here — using the same rules as the MCP tool — to keep the two surfaces in parity.
    Returns the same envelope shape the MCP tool returns.
    """
    total_unfiltered = len(files)
    if types:
        exts = [t.strip().lower().lstrip(".") for t in types.split(",") if t.strip()]
        files = [f for f in files if any(file_name(f).lower().endswith(f".{e}") for e in exts)]
    if search:
        needle = search.lower()
        files = [f for f in files if needle in file_name(f).lower()]
    filtered_count = len(files)
    start = max(offset or 0, 0)
    page = files[start : start + limit] if limit is not None else files[start:]
    has_more = (start + limit) < filtered_count if limit is not None else False
    return {
        "files": page,
        "count": len(page),
        "total": filtered_count,
        "totalUnfiltered": total_unfiltered,
        "hasMore": has_more,
        "offset": start,
        "limit": limit,
        "filters": {"types": types, "search": search},
    }
