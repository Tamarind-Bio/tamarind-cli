"""Whether a caller's requests go to the v1 API: the server says, per key.

The server answers on v1 ``GET /me`` as ``clients.useV1``, from the per-user flag
``cli-sdk-v1-api``. Anything but an explicit ``true`` means classic: no answer (no DNS
yet), a 401, a 404 (a caller outside v1), a body that isn't JSON, the field missing or
false. The answer is cached for a few minutes per (v1 base, key); the cache never holds
the key itself, only a hash of it.

The v1 base comes from the classic one, so one setting names the environment. A base
this module doesn't know (a local server) has no v1, and stays classic.
``TAMARIND_V1_API_BASE`` overrides it, for tests against another environment, and
``TAMARIND_API=classic`` turns v1 off entirely.
"""

from __future__ import annotations

import hashlib
import json
import os
import threading
import time
import uuid
from pathlib import Path
from typing import Protocol

import httpx

from tamarind.attribution import client_headers
from tamarind.errors import UsageError

FLAG = "cli-sdk-v1-api"
PROBE_TIMEOUT = 5.0
CACHE_SECONDS = 300.0
# How long an answer is kept at all: past CACHE_SECONDS it only decides what --help
# lists (which never asks the server), until a command asks again.
KEEP_SECONDS = 7 * 24 * 3600.0
CACHE_FILE = "v1-flag.json"

_PRODUCTION = "https://api.tamarind.bio"
_STAGING = "https://api-staging.tamarind.bio"
# Hosts of the classic API and catalog, and the v1 API in the same environment.
_V1_FOR_HOST = {
    "app.tamarind.bio": _PRODUCTION,
    "mcp.tamarind.bio": _PRODUCTION,
    "staging.tamarind.bio": _STAGING,
    "mcp-staging.tamarind.bio": _STAGING,
}


class V1NotEnabledError(UsageError):
    """An operation only the v1 API has, for a caller it isn't enabled for yet."""

    def __init__(self, what: str):
        super().__init__(f"{what} uses the v1 API, which isn't enabled for this account yet.")


def v1_base_for(base_url: str | None) -> str | None:
    """The v1 base for a classic API or catalog base; None when there isn't one."""
    override = os.environ.get("TAMARIND_V1_API_BASE", "").strip()
    if override:
        return override.rstrip("/")
    try:
        host = httpx.URL(str(base_url or "")).host
    except (httpx.InvalidURL, TypeError, ValueError):
        return None
    return _V1_FOR_HOST.get(host)


def disabled() -> bool:
    """``TAMARIND_API=classic``: never ask, never route."""
    return os.environ.get("TAMARIND_API", "").strip().lower() == "classic"


def cache_key(v1_base: str, api_key: str) -> str:
    return hashlib.sha256(f"{v1_base}\n{api_key}".encode()).hexdigest()


class FlagCache(Protocol):
    def get(self, key: str, *, max_age: float = CACHE_SECONDS) -> bool | None: ...

    def set(self, key: str, value: bool) -> None: ...


class MemoryFlagCache:
    """Answers kept in this process."""

    def __init__(self) -> None:
        self._items: dict[str, tuple[bool, float]] = {}
        self._lock = threading.Lock()

    def get(self, key: str, *, max_age: float = CACHE_SECONDS) -> bool | None:
        with self._lock:
            item = self._items.get(key)
        if item is None or time.monotonic() - item[1] > max_age:
            return None
        return item[0]

    def set(self, key: str, value: bool) -> None:
        with self._lock:
            self._items[key] = (value, time.monotonic())


