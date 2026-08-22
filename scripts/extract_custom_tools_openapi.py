"""Extract the Custom Tools operation slice from Tamarind's public OpenAPI."""

from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path
from typing import Any


CUSTOM_TOOLS_PATH = "/custom-tools"
HTTP_METHODS = frozenset({"get", "post", "put", "patch", "delete"})
OPENAPI_OPERATION_KEYS = HTTP_METHODS | {"head", "options", "trace"}
OPAQUE_VALUE_KEYS = frozenset({"example", "examples", "default", "const", "enum"})


def _is_custom_tools_path(path: str) -> bool:
    return path == CUSTOM_TOOLS_PATH or path.startswith(f"{CUSTOM_TOOLS_PATH}/")


def _schema_refs(node: object, *, opaque: bool = False) -> set[str]:
    refs: set[str] = set()
    if opaque:
        return refs
    if isinstance(node, dict):
        ref = node.get("$ref")
        if isinstance(ref, str) and ref.startswith("#/components/schemas/"):
            token = ref[len("#/components/schemas/") :]
            refs.add(token.replace("~1", "/").replace("~0", "~"))
        for key, value in node.items():
            refs.update(
                _schema_refs(value, opaque=key in OPAQUE_VALUE_KEYS or key.startswith("x-"))
            )
    elif isinstance(node, list):
        for value in node:
            refs.update(_schema_refs(value))
    return refs


def _component_refs(node: object, kind: str, *, opaque: bool = False) -> set[str]:
    refs: set[str] = set()
    if opaque:
        return refs
    prefix = f"#/components/{kind}/"
    if isinstance(node, dict):
        ref = node.get("$ref")
        if isinstance(ref, str) and ref.startswith(prefix):
            refs.add(ref[len(prefix) :].replace("~1", "/").replace("~0", "~"))
        for key, value in node.items():
            refs.update(
                _component_refs(
                    value,
                    kind,
                    opaque=key in OPAQUE_VALUE_KEYS or key.startswith("x-"),
                )
            )
    elif isinstance(node, list):
        for value in node:
            refs.update(_component_refs(value, kind))
    return refs


def _security_scheme_names(requirements: object) -> set[str]:
    names: set[str] = set()
    if isinstance(requirements, list):
        for requirement in requirements:
            if isinstance(requirement, dict):
                names.update(str(name) for name in requirement)
    return names


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
        if "servers" in path_item:
            raise ValueError(f"Path-level servers are outside the SDK profile: {path}")
        unsupported = OPENAPI_OPERATION_KEYS.intersection(path_item) - HTTP_METHODS
        if unsupported:
            raise ValueError(
                f"Unsupported Custom Tools HTTP methods at {path}: {sorted(unsupported)}"
            )
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
    # Response-map keys such as `default` are structural, while Schema Object
    # `default` values are opaque literal data. Start the reachability walk from
    # each response value so those two meanings never share traversal rules.
    response_roots = [
        response
        for path_item in paths.values()
        for method in HTTP_METHODS
        if isinstance((operation := path_item.get(method)), dict)
        for response in operation.get("responses", {}).values()
    ]
    retained_responses = _reachable_components(response_roots, responses, "responses")

    reachable = (
        _schema_refs(paths)
        | _schema_refs(retained_responses)
        | _schema_refs(retained_parameters)
        | _schema_refs(retained_request_bodies)
    )
    pending = list(reachable)
    while pending:
        name = pending.pop()
        for child in _schema_refs(schemas.get(name, {})) - reachable:
            reachable.add(child)
            pending.append(child)

    security_schemes = components.get("securitySchemes", {})
    inherited_security = spec.get("security", [])
    retained_security_names = _security_scheme_names(inherited_security)
    for path_item in paths.values():
        for method in HTTP_METHODS:
            operation = path_item.get(method)
            if isinstance(operation, dict) and "security" in operation:
                retained_security_names.update(_security_scheme_names(operation["security"]))
    extracted_components = {
        "schemas": {name: deepcopy(schemas[name]) for name in sorted(reachable)},
        "securitySchemes": {
            name: deepcopy(security_schemes[name]) for name in sorted(retained_security_names)
        },
    }
    if retained_responses:
        extracted_components["responses"] = retained_responses
    if retained_parameters:
        extracted_components["parameters"] = retained_parameters
    if retained_request_bodies:
        extracted_components["requestBodies"] = retained_request_bodies
    extracted = {
        "openapi": spec["openapi"],
        "info": deepcopy(spec["info"]),
        "servers": deepcopy(spec.get("servers", [])),
        "security": deepcopy(spec.get("security", [])),
        "paths": deepcopy(paths),
        "components": extracted_components,
    }
    dialect = spec.get("jsonSchemaDialect")
    if dialect is not None:
        extracted["jsonSchemaDialect"] = deepcopy(dialect)
    return extracted


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
