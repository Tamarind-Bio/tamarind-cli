"""Extract the Custom Tools operation slice from Tamarind's public OpenAPI."""

from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path
from typing import Any


CUSTOM_TOOLS_PATH = "/custom-tools"
HTTP_METHODS = frozenset({"get", "post", "put", "patch", "delete"})


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


def _component_refs(node: object, kind: str) -> set[str]:
    refs: set[str] = set()
    prefix = f"#/components/{kind}/"
    if isinstance(node, dict):
        ref = node.get("$ref")
        if isinstance(ref, str) and ref.startswith(prefix):
            refs.add(ref[len(prefix) :].replace("~1", "/").replace("~0", "~"))
        for value in node.values():
            refs.update(_component_refs(value, kind))
    elif isinstance(node, list):
        for value in node:
            refs.update(_component_refs(value, kind))
    return refs


def _reachable_components(
    roots: object,
    components: dict[str, Any],
    kind: str,
) -> dict[str, Any]:
    reachable = _component_refs(roots, kind)
    pending = list(reachable)
    while pending:
        name = pending.pop()
        for child in _component_refs(components.get(name, {}), kind) - reachable:
            reachable.add(child)
            pending.append(child)
    return {name: deepcopy(components[name]) for name in sorted(reachable)}


def _resolve_component(
    value: dict[str, Any],
    kind: str,
    components: dict[str, Any],
    seen: frozenset[str] = frozenset(),
) -> dict[str, Any]:
    ref = value.get("$ref")
    if not isinstance(ref, str):
        return value
    prefix = f"#/components/{kind}/"
    if not ref.startswith(prefix):
        raise ValueError(f"Unsupported {kind} reference: {ref}")
    if ref in seen:
        raise ValueError(f"Cyclic {kind} reference: {ref}")
    name = ref[len(prefix) :].replace("~1", "/").replace("~0", "~")
    target = components.get(name)
    if not isinstance(target, dict):
        raise ValueError(f"Unresolved {kind} reference: {ref}")
    return _resolve_component(target, kind, components, seen | {ref})


def extract(spec: dict[str, Any]) -> dict[str, Any]:
    components = spec.get("components", {})
    path_items = components.get("pathItems", {})
    custom_path_items = {
        path: path_item
        for path, path_item in spec.get("paths", {}).items()
        if _is_custom_tools_path(path) and isinstance(path_item, dict)
    }
    retained_path_items = _reachable_components(custom_path_items, path_items, "pathItems")
    paths: dict[str, Any] = {}
    for path, unresolved_path_item in custom_path_items.items():
        path_item = _resolve_component(unresolved_path_item, "pathItems", retained_path_items)
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

    schemas = components.get("schemas", {})
    responses = components.get("responses", {})
    parameters = components.get("parameters", {})
    request_bodies = components.get("requestBodies", {})
    retained_parameters = _reachable_components(paths, parameters, "parameters")
    retained_request_bodies = _reachable_components(paths, request_bodies, "requestBodies")

    reachable = (
        _schema_refs(paths)
        | _schema_refs(responses)
        | _schema_refs(retained_parameters)
        | _schema_refs(retained_request_bodies)
    )
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
    if retained_request_bodies:
        extracted_components["requestBodies"] = retained_request_bodies
    if retained_path_items:
        extracted_components["pathItems"] = retained_path_items

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
