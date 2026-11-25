"""Configuration and credential resolution.

Settings are resolved in this order (first wins):

    1. an explicit value passed on the command line (``--api-key`` etc.)
    2. an environment variable (``TAMARIND_API_KEY`` / ``TAMARIND_API_BASE`` /
       ``TAMARIND_CATALOG_BASE`` / ``TAMARIND_PROFILE``)
    3. the selected profile in ``~/.tamarind/config.json``
    4. a built-in default (base URLs only — there is no default API key)

This mirrors how the AWS CLI and similar tools layer flags > env > file, so it
is predictable for both humans and agents (an agent typically just exports
``TAMARIND_API_KEY``).

The credential is an API key, or a service account's OAuth client ID and secret
(``--client-id`` or ``client_id=``, ``TAMARIND_CLIENT_ID`` / ``TAMARIND_CLIENT_SECRET``,
or the profile's ``client_id`` / ``client_secret``; the CLI never takes the secret from the
command line, where other users and logs can see it), which
are traded for one-hour access tokens (:mod:`tamarind.oauth`). Each value resolves in the
order above. When both kinds are set, the one set at the more specific level wins: an
explicit value over the environment, the environment over the profile. At the same level
the API key wins. A client ID without a secret, or a secret without an ID, is an error.
"""

from __future__ import annotations

import json
import os
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

from tamarind.custom_tools._contract import OPENAPI_SERVER_URL
from tamarind.errors import UsageError
from tamarind.oauth import ClientCredentials, shared, token_url_for

DEFAULT_API_BASE = OPENAPI_SERVER_URL
# Discovery (tools/schema/modalities/functions) is served by the catalog
# service. It is a separate host from the job API because the catalog runs
# behind per-org visibility logic; see the package docstring.
DEFAULT_CATALOG_BASE = "https://mcp.tamarind.bio"

DEFAULT_PROFILE = "default"


def config_dir() -> Path:
    """Resolved each call so TAMARIND_CONFIG_DIR can change between invocations."""
    return Path(os.environ.get("TAMARIND_CONFIG_DIR", Path.home() / ".tamarind"))


def config_path() -> Path:
    return config_dir() / "config.json"


@dataclass
class Config:
    """Resolved settings for a single invocation."""

    api_key: str | None
    api_base: str
    catalog_base: str
    profile: str
    # A service account's OAuth client credentials, when they are the credential in use.
    client_id: str | None = None
    client_secret: str | None = field(default=None, repr=False)
    # Why the client credentials can't be used (half of the pair is set).
    credential_problem: str | None = None

    @property
    def has_key(self) -> bool:
        return bool(self.api_key)

    def client_credentials(self) -> ClientCredentials | None:
        """The process's shared token source for this client ID and secret, or None when
        the credential in use is an API key or there is none. Half a pair raises
        :class:`~tamarind.errors.UsageError`."""
        if self.credential_problem:
            raise UsageError(self.credential_problem)
        if not (self.client_id and self.client_secret):
            return None
        return shared(self.client_id, self.client_secret, token_url=token_url_for(self.api_base))


def _read_store() -> dict:
    path = config_path()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def _write_store(store: dict) -> None:
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(store, indent=2) + "\n")
    # Credentials live here — keep the file private (best effort on POSIX).
    try:
        path.chmod(0o600)
    except OSError:
        pass


def _normalize_base(url: str) -> str:
    """Trailing slash matters for httpx base_url + relative paths."""
    return url if url.endswith("/") else url + "/"


def resolve_profile_name(profile: str | None) -> str:
    if profile:
        return profile
    if os.environ.get("TAMARIND_PROFILE"):
        return os.environ["TAMARIND_PROFILE"]
    store = _read_store()
    return store.get("current_profile", DEFAULT_PROFILE)


def _first(*values: str | None) -> tuple[str | None, int | None]:
    """The first value given, and its level (0 explicit, 1 environment, 2 profile)."""
    for level, value in enumerate(values):
        if value:
            return value, level
    return None, None


def load_config(
    *,
    api_key: str | None = None,
    client_id: str | None = None,
    client_secret: str | None = None,
    api_base: str | None = None,
    catalog_base: str | None = None,
    profile: str | None = None,
) -> Config:
    """Resolve effective settings (flags > env > profile > default)."""
    profile_name = resolve_profile_name(profile)
    store = _read_store()
    prof = store.get("profiles", {}).get(profile_name, {})

    resolved_key, key_level = _first(api_key, os.environ.get("TAMARIND_API_KEY"), prof.get("api_key"))
    resolved_id, id_level = _first(client_id, os.environ.get("TAMARIND_CLIENT_ID"), prof.get("client_id"))
    resolved_secret, secret_level = _first(
        client_secret, os.environ.get("TAMARIND_CLIENT_SECRET"), prof.get("client_secret")
    )
    problem = None
    if resolved_id and not resolved_secret:
        problem = (
            "A client ID needs its client secret: set TAMARIND_CLIENT_SECRET or run "
            "`tamarind auth login --client-id`."
        )
    elif resolved_secret and not resolved_id:
        problem = "A client secret needs its client ID: set TAMARIND_CLIENT_ID or pass --client-id."
    pair_level = (
        min(id_level, secret_level)
        if id_level is not None and secret_level is not None
        else None
    )
    if pair_level is not None and (key_level is None or pair_level < key_level):
        resolved_key = None
    else:
        resolved_id = resolved_secret = None
    resolved_api_base = (
        api_base or os.environ.get("TAMARIND_API_BASE") or prof.get("api_base") or DEFAULT_API_BASE
    )
    resolved_catalog_base = (
        catalog_base
        or os.environ.get("TAMARIND_CATALOG_BASE")
        or prof.get("catalog_base")
        or DEFAULT_CATALOG_BASE
    )

    return Config(
        api_key=resolved_key,
        api_base=_normalize_base(resolved_api_base),
        catalog_base=_normalize_base(resolved_catalog_base),
        profile=profile_name,
        client_id=resolved_id,
        client_secret=resolved_secret,
        credential_problem=problem,
    )


def save_profile(
    profile: str,
    *,
    api_key: str | None = None,
    client_id: str | None = None,
    client_secret: str | None = None,
    api_base: str | None = None,
    catalog_base: str | None = None,
    make_current: bool = True,
    forget: Iterable[str] = (),
) -> None:
    """Persist credentials/endpoints for a profile to ``~/.tamarind/config.json``.
    ``forget`` names fields to remove from the profile."""
    store = _read_store()
    profiles = store.setdefault("profiles", {})
    prof = profiles.setdefault(profile, {})
    for name in forget:
        prof.pop(name, None)
    if api_key is not None:
        prof["api_key"] = api_key
    if client_id is not None:
        prof["client_id"] = client_id
    if client_secret is not None:
        prof["client_secret"] = client_secret
    if api_base is not None:
        prof["api_base"] = api_base
    if catalog_base is not None:
        prof["catalog_base"] = catalog_base
    if make_current:
        store["current_profile"] = profile
    _write_store(store)


def mask_key(key: str | None) -> str:
    if not key:
        return "<none>"
    if len(key) <= 8:
        return "*" * len(key)
    return f"{key[:4]}…{key[-4:]}"
