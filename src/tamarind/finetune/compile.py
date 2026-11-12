"""Keep config.json's `finetune` block in step with the `@tm` decorators, as the server reads them.

There is one decorator grammar and it lives on the platform: a build reads the decorators out of
the uploaded source and derives the block, and `POST /custom-tools/validate-config` does the
same without building. This module sends the folder's `.py` files to that endpoint and writes
back the config.json the build would use, so the SDK never carries a second copy of the grammar
that could drift from the server's.
"""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import stat
from typing import Any, Protocol

SKIPPED_DIRS = {"__pycache__", "node_modules", "venv", ".venv", "site-packages", "build", "dist"}
MAX_SOURCE_BYTES = 2 * 1024 * 1024
MAX_SOURCES = 500


class FinetuneCompileError(ValueError):
    """The decorators cannot become a block, or config.json cannot be synced. The message names the file."""

    def __init__(self, path: str, lineno: int | None, message: str) -> None:
        where = f"{path}:{lineno}" if lineno else path
        super().__init__(f"{where}: {message}" if path else message)
        self.path = path
        self.lineno = lineno


@dataclass(frozen=True)
class SourceText:
    relative: str
    text: str


@dataclass(frozen=True)
class CompiledFinetune:
    """What the server read off the decorators: `block` is config.json's `finetune`."""

    block: dict[str, Any]
    resources: dict[str, Any]
    sources: tuple[str, ...]


@dataclass(frozen=True)
class SyncResult:
    compiled: CompiledFinetune | None
    #: True when config.json differs from what a build would use (derived or stale).
    changed: bool
    #: The config.json text a build would use.
    config_text: str
    warnings: tuple[tuple[str, str], ...] = ()


class ConfigValidator(Protocol):
    def validate_config(self, *, config: str, sources: list[dict[str, str]]) -> dict[str, Any]: ...


def iter_python_sources(folder: str | Path) -> list[SourceText]:
    """Every .py file under `folder`, as (relative path, text), skipping environments, caches and links."""
    root = Path(folder)
    out: list[SourceText] = []
    for path in sorted(root.rglob("*.py")):
        parts = path.relative_to(root).parts
        if any(p.startswith(".") or p in SKIPPED_DIRS for p in parts[:-1]) or path.is_symlink():
            continue
        if path.stat().st_size > MAX_SOURCE_BYTES:
            continue
        out.append(SourceText(path.relative_to(root).as_posix(), path.read_text(encoding="utf-8")))
        if len(out) >= MAX_SOURCES:
            break
    return out


def mentions_decorators(sources: list[SourceText]) -> bool:
    """A cheap local hint that the folder carries `@tm` decorators the server will compile."""
    return any("tamarind" in s.text and "training_run" in s.text for s in sources)


def sync_config_json(folder: str | Path, *, write: bool, validator: ConfigValidator) -> SyncResult:
    """Ask the platform what config.json the decorators in `folder` describe, and write it back.

    With `write`, config.json is rewritten only when it differs. The folder and config.json must
    be real (no symlink at either), and the write never follows a link, so neither the CLI command
    nor `build()` can rewrite a file outside the source folder. The server is the one that parses
    config.json and compiles the decorators; a config it refuses is reported, never rewritten.
    """
    root = Path(folder)
    if root.is_symlink() or not root.is_dir():
        raise FinetuneCompileError(
            str(folder), None, "the source folder must be a real directory, not a symlink"
        )
    config_path = root / "config.json"
    sources = iter_python_sources(root)
    try:
        metadata = os.lstat(config_path)
    except FileNotFoundError:
        if not mentions_decorators(sources):
            return SyncResult(None, False, "")
        raise FinetuneCompileError(
            "config.json",
            None,
            "config.json is required; the decorators only fill its finetune block",
        ) from None
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise FinetuneCompileError(
            "config.json", None, "config.json must be a regular file, not a symlink"
        )
    text = config_path.read_text(encoding="utf-8")
    if not sources:
        return SyncResult(None, False, text)

    response = validator.validate_config(
        config=text, sources=[{"path": s.relative, "content": s.text} for s in sources]
    )
    derivation = response.get("finetune")
    corrected = derivation.get("config") if isinstance(derivation, dict) else None
    errors = response.get("errors") or []
    if errors and not isinstance(corrected, str):
        # A config the build refuses for a reason a sync cannot fix: decorators that do not compile,
        # or a config.json that is itself invalid. Report it; never rewrite it.
        raise FinetuneCompileError(
            "", None, str(errors[0].get("message", "config.json was refused"))
        )
    compiled = None
    if isinstance(derivation, dict) and isinstance(derivation.get("block"), dict):
        compiled = CompiledFinetune(
            block=dict(derivation["block"]),
            resources=dict(derivation.get("resources") or {}),
            sources=tuple(derivation.get("sources") or ()),
        )
    if not isinstance(corrected, str):
        return SyncResult(compiled, False, text, _warnings(response))
    if write:
        _write_nofollow(config_path, corrected)
    return SyncResult(compiled, True, corrected, _warnings(response))


def _warnings(response: dict[str, Any]) -> tuple[tuple[str, str], ...]:
    return tuple(
        (str(w.get("code", "")), str(w.get("message", "")))
        for w in (response.get("warnings") or [])
        if isinstance(w, dict)
    )


def _write_nofollow(path: Path, text: str) -> None:
    """Rewrite `path` in place without following a link that appeared since the lstat above."""
    flags = os.O_WRONLY | os.O_TRUNC | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags)
    try:
        os.write(fd, text.encode("utf-8"))
    finally:
        os.close(fd)
