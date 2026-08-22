"""Project the Custom Tools contract from Tamarind's complete public OpenAPI."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

CUSTOM_TOOLS_TAG = "custom-tools"
HTTP_METHODS = frozenset({"get", "post", "put", "patch", "delete"})
OPAQUE_VALUE_KEYS = frozenset({"example", "examples", "default", "const", "enum"})
SCHEMA_CHILD_KEYS = frozenset({"additionalProperties", "items"})
SCHEMA_CHILD_ARRAY_KEYS = frozenset({"allOf", "anyOf", "oneOf", "prefixItems"})


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


def _component_refs(node: object, kind: str) -> set[str]:
    return _refs(node, f"#/components/{kind}/")


def _reachable_components(roots: object, components: dict[str, Any], kind: str) -> dict[str, Any]:
    reachable = _component_refs(roots, kind)
    pending = list(reachable)
    while pending:
        name = pending.pop()
        for child in _component_refs(components.get(name, {}), kind) - reachable:
            reachable.add(child)
            pending.append(child)
    return {name: deepcopy(components[name]) for name in sorted(reachable)}


def _schema_refs(node: object, *, schema_context: bool = False) -> set[str]:
    return _refs(node, "#/components/schemas/", schema_context=schema_context)


def _security_scheme_names(requirements: object) -> set[str]:
    names: set[str] = set()
    if isinstance(requirements, list):
        for requirement in requirements:
            if isinstance(requirement, dict):
                names.update(str(name) for name in requirement)
    return names


def _resolve_path_item(
    document: dict[str, Any],
    path_item: object,
    *,
    location: str,
    seen: frozenset[str] = frozenset(),
) -> dict[str, Any] | None:
    if not isinstance(path_item, dict):
        return None
    ref = path_item.get("$ref")
    if ref is None:
        return path_item
    if not isinstance(ref, str) or not ref.startswith("#/components/pathItems/"):
        raise ValueError(f"{location}.$ref must target a local components/pathItems entry")
    if set(path_item) != {"$ref"}:
        raise ValueError(f"{location} cannot combine $ref with sibling fields")
    if ref in seen:
        raise ValueError(f"{location} contains a recursive Path Item reference")
    name = ref.removeprefix("#/components/pathItems/").replace("~1", "/").replace("~0", "~")
    components = document.get("components", {})
    path_items = components.get("pathItems", {}) if isinstance(components, dict) else {}
    if not isinstance(path_items, dict) or name not in path_items:
        raise ValueError(f"{location} references missing Path Item {ref!r}")
    resolved = _resolve_path_item(
        document,
        path_items[name],
        location=f"components.pathItems.{name}",
        seen=seen | {ref},
    )
    if resolved is None:
        raise ValueError(f"components.pathItems.{name} must be an object")
    return resolved


def project_custom_tools(document: dict[str, Any]) -> dict[str, Any]:
    """Select tagged Custom Tools operations and their reachable component closure."""

    paths: dict[str, Any] = {}
    for path, path_item in document.get("paths", {}).items():
        resolved_path_item = _resolve_path_item(document, path_item, location=f"paths.{path}")
        if resolved_path_item is None:
            continue
        selected = {
            method: operation
            for method, operation in resolved_path_item.items()
            if method in HTTP_METHODS
            and isinstance(operation, dict)
            and CUSTOM_TOOLS_TAG in operation.get("tags", [])
        }
        if selected:
            if isinstance(resolved_path_item.get("parameters"), list):
                selected["parameters"] = resolved_path_item["parameters"]
            paths[path] = selected

    if not paths:
        raise ValueError(f"Public OpenAPI has no operations tagged {CUSTOM_TOOLS_TAG!r}")

    components = document.get("components", {})
    parameters = _reachable_components(paths, components.get("parameters", {}), "parameters")
    request_bodies = _reachable_components(
        paths, components.get("requestBodies", {}), "requestBodies"
    )
    response_roots = [
        response
        for path_item in paths.values()
        for method in HTTP_METHODS
        if isinstance((operation := path_item.get(method)), dict)
        for response in operation.get("responses", {}).values()
    ]
    responses = _reachable_components(response_roots, components.get("responses", {}), "responses")

    schemas = components.get("schemas", {})
    reachable = (
        _schema_refs(paths)
        | _schema_refs(parameters)
        | _schema_refs(request_bodies)
        | _schema_refs(responses)
    )
    pending = list(reachable)
    while pending:
        name = pending.pop()
        for child in _schema_refs(schemas.get(name, {}), schema_context=True) - reachable:
            reachable.add(child)
            pending.append(child)

    inherited_security = document.get("security", [])
    security_names = _security_scheme_names(inherited_security)
    for path_item in paths.values():
        for method in HTTP_METHODS:
            operation = path_item.get(method)
            if isinstance(operation, dict) and "security" in operation:
                security_names.update(_security_scheme_names(operation["security"]))
    security_schemes = components.get("securitySchemes", {})

    projected_components: dict[str, Any] = {
        "schemas": {name: deepcopy(schemas[name]) for name in sorted(reachable)},
        "securitySchemes": {
            name: deepcopy(security_schemes[name]) for name in sorted(security_names)
        },
    }
    for key, values in (
        ("parameters", parameters),
        ("requestBodies", request_bodies),
        ("responses", responses),
    ):
        if values:
            projected_components[key] = values

    projected = {
        "openapi": document["openapi"],
        "info": deepcopy(document["info"]),
        "servers": deepcopy(document.get("servers", [])),
        "security": deepcopy(inherited_security),
        "paths": deepcopy(paths),
        "components": projected_components,
    }
    if "jsonSchemaDialect" in document:
        projected["jsonSchemaDialect"] = deepcopy(document["jsonSchemaDialect"])
    return projected
