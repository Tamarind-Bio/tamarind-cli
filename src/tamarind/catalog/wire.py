"""The catalog boundary: raw schema payloads in, frozen types out.

A tool schema is the one catalog payload with structure worth modelling — callers
ask it two questions (what is required, and what does a runnable example look like)
and both were previously answered by re-walking nested dicts at the call site.

Tolerant in, strict out: a schema missing `parameters` or `exampleJob` parses to
empty rather than raising, because those are optional in practice.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from collections.abc import Iterable
from typing import Any, Mapping

# The response keys this boundary owns. Named so the architecture test can DERIVE
# the "shape knowledge stays here" rule from it rather than restating it.
_SCHEMA_KEYS = ("parameters", "exampleJob", "settings", "name", "required")


@dataclass(frozen=True)
class Parameter:
    """One tool parameter. ``raw`` keeps the full definition for rendering."""

    name: str
    required: bool = False
    raw: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ToolSchema:
    """A tool's parameter schema plus its example job."""

    parameters: tuple[Parameter, ...] = ()
    example_settings: Mapping[str, Any] = field(default_factory=dict)
    raw: Mapping[str, Any] = field(default_factory=dict)

    @property
    def required_names(self) -> tuple[str, ...]:
        """Names of parameters marked required (top-level; ignores task-gated ones)."""
        return tuple(p.name for p in self.parameters if p.required and p.name)


def parse_parameter(payload: Any) -> Parameter:
    if not isinstance(payload, Mapping):
        return Parameter(name="")
    return Parameter(
        name=str(payload.get("name") or ""),
        required=bool(payload.get("required")),
        raw=payload,
    )


def _iter_parameters(params: Any) -> tuple[Any, ...]:
    """The parameter collection, accepting any sequence the caller supplies.

    Deliberately NOT `isinstance(params, list)`. The helper this replaced iterated
    whatever it was given, so an SDK caller passing a tuple got their required names
    back; narrowing to the concrete JSON list type silently returned nothing instead —
    valid caller data lost with no error. Strings and mappings are excluded because
    iterating them yields characters and keys, which the old code would have crashed
    on rather than answered.
    """
    if params is None or isinstance(params, (str, bytes)) or isinstance(params, Mapping):
        return ()
    if isinstance(params, Iterable):
        return tuple(params)
    return ()


def _example_settings(example: Any) -> dict[str, Any]:
    """The example job's settings, or empty when the payload isn't shaped like that.

    `dict(...)` raises TypeError on a scalar and ValueError on a malformed list, so
    copying without checking turned a surprising catalog payload into a traceback out
    of `schema --example` — the opposite of what this module promises. Tolerant in.
    """
    if not isinstance(example, Mapping):
        return {}
    settings = example.get("settings")
    return dict(settings) if isinstance(settings, Mapping) else {}


def parse_schema(payload: Any) -> ToolSchema:
    """Normalize a tool schema. Never raises."""
    if not isinstance(payload, Mapping):
        return ToolSchema()
    example = payload.get("exampleJob") or {}
    return ToolSchema(
        parameters=tuple(parse_parameter(p) for p in _iter_parameters(payload.get("parameters"))),
        example_settings=_example_settings(example),
        raw=payload,
    )
