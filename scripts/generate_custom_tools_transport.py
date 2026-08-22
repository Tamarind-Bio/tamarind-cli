"""Generate Custom Tools wire types and HTTP methods from OpenAPI."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import keyword
from pathlib import Path
import re
from typing import Any
from urllib.parse import urlsplit


HTTP_METHODS = ("get", "post", "put", "patch", "delete")
ASYNC_METHODS = frozenset({"get_custom_tool_version", "list_custom_tool_build_logs"})
PUBLIC_PROPERTY_ALIASES = (
    (
        ("PublicCustomTool", "PublicCreateCustomToolRequest", "PublicUpdateCustomToolRequest"),
        "gpuType",
        "GpuType",
    ),
    (
        ("PublicCustomTool", "PublicCreateCustomToolRequest", "PublicUpdateCustomToolRequest"),
        "memory",
        "MemorySize",
    ),
)
SUPPORTED_API_KEY_HEADER = "x-api-key"
GENERATED_MODULE_NAMES = frozenset(
    {
        "Any",
        "GeneratedCustomToolsTransport",
        "HTTPClient",
        "Literal",
        "NotRequired",
        "OPENAPI_SERVER_URL",
        "OPENAPI_SHA256",
        "Protocol",
        "TypeAlias",
        "TypedDict",
        "_segment",
        "cast",
        "overload",
    }
)
REFERENCE_ANNOTATION_SIBLINGS = frozenset(
    {
        "title",
        "description",
        "default",
        "examples",
        "deprecated",
        "readOnly",
        "writeOnly",
        "$comment",
    }
)


def _validate_server_contract(spec: dict[str, Any]) -> str:
    servers = spec.get("servers")
    if not isinstance(servers, list) or len(servers) != 1 or not isinstance(servers[0], dict):
        raise ValueError("Exactly one global OpenAPI server is required")
    server = servers[0]
    if set(server) - {"url", "description"}:
        raise ValueError("OpenAPI server variables and extensions are outside the SDK profile")
    url = server.get("url")
    if not isinstance(url, str) or "{" in url or "}" in url:
        raise ValueError("A concrete global OpenAPI server URL is required")
    parsed = urlsplit(url)
    if (
        parsed.scheme != "https"
        or not parsed.netloc
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("The global OpenAPI server URL is outside the SDK profile")
    return url.rstrip("/") + "/"


def _validate_auth_contract(spec: dict[str, Any]) -> None:
    if not str(spec.get("openapi", "")).startswith("3.1."):
        raise ValueError("Only OpenAPI 3.1 documents are supported")
    if spec.get("jsonSchemaDialect") is not None:
        raise ValueError("Custom JSON Schema dialects are outside the generated SDK profile")
    schemes = spec.get("components", {}).get("securitySchemes", {})
    supported = {
        name
        for name, scheme in schemes.items()
        if isinstance(scheme, dict)
        and scheme.get("type") == "apiKey"
        and scheme.get("in") == "header"
        and str(scheme.get("name", "")).lower() == SUPPORTED_API_KEY_HEADER
    }
    if len(supported) != 1:
        raise ValueError("Exactly one x-api-key authentication scheme is required")
    supported_requirement = {next(iter(supported)): []}
    global_security = spec.get("security", [])
    for path_item in spec.get("paths", {}).values():
        if "servers" in path_item:
            raise ValueError("Path-level servers are outside the SDK profile")
        for method in HTTP_METHODS:
            operation = path_item.get(method)
            if not isinstance(operation, dict):
                continue
            if "servers" in operation:
                raise ValueError(
                    f"{operation.get('operationId')} has operation-level servers outside the SDK profile"
                )
            requirements = operation.get("security", global_security)
            if not isinstance(requirements, list) or not requirements:
                raise ValueError(f"{operation.get('operationId')} has unsupported authentication")
            if any(
                not isinstance(requirement, dict) or requirement != supported_requirement
                for requirement in requirements
            ):
                raise ValueError(f"{operation.get('operationId')} has unsupported authentication")


def _name(value: str) -> str:
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", value)
    return re.sub(r"[^a-zA-Z0-9]+", "_", value).strip("_").lower()


def _validated_python_name(value: object, *, label: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{label} is outside the generated SDK profile: {value}")
    name = _name(value)
    if not name.isidentifier() or keyword.iskeyword(name):
        raise ValueError(f"{label} is outside the generated SDK profile: {value}")
    return name


def _annotation(schema: dict[str, Any]) -> str:
    if "allOf" in schema:
        raise ValueError("allOf schemas are outside the generated SDK profile")
    if "prefixItems" in schema:
        raise ValueError("prefixItems schemas are outside the generated SDK profile")
    if "$ref" in schema:
        ref = schema["$ref"]
        if not isinstance(ref, str) or not ref.startswith("#/components/schemas/"):
            raise ValueError(
                f"External schema references are outside the generated SDK profile: {ref}"
            )
        unsupported_siblings = set(schema) - {"$ref"} - REFERENCE_ANNOTATION_SIBLINGS
        if unsupported_siblings:
            raise ValueError(
                "Schema reference siblings are outside the generated SDK profile: "
                f"{sorted(unsupported_siblings)}"
            )
        return ref.rsplit("/", 1)[-1]
    if "anyOf" in schema:
        unsupported_siblings = set(schema) - {"anyOf"} - REFERENCE_ANNOTATION_SIBLINGS
        if unsupported_siblings:
            raise ValueError(
                "anyOf schema siblings are outside the generated SDK profile: "
                f"{sorted(unsupported_siblings)}"
            )
        parts = [_annotation(part) for part in schema["anyOf"]]
        return " | ".join(dict.fromkeys(parts))
    if "oneOf" in schema:
        unsupported_siblings = set(schema) - {"oneOf"} - REFERENCE_ANNOTATION_SIBLINGS
        if unsupported_siblings:
            raise ValueError(
                "oneOf schema siblings are outside the generated SDK profile: "
                f"{sorted(unsupported_siblings)}"
            )
        return " | ".join(dict.fromkeys(_annotation(part) for part in schema["oneOf"]))
    kind = schema.get("type")
    admitted_kinds = (
        set(kind) if isinstance(kind, list) else {kind} if isinstance(kind, str) else set()
    )

    def admitted(value: object) -> bool:
        if not admitted_kinds:
            return True
        if value is None:
            return "null" in admitted_kinds
        if isinstance(value, bool):
            return "boolean" in admitted_kinds
        if isinstance(value, int):
            return "integer" in admitted_kinds or "number" in admitted_kinds
        if isinstance(value, float):
            return "number" in admitted_kinds
        if isinstance(value, str):
            return "string" in admitted_kinds
        if isinstance(value, list):
            return "array" in admitted_kinds
        if isinstance(value, dict):
            return "object" in admitted_kinds
        return False

    if "const" in schema:
        if not admitted(schema["const"]):
            raise ValueError("Const value conflicts with its declared schema type")
        return f"Literal[{schema['const']!r}]"
    if "enum" in schema:
        if not isinstance(schema["enum"], list) or any(
            not admitted(value) for value in schema["enum"]
        ):
            raise ValueError("Enum values conflict with their declared schema type")
        return "Literal[" + ", ".join(repr(value) for value in schema["enum"]) + "]"
    if isinstance(kind, list):
        siblings = {key: value for key, value in schema.items() if key != "type"}
        return " | ".join(dict.fromkeys(_annotation({**siblings, "type": item}) for item in kind))
    if kind == "null":
        return "None"
    if kind == "string":
        return "str"
    if kind == "integer":
        return "int"
    if kind == "number":
        return "float"
    if kind == "boolean":
        return "bool"
    if kind == "array":
        items = schema.get("items")
        if not isinstance(items, dict):
            raise ValueError("Array schemas without items are outside the generated SDK profile")
        return f"list[{_annotation(items)}]"
    if kind == "object":
        if schema.get("properties") or schema.get("additionalProperties") is False:
            raise ValueError("inline object schemas are outside the generated SDK profile")
        additional = schema.get("additionalProperties")
        return (
            f"dict[str, {_annotation(additional)}]"
            if isinstance(additional, dict)
            else "dict[str, Any]"
        )
    raise ValueError("Unconstrained schemas are outside the generated SDK profile")


def _parameter_annotation(schema: dict[str, Any]) -> str:
    """Use None only as the SDK's omission marker for optional parameters."""
    if isinstance(schema.get("type"), list):
        kinds = [kind for kind in schema["type"] if kind != "null"]
        siblings = {key: value for key, value in schema.items() if key != "type"}
        return " | ".join(dict.fromkeys(_annotation({**siblings, "type": kind}) for kind in kinds))
    if isinstance(schema.get("enum"), list) and None in schema["enum"]:
        values = [value for value in schema["enum"] if value is not None]
        return _annotation({"enum": values})
    alternatives = schema.get("anyOf", schema.get("oneOf"))
    if isinstance(alternatives, list):
        retained = [
            alternative
            for alternative in alternatives
            if not isinstance(alternative, dict) or alternative.get("type") != "null"
        ]
        return " | ".join(
            dict.fromkeys(_parameter_annotation(alternative) for alternative in retained)
        )
    return _annotation(schema)


