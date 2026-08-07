"""Catalog decisions: pulling runnable bits out of a tool schema. Pure."""

from __future__ import annotations

from typing import Any


def example_settings(schema: dict[str, Any]) -> dict[str, Any]:
    """Pull a runnable ``settings`` dict out of a schema's exampleJob, if present."""
    example = schema.get("exampleJob") or {}
    return dict(example.get("settings") or {})


def required_param_names(schema: dict[str, Any]) -> list[str]:
    """Names of parameters marked required (top-level; ignores task-gated ones)."""
    out = []
    for p in schema.get("parameters", []):
        if p.get("required") and p.get("name"):
            out.append(p["name"])
    return out
