"""Generate Custom Tools wire types and HTTP methods from OpenAPI."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any


HTTP_METHODS = ("get", "post", "put", "patch", "delete")
ASYNC_METHODS = frozenset({"get_custom_tool_version", "list_custom_tool_build_logs"})
PUBLIC_PROPERTY_ALIASES = (
    ("PublicCustomTool", "gpuType", "GpuType"),
    ("PublicCustomTool", "memory", "MemorySize"),
)
SUPPORTED_API_KEY_HEADER = "x-api-key"


def _validate_auth_contract(spec: dict[str, Any]) -> None:
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
    global_security = spec.get("security", [])
    for path_item in spec.get("paths", {}).values():
        for method in HTTP_METHODS:
            operation = path_item.get(method)
            if not isinstance(operation, dict):
                continue
            requirements = operation.get("security", global_security)
            if not isinstance(requirements, list) or not requirements:
                raise ValueError(f"{operation.get('operationId')} has unsupported authentication")
            if any(
                not isinstance(requirement, dict)
                or set(requirement) != supported
                or any(scopes for scopes in requirement.values())
                for requirement in requirements
            ):
                raise ValueError(f"{operation.get('operationId')} has unsupported authentication")


def _name(value: str) -> str:
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", value)
    return re.sub(r"[^a-zA-Z0-9]+", "_", value).strip("_").lower()


def _annotation(schema: dict[str, Any]) -> str:
    if "allOf" in schema:
        raise ValueError("allOf schemas are outside the generated SDK profile")
    if "$ref" in schema:
        return schema["$ref"].rsplit("/", 1)[-1]
    if "anyOf" in schema:
        parts = [_annotation(part) for part in schema["anyOf"]]
        return " | ".join(dict.fromkeys(parts))
    if "oneOf" in schema:
        return " | ".join(dict.fromkeys(_annotation(part) for part in schema["oneOf"]))
    if "const" in schema:
        return f"Literal[{schema['const']!r}]"
    if "enum" in schema:
        return "Literal[" + ", ".join(repr(value) for value in schema["enum"]) + "]"
    kind = schema.get("type")
    if isinstance(kind, list):
        return " | ".join(dict.fromkeys(_annotation({"type": item}) for item in kind))
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
        return f"list[{_annotation(schema.get('items', {}))}]"
    if kind == "object":
        if schema.get("properties") or schema.get("additionalProperties") is False:
            raise ValueError("inline object schemas are outside the generated SDK profile")
        additional = schema.get("additionalProperties")
        return (
            f"dict[str, {_annotation(additional)}]"
            if isinstance(additional, dict)
            else "dict[str, Any]"
        )
    return "Any"


def _parameter_annotation(schema: dict[str, Any]) -> str:
    """Use None only as the SDK's omission marker for optional parameters."""
    if isinstance(schema.get("type"), list):
        kinds = [kind for kind in schema["type"] if kind != "null"]
        return " | ".join(dict.fromkeys(_annotation({"type": kind}) for kind in kinds))
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
    if schema.get("type") in {"array", "object"}:
        return True
    alternatives = schema.get("anyOf", schema.get("oneOf", []))
    return isinstance(alternatives, list) and any(
        isinstance(alternative, dict) and _is_structured(alternative, schemas)
        for alternative in alternatives
    )


def _validate_parameter_profile(parameter: dict[str, Any], schemas: dict[str, Any]) -> None:
    location = parameter.get("in")
    schema = parameter.get("schema")
    if location not in {"path", "query", "header"} or not isinstance(schema, dict):
        raise ValueError(f"Unsupported parameter: {parameter.get('name')}")
    if parameter.get("required") and _is_nullable(schema, schemas):
        raise ValueError(
            f"Required nullable wire parameter is outside the SDK profile: {parameter.get('name')}"
        )
    if location == "query" and (
        parameter.get("style", "form") != "form" or _is_structured(schema, schemas)
    ):
        raise ValueError(
            f"Structured query parameter is outside the SDK profile: {parameter.get('name')}"
        )
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


def generate(spec: dict[str, Any]) -> str:
    _validate_auth_contract(spec)
    components = spec.get("components", {})
    schemas = components.get("schemas", {})
    parameter_components = components.get("parameters", {})
    request_body_components = components.get("requestBodies", {})
    response_components = components.get("responses", {})
    public_aliases = [
        f"{alias}: TypeAlias = {_annotation(schemas[model]['properties'][field])}"
        for model, field, alias in PUBLIC_PROPERTY_ALIASES
    ]
    schema_aliases: list[str] = []
    objects: list[str] = []
    for name in sorted(schemas):
        schema = schemas[name]
        if schema.get("type") != "object" or not schema.get("properties"):
            schema_aliases.append(f"{name}: TypeAlias = {_annotation(schema)}")
            continue
        required = set(schema.get("required", []))
        lines = [f"class {name}(TypedDict):"]
        for field, field_schema in schema["properties"].items():
            annotation = _annotation(field_schema)
            if field not in required:
                annotation = f"NotRequired[{annotation}]"
            lines.append(f"    {field}: {annotation}")
        objects.append("\n".join(lines))

    methods: list[str] = []
    async_methods: list[str] = []
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
            for parameter in parameters:
                _validate_parameter_profile(parameter, schemas)
                wire_name = parameter["name"]
                py_name = _name(wire_name)
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
            method_name = _name(operation["operationId"])
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
    typing_names = (
        "Any, Literal, TypeAlias, TypedDict, cast"
        if uses_any
        else "Literal, TypeAlias, TypedDict, cast"
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
