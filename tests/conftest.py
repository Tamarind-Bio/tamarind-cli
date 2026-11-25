"""Shared test setup."""

from __future__ import annotations

from typing import Any, Callable

import pytest

from tamarind import oauth
from tamarind._v1 import switch
from tamarind.http import HTTPClient


@pytest.fixture(autouse=True)
def _v1_switch_off(monkeypatch):
    """No test asks a real server whether v1 is on: the answer is "no" (classic) unless a
    test turns it on, and every test starts with an empty in-process cache. No test
    inherits a token, or client credentials from the environment."""
    monkeypatch.setattr(switch, "probe", lambda *args, **kwargs: False)
    monkeypatch.setattr(switch, "_PROCESS_CACHE", switch.MemoryFlagCache())
    monkeypatch.setattr(oauth, "_SHARED", {})
    monkeypatch.delenv("TAMARIND_CLIENT_ID", raising=False)
    monkeypatch.delenv("TAMARIND_CLIENT_SECRET", raising=False)
    yield


def turn_v1_on(
    monkeypatch: pytest.MonkeyPatch,
    *,
    client: Any = None,
    factory: Callable[..., Any] | None = None,
) -> None:
    """The server says v1 is on for every key. v1 calls go to ``client`` (a fake v1 SDK
    client), or to what ``factory(http, **options)`` builds, when given."""
    monkeypatch.setattr(switch, "probe", lambda *args, **kwargs: True)
    if client is not None:
        factory = lambda http, **options: client  # noqa: E731
    if factory is not None:
        made = factory
        monkeypatch.setattr(HTTPClient, "_new_v1", lambda self, **options: made(self, **options))


def remember_v1(directory: Any, api_key: str, value: bool = True, base: str = "https://api.tamarind.bio") -> None:
    """What an earlier command learned, in the CLI's cache file: v1 is on for ``api_key``."""
    switch.FileFlagCache(directory).set(switch.cache_key(base, api_key), value)
