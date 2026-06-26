"""`tamarind auth` — credential management."""

from __future__ import annotations

from typing import Optional

import typer

from ... import rest
from ...config import mask_key, save_profile
from ...errors import AuthError
from ...http import HTTPClient
from .. import output

app = typer.Typer(no_args_is_help=True)


def _check_key(api_base: str, api_key: str) -> bool:
    """Return True if the key authenticates against the job API."""
    with HTTPClient(api_base, api_key) as client:
        try:
            rest.get_jobs(client, limit=1)
            return True
        except AuthError:
            return False


@app.command()
def login(
    ctx: typer.Context,
    api_key: Optional[str] = typer.Option(
        None, "--api-key", help="API key. If omitted, you'll be prompted.", show_default=False
    ),
    no_verify: bool = typer.Option(False, "--no-verify", help="Skip verifying the key."),
) -> None:
    """Store an API key in the current profile (~/.tamarind/config.json).

    Get a key from https://app.tamarind.bio (Settings → API), or set
    TAMARIND_API_KEY in the environment to skip storing one.
    """
    state = ctx.obj
    cfg = state.config()
    key = api_key or typer.prompt("Tamarind API key", hide_input=True)
    key = key.strip()

    if not no_verify and not _check_key(cfg.api_base, key):
        raise AuthError("That API key was rejected by the API. Not saved.")

    save_profile(cfg.profile, api_key=key)
    output.emit(
        {"ok": True, "profile": cfg.profile, "verified": not no_verify},
        state.output,
        human=f"Saved API key to profile '{cfg.profile}'.",
    )


@app.command()
def status(ctx: typer.Context) -> None:
    """Show the active profile, endpoints, and whether the key works."""
    state = ctx.obj
    cfg = state.config()
    verified = cfg.has_key and _check_key(cfg.api_base, cfg.api_key)
    result = {
        "profile": cfg.profile,
        "apiKey": mask_key(cfg.api_key),
        "hasKey": cfg.has_key,
        "verified": verified,
        "apiBase": cfg.api_base,
        "catalogBase": cfg.catalog_base,
    }
    human = (
        f"profile:      {cfg.profile}\n"
        f"api key:      {mask_key(cfg.api_key)} ({'verified' if verified else 'not verified'})\n"
        f"job api:      {cfg.api_base}\n"
        f"catalog api:  {cfg.catalog_base}"
    )
    output.emit(result, state.output, human=human)


@app.command()
def logout(ctx: typer.Context) -> None:
    """Remove the stored API key from the current profile."""
    state = ctx.obj
    cfg = state.config()
    save_profile(cfg.profile, api_key="", make_current=False)
    output.emit(
        {"ok": True, "profile": cfg.profile},
        state.output,
        human=f"Cleared API key for profile '{cfg.profile}'.",
    )
