"""Normalize validated OpenAPI into the small Custom Tools SDK IR."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from hashlib import sha256
import json
from typing import Any, cast

from .ir import (
    Api,
    Constraint,
    Field,
    JsonArray,
    JsonObject,
    JsonValue,
    Operation,
    Parameter,
    RequestBody,
    Response,
    Scalar,
    Schema,
    SchemaDefinition,
    SchemaKind,
)
from .profile import HTTP_METHODS, _dereference, validate_profile


def _json_value(value: object) -> JsonValue:
    if isinstance(value, Mapping):
        return JsonObject(tuple((str(key), _json_value(child)) for key, child in value.items()))
    if isinstance(value, list):
        return JsonArray(tuple(_json_value(child) for child in value))
    return cast(Scalar, value)


def _schema(value: Mapping[str, Any]) -> Schema:
    if "$ref" in value:
        ref = cast(str, value["$ref"])
        name = ref.removeprefix("#/components/schemas/").replace("~1", "/").replace("~0", "~")
        return Schema(
            kind="reference",
            reference=name,
            description=value.get("description"),
            has_default="default" in value,
            default=_json_value(value.get("default")),
        )

    if "anyOf" in value:
        non_null = next(part for part in value["anyOf"] if part.get("type") != "null")
        normalized = _schema(non_null)
        return replace(
            normalized,
            nullable=True,
            description=value.get("description", normalized.description),
            has_default="default" in value or normalized.has_default,
            default=(_json_value(value["default"]) if "default" in value else normalized.default),
        )

    kind = cast(SchemaKind, value["type"])
    constraints = tuple(
        Constraint(cast(Any, key), value[key])
        for key in (
            "minLength",
            "maxLength",
            "pattern",
            "minimum",
            "maximum",
            "minItems",
            "maxItems",
        )
        if key in value
    )
    description = cast(str | None, value.get("description"))
    enum = tuple(cast(list[Scalar], value.get("enum", [])))
    has_const = "const" in value
    const = cast(Scalar, value.get("const"))
    has_default = "default" in value
    default = _json_value(value.get("default"))
    if kind == "array":
        return Schema(
            kind="array",
            description=description,
            items=_schema(value["items"]),
            enum=enum,
            has_const=has_const,
            const=const,
            has_default=has_default,
            default=default,
            constraints=constraints,
        )
    if kind == "object":
        required = set(value.get("required", []))
        fields = tuple(
            Field(
                wire_name=name,
                schema=_schema(child),
                required=name in required,
                description=child.get("description"),
            )
            for name, child in value.get("properties", {}).items()
        )
        additional = value.get("additionalProperties")
        normalized_additional = (
            _schema(additional) if isinstance(additional, Mapping) else additional
        )
        object_kind: SchemaKind = (
            "map" if not fields and isinstance(normalized_additional, Schema) else "object"
        )
        return Schema(
            kind=object_kind,
            description=description,
            fields=fields,
            additional_properties=normalized_additional,
            enum=enum,
            has_const=has_const,
            const=const,
            has_default=has_default,
            default=default,
            constraints=constraints,
        )
    return Schema(
        kind=kind,
        description=description,
        enum=enum,
        has_const=has_const,
        const=const,
        has_default=has_default,
        default=default,
        constraints=constraints,
    )


def _parameter(document: Mapping[str, Any], value: object) -> Parameter:
    raw = _dereference(document, value, "parameter", "parameters")
    schema = _schema(raw["schema"])
    return Parameter(
        wire_name=raw["name"],
        location=raw["in"],
        required=raw.get("required", False),
        # FastAPI models absent optional query values as JSON Schema null. The
        # transport models absence in the Python signature, not in the wire value.
        schema=replace(schema, nullable=False) if not raw.get("required", False) else schema,
        description=raw.get("description"),
    )


def _request_body(document: Mapping[str, Any], value: object) -> RequestBody:
    raw = _dereference(document, value, "requestBody", "requestBodies")
    schema = raw["content"]["application/json"]["schema"]
    return RequestBody(required=raw.get("required", False), schema=_schema(schema))


def _response(document: Mapping[str, Any], status: str, value: object) -> Response:
    raw = _dereference(document, value, f"response {status}", "responses")
    content = raw.get("content")
    media = next(iter(content.values())) if content else None
    schema = _schema(media["schema"]) if media else None
    return Response(status=status, description=raw["description"], schema=schema)


def _parameters(
    document: Mapping[str, Any], path_parameters: list[object], operation_parameters: list[object]
) -> tuple[Parameter, ...]:
    merged: dict[tuple[str, str], Parameter] = {}
    for raw in [*path_parameters, *operation_parameters]:
        parameter = _parameter(document, raw)
        merged[(parameter.wire_name, parameter.location)] = parameter
    return tuple(merged.values())


def normalize(document: Mapping[str, Any]) -> Api:
    """Validate and convert an OpenAPI document into emitter-ready semantic data."""

    validate_profile(document)
    components = cast(Mapping[str, Any], document.get("components", {}))
    component_schemas = cast(Mapping[str, Mapping[str, Any]], components.get("schemas", {}))
    schemas = tuple(
        SchemaDefinition(name=name, schema=_schema(schema))
        for name, schema in component_schemas.items()
    )

    operations: list[Operation] = []
    for path, path_item in cast(Mapping[str, Mapping[str, Any]], document["paths"]).items():
        path_parameters = list(path_item.get("parameters", []))
        for method, operation in path_item.items():
            if method not in HTTP_METHODS:
                continue
            operations.append(
                Operation(
                    operation_id=operation["operationId"],
                    method=cast(Any, method.upper()),
                    path=path,
                    parameters=_parameters(
                        document, path_parameters, list(operation.get("parameters", []))
                    ),
                    request_body=(
                        _request_body(document, operation["requestBody"])
                        if "requestBody" in operation
                        else None
                    ),
                    responses=tuple(
                        _response(document, status, response)
                        for status, response in operation["responses"].items()
                    ),
                    summary=operation.get("summary"),
                )
            )

    info = cast(Mapping[str, str], document["info"])
    servers = cast(list[Mapping[str, str]], document.get("servers", []))
    canonical = json.dumps(document, sort_keys=True, separators=(",", ":")).encode()
    return Api(
        title=info["title"],
        version=info["version"],
        server_url=servers[0]["url"].rstrip("/") + "/",
        source_sha256=sha256(canonical).hexdigest(),
        schemas=schemas,
        operations=tuple(operations),
    )
