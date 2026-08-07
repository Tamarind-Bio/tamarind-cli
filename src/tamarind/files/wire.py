"""The workspace-file boundary: raw entries in, frozen types out.

A file entry arrives as a bare name string in most responses and as an object when
metadata was requested — and historically as neither, which is why the name reader
is tolerant. That variance is absorbed here, once.

Tolerant in, strict out: an unrecognized entry parses to its string form rather than
raising, because a listing is a read and a surprising entry should not fail it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

_NAME_KEYS = ("name", "filename", "key")


@dataclass(frozen=True)
class FileEntry:
    """One workspace file. ``raw`` keeps the server's full entry for rendering."""

    name: str
    size: int | None = None
    last_modified: str | None = None
    raw: Any = field(default_factory=dict)


def parse_file(entry: Any) -> FileEntry:
    """Normalize one file entry. Never raises."""
    if isinstance(entry, str):
        return FileEntry(name=entry, raw=entry)
    if isinstance(entry, Mapping):
        name = ""
        for key in _NAME_KEYS:
            if entry.get(key):
                name = str(entry[key])
                break
        size = entry.get("size")
        return FileEntry(
            name=name,
            size=size if isinstance(size, int) else None,
            last_modified=(
                str(entry["lastModified"]) if entry.get("lastModified") is not None else None
            ),
            raw=entry,
        )
    return FileEntry(name=str(entry), raw=entry)