def _response_type(operation: dict[str, Any], components: dict[str, Any]) -> tuple[str, bool]:
    successes = [
        value for code, value in operation.get("responses", {}).items() if str(code).startswith("2")
    ]
    if len(successes) != 1:
        raise ValueError(
            f"{operation.get('operationId')} must declare exactly one successful response"
        )
    success = _resolve_component(successes[0], "responses", components)
    if success.get("headers"):
        raise ValueError(f"{operation.get('operationId')} has unsupported success headers")
    content = success.get("content", {})
    if not isinstance(content, dict) or set(content) - {"application/json"}:
        raise ValueError(f"{operation.get('operationId')} has unsupported success content")
    json_content = content.get("application/json")
    if not isinstance(json_content, dict):
        return "None", False
    schema = json_content.get("schema")
    if not isinstance(schema, dict):
        raise ValueError(f"{operation.get('operationId')} has no JSON success schema")
    return _annotation(schema), True


def _validate_error_contract(
    operation: dict[str, Any],
    response_components: dict[str, Any],
    schemas: dict[str, Any],
) -> None:
    """Every generated operation uses HTTPClient's RFC problem mapper."""
    for code, unresolved in operation.get("responses", {}).items():
        if str(code).startswith("2"):
            continue
        if not isinstance(unresolved, dict):
            raise ValueError(f"{operation.get('operationId')} has an invalid error response")
        response = _resolve_component(unresolved, "responses", response_components)
        content = response.get("content")
        if not isinstance(content, dict) or set(content) != {"application/problem+json"}:
            raise ValueError(
                f"{operation.get('operationId')} has an unsupported error response contract"
            )
        media = content["application/problem+json"]
        schema = media.get("schema") if isinstance(media, dict) else None
        if not isinstance(schema, dict):
            raise ValueError(
                f"{operation.get('operationId')} has an unsupported error response contract"
            )
        problem = _resolve_schema(schema, schemas)
        required = set(problem.get("required", []))
        properties = problem.get("properties", {})
        code_schema = properties.get("code") if isinstance(properties, dict) else None
        if (
            problem.get("type") != "object"
            or not {"type", "title", "status", "code"}.issubset(required)
            or not isinstance(properties, dict)
            or not isinstance(code_schema, dict)
            or code_schema.get("type") != "string"
        ):
            raise ValueError(
                f"{operation.get('operationId')} has an unsupported error response contract"
            )


