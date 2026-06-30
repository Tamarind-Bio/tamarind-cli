"""Resolve job inputs from files, stdin, or inline ``--set`` overrides.

A job's ``settings`` can come from:

- ``--input job.yaml`` (YAML or JSON, by content) — the file holds the
  ``settings`` object (the same shape as a schema's ``exampleJob.settings``),
  or a full ``{jobName, type, settings}`` envelope.
- ``--input -`` to read that document from stdin.
- ``@yaml://./job.yaml`` / ``@json://./job.json`` reference syntax, matching the
  convention other agent CLIs use.
- ``--set key=value`` (repeatable) to set/override individual settings inline;
  the value is parsed as a YAML scalar (so ``--set numSamples=5`` is an int).
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from ..errors import ValidationError


@dataclass
class JobInput:
    settings: dict[str, Any]
    job_type: str | None = None
    job_name: str | None = None


def _load_text(source: str) -> str:
    """Read raw text from a path, stdin (``-``), or an ``@scheme://path`` ref."""
    if source == "-":
        return sys.stdin.read()
    if source.startswith("@"):
        # @yaml://./file.yaml  or  @json://./file.json  or  @./file
        body = source[1:]
        for scheme in ("yaml://", "json://", "file://"):
            if body.startswith(scheme):
                body = body[len(scheme) :]
                break
        source = body
    path = Path(source).expanduser()
    if not path.exists():
        raise ValidationError(f"Input file not found: {path}")
    return path.read_text()


def _parse_document(text: str) -> Any:
    text = text.strip()
    if not text:
        return {}
    # YAML is a superset of JSON, so safe_load handles both.
    try:
        return yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ValidationError(f"Could not parse input as YAML/JSON: {exc}") from exc


def _coerce_scalar(raw: str) -> Any:
    try:
        return yaml.safe_load(raw)
    except yaml.YAMLError:
        return raw


def _apply_sets(settings: dict[str, Any], pairs: list[str]) -> None:
    for pair in pairs:
        if "=" not in pair:
            raise ValidationError(f"--set expects key=value, got: {pair!r}")
        key, raw = pair.split("=", 1)
        settings[key.strip()] = _coerce_scalar(raw)


def _looks_like_envelope(doc: dict[str, Any]) -> bool:
    return "settings" in doc and ("type" in doc or "jobName" in doc)


def resolve_job_input(
    input_source: str | None,
    set_pairs: list[str] | None,
) -> JobInput:
    """Build a :class:`JobInput` from ``--input`` and ``--set`` options."""
    settings: dict[str, Any] = {}
    job_type: str | None = None
    job_name: str | None = None

    if input_source:
        doc = _parse_document(_load_text(input_source))
        if doc is None:
            doc = {}
        if not isinstance(doc, dict):
            raise ValidationError(
                "Input must be a mapping (the job settings, or a "
                "{jobName, type, settings} object)."
            )
        if _looks_like_envelope(doc):
            settings = dict(doc.get("settings") or {})
            job_type = doc.get("type")
            job_name = doc.get("jobName")
        else:
            settings = dict(doc)

    if set_pairs:
        _apply_sets(settings, set_pairs)

    return JobInput(settings=settings, job_type=job_type, job_name=job_name)


def dump_settings(settings: dict[str, Any]) -> str:
    return json.dumps(settings, indent=2, default=str)
