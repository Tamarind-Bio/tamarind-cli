"""The v1 contract's operations, as the CLI needs them.

``_operations.json`` is generated from ``openapi/api-v1.yaml`` by
``scripts/gen_v1_cli_manifest.py``; a test fails when it is stale. Each entry
names the operation's CLI command (``x-clients.cli``), its SDK method
(``x-clients.sdk``), and its path parameters, query parameters and body.
"""

from __future__ import annotations

import json
from functools import lru_cache
from importlib import resources
from typing import Any


@lru_cache(maxsize=1)
def _document() -> dict[str, Any]:
    text = resources.files(__package__).joinpath("_operations.json").read_text(encoding="utf-8")
    return json.loads(text)


def operations() -> tuple[dict[str, Any], ...]:
    return tuple(_document()["operations"])


def group_help(path: tuple[str, ...]) -> str:
    """The contract tag's name and description for a command group, e.g. ``projects``."""
    tags = [op.get("tag") for p, op in by_cli_path().items() if p[: len(path)] == path]
    tag = next((t for t in tags if t), None)
    if not tag:
        return ""
    description = _document().get("tags", {}).get(tag) or ""
    return f"{tag} (v1). {description}".strip()


@lru_cache(maxsize=1)
def by_id() -> dict[str, dict[str, Any]]:
    return {op["operationId"]: op for op in operations()}


def operation(operation_id: str) -> dict[str, Any]:
    return by_id()[operation_id]


@lru_cache(maxsize=1)
def by_cli_path() -> dict[tuple[str, ...], dict[str, Any]]:
    """CLI command path → operation. Where two operations share a command (the
    upload and its multipart completion), the first one listed owns it."""
    out: dict[tuple[str, ...], dict[str, Any]] = {}
    for op in operations():
        if op.get("cli"):
            out.setdefault(tuple(op["cli"].split()), op)
    return out


def children(prefix: tuple[str, ...]) -> list[str]:
    """The next command names under ``prefix`` in the contract, in contract order."""
    names: list[str] = []
    for path in by_cli_path():
        if len(path) > len(prefix) and path[: len(prefix)] == prefix:
            name = path[len(prefix)]
            if name not in names:
                names.append(name)
    return names


def has_children(path: tuple[str, ...]) -> bool:
    return any(len(p) > len(path) and p[: len(path)] == path for p in by_cli_path())
