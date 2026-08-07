"""Catalog decisions: pulling runnable bits out of a tool schema. Pure."""

from __future__ import annotations

from typing import Any

from . import wire


def example_settings(schema: dict[str, Any]) -> dict[str, Any]:
    """Pull a runnable ``settings`` dict out of a schema's exampleJob, if present."""
    return dict(wire.parse_schema(schema).example_settings)


def required_param_names(schema: dict[str, Any]) -> list[str]:
    """Names of parameters marked required (top-level; ignores task-gated ones)."""
    return list(wire.parse_schema(schema).required_names)