def _body_type(operation: dict[str, Any], components: dict[str, Any]) -> tuple[str, bool] | None:
    request_body = operation.get("requestBody", {})
    if not isinstance(request_body, dict) or not request_body:
        return None
    request_body = _resolve_component(request_body, "requestBodies", components)
    content = request_body.get("content")
    if not isinstance(content, dict) or set(content) != {"application/json"}:
        raise ValueError(f"{operation.get('operationId')} has unsupported request content")
    media = content["application/json"]
    schema = media.get("schema") if isinstance(media, dict) else None
    if not isinstance(schema, dict):
        raise ValueError(f"{operation.get('operationId')} has no JSON request schema")
    return _annotation(schema), request_body.get("required") is True


def _resolve_schema(
    schema: dict[str, Any], schemas: dict[str, Any], seen: frozenset[str] = frozenset()
) -> dict[str, Any]:
    ref = schema.get("$ref")
    if not isinstance(ref, str):
        return schema
    prefix = "#/components/schemas/"
    if not ref.startswith(prefix) or ref in seen:
        raise ValueError(f"Unsupported or cyclic schema reference: {ref}")
    target = schemas.get(ref[len(prefix) :])
    if not isinstance(target, dict):
        raise ValueError(f"Unresolved schema reference: {ref}")
    resolved = _resolve_schema(target, schemas, seen | {ref})
    return {**resolved, **{key: value for key, value in schema.items() if key != "$ref"}}


