"""Discovery / catalog client.

The tool catalog and per-tool schemas are gated by per-org visibility logic
that runs server-side, so the CLI consumes them over HTTP from the catalog
service (the ``/catalog/*`` routes) rather than reading the database directly.

These routes return exactly the JSON the MCP's discovery tools return
(``getAvailableTools``, ``listModalities``, ``listTags``, ``getJobSchema``),
because both are served by the same shared implementation. So whatever a tool
looks like in the MCP, it looks identical here.
"""

from __future__ import annotations

from typing import Any

from .http import HTTPClient

CATALOG_PREFIX = "catalog"


def list_tools(
    client: HTTPClient,
    *,
    modality: str | None = None,
    function: str | None = None,
    search: str | None = None,
    custom: bool | None = None,
) -> dict:
    """GET /catalog/tools — the filtered tool catalog (mirrors getAvailableTools)."""
    params = {
        "modality": modality,
        "function": function,
        "search": search,
        "custom": "true" if custom else None,
    }
    return client.get_json(f"{CATALOG_PREFIX}/tools", params=params)


def list_modalities(client: HTTPClient) -> dict:
    """GET /catalog/modalities — molecule types you can filter by."""
    return client.get_json(f"{CATALOG_PREFIX}/modalities")


def list_functions(client: HTTPClient) -> dict:
    """GET /catalog/functions — functions (tags) you can filter by."""
    return client.get_json(f"{CATALOG_PREFIX}/functions")


def get_schema(client: HTTPClient, job_type: str) -> dict:
    """GET /catalog/tools/{jobType}/schema — full parameter schema + example job."""
    return client.get_json(f"{CATALOG_PREFIX}/tools/{job_type}/schema")


# -- helpers for rendering / example extraction ---------------------------


def _conditional_true(conditionals: list[dict], values: dict[str, Any]) -> bool:
    """Is a parameter's conditional gate satisfied by ``values``?

    A direct port of `conditionalTrue` in the website's src/shared_utils.js, which is what
    /submit-job enforces (via `inactiveSpecifiedFieldError`). The list is AND-ed, and a
    controller missing from ``values`` fails the gate — same as there. Kept in step with
    that function: a checkType it grows and we don't just means we prune nothing extra,
    which is the safe direction (the server still rejects it) but is worth syncing.
    """
    for cond in conditionals:
        other = cond.get("otherSettingName")
        if other not in values:
            return False
        actual, expected = values[other], cond.get("otherSettingValue")
        check = cond.get("checkType")
        if check == "equals":
            if actual != expected:
                return False
        elif check == "not-equals":
            if actual == expected:
                return False
        elif check == "includes":
            # An array `otherSettingValue` means "scalar is one of [...]"; otherwise the
            # controller is a multiselect that must contain the value.
            if isinstance(expected, list):
                if actual not in expected:
                    return False
            elif isinstance(actual, list) and expected not in actual:
                return False
        elif check == "greaterThan":
            if not _as_float(actual) > _as_float(expected):
                return False
        elif check == "lessThan":
            if not _as_float(actual) < _as_float(expected):
                return False
        elif check == "exists":
            if not actual and actual != 0:
                return False
        elif check == "notEmpty":
            if isinstance(actual, (list, str)):
                if len(actual) == 0:
                    return False
            else:
                return False
        # An unrecognized checkType is skipped, as the JS `default:` branch does.
    return True


def _as_float(value: Any) -> float:
    """JS `parseFloat` semantics: unparseable compares false, never raises."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def example_settings(schema: dict[str, Any]) -> dict[str, Any]:
    """Pull a *submittable* ``settings`` dict out of a schema's exampleJob, if present.

    The catalog builds `exampleJob.settings` by collecting every parameter's `example`,
    including ones gated behind a `conditionals` controller it does not also set. Submitting
    that verbatim is rejected — boltz's example carries `ligands`, `dna` and `rna` without
    `addLigands`/`addDNA`/`addRNA`, and /submit-job answers `boltz field "ligands" can only
    be set when addLigands equals true`. So drop the fields whose gate is not satisfied,
    leaving an example that actually submits.

    Gates are evaluated against the example merged over the schema's defaults, because the
    server validates post-autofill settings: a field gated on `useMSA: true` is legitimately
    active when `useMSA` defaults to true and nobody overrode it. Pruning repeats to a fixed
    point, since a dropped field can itself be another field's controller (boltz
    `version` -> `predictAffinity` -> `binderChain`).
    """
    example = schema.get("exampleJob") or {}
    settings = dict(example.get("settings") or {})
    if not settings:
        return settings

    params = [p for p in schema.get("parameters", []) if p.get("name")]
    gated = {p["name"]: p["conditionals"] for p in params if p.get("conditionals")}
    if not gated:
        return settings
    defaults = {p["name"]: p["default"] for p in params if "default" in p}

    while True:
        values = {**defaults, **settings}
        dropped = [
            name
            for name in settings
            if name in gated and not _conditional_true(gated[name], values)
        ]
        if not dropped:
            return settings
        for name in dropped:
            del settings[name]


def required_param_names(schema: dict[str, Any]) -> list[str]:
    """Names of parameters marked required (top-level; ignores task-gated ones)."""
    out = []
    for p in schema.get("parameters", []):
        if p.get("required") and p.get("name"):
            out.append(p["name"])
    return out
