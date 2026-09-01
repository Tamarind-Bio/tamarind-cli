"""``tamarind`` command-line entry point.

Layout: a global callback resolves config (key, endpoints, profile, output
mode) onto ``ctx.obj``; each command builds a short-lived HTTP client from it.
All Tamarind errors propagate to :func:`run`, which prints them and exits with
the error's stable exit code (see :mod:`tamarind.errors`).
"""

from __future__ import annotations

from dataclasses import dataclass
import sys
from typing import Optional

import typer

try:  # Newer Typer can vendor Click as ``typer._click``.
    from typer._click.exceptions import ClickException
except ImportError:  # pragma: no cover - older Typer uses the external Click package
    from click import ClickException

from .. import __version__
from ..config import Config, load_config
from ..errors import ExitCode, TamarindError
from ..http import HTTPClient
from ..custom_tools.client import Tamarind
from . import output
from .output import OutputMode
from .commands import auth as auth_cmds
from .commands import catalog as catalog_cmds
from .commands import files as files_cmds
from .commands import jobs as jobs_cmds
from .commands import custom_tools as custom_tools_cmds


# Typer exposes the matching Abort class across both external-Click and
# vendored-Click releases. Importing it beside ClickException from
# ``typer._click.exceptions`` is not portable because that module does not
# export Abort in Typer 0.27.
Abort = typer.Abort


# The callback updates this before any command runs. Keeping the resolved mode
# here lets the outer console-script boundary render exceptions after Click has
# unwound its context. A process executes one CLI invocation, so this is scoped
# to exactly the lifecycle it represents.
_active_output_mode = OutputMode(json=not output.is_tty(), quiet=False)
_GLOBAL_VALUE_OPTIONS = {"--api-key", "--api-base", "--catalog-base", "--profile"}
_GLOBAL_FLAG_OPTIONS = {"--json", "--no-json", "--quiet", "-q"}
_COMMAND_GROUPS = {"auth", "custom-tools", "files"}


def _missing_command_message(argv: list[str]) -> str | None:
    """Detect JSON invocations that would otherwise print Rich help to stdout."""
    if any(arg in {"--help", "-h", "--version"} for arg in argv):
        return None
    remaining: list[str] = []
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg in _GLOBAL_VALUE_OPTIONS:
            # Let Click report the precise missing-option-value error instead
            # of misclassifying a dangling global flag as a missing command.
            if index + 1 >= len(argv) or argv[index + 1].startswith("-"):
                return None
            index += 2
            continue
        if any(arg.startswith(f"{option}=") for option in _GLOBAL_VALUE_OPTIONS):
            index += 1
            continue
        if arg in _GLOBAL_FLAG_OPTIONS:
            index += 1
            continue
        remaining.append(arg)
        index += 1
    if not remaining:
        return "Missing command."
    if len(remaining) == 1 and remaining[0] in _COMMAND_GROUPS:
        return f"Missing command for '{remaining[0]}'."
    return None


@dataclass
class State:
    """Per-invocation state stored on the Typer context."""

    output: OutputMode
    _kwargs: dict

    def config(self) -> Config:
        return load_config(**self._kwargs)

    def rest_client(self) -> HTTPClient:
        cfg = self.config()
        return HTTPClient(cfg.api_base, cfg.api_key)

    def catalog_client(self) -> HTTPClient:
        cfg = self.config()
        return HTTPClient(cfg.catalog_base, cfg.api_key)

    def sdk_client(self) -> Tamarind:
        """Build the shared SDK with this invocation's resolved credentials."""
        cfg = self.config()
        return Tamarind(api_key=cfg.api_key, api_base=cfg.api_base, profile=cfg.profile)