def _is_nullable(schema: dict[str, Any], schemas: dict[str, Any]) -> bool:
    schema = _resolve_schema(schema, schemas)
    kind = schema.get("type")
    if kind == "null" or isinstance(kind, list) and "null" in kind:
        return True
    if "const" in schema and schema["const"] is None:
        return True
    enum = schema.get("enum")
    if isinstance(enum, list) and None in enum:
        return True
    alternatives = schema.get("anyOf", schema.get("oneOf", []))
    return isinstance(alternatives, list) and any(
        isinstance(alternative, dict) and _is_nullable(alternative, schemas)
        for alternative in alternatives
    )


def _is_structured(schema: dict[str, Any], schemas: dict[str, Any]) -> bool:
    schema = _resolve_schema(schema, schemas)
    kind = schema.get("type")
    if (
        kind in {"array", "object"}
        if isinstance(kind, str)
        else bool(isinstance(kind, list) and {"array", "object"}.intersection(kind))
    ):
        return True
    alternatives = schema.get("anyOf", schema.get("oneOf", []))
    return isinstance(alternatives, list) and any(
        isinstance(alternative, dict) and _is_structured(alternative, schemas)
        for alternative in alternatives
    )


def _has_only_string_values(schema: dict[str, Any], schemas: dict[str, Any]) -> bool:
    """Whether every non-null value admitted by a scalar schema is a string."""
    schema = _resolve_schema(schema, schemas)
    if schema.get("type") == "null" or schema.get("const") is None and "const" in schema:
        return True
    if "const" in schema:
        return isinstance(schema["const"], str)
    enum = schema.get("enum")
    if isinstance(enum, list):
        return all(value is None or isinstance(value, str) for value in enum)
    kind = schema.get("type")
    if isinstance(kind, list):
        return all(item in {"string", "null"} for item in kind)
    alternatives = schema.get("anyOf", schema.get("oneOf"))
    if isinstance(alternatives, list):
        return all(
            isinstance(alternative, dict) and _has_only_string_values(alternative, schemas)
            for alternative in alternatives
        )
    return kind == "string"


def _validate_parameter_profile(parameter: dict[str, Any], schemas: dict[str, Any]) -> None:
    location = parameter.get("in")
    schema = parameter.get("schema")
    if location not in {"path", "query", "header"} or not isinstance(schema, dict):
        raise ValueError(f"Unsupported parameter: {parameter.get('name')}")
    if _is_nullable(schema, schemas):
        raise ValueError(
            f"Nullable wire parameter is outside the SDK profile: {parameter.get('name')}"
        )
    if _is_structured(schema, schemas):
        raise ValueError(
            f"Structured {location} parameter is outside the SDK profile: {parameter.get('name')}"
        )
    if location in {"path", "header"} and not _has_only_string_values(schema, schemas):
        raise ValueError(
            f"Non-string {location} parameter is outside the SDK profile: {parameter.get('name')}"
        )
    if location == "query" and parameter.get("style", "form") != "form":
        raise ValueError(f"Unsupported query parameter style: {parameter.get('name')}")
    if location == "query" and parameter.get("allowReserved") is True:
        raise ValueError(f"Unsupported allowReserved query parameter: {parameter.get('name')}")
    if location == "path" and parameter.get("style", "simple") != "simple":
        raise ValueError(f"Unsupported path parameter style: {parameter.get('name')}")


def _request_lines(
    call: list[str],
    *,
    async_method: bool,
    optional_body: bool,
) -> list[str]:
    request = "await self._client.request_async" if async_method else "self._client.request"
    if not optional_body:
        return [f"        response = {request}(", *call, "        )"]
    with_body = [*call[:-1], "            json=body,", call[-1]]
    return [
        "        if body is None:",
        f"            response = {request}(",
        *[f"    {line}" for line in call],
        "            )",
        "        else:",
        f"            response = {request}(",
        *[f"    {line}" for line in with_body],
        "            )",
    ]


def _operation_parameters(
    path_item: dict[str, Any],
    operation: dict[str, Any],
    parameter_components: dict[str, Any],
) -> list[dict[str, Any]]:
    """Merge path parameters with operation overrides by OpenAPI identity."""
    merged: dict[tuple[object, object], dict[str, Any]] = {}
    for parameter in [*path_item.get("parameters", []), *operation.get("parameters", [])]:
        if isinstance(parameter, dict):
            resolved = _resolve_component(parameter, "parameters", parameter_components)
            merged[(resolved.get("in"), resolved.get("name"))] = resolved
    return list(merged.values())


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


