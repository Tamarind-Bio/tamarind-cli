"""`tamarind auth` — credential management."""

from __future__ import annotations

from typing import Optional

import typer

from ... import rest
from ...config import config_dir, save_profile
from ...errors import AuthError, UsageError
from ...http import HTTPClient
from ...oauth import ClientCredentials, token_url_for
from ..._v1.switch import FileFlagCache
from .. import output
from ..v1.generic import ContractGroup

app = typer.Typer(no_args_is_help=True, cls=ContractGroup)

_CLIENT_FIELDS = ("client_id", "client_secret")


def _check_key(
    api_base: str, api_key: str | None, credentials: ClientCredentials | None = None
) -> bool:
    """Return True if the key (or the client credentials' token) authenticates against
    the job API (v1's, when v1 is on for it)."""
    with HTTPClient(
        api_base, api_key, flag_cache=FileFlagCache(config_dir()), credentials=credentials
    ) as client:
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
    client_id: Optional[str] = typer.Option(
        None,
        "--client-id",
        help="Store a service account's client ID and secret instead of an API key.",
        show_default=False,
    ),
    client_secret: Optional[str] = typer.Option(
        None,
        "--client-secret",
        help="The service account's client secret. If omitted, you'll be prompted.",
        show_default=False,
    ),
    no_verify: bool = typer.Option(False, "--no-verify", help="Skip verifying the key."),
) -> None:
    """Store an API key, or a service account's client ID and secret, in the current
    profile (~/.tamarind/config.json).

    Get a key from https://app.tamarind.bio (Settings → API), or set
    TAMARIND_API_KEY in the environment to skip storing one. A service account that
    signs in with OAuth has a client ID and secret instead: pass --client-id, or set
    TAMARIND_CLIENT_ID and TAMARIND_CLIENT_SECRET.
    """
    state = ctx.obj
    cfg = state.config()
    if client_id is not None or client_secret is not None:
        if api_key is not None:
            raise UsageError("Pass --api-key, or --client-id and --client-secret, not both.")
        if not client_id or not client_id.strip():
            raise UsageError("--client-secret needs --client-id.")
        _login_client(state, cfg, client_id.strip(), client_secret, verify=not no_verify)
        return
    key = api_key or typer.prompt("Tamarind API key", hide_input=True)
    key = key.strip()

    if not no_verify and not _check_key(cfg.api_base, key):
        raise AuthError("That API key was rejected by the API. Not saved.")

    save_profile(cfg.profile, api_key=key, forget=_CLIENT_FIELDS)
    output.emit(
        {"ok": True, "profile": cfg.profile, "verified": not no_verify},
        state.output,
        human=f"Saved API key to profile '{cfg.profile}'.",
    )


def _login_client(state, cfg, client_id: str, client_secret: str | None, *, verify: bool) -> None:
    secret = (client_secret or typer.prompt("Client secret", hide_input=True)).strip()
    if not secret:
        raise UsageError("The client secret is empty.")
    if verify:
        # Its own token source, not the process's shared one: a secret that fails here
        # leaves nothing behind.
        credentials = ClientCredentials(client_id, secret, token_url=token_url_for(cfg.api_base))
        try:
            # The token first, so a refusal there keeps its reason (not enabled, bad secret).
            credentials.token()
        except AuthError as exc:
            raise AuthError(f"{exc.message} Not saved.", detail=exc.detail) from None
        if not _check_key(cfg.api_base, None, credentials):
            raise AuthError("Those client credentials were rejected by the API. Not saved.")
    save_profile(cfg.profile, client_id=client_id, client_secret=secret, forget=("api_key",))
    output.emit(
        {"ok": True, "profile": cfg.profile, "clientId": client_id, "verified": verify},
        state.output,
        human=f"Saved client ID {client_id} and its secret to profile '{cfg.profile}'.",
    )


@app.command()
def status(ctx: typer.Context) -> None:
    """Show the active profile and whether its credentials work."""
    state = ctx.obj
    cfg = state.config()
    credentials = cfg.client_credentials()
    if credentials is not None:
        verified = _check_key(cfg.api_base, None, credentials)
        output.emit(
            {
                "profile": cfg.profile,
                "hasKey": False,
                "hasClientCredentials": True,
                "clientId": cfg.client_id,
                "verified": verified,
            },
            state.output,
            human=(
                f"profile:      {cfg.profile}\n"
                f"client id:    {cfg.client_id} "
                f"({'verified' if verified else 'not verified'})"
            ),
        )
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


@app.command()
def logout(ctx: typer.Context) -> None:
    """Remove the stored API key (and client ID and secret) from the current profile."""
    state = ctx.obj
    cfg = state.config()
    had_client = _profile_has_client(cfg.profile)
    save_profile(cfg.profile, api_key="", make_current=False, forget=_CLIENT_FIELDS)
    output.emit(
        {"ok": True, "profile": cfg.profile},
        state.output,
        human=(
            f"Cleared API key and client credentials for profile '{cfg.profile}'."
            if had_client
            else f"Cleared API key for profile '{cfg.profile}'."
        ),
    )


def _profile_has_client(profile: str) -> bool:
    from ...config import _read_store

    stored = _read_store().get("profiles", {}).get(profile, {})
    return any(stored.get(name) for name in _CLIENT_FIELDS)
