"""``tamarind`` command-line entry point.

Layout: a global callback resolves config (key, endpoints, profile, output
mode) onto ``ctx.obj``; each command builds a short-lived HTTP client from it.
All Tamarind errors propagate to :func:`run`, which prints them and exits with
the error's stable exit code (see :mod:`tamarind.errors`).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import typer

from .. import __version__
from ..config import Config, load_config
from ..errors import TamarindError
from ..http import HTTPClient
from . import output
from .output import OutputMode
from .commands import auth as auth_cmds
from .commands import catalog as catalog_cmds
from .commands import files as files_cmds
from .commands import jobs as jobs_cmds


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
    resolved_json = json_output if json_output is not None else (not output.is_tty())
    ctx.obj = State(
        output=OutputMode(json=resolved_json, quiet=quiet),
        _kwargs={
            "api_key": api_key,
            "api_base": api_base,
            "catalog_base": catalog_base,
            "profile": profile,
        },
    )


# Sub-apps (grouped commands)
app.add_typer(auth_cmds.app, name="auth", help="Manage credentials.")
app.add_typer(files_cmds.app, name="files", help="List, upload, and delete workspace files.")

# Flat commands
catalog_cmds.register(app)
jobs_cmds.register(app)


def run() -> None:
    """Console-script entry point with global error→exit-code mapping."""
    try:
        app()
    except TamarindError as exc:
        output.error(exc.message)
        if exc.detail is not None:
            typer.echo(typer.style(str(exc.detail), dim=True), err=True)
        raise SystemExit(exc.exit_code)


if __name__ == "__main__":
    run()