class FileFlagCache:
    """Answers kept in ``<directory>/v1-flag.json`` (mode 0600), so separate processes
    (CLI commands) share them. Best effort: a file that can't be read or written just
    means asking again."""

    def __init__(self, directory: str | os.PathLike[str]):
        self.path = Path(directory) / CACHE_FILE

    def _read(self) -> dict[str, dict[str, object]]:
        try:
            data = json.loads(self.path.read_text())
        except (OSError, ValueError):
            return {}
        return data if isinstance(data, dict) else {}

    @staticmethod
    def _fresh(entry: object, now: float, max_age: float) -> bool:
        if not isinstance(entry, dict):
            return False
        at = entry.get("at")
        return isinstance(at, (int, float)) and 0 <= now - at <= max_age

    def get(self, key: str, *, max_age: float = CACHE_SECONDS) -> bool | None:
        entry = self._read().get(key)
        if not isinstance(entry, dict) or not self._fresh(entry, time.time(), max_age):
            return None
        value = entry.get("useV1")
        return value if isinstance(value, bool) else None

    def set(self, key: str, value: bool) -> None:
        now = time.time()
        data = {k: v for k, v in self._read().items() if self._fresh(v, now, KEEP_SECONDS)}
        data[key] = {"useV1": value, "at": now}
        # A fresh, unguessable name, opened only if nothing is there yet and never through
        # a link: in a shared config directory nobody can plant a file or symlink for the
        # write to land on.
        temporary = self.path.with_name(f".{CACHE_FILE}.{uuid.uuid4().hex}")
        made = False
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
            handle = os.open(temporary, flags, 0o600)
            made = True
            with os.fdopen(handle, "w") as out:
                json.dump(data, out)
            os.replace(temporary, self.path)
        except OSError:
            if made:  # only ever remove the file this write made
                try:
                    temporary.unlink()
                except OSError:
                    pass


_PROCESS_CACHE = MemoryFlagCache()


def probe(v1_base: str, api_key: str, *, timeout: float = PROBE_TIMEOUT) -> bool:
    """Ask v1 ``GET /me`` once (no retries): True only for ``clients.useV1: true``."""
    from tamarind import __version__

    headers = {
        "Accept": "application/json",
        "User-Agent": f"tamarind-cli/{__version__}",
        **client_headers(),
        "x-api-key": api_key,
    }
    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.get(f"{v1_base}/me", headers=headers, follow_redirects=False)
        if response.status_code != 200:
            return False
        body = response.json()
    except (httpx.HTTPError, ValueError):
        return False
    clients = body.get("clients") if isinstance(body, dict) else None
    return isinstance(clients, dict) and clients.get("useV1") is True


class Switch:
    """One client's answer to "does this key use v1?", asked when first needed and then
    kept for the client's life, so a long wait never changes API halfway through. A new
    client reads the shared cache, so a changed flag reaches the next command (or client)
    within :data:`CACHE_SECONDS`."""

    def __init__(self, api_key: str | None, v1_base: str | None, cache: FlagCache | None = None):
        self.api_key = api_key
        self.v1_base = v1_base.rstrip("/") if v1_base else None
        self._cache = cache
        self._lock = threading.Lock()
        self._known: bool | None = None

    def _key(self) -> str | None:
        if not self.api_key or not self.v1_base or disabled():
            return None
        return cache_key(self.v1_base, self.api_key)

    def _caches(self) -> list[FlagCache]:
        # This process's answers first, then the given cache (the CLI's file): a cache
        # file that can't be written still means one question per process, not per client.
        caches: list[FlagCache] = [_PROCESS_CACHE]
        if self._cache is not None and self._cache is not _PROCESS_CACHE:
            caches.append(self._cache)
        return caches

    def _read(self, key: str, max_age: float) -> bool | None:
        for cache in self._caches():
            value = cache.get(key, max_age=max_age)
            if value is not None:
                return value
        return None

    def cached(self, *, max_age: float = CACHE_SECONDS) -> bool | None:
        """This client's answer, or else one no older than ``max_age`` in the caches;
        never the network."""
        key = self._key()
        if key is None:
            return False
        if self._known is not None:
            return self._known
        return self._read(key, max_age)

    def last_known(self) -> bool | None:
        """The last answer kept (``--help`` lists v1 commands by it), however old."""
        return self.cached(max_age=KEEP_SECONDS)

    def on(self) -> bool:
        key = self._key()
        if key is None:
            return False
        with self._lock:
            if self._known is not None:
                return self._known
            known = self._read(key, CACHE_SECONDS)
            if known is None:
                assert self.v1_base is not None and self.api_key is not None
                known = probe(self.v1_base, self.api_key)
                for cache in self._caches():
                    cache.set(key, known)
            # Kept for this client's life, however it was learned: a long wait never
            # changes API halfway through.
            self._known = known
            return known
