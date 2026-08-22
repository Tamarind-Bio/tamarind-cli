"""Validation for the deliberately small Tamarind Custom Tools OpenAPI profile."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any
from urllib.parse import urlsplit

HTTP_METHODS = {"delete", "get", "patch", "post", "put"}
PARAMETER_LOCATIONS = {"path", "query"}
SCHEMA_TYPES = {"array", "boolean", "integer", "null", "number", "object", "string"}
COMPOSITION_KEYS = {"allOf", "not", "oneOf"}
CONSTRAINT_KEYS = {"maxLength", "maximum", "minLength", "minimum", "pattern"}
UNSUPPORTED_SCHEMA_KEYS = {
    "contains",
    "dependentSchemas",
    "discriminator",
    "else",
    "if",
    "patternProperties",
    "prefixItems",
    "propertyNames",
    "then",
    "unevaluatedProperties",
}
REFERENCE_ANNOTATIONS = {
    "default",
    "deprecated",
    "description",
    "examples",
    "readOnly",
    "title",
    "writeOnly",
}


class ProfileViolation(ValueError):
    """An OpenAPI document uses behavior outside the supported profile."""

    def __init__(self, location: str, message: str) -> None:
        super().__init__(f"{location}: {message}")
        self.location = location
        self.message = message


def _mapping(value: object, location: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ProfileViolation(location, "must be an object")
    return value


def _sequence(value: object, location: str) -> Sequence[Any]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise ProfileViolation(location, "must be an array")
    return value


def _component(document: Mapping[str, Any], ref: str, location: str) -> Mapping[str, Any]:
    if not ref.startswith("#/components/"):
        raise ProfileViolation(location, "external references are not supported")
    parts = ref.removeprefix("#/components/").split("/")
    if len(parts) != 2:
        raise ProfileViolation(location, "references must target a named component")
    category, encoded_name = parts
    if category not in {"parameters", "requestBodies", "responses", "schemas"}:
        raise ProfileViolation(location, f"component references to {category!r} are not supported")
    name = encoded_name.replace("~1", "/").replace("~0", "~")
    components = _mapping(document.get("components", {}), "components")
    collection = _mapping(components.get(category, {}), f"components.{category}")
    target = collection.get(name)
    if target is None:
        raise ProfileViolation(location, f"reference target {ref!r} does not exist")
    return _mapping(target, f"components.{category}.{name}")


def _dereference(
    document: Mapping[str, Any],
    value: object,
    location: str,
    expected_category: str,
    seen: frozenset[str] = frozenset(),
) -> Mapping[str, Any]:
    item = _mapping(value, location)
    ref = item.get("$ref")
    if ref is None:
        return item
    if not isinstance(ref, str):
        raise ProfileViolation(f"{location}.$ref", "must be a string")
    unsupported = set(item) - {"$ref"} - REFERENCE_ANNOTATIONS
    if unsupported:
        raise ProfileViolation(
            location, f"reference siblings are not supported: {sorted(unsupported)}"
        )
    prefix = f"#/components/{expected_category}/"
    if not ref.startswith(prefix):
        raise ProfileViolation(location, f"must reference components/{expected_category}")
    if ref in seen:
        raise ProfileViolation(location, "recursive component references are not supported")
    return _dereference(
        document,
        _component(document, ref, location),
        location,
        expected_category,
        seen | {ref},
    )


def _validate_schema(
    document: Mapping[str, Any], value: object, location: str, stack: frozenset[str] = frozenset()
) -> None:
    schema = _mapping(value, location)
    ref = schema.get("$ref")
    if ref is not None:
        if not isinstance(ref, str):
            raise ProfileViolation(f"{location}.$ref", "must be a string")
        unsupported = set(schema) - {"$ref"} - REFERENCE_ANNOTATIONS
        if unsupported:
            raise ProfileViolation(
                location, f"reference siblings are not supported: {sorted(unsupported)}"
            )
        if not ref.startswith("#/components/schemas/"):
            raise ProfileViolation(
                location, "schema references must target local component schemas"
            )
        if ref in stack:
            raise ProfileViolation(location, "recursive schema references are not supported")
        target = _component(document, ref, location)
        _validate_schema(document, target, location, stack | {ref})
        return

    unsupported_composition = COMPOSITION_KEYS & set(schema)
    if unsupported_composition:
        raise ProfileViolation(
            location, f"schema composition is not supported: {sorted(unsupported_composition)}"
        )
    unsupported_keywords = UNSUPPORTED_SCHEMA_KEYS & set(schema)
    if unsupported_keywords:
        raise ProfileViolation(
            location, f"schema keywords are not supported: {sorted(unsupported_keywords)}"
        )
    if "anyOf" in schema:
        unsupported = set(schema) - {"anyOf"} - REFERENCE_ANNOTATIONS
        if unsupported:
            raise ProfileViolation(
                location, f"nullable anyOf siblings are not supported: {sorted(unsupported)}"
            )
        alternatives = _sequence(schema["anyOf"], f"{location}.anyOf")
        if len(alternatives) != 2:
            raise ProfileViolation(location, "anyOf is supported only for one schema plus null")
        null_count = sum(
            isinstance(part, Mapping) and part.get("type") == "null" for part in alternatives
        )
        if null_count != 1:
            raise ProfileViolation(location, "anyOf is supported only for one schema plus null")
        non_null = next(
            part
            for part in alternatives
            if not (isinstance(part, Mapping) and part.get("type") == "null")
        )
        _validate_schema(document, non_null, f"{location}.anyOf")
        return

    kind = schema.get("type")
    if not isinstance(kind, str) or kind not in SCHEMA_TYPES:
        raise ProfileViolation(location, f"must declare one supported type, got {kind!r}")

    if "enum" in schema:
        enum = _sequence(schema["enum"], f"{location}.enum")
        if not enum:
            raise ProfileViolation(f"{location}.enum", "must not be empty")
        if any(
            isinstance(item, (Mapping, Sequence)) and not isinstance(item, str) for item in enum
        ):
            raise ProfileViolation(f"{location}.enum", "values must be JSON scalars")

    if kind == "array":
        if "items" not in schema:
            raise ProfileViolation(location, "array schemas must declare items")
        _validate_schema(document, schema["items"], f"{location}.items", stack)
    elif kind == "object":
        properties = _mapping(schema.get("properties", {}), f"{location}.properties")
        required = _sequence(schema.get("required", []), f"{location}.required")
        if any(not isinstance(name, str) for name in required):
            raise ProfileViolation(f"{location}.required", "entries must be strings")
        missing = set(required) - set(properties)
        if missing:
            raise ProfileViolation(
                location, f"required properties are not declared: {sorted(missing)}"
            )
        for name, child in properties.items():
            _validate_schema(document, child, f"{location}.properties.{name}", stack)
        additional = schema.get("additionalProperties")
        if additional is not None and not isinstance(additional, bool):
            _validate_schema(document, additional, f"{location}.additionalProperties", stack)

    for key in CONSTRAINT_KEYS & set(schema):
        value = schema[key]
        if key == "pattern" and not isinstance(value, str):
            raise ProfileViolation(f"{location}.{key}", "must be a string")
        if key != "pattern" and (isinstance(value, bool) or not isinstance(value, (int, float))):
            raise ProfileViolation(f"{location}.{key}", "must be a number")


def _validate_parameter(document: Mapping[str, Any], value: object, location: str) -> None:
    parameter = _dereference(document, value, location, "parameters")
    name = parameter.get("name")
    if not isinstance(name, str) or not name:
        raise ProfileViolation(f"{location}.name", "must be a non-empty string")
    parameter_location = parameter.get("in")
    if parameter_location not in PARAMETER_LOCATIONS:
        raise ProfileViolation(f"{location}.in", "only path and query parameters are supported")
    if parameter_location == "path" and parameter.get("required") is not True:
        raise ProfileViolation(location, "path parameters must be required")
    if "schema" not in parameter:
        raise ProfileViolation(location, "parameters must declare a schema")
    _validate_schema(document, parameter["schema"], f"{location}.schema")


def _validate_server_and_auth(document: Mapping[str, Any]) -> None:
    servers = _sequence(document.get("servers"), "servers")
    if len(servers) != 1:
        raise ProfileViolation("servers", "exactly one global server is required")
    server = _mapping(servers[0], "servers[0]")
    if set(server) - {"description", "url"}:
        raise ProfileViolation("servers[0]", "server variables and extensions are not supported")
    url = server.get("url")
    if not isinstance(url, str) or "{" in url or "}" in url:
        raise ProfileViolation("servers[0].url", "must be a concrete HTTPS URL")
    parsed = urlsplit(url)
    if (
        parsed.scheme != "https"
        or not parsed.netloc
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        raise ProfileViolation("servers[0].url", "must be a concrete HTTPS URL")

    components = _mapping(document.get("components", {}), "components")
    schemes = _mapping(components.get("securitySchemes", {}), "components.securitySchemes")
    matching = [
        name
        for name, raw_scheme in schemes.items()
        if isinstance(raw_scheme, Mapping)
        and raw_scheme.get("type") == "apiKey"
        and raw_scheme.get("in") == "header"
        and str(raw_scheme.get("name", "")).lower() == "x-api-key"
    ]
    if len(matching) != 1:
        raise ProfileViolation(
            "components.securitySchemes", "exactly one x-api-key header scheme is required"
        )
    expected: list[dict[str, list[str]]] = [{matching[0]: []}]
    if document.get("security") != expected:
        raise ProfileViolation("security", "global x-api-key authentication is required")


def _json_schema(
    document: Mapping[str, Any],
    content: object,
    location: str,
    allowed_media_types: frozenset[str],
) -> None:
    media = _mapping(content, location)
    if len(media) != 1 or not set(media) <= allowed_media_types:
        supported = ", ".join(sorted(allowed_media_types))
        raise ProfileViolation(
            location, f"exactly one supported media type is required: {supported}"
        )
    media_type = next(iter(media))
    json_media = _mapping(media[media_type], f"{location}.{media_type}")
    if "schema" not in json_media:
        raise ProfileViolation(location, f"{media_type} content must declare a schema")
    _validate_schema(document, json_media["schema"], f"{location}.{media_type}.schema")


def _validate_request_body(document: Mapping[str, Any], value: object, location: str) -> None:
    body = _dereference(document, value, location, "requestBodies")
    _json_schema(
        document,
        body.get("content"),
        f"{location}.content",
        frozenset({"application/json"}),
    )


def _validate_response(document: Mapping[str, Any], value: object, location: str) -> None:
    response = _dereference(document, value, location, "responses")
    if not isinstance(response.get("description"), str):
        raise ProfileViolation(f"{location}.description", "must be a string")
    if "content" in response:
        _json_schema(
            document,
            response["content"],
            f"{location}.content",
            frozenset({"application/json", "application/problem+json"}),
        )
    if "links" in response:
        raise ProfileViolation(f"{location}.links", "response links are not supported")


def validate_profile(document: Mapping[str, Any]) -> None:
    """Reject constructs the normalized IR and Python generator do not promise to support."""

    if document.get("openapi") not in {"3.1.0", "3.1.1"}:
        raise ProfileViolation("openapi", "the profile requires OpenAPI 3.1")
    if "webhooks" in document:
        raise ProfileViolation("webhooks", "webhooks are not supported")
    if document.get("jsonSchemaDialect") is not None:
        raise ProfileViolation("jsonSchemaDialect", "custom JSON Schema dialects are not supported")
    info = _mapping(document.get("info"), "info")
    if not isinstance(info.get("title"), str) or not isinstance(info.get("version"), str):
        raise ProfileViolation("info", "title and version must be strings")
    _validate_server_and_auth(document)

    components = _mapping(document.get("components", {}), "components")
    schemas = _mapping(components.get("schemas", {}), "components.schemas")
    for name, schema in schemas.items():
        _validate_schema(document, schema, f"components.schemas.{name}")

    paths = _mapping(document.get("paths"), "paths")
    operation_ids: set[str] = set()
    for path, raw_path_item in paths.items():
        path_item = _mapping(raw_path_item, f"paths.{path}")
        for index, parameter in enumerate(path_item.get("parameters", [])):
            _validate_parameter(document, parameter, f"paths.{path}.parameters[{index}]")
        for method, raw_operation in path_item.items():
            if method == "parameters" or method.startswith("x-"):
                continue
            if method not in HTTP_METHODS:
                raise ProfileViolation(f"paths.{path}.{method}", "HTTP method is not supported")
            operation = _mapping(raw_operation, f"paths.{path}.{method}")
            if "servers" in operation or "servers" in path_item:
                raise ProfileViolation(
                    f"paths.{path}.{method}.servers", "server overrides are not supported"
                )
            if "security" in operation:
                raise ProfileViolation(
                    f"paths.{path}.{method}.security", "operation auth overrides are not supported"
                )
            if "callbacks" in operation:
                raise ProfileViolation(
                    f"paths.{path}.{method}.callbacks", "callbacks are not supported"
                )
            operation_id = operation.get("operationId")
            if not isinstance(operation_id, str) or not operation_id:
                raise ProfileViolation(f"paths.{path}.{method}.operationId", "is required")
            if operation_id in operation_ids:
                raise ProfileViolation(f"paths.{path}.{method}.operationId", "must be unique")
            operation_ids.add(operation_id)
            for index, parameter in enumerate(operation.get("parameters", [])):
                _validate_parameter(
                    document, parameter, f"paths.{path}.{method}.parameters[{index}]"
                )
            if "requestBody" in operation:
                _validate_request_body(
                    document, operation["requestBody"], f"paths.{path}.{method}.requestBody"
                )
            responses = _mapping(operation.get("responses"), f"paths.{path}.{method}.responses")
            if not responses:
                raise ProfileViolation(f"paths.{path}.{method}.responses", "must not be empty")
            for status, response in responses.items():
                _validate_response(document, response, f"paths.{path}.{method}.responses.{status}")
