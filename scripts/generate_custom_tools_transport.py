"""Generate Custom Tools wire types and HTTP methods from OpenAPI."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any


HTTP_METHODS = ("get", "post", "put", "patch", "delete")


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


def _response_type(operation: dict[str, Any]) -> str:
    responses = operation.get("responses", {})
    success = next((value for code, value in responses.items() if str(code).startswith("2")), {})
    schema = success.get("content", {}).get("application/json", {}).get("schema", {})
    return _annotation(schema)


def _body_type(operation: dict[str, Any]) -> str | None:
    schema = (
        operation.get("requestBody", {})
        .get("content", {})
        .get("application/json", {})
        .get("schema")
    )
    return _annotation(schema) if isinstance(schema, dict) else None


def generate(spec: dict[str, Any]) -> str:
    schemas = spec.get("components", {}).get("schemas", {})
    aliases: list[str] = []
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
    for path, path_item in sorted(spec.get("paths", {}).items()):
        for method in HTTP_METHODS:
            operation = path_item.get(method)
            if not operation:
                continue
            parameters = operation.get("parameters", [])
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

            body_type = _body_type(operation)
            if body_type:
                required_params.append(f"body: {body_type}")
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
            result = _response_type(operation)
            path_literal = (
                f"f{rendered_path!r}" if "_segment(" in rendered_path else repr(rendered_path)
            )
            call = [f"            {method.upper()!r},", f"            {path_literal},"]
            if query_params:
                call.append(f"            params={query},")
            if header_params:
                call.append(f"            headers={headers},")
            if body_type:
                call.append("            json=body,")
            call.append("            timeout=timeout,")
            methods.append(
                "\n".join(
                    [
                        f"    def {_name(operation['operationId'])}({signature}) -> {result}:",
                        "        response = self._client.request(",
                        *call,
                        "        )",
                        f"        return cast({result}, response.json())",
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
            "    def fork(self) -> GeneratedCustomToolsTransport:",
            "        return GeneratedCustomToolsTransport(self._client.fork())",
            "",
            "    def close(self) -> None:",
            "        self._client.close()",
            "",
            "\n\n".join(methods),
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
