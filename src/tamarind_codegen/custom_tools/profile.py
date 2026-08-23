"""Validation for the deliberately small Tamarind Custom Tools OpenAPI profile."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import ipaddress
import math
import re
from typing import Any
from urllib.parse import urlsplit

HTTP_METHODS = {"delete", "get", "patch", "post", "put"}
PARAMETER_LOCATIONS = {"header", "path", "query"}
SCHEMA_TYPES = {"array", "boolean", "integer", "null", "number", "object", "string"}
JSON_SCHEMA_DIALECTS = {
    "https://json-schema.org/draft/2020-12/schema",
    "https://spec.openapis.org/oas/3.1/dialect/base",
}
DOCUMENT_FIELDS = {
    "components",
    "info",
    "jsonSchemaDialect",
    "openapi",
    "paths",
    "security",
    "servers",
}
INFO_FIELDS = {"description", "summary", "title", "version"}
SERVER_FIELDS = {"description", "url"}
COMPONENT_FIELDS = {
    "parameters",
    "requestBodies",
    "responses",
    "schemas",
    "securitySchemes",
}
PATH_ITEM_FIELDS = HTTP_METHODS | {"description", "parameters", "summary"}
OPERATION_FIELDS = {
    "description",
    "operationId",
    "parameters",
    "requestBody",
    "responses",
    "summary",
    "tags",
    "x-doc-group",
    "x-tamarind-group",
}
PARAMETER_FIELDS = {
    "allowReserved",
    "description",
    "explode",
    "in",
    "name",
    "required",
    "schema",
    "style",
}
REQUEST_BODY_FIELDS = {"content", "description", "required"}
RESPONSE_FIELDS = {"content", "description"}
MEDIA_TYPE_FIELDS = {"schema"}
SECURITY_SCHEME_FIELDS = {"description", "in", "name", "type"}
COMPOSITION_KEYS = {"allOf", "not", "oneOf"}
CARDINALITY_CONSTRAINT_KEYS = {"maxItems", "maxLength", "minItems", "minLength"}
NUMERIC_BOUND_KEYS = {"maximum", "minimum"}
CONSTRAINT_KEYS = CARDINALITY_CONSTRAINT_KEYS | NUMERIC_BOUND_KEYS | {"pattern"}
SCHEMA_ANNOTATIONS = {"default", "description", "title"}
SCHEMA_COMMON_KEYS = SCHEMA_ANNOTATIONS | {"const", "enum", "type"}
SCHEMA_KEYS_BY_TYPE = {
    "array": {"items", "maxItems", "minItems"},
    "boolean": set(),
    "integer": {"maximum", "minimum"},
    "null": set(),
    "number": {"maximum", "minimum"},
    "object": {"additionalProperties", "properties", "required"},
    "string": {"maxLength", "minLength", "pattern"},
}
RESPONSE_STATUS_PATTERN = re.compile(r"[1-5](?:[0-9]{2}|XX)\Z")
HTTP_TOKEN_PATTERN = re.compile(r"[!#$%&'*+\-.^_`|~0-9A-Za-z]+\Z")
HOSTNAME_PATTERN = re.compile(
    r"(?=.{1,253}\Z)[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)*\Z"
)
URL_PATH_PATTERN = re.compile(r"(?:[A-Za-z0-9\-._~!$&'()*+,;=:@/]|%[0-9A-Fa-f]{2})*\Z")
BODYLESS_RESPONSE_STATUSES = {"204", "205", "304"}


class ProfileViolation(ValueError):
    """An OpenAPI document uses behavior outside the supported profile."""

    def __init__(self, location: str, message: str) -> None:
        super().__init__(f"{location}: {message}")
        self.location = location
        self.message = message


def _reject_unsupported_fields(
    value: Mapping[str, Any], allowed: set[str], location: str, object_name: str
) -> None:
    unsupported = set(value) - allowed
    if unsupported:
        raise ProfileViolation(
            location, f"{object_name} fields are not supported: {sorted(unsupported)}"
        )


def _mapping(value: object, location: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ProfileViolation(location, "must be an object")
    return value


def _sequence(value: object, location: str) -> Sequence[Any]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise ProfileViolation(location, "must be an array")
    return value


def _value_matches_type(value: object, kind: str) -> bool:
    if kind == "null":
        return value is None
    if kind == "boolean":
        return isinstance(value, bool)
    if kind == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if kind == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if kind == "string":
        return isinstance(value, str)
    if kind == "array":
        return isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray))
    if kind == "object":
        return isinstance(value, Mapping)
    return False


def _validate_default(value: Mapping[str, Any], kind: str, nullable: bool, location: str) -> None:
    if "default" not in value:
        return
    default = value["default"]
    if default is None and nullable:
        return
    if not _value_matches_type(default, kind):
        raise ProfileViolation(f"{location}.default", "must match the declared type")


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
    unsupported = set(item) - {"$ref"}
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
    document: Mapping[str, Any],
    value: object,
    location: str,
    stack: frozenset[str] = frozenset(),
    *,
    named: bool = False,
) -> None:
    schema = _mapping(value, location)
    ref = schema.get("$ref")
    if ref is not None:
        if not isinstance(ref, str):
            raise ProfileViolation(f"{location}.$ref", "must be a string")
        unsupported = set(schema) - {"$ref", "default", "description"}
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
        _validate_schema(document, target, location, stack | {ref}, named=True)
        resolved_kind, resolved_nullable = _schema_shape(document, target, location)
        _validate_default(schema, resolved_kind, resolved_nullable, location)
        return

    unsupported_composition = COMPOSITION_KEYS & set(schema)
    if unsupported_composition:
        raise ProfileViolation(
            location, f"schema composition is not supported: {sorted(unsupported_composition)}"
        )
    if "anyOf" in schema:
        unsupported = set(schema) - {"anyOf"} - SCHEMA_ANNOTATIONS
        if unsupported:
            raise ProfileViolation(
                location, f"nullable anyOf siblings are not supported: {sorted(unsupported)}"
            )
        alternatives = _sequence(schema["anyOf"], f"{location}.anyOf")
        if len(alternatives) != 2:
            raise ProfileViolation(location, "anyOf is supported only for one schema plus null")
        null_branches = [
            part
            for part in alternatives
            if isinstance(part, Mapping) and part.get("type") == "null"
        ]
        if len(null_branches) != 1:
            raise ProfileViolation(location, "anyOf is supported only for one schema plus null")
        if dict(null_branches[0]) != {"type": "null"}:
            raise ProfileViolation(location, "the nullable branch must be exactly {'type': 'null'}")
        non_null = next(
            part
            for part in alternatives
            if not (isinstance(part, Mapping) and part.get("type") == "null")
        )
        _validate_schema(document, non_null, f"{location}.anyOf", stack, named=named)
        nullable_kind, _ = _schema_shape(document, non_null, f"{location}.anyOf")
        if named and nullable_kind == "object":
            raise ProfileViolation(location, "named object schemas cannot be nullable")
        _validate_default(schema, nullable_kind, True, location)
        return

    kind = schema.get("type")
    if not isinstance(kind, str) or kind not in SCHEMA_TYPES:
        raise ProfileViolation(location, f"must declare one supported type, got {kind!r}")
    unsupported = set(schema) - SCHEMA_COMMON_KEYS - SCHEMA_KEYS_BY_TYPE[kind]
    if unsupported:
        raise ProfileViolation(
            location, f"schema keywords are not supported: {sorted(unsupported)}"
        )

    if "enum" in schema:
        enum = _sequence(schema["enum"], f"{location}.enum")
        if not enum:
            raise ProfileViolation(f"{location}.enum", "must not be empty")
        if any(
            isinstance(item, (Mapping, Sequence)) and not isinstance(item, str) for item in enum
        ):
            raise ProfileViolation(f"{location}.enum", "values must be JSON scalars")
        if any(not _value_matches_type(item, kind) for item in enum):
            raise ProfileViolation(f"{location}.enum", "values must match the declared type")
        if kind == "number":
            raise ProfileViolation(
                f"{location}.enum",
                "number enums cannot be represented faithfully as Python Literal types",
            )
    if "enum" in schema and "const" in schema:
        raise ProfileViolation(location, "schemas cannot combine enum and const")
    if "const" in schema:
        const = schema["const"]
        if isinstance(const, (Mapping, Sequence)) and not isinstance(const, str):
            raise ProfileViolation(f"{location}.const", "must be a JSON scalar")
        if not _value_matches_type(const, kind):
            raise ProfileViolation(f"{location}.const", "must match the declared type")
        if kind == "number":
            raise ProfileViolation(
                f"{location}.const",
                "number consts cannot be represented faithfully as Python Literal types",
            )
    _validate_default(schema, kind, False, location)

    if kind == "array":
        if "items" not in schema:
            raise ProfileViolation(location, "array schemas must declare items")
        _validate_schema(document, schema["items"], f"{location}.items", stack)
    elif kind == "object":
        properties = _mapping(schema.get("properties", {}), f"{location}.properties")
        if properties and not named:
            raise ProfileViolation(location, "structured object schemas must be named components")
        required = _sequence(schema.get("required", []), f"{location}.required")
        if any(not isinstance(name, str) for name in required):
            raise ProfileViolation(f"{location}.required", "entries must be strings")
        if len(required) != len(set(required)):
            raise ProfileViolation(f"{location}.required", "entries must be unique")
        missing = set(required) - set(properties)
        if missing:
            raise ProfileViolation(
                location, f"required properties are not declared: {sorted(missing)}"
            )
        for name, child in properties.items():
            _validate_schema(document, child, f"{location}.properties.{name}", stack)
        has_additional = "additionalProperties" in schema
        additional = schema.get("additionalProperties")
        if has_additional and not isinstance(additional, (bool, Mapping)):
            raise ProfileViolation(
                f"{location}.additionalProperties",
                "must be a boolean or schema object",
            )
        if properties and additional is not False:
            raise ProfileViolation(
                location,
                "object schemas with properties must set additionalProperties to false",
            )
        if not properties and additional is False:
            raise ProfileViolation(location, "closed empty object schemas are not supported")
        if isinstance(additional, Mapping):
            _validate_schema(document, additional, f"{location}.additionalProperties", stack)

    for key in CONSTRAINT_KEYS & set(schema):
        value = schema[key]
        if key == "pattern":
            if not isinstance(value, str):
                raise ProfileViolation(f"{location}.{key}", "must be a string")
            try:
                re.compile(value)
            except re.error as exc:
                raise ProfileViolation(
                    f"{location}.{key}", "must be a valid Python regular expression"
                ) from exc
        if key in CARDINALITY_CONSTRAINT_KEYS and (
            isinstance(value, bool) or not isinstance(value, int) or value < 0
        ):
            raise ProfileViolation(f"{location}.{key}", "must be a non-negative integer")
        if key in NUMERIC_BOUND_KEYS and (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
        ):
            raise ProfileViolation(f"{location}.{key}", "must be a finite number")


def _schema_shape(document: Mapping[str, Any], value: object, location: str) -> tuple[str, bool]:
    schema = _mapping(value, location)
    ref = schema.get("$ref")
    if isinstance(ref, str):
        return _schema_shape(document, _component(document, ref, location), location)
    if "anyOf" in schema:
        alternatives = _sequence(schema["anyOf"], f"{location}.anyOf")
        non_null = next(
            part
            for part in alternatives
            if not (isinstance(part, Mapping) and part.get("type") == "null")
        )
        kind, _ = _schema_shape(document, non_null, location)
        return kind, True
    return str(schema["type"]), False


def _validate_parameter(
    document: Mapping[str, Any], value: object, location: str
) -> tuple[str, str]:
    parameter = _dereference(document, value, location, "parameters")
    _reject_unsupported_fields(parameter, PARAMETER_FIELDS, location, "parameter")
    name = parameter.get("name")
    if not isinstance(name, str) or not name:
        raise ProfileViolation(f"{location}.name", "must be a non-empty string")
    parameter_location = parameter.get("in")
    if parameter_location not in PARAMETER_LOCATIONS:
        raise ProfileViolation(
            f"{location}.in", "only header, path and query parameters are supported"
        )
    if "required" in parameter and not isinstance(parameter["required"], bool):
        raise ProfileViolation(f"{location}.required", "must be a boolean")
    if parameter_location == "path" and parameter.get("required") is not True:
        raise ProfileViolation(location, "path parameters must be required")
    if "schema" not in parameter:
        raise ProfileViolation(location, "parameters must declare a schema")
    expected_style = "form" if parameter_location == "query" else "simple"
    expected_explode = parameter_location == "query"
    if parameter.get("style", expected_style) != expected_style:
        raise ProfileViolation(location, "non-default parameter style is not supported")
    if parameter.get("explode", expected_explode) is not expected_explode:
        raise ProfileViolation(location, "non-default parameter explode is not supported")
    if parameter.get("allowReserved", False) is not False:
        raise ProfileViolation(location, "allowReserved parameters are not supported")
    _validate_schema(document, parameter["schema"], f"{location}.schema")
    kind, nullable = _schema_shape(document, parameter["schema"], f"{location}.schema")
    if kind not in {"boolean", "integer", "number", "string"}:
        raise ProfileViolation(location, "parameters must use scalar schemas")
    if nullable and (parameter_location != "query" or parameter.get("required") is True):
        raise ProfileViolation(location, "required parameters cannot be nullable")
    if parameter_location == "path" and kind != "string":
        raise ProfileViolation(location, "path parameters must use string schemas")
    if parameter_location == "header" and kind != "string":
        raise ProfileViolation(location, "header parameters must use string schemas")
    if parameter_location == "header" and HTTP_TOKEN_PATTERN.fullmatch(name) is None:
        raise ProfileViolation(f"{location}.name", "must be a valid HTTP header name")
    if parameter_location == "header" and name.casefold() == "x-api-key":
        raise ProfileViolation(location, "x-api-key is owned by the authenticated transport")
    return name, parameter_location


def _validate_parameter_list(
    document: Mapping[str, Any], value: object, location: str
) -> set[tuple[str, str]]:
    parameters = _sequence(value, location)
    identities: set[tuple[str, str]] = set()
    for index, parameter in enumerate(parameters):
        identity = _validate_parameter(document, parameter, f"{location}[{index}]")
        if identity in identities:
            raise ProfileViolation(f"{location}[{index}]", "duplicate parameter")
        identities.add(identity)
    return identities


def _validate_server_and_auth(document: Mapping[str, Any]) -> None:
    servers = _sequence(document.get("servers"), "servers")
    if len(servers) != 1:
        raise ProfileViolation("servers", "exactly one global server is required")
    server = _mapping(servers[0], "servers[0]")
    _reject_unsupported_fields(server, SERVER_FIELDS, "servers[0]", "server")
    url = server.get("url")
    if (
        not isinstance(url, str)
        or "{" in url
        or "}" in url
        or any(
            character.isspace() or ord(character) < 0x20 or ord(character) == 0x7F
            for character in url
        )
    ):
        raise ProfileViolation("servers[0].url", "must be a concrete HTTPS URL")
    try:
        parsed = urlsplit(url)
        hostname = parsed.hostname
        parsed.port
    except ValueError as exc:
        raise ProfileViolation("servers[0].url", "must be a concrete HTTPS URL") from exc
    valid_hostname = False
    if hostname:
        try:
            ipaddress.ip_address(hostname)
            valid_hostname = True
        except ValueError:
            valid_hostname = HOSTNAME_PATTERN.fullmatch(hostname) is not None
    if (
        parsed.scheme != "https"
        or not parsed.netloc
        or not valid_hostname
        or parsed.username is not None
        or parsed.password is not None
        or URL_PATH_PATTERN.fullmatch(parsed.path) is None
        or parsed.query
        or parsed.fragment
    ):
        raise ProfileViolation("servers[0].url", "must be a concrete HTTPS URL")

    components = _mapping(document.get("components", {}), "components")
    schemes = _mapping(components.get("securitySchemes", {}), "components.securitySchemes")
    for name, raw_scheme in schemes.items():
        scheme = _mapping(raw_scheme, f"components.securitySchemes.{name}")
        _reject_unsupported_fields(
            scheme,
            SECURITY_SCHEME_FIELDS,
            f"components.securitySchemes.{name}",
            "security scheme",
        )
    matching = [
        name
        for name, raw_scheme in schemes.items()
        if isinstance(raw_scheme, Mapping)
        and raw_scheme.get("type") == "apiKey"
        and raw_scheme.get("in") == "header"
        and str(raw_scheme.get("name", "")).lower() == "x-api-key"
    ]
    if len(schemes) != 1 or len(matching) != 1:
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
    _reject_unsupported_fields(
        json_media, MEDIA_TYPE_FIELDS, f"{location}.{media_type}", "media type"
    )
    if "schema" not in json_media:
        raise ProfileViolation(location, f"{media_type} content must declare a schema")
    _validate_schema(document, json_media["schema"], f"{location}.{media_type}.schema")


def _validate_request_body(document: Mapping[str, Any], value: object, location: str) -> None:
    body = _dereference(document, value, location, "requestBodies")
    _reject_unsupported_fields(body, REQUEST_BODY_FIELDS, location, "request body")
    if "required" in body and not isinstance(body["required"], bool):
        raise ProfileViolation(f"{location}.required", "must be a boolean")
    _json_schema(
        document,
        body.get("content"),
        f"{location}.content",
        frozenset({"application/json"}),
    )
    schema = body["content"]["application/json"]["schema"]
    kind, nullable = _schema_shape(document, schema, f"{location}.content.schema")
    if nullable or kind == "null":
        raise ProfileViolation(location, "request bodies must use non-null schemas")


def _validate_response(
    document: Mapping[str, Any],
    value: object,
    location: str,
    *,
    status: str | None = None,
) -> None:
    response = _dereference(document, value, location, "responses")
    _reject_unsupported_fields(response, RESPONSE_FIELDS, location, "response")
    if not isinstance(response.get("description"), str):
        raise ProfileViolation(f"{location}.description", "must be a string")
    if "content" in response:
        content = _mapping(response["content"], f"{location}.content")
        if content:
            if status in BODYLESS_RESPONSE_STATUSES:
                raise ProfileViolation(
                    location, f"HTTP {status} responses must not declare content"
                )
            if status == "2XX":
                raise ProfileViolation(
                    location,
                    "2XX wildcard responses must not declare content because the range includes bodyless statuses",
                )
            _json_schema(
                document,
                content,
                f"{location}.content",
                frozenset({"application/json", "application/problem+json"}),
            )


def validate_profile(document: Mapping[str, Any]) -> None:
    """Reject constructs the normalized IR and Python generator do not promise to support."""

    _reject_unsupported_fields(document, DOCUMENT_FIELDS, "document", "document")
    if document.get("openapi") not in {"3.1.0", "3.1.1"}:
        raise ProfileViolation("openapi", "the profile requires OpenAPI 3.1")
    dialect = document.get("jsonSchemaDialect")
    if dialect is not None and (
        not isinstance(dialect, str) or dialect not in JSON_SCHEMA_DIALECTS
    ):
        raise ProfileViolation(
            "jsonSchemaDialect", "only the standard OpenAPI and JSON Schema dialects are supported"
        )
    info = _mapping(document.get("info"), "info")
    _reject_unsupported_fields(info, INFO_FIELDS, "info", "info")
    if not isinstance(info.get("title"), str) or not isinstance(info.get("version"), str):
        raise ProfileViolation("info", "title and version must be strings")

    components = _mapping(document.get("components", {}), "components")
    _reject_unsupported_fields(components, COMPONENT_FIELDS, "components", "components")
    _validate_server_and_auth(document)
    schemas = _mapping(components.get("schemas", {}), "components.schemas")
    for name, schema in schemas.items():
        _validate_schema(document, schema, f"components.schemas.{name}", named=True)
    parameters = _mapping(components.get("parameters", {}), "components.parameters")
    for name, parameter in parameters.items():
        _validate_parameter(document, parameter, f"components.parameters.{name}")
    request_bodies = _mapping(components.get("requestBodies", {}), "components.requestBodies")
    for name, request_body in request_bodies.items():
        _validate_request_body(document, request_body, f"components.requestBodies.{name}")
    component_responses = _mapping(components.get("responses", {}), "components.responses")
    for name, response in component_responses.items():
        _validate_response(document, response, f"components.responses.{name}")

    paths = _mapping(document.get("paths"), "paths")
    operation_ids: set[str] = set()
    for path, raw_path_item in paths.items():
        if not isinstance(path, str) or not path.startswith("/"):
            raise ProfileViolation(f"paths.{path}", "path keys must start with '/'")
        if (
            "?" in path
            or "#" in path
            or any(ord(character) <= 0x20 or ord(character) == 0x7F for character in path)
        ):
            raise ProfileViolation(
                f"paths.{path}",
                "path keys must not contain query, fragment, whitespace, or control characters",
            )
        if re.fullmatch(r"(?:[^{}]|\{[^{}]+\})*", path) is None:
            raise ProfileViolation(
                f"paths.{path}",
                "path keys must use balanced, nonempty template expressions",
            )
        path_item = _mapping(raw_path_item, f"paths.{path}")
        _reject_unsupported_fields(path_item, PATH_ITEM_FIELDS, f"paths.{path}", "path item")
        path_parameter_identities = _validate_parameter_list(
            document, path_item.get("parameters", []), f"paths.{path}.parameters"
        )
        for method, raw_operation in path_item.items():
            if method in {"description", "parameters", "summary"}:
                continue
            operation = _mapping(raw_operation, f"paths.{path}.{method}")
            _reject_unsupported_fields(
                operation, OPERATION_FIELDS, f"paths.{path}.{method}", "operation"
            )
            operation_id = operation.get("operationId")
            if not isinstance(operation_id, str) or not operation_id:
                raise ProfileViolation(f"paths.{path}.{method}.operationId", "is required")
            if operation_id in operation_ids:
                raise ProfileViolation(f"paths.{path}.{method}.operationId", "must be unique")
            operation_ids.add(operation_id)
            tags = _sequence(operation.get("tags", []), f"paths.{path}.{method}.tags")
            if any(not isinstance(tag, str) for tag in tags):
                raise ProfileViolation(f"paths.{path}.{method}.tags", "entries must be strings")
            operation_parameter_identities = _validate_parameter_list(
                document,
                operation.get("parameters", []),
                f"paths.{path}.{method}.parameters",
            )
            effective_parameter_identities = (
                path_parameter_identities | operation_parameter_identities
            )
            path_parameter_names = {
                name for name, location in effective_parameter_identities if location == "path"
            }
            template_parameter_names = set(re.findall(r"\{([^{}]+)\}", path))
            if path_parameter_names != template_parameter_names:
                raise ProfileViolation(
                    f"paths.{path}.{method}.parameters",
                    "path parameters must exactly match the path template",
                )
            if "requestBody" in operation:
                _validate_request_body(
                    document, operation["requestBody"], f"paths.{path}.{method}.requestBody"
                )
            responses = _mapping(operation.get("responses"), f"paths.{path}.{method}.responses")
            if not responses:
                raise ProfileViolation(f"paths.{path}.{method}.responses", "must not be empty")
            for status, response in responses.items():
                if not isinstance(status, str) or (
                    status != "default" and RESPONSE_STATUS_PATTERN.fullmatch(status) is None
                ):
                    raise ProfileViolation(
                        f"paths.{path}.{method}.responses.{status}",
                        "must be default, a three-digit HTTP status, or an nXX range",
                    )
                _validate_response(
                    document,
                    response,
                    f"paths.{path}.{method}.responses.{status}",
                    status=status,
                )
            successful = [status for status in responses if status.startswith("2")]
            if len(successful) != 1:
                raise ProfileViolation(
                    f"paths.{path}.{method}.responses",
                    "exactly one successful response is required",
                )