app = typer.Typer(
    name="tamarind",
    help=(
        "Tamarind Bio CLI — discover tools, submit and monitor protein/molecule "
        "jobs, and download results.\n\n"
        "Auth: export TAMARIND_API_KEY, or run `tamarind auth login`.\n"
        "Agents: pass --json (the default when stdout is not a terminal)."
    ),
    no_args_is_help=True,
    add_completion=False,
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"tamarind {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    ctx: typer.Context,
    api_key: Optional[str] = typer.Option(
        None, "--api-key", envvar="TAMARIND_API_KEY", help="API key (overrides env/profile).", show_default=False
    ),
    api_base: Optional[str] = typer.Option(
        None, "--api-base", envvar="TAMARIND_API_BASE", help="Job API base URL.", show_default=False
    ),
    catalog_base: Optional[str] = typer.Option(
        None, "--catalog-base", envvar="TAMARIND_CATALOG_BASE", help="Catalog (discovery) base URL.", show_default=False
    ),
    profile: Optional[str] = typer.Option(
        None, "--profile", envvar="TAMARIND_PROFILE", help="Named profile in ~/.tamarind/config.json.", show_default=False
    ),
    json_output: Optional[bool] = typer.Option(
        None, "--json/--no-json", help="Machine JSON output. Defaults on when stdout isn't a TTY.", show_default=False
    ),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress status lines."),
    _version: Optional[bool] = typer.Option(
        None, "--version", callback=_version_callback, is_eager=True, help="Show version and exit."
    ),
) -> None:
    global _active_output_mode
    resolved_json = json_output if json_output is not None else (not output.is_tty())
    _active_output_mode = OutputMode(json=resolved_json, quiet=quiet)
    ctx.obj = State(
        output=_active_output_mode,
        _kwargs={
            "api_key": api_key,
            "api_base": api_base,
            "catalog_base": catalog_base,
            "profile": profile,
        },
    )


# Sub-apps (grouped commands)
app.add_typer(auth_cmds.app, name="auth", help="Manage credentials.")
app.add_typer(
    custom_tools_cmds.app,
    name="custom-tools",
    help="Create, build, publish, and inspect organization Custom Tools.",
)
app.add_typer(files_cmds.app, name="files", help="List, upload, and delete workspace files.")

# Flat commands
catalog_cmds.register(app)
jobs_cmds.register(app)


def run() -> None:
    """Console-script entry point with global error→exit-code mapping."""
    global _active_output_mode
    # Reset for callers that invoke ``run`` repeatedly in-process (notably
    # tests). Read explicit output flags as a fallback for parse errors that
    # occur before the root callback can resolve them.
    resolved_json = not output.is_tty()
    for arg in sys.argv[1:]:
        if arg == "--json":
            resolved_json = True
        elif arg == "--no-json":
            resolved_json = False
    _active_output_mode = OutputMode(json=resolved_json, quiet=False)
    missing_command = _missing_command_message(sys.argv[1:])
    if resolved_json and missing_command is not None:
        output.error(
            missing_command,
            _active_output_mode,
            error_type="UsageError",
            exit_code=ExitCode.USAGE,
        )
        raise SystemExit(ExitCode.USAGE)
    try:
        # Disabling Click's standalone exception handling lets this boundary
        # render usage failures as JSON too. Command-level typer.Exit values
        # come back as an integer and are forwarded unchanged.
        exit_code = app(standalone_mode=False)
    except TamarindError as exc:
        output.error(
            exc.message,
            _active_output_mode,
            error_type=type(exc).__name__,
            exit_code=exc.exit_code,
            detail=exc.detail,
        )
        if exc.detail is not None and not _active_output_mode.json:
            typer.echo(typer.style(str(exc.detail), dim=True), err=True)
        raise SystemExit(exc.exit_code)
    except ClickException as exc:
        if _active_output_mode.json:
            output.error(
                exc.format_message(),
                _active_output_mode,
                error_type=type(exc).__name__,
                exit_code=exc.exit_code,
            )
        else:
            exc.show()
        raise SystemExit(exc.exit_code)
    except Abort:
        if _active_output_mode.json:
            output.error(
                "Aborted.",
                _active_output_mode,
                error_type="Abort",
                exit_code=ExitCode.ERROR,
            )
        else:
            typer.echo("Aborted!", err=True)
        raise SystemExit(ExitCode.ERROR)
    if isinstance(exit_code, int) and exit_code != ExitCode.OK:
        raise SystemExit(exit_code)


if __name__ == "__main__":
    run()
