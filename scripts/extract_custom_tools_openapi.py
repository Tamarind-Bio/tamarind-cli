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
SCHEMA_CHILD_KEYS = frozenset({"additionalProperties", "items"})
SCHEMA_CHILD_ARRAY_KEYS = frozenset({"allOf", "anyOf", "oneOf", "prefixItems"})


def _is_custom_tools_path(path: str) -> bool:
    return path == CUSTOM_TOOLS_PATH or path.startswith(f"{CUSTOM_TOOLS_PATH}/")


def _refs(node: object, prefix: str, *, schema_context: bool = False) -> set[str]:
    refs: set[str] = set()
    if isinstance(node, dict):
        ref = node.get("$ref")
        if isinstance(ref, str) and ref.startswith(prefix):
            token = ref[len(prefix) :]
            refs.add(token.replace("~1", "/").replace("~0", "~"))
        for key, value in node.items():
            if key.startswith("x-") or (schema_context and key in OPAQUE_VALUE_KEYS):
                continue
            if schema_context and key == "properties" and isinstance(value, dict):
                for property_schema in value.values():
                    refs.update(_refs(property_schema, prefix, schema_context=True))
                continue
            child_is_schema = key == "schema" or (
                schema_context and key in SCHEMA_CHILD_KEYS | SCHEMA_CHILD_ARRAY_KEYS
            )
            refs.update(_refs(value, prefix, schema_context=child_is_schema))
    elif isinstance(node, list):
        for value in node:
            refs.update(_refs(value, prefix, schema_context=schema_context))
    return refs


def _schema_refs(node: object, *, schema_context: bool = False) -> set[str]:
    return _refs(node, "#/components/schemas/", schema_context=schema_context)


def _component_refs(node: object, kind: str) -> set[str]:
    return _refs(node, f"#/components/{kind}/")


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
    resolved = _resolve_component(target, kind, components, seen | {ref})
    siblings = {key: child for key, child in value.items() if key != "$ref"}
    conflicts = resolved.keys() & siblings.keys()
    if conflicts:
        raise ValueError(f"Ambiguous {kind} reference siblings for {ref}: {sorted(conflicts)}")
    return {**resolved, **siblings}


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
        for child in _schema_refs(schemas.get(name, {}), schema_context=True) - reachable:
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
    spec = json.loads(args.source.read_text(encoding="utf-8"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(extract(spec), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
