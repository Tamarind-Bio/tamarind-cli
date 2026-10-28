"""Consume the versioned directory API without mistaking a page for a full list."""
from __future__ import annotations

import json
from typing import Any

from .errors import TamarindError


def collect_file_pages(client, *, folder=None, include_folders=False, include_metadata=False,
                       max_pages=1000, max_bytes=32 * 1024 * 1024) -> list[Any]:
    """Return a complete catalog listing, or raise; never return a partial list.

    Older servers ignore version=2 and return the legacy array. Accept that only
    on the first request. Cursor pages may be empty while still having a successor.
    """
    params = {"version": "2", "limit": 100}
    if folder:
        params["folder"] = folder
    if include_folders:
        params["includeFolders"] = "true"
    if include_metadata:
        params["includeMetadata"] = "true"
    files: list[Any] = []
    seen: set[str] = set()
    size = 0
    for page_number in range(max_pages):
        page = client.get_json("files", params=params)
        size += len(json.dumps(page).encode())
        if size > max_bytes:
            raise TamarindError("File listing exceeded the response budget; use a narrower folder.")
        if isinstance(page, list) and page_number == 0:
            return page
        if not isinstance(page, dict) or not isinstance(page.get("files"), list):
            raise TamarindError("Invalid paginated file response.")
        cursor = page.get("nextCursor")
        if "nextCursor" not in page or page.get("hasMore") is not bool(cursor):
            raise TamarindError("Inconsistent paginated file response.")
        files.extend(page["files"])
        if cursor is None:
            return files
        if not isinstance(cursor, str) or not cursor or cursor in seen:
            raise TamarindError("File listing returned a repeated or invalid cursor.")
        seen.add(cursor)
        params = {**params, "cursor": cursor}
    raise TamarindError("File listing exceeded the page budget; use a narrower folder.")
