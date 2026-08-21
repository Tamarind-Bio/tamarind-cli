"""Extract the Custom Tools operation slice from Tamarind's public OpenAPI."""

from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path
from typing import Any


CUSTOM_TOOLS_PATH = "/custom-tools"
HTTP_METHODS = frozenset({"get", "post", "put", "patch", "delete"})
PARAMETER_REF_PREFIX = "#/components/parameters/"


def _is_custom_tools_path(path: str) -> bool:
    return path == CUSTOM_TOOLS_PATH or path.startswith(f"{CUSTOM_TOOLS_PATH}/")


def _schema_refs(node: object) -> set[str]:
    refs: set[str] = set()
    if isinstance(node, dict):
        ref = node.get("$ref")
        if isinstance(ref, str) and ref.startswith("#/components/schemas/"):
            refs.add(ref.rsplit("/", 1)[-1])
        for value in node.values():
            refs.update(_schema_refs(value))
    elif isinstance(node, list):
        for value in node:
            refs.update(_schema_refs(value))
    return refs


def _parameter_refs(node: object) -> set[str]:
    refs: set[str] = set()
    if isinstance(node, dict):
        ref = node.get("$ref")
        if isinstance(ref, str) and ref.startswith(PARAMETER_REF_PREFIX):
            refs.add(ref[len(PARAMETER_REF_PREFIX) :].replace("~1", "/").replace("~0", "~"))
        for value in node.values():
            refs.update(_parameter_refs(value))
    elif isinstance(node, list):
        for value in node:
            refs.update(_parameter_refs(value))
    return refs


def extract(spec: dict[str, Any]) -> dict[str, Any]:
    paths: dict[str, Any] = {}
    for path, path_item in spec.get("paths", {}).items():
        if not _is_custom_tools_path(path):
            continue
        selected: dict[str, Any] = {
            method: operation
            for method, operation in path_item.items()
            if method in HTTP_METHODS and isinstance(operation, dict)
        }
        if selected:
            path_parameters = path_item.get("parameters")
            if isinstance(path_parameters, list):
                selected["parameters"] = path_parameters
            paths[path] = selected

    components = spec.get("components", {})
    schemas = components.get("schemas", {})
    responses = components.get("responses", {})
    parameters = components.get("parameters", {})
    reachable_parameters = _parameter_refs(paths)
    pending_parameters = list(reachable_parameters)
    while pending_parameters:
        name = pending_parameters.pop()
        for child in _parameter_refs(parameters.get(name, {})) - reachable_parameters:
            reachable_parameters.add(child)
            pending_parameters.append(child)
    retained_parameters = {
        name: deepcopy(parameters[name]) for name in sorted(reachable_parameters)
    }

    reachable = _schema_refs(paths) | _schema_refs(responses) | _schema_refs(retained_parameters)
    pending = list(reachable)
    while pending:
        name = pending.pop()
        for child in _schema_refs(schemas.get(name, {})) - reachable:
            reachable.add(child)
            pending.append(child)

    extracted_components = {
        "schemas": {name: deepcopy(schemas[name]) for name in sorted(reachable)},
        "securitySchemes": deepcopy(components.get("securitySchemes", {})),
        "responses": deepcopy(responses),
    }
    if retained_parameters:
        extracted_components["parameters"] = retained_parameters

    return {
        "openapi": spec["openapi"],
        "info": deepcopy(spec["info"]),
        "servers": deepcopy(spec.get("servers", [])),
        "security": deepcopy(spec.get("security", [])),
        "paths": deepcopy(paths),
        "components": extracted_components,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    spec = json.loads(args.source.read_text())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(extract(spec), indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
