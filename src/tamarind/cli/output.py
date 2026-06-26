"""Output helpers.

Every command can emit either machine JSON (``--json``, the default when stdout
is not a TTY) or a compact human rendering. Agents should pass ``--json`` (or
just rely on the non-TTY default) and parse stdout.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from typing import Any, Sequence

import typer


@dataclass
class OutputMode:
    json: bool
    quiet: bool


def emit(obj: Any, mode: OutputMode, *, human: str | None = None) -> None:
    """Emit a result. In JSON mode print ``obj`` as JSON; otherwise ``human``."""
    if mode.json:
        typer.echo(json.dumps(obj, indent=2, default=str))
    elif human is not None:
        typer.echo(human)
    else:
        typer.echo(json.dumps(obj, indent=2, default=str))


def info(message: str, mode: OutputMode) -> None:
    """A status line for humans; suppressed in JSON/quiet mode (goes to stderr)."""
    if mode.json or mode.quiet:
        return
    typer.secho(message, err=True, fg=typer.colors.BRIGHT_BLACK)


def error(message: str) -> None:
    typer.secho(f"error: {message}", err=True, fg=typer.colors.RED)


def render_table(rows: Sequence[dict[str, Any]], columns: Sequence[str]) -> str:
    """Render a fixed-width text table. ``columns`` are the dict keys to show."""
    if not rows:
        return "(none)"
    widths = {c: len(c) for c in columns}
    str_rows: list[dict[str, str]] = []
    for r in rows:
        sr = {}
        for c in columns:
            val = r.get(c)
            text = "" if val is None else str(val)
            sr[c] = text
            widths[c] = max(widths[c], len(text))
        str_rows.append(sr)
    header = "  ".join(c.ljust(widths[c]) for c in columns)
    sep = "  ".join("-" * widths[c] for c in columns)
    lines = [header, sep]
    for sr in str_rows:
        lines.append("  ".join(sr[c].ljust(widths[c]) for c in columns))
    return "\n".join(lines)


def is_tty() -> bool:
    return sys.stdout.isatty()
