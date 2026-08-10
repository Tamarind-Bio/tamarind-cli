"""Output helpers.

Every command can emit either machine JSON (``--json``, the default when stdout
is not a TTY) or a compact human rendering. Agents should pass ``--json`` (or
just rely on the non-TTY default) and parse stdout.
"""

from __future__ import annotations

import json
import shutil
import sys
from dataclasses import dataclass
from typing import Any, Sequence

import typer

from ..errors import ExitCode

# Smallest a column may be shrunk to when fitting the table to the terminal.
_MIN_COL = 6
_ELLIPSIS = "…"


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


def error(
    message: str,
    mode: OutputMode | None = None,
    *,
    error_type: str = "TamarindError",
    exit_code: int = ExitCode.ERROR,
    detail: Any = None,
) -> None:
    """Emit a stable error representation to stderr.

    Human mode keeps the existing compact red ``error: ...`` rendering. JSON
    mode emits one JSON document so agents never need to scrape Rich-formatted
    stderr. ``detail`` is deliberately nested under the error object and is
    omitted when absent, keeping the common shape small and stable.
    """
    if mode is not None and mode.json:
        err: dict[str, Any] = {
            "type": error_type,
            "message": message,
            "exitCode": int(exit_code),
        }
        if detail is not None:
            err["detail"] = detail
        typer.echo(json.dumps({"error": err}, indent=2, default=str), err=True)
        return
    typer.secho(f"error: {message}", err=True, fg=typer.colors.RED)


def confirm_destructive(action: str, *, yes: bool, mode: OutputMode) -> None:
    """Guard a destructive action (``action`` is a verb phrase, e.g.
    ``"permanently delete job 'x'"``).

    - Already confirmed with ``--yes``/``-y``: proceed.
    - Interactive human terminal: prompt, aborting on "no".
    - Non-interactive or JSON mode (agents, scripts, pipes): there is no one to
      prompt, so *refuse* unless ``--yes`` was passed. This stops an agent from
      destroying data it never explicitly confirmed, and exits with the usage
      code (2) so the caller can tell it apart from a real failure.

    A real prompt needs a human at a terminal on BOTH ends — stdout to show the
    question and stdin to read the answer. If either is redirected/piped (e.g.
    ``printf 'y\\n' | tamarind delete …``), we refuse rather than let
    ``typer.confirm`` consume the piped input as a "yes".
    """
    if yes:
        return
    if mode.json or not is_tty() or not is_stdin_tty():
        error(
            f"Refusing to {action} without confirmation in non-interactive mode. "
            "Pass --yes/-y to confirm.",
            mode,
            error_type="UsageError",
            exit_code=ExitCode.USAGE,
        )
        raise typer.Exit(ExitCode.USAGE)
    prompt = action[:1].upper() + action[1:]
    typer.confirm(f"{prompt}?", abort=True)


def _terminal_width(default: int = 100) -> int:
    """Best-effort terminal width; a sane default when stdout isn't a TTY."""
    try:
        cols = shutil.get_terminal_size((default, 24)).columns
    except (OSError, ValueError):
        return default
    return cols if cols and cols > 0 else default


def _truncate(text: str, width: int) -> str:
    """Clip ``text`` to ``width`` columns, marking the cut with an ellipsis."""
    if width <= 0:
        return ""
    if len(text) <= width:
        return text
    if width == 1:
        return _ELLIPSIS
    return text[: width - 1] + _ELLIPSIS


def _cell(value: Any) -> str:
    """Stringify a cell value, flattening whitespace so it can't break the grid."""
    if value is None:
        return ""
    return " ".join(str(value).split())


def _looks_numeric(text: str) -> bool:
    """True for integer/decimal counts (so numeric columns can be right-aligned)."""
    if not text:
        return False
    t = text.strip().lstrip("-").replace(",", "")
    if t.count(".") == 1:
        t = t.replace(".", "", 1)
    return t.isdigit()


def render_table(
    rows: Sequence[dict[str, Any]], columns: Sequence[str], *, max_width: int | None = None
) -> str:
    """Render a plain-text table that stays readable regardless of cell content.

    The table is shrunk to fit the terminal width (widest column first), long
    cells are truncated with an ellipsis, numeric columns are right-aligned, and
    no line carries trailing whitespace. Empty input renders ``(none)``.
    """
    if not rows:
        return "(none)"
    max_width = max_width or _terminal_width()

    str_rows: list[dict[str, str]] = [{c: _cell(r.get(c)) for c in columns} for r in rows]
    widths = {c: max([len(c), *(len(sr[c]) for sr in str_rows)]) for c in columns}
    # A column is numeric (→ right-aligned) only if it has values and all are numbers.
    numeric = {
        c: any(sr[c] for sr in str_rows) and all(_looks_numeric(sr[c]) for sr in str_rows if sr[c])
        for c in columns
    }

    # Shrink the widest column repeatedly until the table fits the terminal.
    overhead = 2 * (len(columns) - 1)
    while sum(widths.values()) + overhead > max_width:
        widest = max(columns, key=lambda c: widths[c])
        if widths[widest] <= _MIN_COL:
            break
        widths[widest] -= 1

    def cell(text: str, c: str) -> str:
        clipped = _truncate(text, widths[c])
        return clipped.rjust(widths[c]) if numeric[c] else clipped.ljust(widths[c])

    def line(get) -> str:
        return "  ".join(cell(get(c), c) for c in columns).rstrip()

    lines = [
        line(lambda c: c),  # header
        "  ".join("-" * widths[c] for c in columns).rstrip(),  # separator rule
    ]
    lines.extend(line(lambda c, sr=sr: sr[c]) for sr in str_rows)
    return "\n".join(lines)


def is_tty() -> bool:
    return sys.stdout.isatty()


def is_stdin_tty() -> bool:
    return sys.stdin.isatty()
