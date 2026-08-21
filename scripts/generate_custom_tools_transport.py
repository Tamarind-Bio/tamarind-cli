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


def _name(value: str) -> str:
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", value)
    return re.sub(r"[^a-zA-Z0-9]+", "_", value).strip("_").lower()


def _annotation(schema: dict[str, Any]) -> str:
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
        additional = schema.get("additionalProperties")
        return (
            f"dict[str, {_annotation(additional)}]"
            if isinstance(additional, dict)
            else "dict[str, Any]"
        )
    return "Any"


def _response_type(operation: dict[str, Any], components: dict[str, Any]) -> tuple[str, bool]:
    responses = operation.get("responses", {})
    success: dict[str, Any] = next(
        (value for code, value in responses.items() if str(code).startswith("2")), {}
    )
    success = _resolve_component(success, "responses", components)
    json_content = success.get("content", {}).get("application/json")
    if not isinstance(json_content, dict):
        return "None", False
    return _annotation(json_content.get("schema", {})), True


def _body_type(operation: dict[str, Any], components: dict[str, Any]) -> tuple[str, bool] | None:
    request_body = operation.get("requestBody", {})
    if not isinstance(request_body, dict):
        return None
    request_body = _resolve_component(request_body, "requestBodies", components)
    schema = request_body.get("content", {}).get("application/json", {}).get("schema")
    return (
        (_annotation(schema), request_body.get("required") is True)
        if isinstance(schema, dict)
        else None
    )


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
    components = spec.get("components", {})
    schemas = components.get("schemas", {})
    parameter_components = components.get("parameters", {})
    request_body_components = components.get("requestBodies", {})
    response_components = components.get("responses", {})
    aliases = [
        f"{alias}: TypeAlias = {_annotation(schemas[model]['properties'][field])}"
        for model, field, alias in PUBLIC_PROPERTY_ALIASES
    ]
    objects: list[str] = []
    for name in sorted(schemas):
        schema = schemas[name]
        if schema.get("type") != "object" or not schema.get("properties"):
            aliases.append(f"{name}: TypeAlias = {_annotation(schema)}")
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
                wire_name = parameter["name"]
                py_name = _name(wire_name)
                annotation = _annotation(parameter.get("schema", {}))
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
    uses_any = any("Any" in definition for definition in [*aliases, *objects, *methods])
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
            *aliases,
            "",
            *objects,
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