def _wire_schema(schema: dict[str, Any], schemas: dict[str, Any]) -> object:
    """Normalize non-wire annotations before comparing shared public aliases."""
    resolved = _resolve_schema(schema, schemas)
    return {
        key: value
        for key, value in resolved.items()
        if key not in REFERENCE_ANNOTATION_SIBLINGS and key != "default"
    }


def _validate_public_aliases(schemas: dict[str, Any]) -> list[str]:
    aliases: list[str] = []
    for models, field, alias in PUBLIC_PROPERTY_ALIASES:
        field_schemas = [
            schemas[model]["properties"][field]
            for model in models
            if model in schemas and field in schemas[model].get("properties", {})
        ]
        if not field_schemas:
            raise ValueError(f"Public alias {alias} has no source schema")
        normalized = [_wire_schema(schema, schemas) for schema in field_schemas]
        mutation_values = [
            value for value in normalized if value != {"anyOf": [normalized[0], {"type": "null"}]}
        ]
        if any(value != normalized[0] for value in mutation_values):
            raise ValueError(f"Public alias {alias} has divergent mutation schemas")
        aliases.append(f"{alias}: TypeAlias = {_annotation(field_schemas[0])}")
    return aliases


def _schema_alias_order(schemas: dict[str, Any], aliases: set[str]) -> list[str]:
    def dependencies(schema: dict[str, Any]) -> set[str]:
        ref = schema.get("$ref")
        found = (
            {ref.rsplit("/", 1)[-1]}
            if isinstance(ref, str) and ref.startswith("#/components/schemas/")
            else set()
        )
        for key in ("items", "additionalProperties"):
            child = schema.get(key)
            if isinstance(child, dict):
                found.update(dependencies(child))
        for key in ("anyOf", "oneOf"):
            children = schema.get(key)
            if isinstance(children, list):
                for child in children:
                    if isinstance(child, dict):
                        found.update(dependencies(child))
        return found

    ordered: list[str] = []
    pending = set(aliases)
    while pending:
        ready = sorted(name for name in pending if not (dependencies(schemas[name]) & pending))
        if not ready:
            raise ValueError("Cyclic schema aliases are outside the generated SDK profile")
        ordered.extend(ready)
        pending.difference_update(ready)
    return ordered


def _validate_request_object_profile(
    operation: dict[str, Any], request_body_components: dict[str, Any], schemas: dict[str, Any]
) -> None:
    request_body = operation.get("requestBody")
    if not isinstance(request_body, dict):
        return
    resolved_body = _resolve_component(request_body, "requestBodies", request_body_components)
    media = resolved_body.get("content", {}).get("application/json", {})
    schema = media.get("schema") if isinstance(media, dict) else None
    if not isinstance(schema, dict):
        return

    def visit(current: dict[str, Any], seen_refs: frozenset[str] = frozenset()) -> None:
        ref = current.get("$ref")
        if isinstance(ref, str):
            prefix = "#/components/schemas/"
            if not ref.startswith(prefix):
                raise ValueError(f"Unsupported schema reference: {ref}")
            if ref in seen_refs:
                return
            target = schemas.get(ref[len(prefix) :])
            if not isinstance(target, dict):
                raise ValueError(f"Unresolved schema reference: {ref}")
            visit(
                {**target, **{key: value for key, value in current.items() if key != "$ref"}},
                seen_refs | {ref},
            )
            return
        if current.get("patternProperties") or "unevaluatedProperties" in current:
            raise ValueError(
                f"{operation.get('operationId')} has an extension-bearing request object"
            )
        if (
            current.get("type") == "object"
            and current.get("properties")
            and current.get("additionalProperties") is not False
        ):
            raise ValueError(
                f"{operation.get('operationId')} has an extension-bearing request object"
            )
        properties = current.get("properties")
        if isinstance(properties, dict):
            for child in properties.values():
                if isinstance(child, dict):
                    visit(child, seen_refs)
        for key in ("items", "additionalProperties"):
            child = current.get(key)
            if isinstance(child, dict):
                visit(child, seen_refs)
        for key in ("anyOf", "oneOf"):
            children = current.get(key)
            if isinstance(children, list):
                for child in children:
                    if isinstance(child, dict):
                        visit(child, seen_refs)

    visit(schema)


