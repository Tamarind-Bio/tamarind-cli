"""`tamarind auth` — credential management."""

from __future__ import annotations

from typing import Optional

import typer

from ... import rest
from ...config import save_profile
from ...errors import AuthError, TamarindError
from ...http import HTTPClient
from .. import output
from ..v1 import commands as v1
from ..v1.generic import ContractGroup

app = typer.Typer(no_args_is_help=True, cls=ContractGroup)


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

    if not no_verify and not (v1.key_works(state, key) if cfg.is_v1 else _check_key(cfg.api_base, key)):
        raise AuthError("That API key was rejected by the API. Not saved.")

    save_profile(cfg.profile, api_key=key)
    output.emit(
        {"ok": True, "profile": cfg.profile, "verified": not no_verify},
        state.output,
        human=f"Saved API key to profile '{cfg.profile}'.",
    )


@app.command()
def status(ctx: typer.Context) -> None:
    """Show the active profile and whether its key works."""
    state = ctx.obj
    cfg = state.config()
    if cfg.is_v1:
        _status_v1(state, cfg)
        return
    verified = cfg.has_key and _check_key(cfg.api_base, cfg.api_key)
    result = {
        "profile": cfg.profile,
        "hasKey": cfg.has_key,
        "verified": verified,
    }
    human = (
        f"profile:      {cfg.profile}\n"
        f"api key:      {'configured' if cfg.has_key else 'not configured'} "
        f"({'verified' if verified else 'not verified'})"
    )
    output.emit(result, state.output, human=human)


def _status_v1(state, cfg) -> None:
    """``auth status`` on v1: today's fields plus ``me``, the v1 getMe answer."""
    me = None
    if cfg.has_key:
        try:
            me = v1.me(state)
        except TamarindError as exc:
            if not v1.rejected_key(exc):
                raise
            me = None
    result = {
        "profile": cfg.profile,
        "hasKey": cfg.has_key,
        "verified": me is not None,
        "api": "v1",
        "me": me,
    }
    user = (me or {}).get("user") or {}
    org = (me or {}).get("organization") or {}
    human = (
        f"profile:      {cfg.profile}\n"
        f"api:          v1 ({cfg.v1_api_base})\n"
        f"api key:      {'configured' if cfg.has_key else 'not configured'} "
        f"({'verified' if me is not None else 'not verified'})"
    )
    if me is not None:
        human += f"\nuser:         {user.get('email') or user.get('id')}"
        if org:
            human += f"\norganization: {org.get('name') or org.get('id')}"
        human += f"\ntier:         {me.get('tier')}"
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
