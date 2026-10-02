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


# The two names an envelope can give the tool. `submit`/`batch` use `type`;
# `finetune`/`finetune-batch` use `model`, because that is what those API routes
# call it. An envelope is recognised by EITHER, whichever command is running —
# see _looks_like_envelope.
TOOL_KEYS = ("type", "model")


def _looks_like_envelope(doc: dict[str, Any], tool_key: str = "type") -> bool:
    """Whether this document wraps the settings rather than being them.

    Deliberately keyed on the COMMAND's own tool field (or ``jobName``), not on
    either field. Widening it to both regresses raw settings documents that simply
    happen to contain a key called ``model`` or ``type`` beside their own
    ``settings`` — a real shape for ``custom-tools test``, whose schemas are
    user-defined, and for ``submit``/``validate``. Those documents must keep being
    read as settings.

    The dangerous half of the ambiguity — an envelope that names a DIFFERENT tool
    under the other key, which used to be dropped in silence — is handled once we
    already know this is an envelope, by :func:`envelope_tool_value`.
    """
    return "settings" in doc and (tool_key in doc or "jobName" in doc)


def _tool_identity(value: object) -> tuple[str, str]:
    """Compare two tool names the SAME way :func:`effective_job_type` does.

    That function trims and lowercases before deciding a name agrees with the
    command's tool, so a raw comparison here would disagree with it and reject
    ``{type: "ESM2", model: "esm2"}`` as two different tools when it is one.

    Non-strings are tagged separately rather than rendered into the string space:
    ``repr(1)`` is ``"1"``, which would make ``{type: 1, model: "1"}`` look like a
    single name and hide a genuinely malformed value that
    :func:`effective_job_type` goes on to reject.
    """
    if isinstance(value, str):
        return ("str", value.strip().lower())
    return ("other", repr(value))


def envelope_tool_value(doc: dict[str, Any], tool_key: str) -> object | None:
    """The tool an envelope names, reconciling BOTH tool keys.

    Called only for a document already recognised as an envelope. Every tool key
    actually present with a value is considered, so:

    - a tool named only under the other key is still seen, instead of being read as
      None and silently discarded while the command-line tool is submitted;
    - two keys naming DIFFERENT tools are refused rather than one being picked. That
      includes ``{type: null, model: esmfold}``, where keying on presence alone
      returned None and never looked at the conflicting ``model``.
    """
    named = {
        key: doc[key] for key in TOOL_KEYS if key in doc and doc[key] is not None
    }
    distinct = {_tool_identity(value) for value in named.values()}
    if len(distinct) > 1:
        pairs = ", ".join(f"{key}: {value!r}" for key, value in sorted(named.items()))
        raise ValidationError(
            f"The input file names two different tools ({pairs}). Keep only one of "
            f"{' or '.join(TOOL_KEYS)}."
        )
    if tool_key in named:
        return named[tool_key]
    return next(iter(named.values()), None)


def effective_job_type(
    cli_tool: str, file_type: object | None, *, tool_key: str = "type"
) -> str:
    """Reconcile the explicit ``<tool>`` argument with a ``type`` in the input file.

    The command's ``<tool>`` argument is authoritative. A ``type`` in the input
    file (envelope form) is only allowed to *agree* with it — a file whose
    ``type`` differs (e.g. running ``submit boltz`` on an ``type: esmfold``
    envelope) is a mistake and is rejected, rather than silently overriding the
    tool you named. Comparison ignores surrounding whitespace and case.

    ``file_type`` comes straight from YAML, so it may parse as a non-string
    (``type: 1`` → int, ``type: true`` → bool). Only None means absent;
    every supplied value must be a string that agrees with the selected tool.

    ``tool_key`` names the field being reconciled, for the error message only:
    the finetune commands carry the tool name in ``model`` rather than ``type``.
    """
    if file_type is not None and (
        not isinstance(file_type, str)
        or file_type.strip().lower() != cli_tool.strip().lower()
    ):
        raise ValidationError(
            f"Tool mismatch: the command targets '{cli_tool}' but the input "
            f"file's {tool_key} is '{file_type}'. Remove the file's '{tool_key}' "
            f"field, or re-run the command with '{file_type}' as the tool."
        )
    return cli_tool


def effective_job_name(cli_name: str | None, file_name: object | None) -> str | None:
    """Choose an explicit name without turning malformed values into generated names."""
    name = cli_name if cli_name is not None else file_name
    if name is not None and (not isinstance(name, str) or not name.strip()):
        raise ValidationError("Job name must be a non-empty string.")
    return name


def resolve_job_input(
    input_source: str | None,
    set_pairs: list[str] | None,
    *,
    tool_key: str = "type",
) -> JobInput:
    """Build a :class:`JobInput` from ``--input`` and ``--set`` options.

    ``tool_key`` is the envelope field naming the tool — ``type`` everywhere
    except the finetune commands, whose API surface calls it ``model``. Without
    it a ``{model, settings}`` envelope would not be recognised as an envelope
    at all, and the whole document would silently become the job's settings.
    """
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
                f"{{jobName, {tool_key}, settings}} object)."
            )
        if _looks_like_envelope(doc, tool_key):
            job_type = envelope_tool_value(doc, tool_key)
            job_name = doc.get("jobName")
            doc = doc["settings"]
        if not isinstance(doc, dict):
            raise ValidationError("Job settings must be a mapping (an object).")
        settings = dict(doc)

    if set_pairs:
        _apply_sets(settings, set_pairs)

    return JobInput(settings=settings, job_type=job_type, job_name=job_name)


def dump_settings(settings: dict[str, Any]) -> str:
    return json.dumps(settings, indent=2, default=str)