def generate(spec: dict[str, Any]) -> str:
    server_url = _validate_server_contract(spec)
    _validate_auth_contract(spec)
    components = spec.get("components", {})
    schemas = components.get("schemas", {})
    public_alias_names = {alias for _, _, alias in PUBLIC_PROPERTY_ALIASES}
    unsupported_schema_names = [
        name
        for name in schemas
        if not str(name).isidentifier()
        or keyword.iskeyword(str(name))
        or name in GENERATED_MODULE_NAMES
        or name in public_alias_names
    ]
    if unsupported_schema_names:
        raise ValueError(
            "Schema component names are outside the generated SDK profile: "
            f"{sorted(unsupported_schema_names)}"
        )
    parameter_components = components.get("parameters", {})
    request_body_components = components.get("requestBodies", {})
    response_components = components.get("responses", {})
    public_aliases = _validate_public_aliases(schemas)
    schema_aliases: list[str] = []
    objects: list[str] = []
    alias_names = {
        name
        for name, schema in schemas.items()
        if schema.get("type") != "object" or not schema.get("properties")
    }
    for name in [*sorted(set(schemas) - alias_names), *_schema_alias_order(schemas, alias_names)]:
        schema = schemas[name]
        if any(
            isinstance(field_schema, dict)
            and (field_schema.get("readOnly") or field_schema.get("writeOnly"))
            for field_schema in schema.get("properties", {}).values()
        ):
            raise ValueError(
                f"Directional properties are outside the generated SDK profile: {name}"
            )
        if schema.get("type") != "object" or not schema.get("properties"):
            schema_aliases.append(f"{name}: TypeAlias = {_annotation(schema)}")
            continue
        required = set(schema.get("required", []))
        if schema.get("additionalProperties") is False:
            unsupported_fields = [
                field
                for field in schema["properties"]
                if not field.isidentifier() or keyword.iskeyword(field)
            ]
            if unsupported_fields:
                raise ValueError(
                    f"Closed object property names are outside the generated SDK profile: "
                    f"{name} {sorted(unsupported_fields)}"
                )
            lines = [f"class {name}(TypedDict):"]
            for field, field_schema in schema["properties"].items():
                annotation = _annotation(field_schema)
                if field not in required:
                    annotation = f"NotRequired[{annotation}]"
                lines.append(f"    {field}: {annotation}")
        else:
            lines = [f"class {name}(Protocol):"]
            for field, field_schema in schema["properties"].items():
                lines.extend(
                    (
                        "    @overload",
                        f"    def __getitem__(self, key: Literal[{field!r}]) -> "
                        f"{_annotation(field_schema)}: ...",
                    )
                )
            lines.extend(
                (
                    "    @overload",
                    "    def __getitem__(self, key: str) -> Any: ...",
                    "    def get(self, key: str, default: Any = None) -> Any: ...",
                )
            )
        objects.append("\n".join(lines))

    methods: list[str] = []
    async_methods: list[str] = []
    method_names: set[str] = set()
    for path, path_item in sorted(spec.get("paths", {}).items()):
        for method in HTTP_METHODS:
            operation = path_item.get(method)
            if not operation:
                continue
            parameters = _operation_parameters(path_item, operation, parameter_components)
            required_params: list[str] = []
            optional_params: list[str] = []
            path_params: list[tuple[str, str]] = []
            query_params: list[tuple[str, str]] = []
            header_params: list[tuple[str, str]] = []
            parameter_names = {"body", "self", "timeout"}
            for parameter in parameters:
                _validate_parameter_profile(parameter, schemas)
                wire_name = parameter["name"]
                py_name = _validated_python_name(
                    wire_name,
                    label=f"{operation.get('operationId')} parameter name",
                )
                if py_name in parameter_names:
                    raise ValueError(
                        f"{operation.get('operationId')} has colliding parameter names: {py_name}"
                    )
                parameter_names.add(py_name)
                annotation = _parameter_annotation(parameter.get("schema", {}))
                entry = f"{py_name}: {annotation}"
                if parameter.get("required"):
                    required_params.append(entry)
                else:
                    optional_annotation = (
                        annotation if "None" in annotation.split(" | ") else f"{annotation} | None"
                    )
                    optional_params.append(f"{py_name}: {optional_annotation} = None")
                target = {"path": path_params, "query": query_params, "header": header_params}[
                    parameter["in"]
                ]
                target.append((wire_name, py_name))

            body = _body_type(operation, request_body_components)
            _validate_request_object_profile(operation, request_body_components, schemas)
            if body is None:
                body_type = None
                body_required = False
            else:
                body_type, body_required = body
                request_body = _resolve_component(
                    operation["requestBody"], "requestBodies", request_body_components
                )
                body_schema = request_body["content"]["application/json"]["schema"]
                if _is_nullable(body_schema, schemas):
                    raise ValueError(f"{operation.get('operationId')} has a nullable request body")
                if body_required:
                    required_params.append(f"body: {body_type}")
                else:
                    optional_params.append(f"body: {body_type} | None = None")
            signature = ", ".join(
                ["self", *required_params, *optional_params, "*", "timeout: float | None = None"]
            )
            rendered_path = path.lstrip("/")
            for wire_name, py_name in path_params:
                rendered_path = rendered_path.replace(
                    "{" + wire_name + "}", "{" + f"_segment({py_name})" + "}"
                )
            query = "{" + ", ".join(f"{wire!r}: {py}" for wire, py in query_params) + "}"
            headers = "{" + ", ".join(f"{wire!r}: {py}" for wire, py in header_params) + "}"
            result, response_has_json = _response_type(operation, response_components)
            _validate_error_contract(operation, response_components, schemas)
            path_literal = (
                f"f{rendered_path!r}" if "_segment(" in rendered_path else repr(rendered_path)
            )
            call = [f"            {method.upper()!r},", f"            {path_literal},"]
            if query_params:
                call.append(f"            params={query},")
            if header_params:
                call.append(f"            headers={headers},")
            if body_type and body_required:
                call.append("            json=body,")
            call.append("            timeout=timeout,")
            method_name = _validated_python_name(
                operation["operationId"],
                label="Operation name",
            )
            emitted_method_names = {
                method_name,
                *({f"{method_name}_async"} if method_name in ASYNC_METHODS else set()),
            }
            collisions = emitted_method_names & method_names
            if collisions:
                raise ValueError(f"Operations have colliding generated names: {sorted(collisions)}")
            method_names.update(emitted_method_names)
            return_line = (
                f"        return cast({result}, response.json())"
                if response_has_json
                else "        return None"
            )
            methods.append(
                "\n".join(
                    [
                        f"    def {method_name}({signature}) -> {result}:",
                        *_request_lines(
                            call,
                            async_method=False,
                            optional_body=bool(body_type and not body_required),
                        ),
                        return_line,
                    ]
                )
            )
            if method_name in ASYNC_METHODS:
                async_methods.append(
                    "\n".join(
                        [
                            f"    async def {method_name}_async({signature}) -> {result}:",
                            *_request_lines(
                                call,
                                async_method=True,
                                optional_body=bool(body_type and not body_required),
                            ),
                            return_line,
                        ]
                    )
                )

    canonical_spec = json.dumps(spec, sort_keys=True, separators=(",", ":")).encode()
    digest = sha256(canonical_spec).hexdigest()
    uses_any = any(
        "Any" in definition for definition in [*public_aliases, *objects, *schema_aliases, *methods]
    )
    uses_protocol = any("(Protocol)" in definition for definition in objects)
    typing_names = (
        "Any, Literal, Protocol, TypeAlias, TypedDict, cast, overload"
        if uses_protocol
        else (
            "Any, Literal, TypeAlias, TypedDict, cast"
            if uses_any
            else "Literal, TypeAlias, TypedDict, cast"
        )
    )
    return "\n".join(
        [
            '"""Generated from openapi/custom-tools-v1.json. Do not edit by hand."""',
            "",
            "from __future__ import annotations",
            "",
            f"from typing import {typing_names}",
            "from typing_extensions import NotRequired",
            "from urllib.parse import quote",
            "",
            "from tamarind.http import HTTPClient",
            "",
            f"OPENAPI_SERVER_URL = {server_url!r}",
            f"OPENAPI_SHA256 = {digest!r}",
            "",
            "def _segment(value: str) -> str:",
            "    return quote(value, safe='')",
            "",
            *public_aliases,
            "",
            *objects,
            "",
            *schema_aliases,
            "",
            "class GeneratedCustomToolsTransport:",
            "    def __init__(self, client: HTTPClient):",
            "        self._client = client",
            "",
            "\n\n".join(methods),
            "\n\n".join(async_methods),
            "",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("spec", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    generated = generate(json.loads(args.spec.read_text()))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(generated)


if __name__ == "__main__":
    main()
