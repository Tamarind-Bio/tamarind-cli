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
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_API_BASE = "https://app.tamarind.bio/api/"
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

    @property
    def has_key(self) -> bool:
        return bool(self.api_key)


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


def load_config(
    *,
    api_key: str | None = None,
    api_base: str | None = None,
    catalog_base: str | None = None,
    profile: str | None = None,
) -> Config:
    """Resolve effective settings (flags > env > profile > default)."""
    profile_name = resolve_profile_name(profile)
    store = _read_store()
    prof = store.get("profiles", {}).get(profile_name, {})

    resolved_key = api_key or os.environ.get("TAMARIND_API_KEY") or prof.get("api_key")
    resolved_api_base = (
        api_base
        or os.environ.get("TAMARIND_API_BASE")
        or prof.get("api_base")
        or DEFAULT_API_BASE
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
    )


def save_profile(
    profile: str,
    *,
    api_key: str | None = None,
    api_base: str | None = None,
    catalog_base: str | None = None,
    make_current: bool = True,
) -> None:
    """Persist credentials/endpoints for a profile to ``~/.tamarind/config.json``."""
    store = _read_store()
    profiles = store.setdefault("profiles", {})
    prof = profiles.setdefault(profile, {})
    if api_key is not None:
        prof["api_key"] = api_key
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
