"""Human rendering for v1 answers. ``--json`` always prints the v1 body itself."""

from __future__ import annotations

from typing import Any

import yaml

from .. import output

# Columns a page's table shows, in this order, when its items carry them.
_COLUMNS = (
    "id",
    "name",
    "path",
    "kind",
    "tool",
    "type",
    "status",
    "displayName",
    "sizeBytes",
    "role",
    "email",
    "createdAt",
    "updatedAt",
)
_MAX_COLUMNS = 6


def _cell(value: Any) -> Any:
    if isinstance(value, (dict, list)):
        return yaml.safe_dump(value, default_flow_style=True, sort_keys=False).strip()
    return value


def table(items: list[Any], columns: list[str] | None = None) -> str:
    rows = [item for item in items if isinstance(item, dict)]
    if not rows:
        return "\n".join(str(item) for item in items) or "(none)"
    if columns is None:
        present = {key for row in rows for key in row}
        columns = [c for c in _COLUMNS if c in present][:_MAX_COLUMNS]
        if not columns:
            columns = list(rows[0])[:_MAX_COLUMNS]
    return output.render_table([{c: _cell(r.get(c)) for c in columns} for r in rows], columns)


def human(body: Any) -> str:
    """A readable rendering: a table for a page, key/value lines for an object."""
    if body is None:
        return "done"
    if isinstance(body, list):
        return table(body)
    if isinstance(body, dict) and isinstance(body.get("items"), list):
        text = table(body["items"])
        if body.get("nextCursor"):
            text += "\n\nMore results: pass --all, or --cursor with the nextCursor in --json."
        return text
    if isinstance(body, dict):
        return yaml.safe_dump(body, sort_keys=False, allow_unicode=True).rstrip()
    return str(body)


def redact(body: Any) -> Any:
    """Signed download/upload links out of ordinary output, as today's job output does
    (``--show-urls`` / ``--show-url`` print them on purpose)."""
    from ..commands.jobs import _sanitize_job_output

    return _sanitize_job_output(body)


def emit(
    body: Any, mode: output.OutputMode, *, human_text: str | None = None, show_urls: bool = False
) -> None:
    if not show_urls:
        body = redact(body)
        text = human_text or human(body)
    else:
        # Links were asked for: show the whole answer, since a page's table has no link column.
        text = human_text or yaml.safe_dump(body, sort_keys=False, allow_unicode=True).rstrip()
    output.emit(body if body is not None else {"ok": True}, mode, human=text)
