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
