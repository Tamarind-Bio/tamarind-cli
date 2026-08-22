"""Generate the Custom Tools Python transport exclusively from normalized IR."""

from __future__ import annotations

import argparse
from dataclasses import replace
import json
import keyword
from pathlib import Path
import re
import unicodedata

from tamarind_codegen.custom_tools import Api, Operation, Parameter, RequestBody, Response, Schema
from tamarind_codegen.custom_tools.ir import Field, SchemaDefinition
from tamarind_codegen.custom_tools.normalize import normalize
from tamarind_codegen.custom_tools.project import project_custom_tools

ASYNC_OPERATIONS = frozenset({"getCustomToolVersion", "listCustomToolBuildLogs"})
HTTP_METHODS = frozenset({"DELETE", "GET", "PATCH", "POST", "PUT"})
PROPERTY_ALIASES = {"gpuType": "GpuType", "memory": "MemorySize"}
RESERVED_NAMES = {
    "Any",
    "GeneratedCustomToolsTransport",
    "HTTPClient",
    "Literal",
    "NotRequired",
    "OPENAPI_SERVER_URL",
    "OPENAPI_SHA256",
    "TypeAlias",
    "TypedDict",
    "_segment",
    "cast",
}


def _python_name(value: str, *, label: str) -> str:
    candidate = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", value)
    candidate = re.sub(r"[^a-zA-Z0-9]+", "_", candidate).strip("_").lower()
    if not candidate.isidentifier() or keyword.iskeyword(candidate):
        raise ValueError(f"{label} cannot be represented as a Python identifier: {value!r}")
    return candidate


def _component_name(value: str) -> str:
    if (
        unicodedata.normalize("NFKC", value) != value
        or not value.isidentifier()
        or keyword.iskeyword(value)
        or value in RESERVED_NAMES
    ):
        raise ValueError(f"Schema name cannot be represented safely in Python: {value!r}")
    return value


def _annotation(schema: Schema) -> str:
    if schema.enum:
        rendered = "Literal[" + ", ".join(repr(value) for value in schema.enum) + "]"
    elif schema.has_const:
        rendered = f"Literal[{schema.const!r}]"
    elif schema.kind == "reference":
        if schema.reference is None:
            raise ValueError("Reference IR is missing its target")
        rendered = _component_name(schema.reference)
    elif schema.kind == "string":
        rendered = "str"
    elif schema.kind == "integer":
        rendered = "int"
    elif schema.kind == "number":
        rendered = "float"
    elif schema.kind == "boolean":
        rendered = "bool"
    elif schema.kind == "null":
        rendered = "None"
    elif schema.kind == "array":
        if schema.items is None:
            raise ValueError("Array IR is missing its item schema")
        rendered = f"list[{_annotation(schema.items)}]"
    elif schema.kind == "map":
        values = schema.additional_properties
        rendered = (
            f"dict[str, {_annotation(values)}]" if isinstance(values, Schema) else "dict[str, Any]"
        )
    elif schema.kind == "object" and not schema.fields:
        rendered = "dict[str, Any]"
    else:
        raise ValueError("An unnamed structured object reached the Python emitter")
    if schema.nullable and rendered != "None":
        return f"{rendered} | None"
    return rendered


def _field_annotation(model_name: str, field: Field) -> str:
    alias = PROPERTY_ALIASES.get(field.wire_name)
    if alias and model_name in {
        "PublicCreateCustomToolRequest",
        "PublicCustomTool",
        "PublicUpdateCustomToolRequest",
    }:
        return f"{alias} | None" if field.schema.nullable else alias
    return _annotation(field.schema)


def _property_aliases(api: Api) -> list[str]:
    by_name = {definition.name: definition.schema for definition in api.schemas}
    lines: list[str] = []
    for wire_name, alias in PROPERTY_ALIASES.items():
        candidates: list[str] = []
        for model_name in (
            "PublicCustomTool",
            "PublicCreateCustomToolRequest",
            "PublicUpdateCustomToolRequest",
        ):
            model = by_name.get(model_name)
            if model is None:
                continue
            field = next((item for item in model.fields if item.wire_name == wire_name), None)
            if field is not None:
                candidates.append(_annotation(replace(field.schema, nullable=False)))
        if not candidates or any(candidate != candidates[0] for candidate in candidates[1:]):
            raise ValueError(f"Public property alias {alias} is missing or inconsistent")
        lines.append(f"{alias}: TypeAlias = {candidates[0]}")
    return lines


def _model(definition: SchemaDefinition) -> str:
    name = _component_name(definition.name)
    schema = definition.schema
    if schema.kind != "object" or not schema.fields:
        return f"{name}: TypeAlias = {_annotation(schema)}"
    fields: list[str] = []
    for field in schema.fields:
        annotation = _field_annotation(definition.name, field)
        if not field.required:
            annotation = f"NotRequired[{annotation}]"
        fields.append(f"        {field.wire_name!r}: {annotation},")
    return "\n".join([f"{name} = TypedDict(", f"    {name!r},", "    {", *fields, "    },", ")"])


def _schema_references(schema: Schema) -> set[str]:
    references = {schema.reference} if schema.kind == "reference" and schema.reference else set()
    if schema.items is not None:
        references.update(_schema_references(schema.items))
    for field in schema.fields:
        references.update(_schema_references(field.schema))
    if isinstance(schema.additional_properties, Schema):
        references.update(_schema_references(schema.additional_properties))
    return references


def _ordered_schema_definitions(api: Api) -> list[SchemaDefinition]:
    by_name = {definition.name: definition for definition in api.schemas}
    if len(by_name) != len(api.schemas):
        raise ValueError("Schema definitions must have unique names")
    ordered: list[SchemaDefinition] = []
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(name: str) -> None:
        if name in visited:
            return
        if name in visiting:
            raise ValueError(f"Recursive schema dependency reached the Python emitter: {name}")
        definition = by_name.get(name)
        if definition is None:
            raise ValueError(f"Schema reference target is missing from the IR: {name}")
        visiting.add(name)
        for dependency in sorted(_schema_references(definition.schema)):
            visit(dependency)
        visiting.remove(name)
        visited.add(name)
        ordered.append(definition)

    for definition in api.schemas:
        visit(definition.name)
    return ordered


def _parameter_annotation(parameter: Parameter) -> str:
    if parameter.schema.nullable:
        raise ValueError(f"Wire parameter cannot be nullable: {parameter.wire_name}")
    annotation = _annotation(parameter.schema)
    if parameter.location == "path" and annotation != "str":
        raise ValueError(f"Path parameter must be a string: {parameter.wire_name}")
    if parameter.schema.kind in {"array", "map", "object"}:
        raise ValueError(f"Structured wire parameter is unsupported: {parameter.wire_name}")
    return annotation


def _body_annotation(body: RequestBody) -> str:
    if body.schema.nullable:
        raise ValueError("Request bodies cannot be nullable in the Python transport")
    return _annotation(body.schema)


def _success(operation: Operation) -> Response:
    responses = [response for response in operation.responses if response.status.startswith("2")]
    if len(responses) != 1:
        raise ValueError(f"{operation.operation_id} must have exactly one successful response")
    return responses[0]


def _request_lines(call: list[str], *, async_method: bool, optional_body: bool) -> list[str]:
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


def _method(operation: Operation, *, async_method: bool) -> tuple[str, str]:
    if operation.method not in HTTP_METHODS:
        raise ValueError(f"Unsupported method in IR: {operation.method}")
    method_name = _python_name(operation.operation_id, label="Operation ID")
    if async_method:
        method_name += "_async"

    required: list[str] = []
    optional: list[str] = []
    path_parameters: list[tuple[str, str]] = []
    query_parameters: list[tuple[str, str]] = []
    header_parameters: list[tuple[str, str]] = []
    used_names = {"body", "self", "timeout"}
    for parameter in operation.parameters:
        py_name = _python_name(parameter.wire_name, label=f"{operation.operation_id} parameter")
        if py_name in used_names:
            raise ValueError(f"{operation.operation_id} has a parameter name collision: {py_name}")
        used_names.add(py_name)
        annotation = _parameter_annotation(parameter)
        if parameter.required:
            required.append(f"{py_name}: {annotation}")
        else:
            optional.append(f"{py_name}: {annotation} | None = None")
        target = {
            "header": header_parameters,
            "path": path_parameters,
            "query": query_parameters,
        }[parameter.location]
        target.append((parameter.wire_name, py_name))

    if operation.request_body is not None:
        annotation = _body_annotation(operation.request_body)
        if operation.request_body.required:
            required.append(f"body: {annotation}")
        else:
            optional.append(f"body: {annotation} | None = None")

    signature = ", ".join(["self", *required, *optional, "*", "timeout: float | None = None"])
    placeholders = set(re.findall(r"\{([^{}]+)\}", operation.path))
    supplied_path_parameters = {wire_name for wire_name, _ in path_parameters}
    if placeholders != supplied_path_parameters:
        raise ValueError(f"{operation.operation_id} path parameters do not match its path template")
    rendered_path = operation.path.lstrip("/")
    for wire_name, py_name in path_parameters:
        rendered_path = rendered_path.replace(
            "{" + wire_name + "}", "{" + f"_segment({py_name})" + "}"
        )
    path_literal = f"f{rendered_path!r}" if "_segment(" in rendered_path else repr(rendered_path)

    call = [f"            {operation.method!r},", f"            {path_literal},"]
    if query_parameters:
        query = "{" + ", ".join(f"{wire!r}: {py}" for wire, py in query_parameters) + "}"
        call.append(f"            params={query},")
    if header_parameters:
        headers = "{" + ", ".join(f"{wire!r}: {py}" for wire, py in header_parameters) + "}"
        call.append(f"            headers={headers},")
    if operation.request_body is not None and operation.request_body.required:
        call.append("            json=body,")
    call.append("            timeout=timeout,")

    success = _success(operation)
    result = _annotation(success.schema) if success.schema is not None else "None"
    return_line = (
        f"        return cast({result}, response.json())"
        if success.schema is not None
        else "        return None"
    )
    prefix = "async def" if async_method else "def"
    lines = [
        f"    {prefix} {method_name}({signature}) -> {result}:",
        *_request_lines(
            call,
            async_method=async_method,
            optional_body=operation.request_body is not None
            and not operation.request_body.required,
        ),
        return_line,
    ]
    return method_name, "\n".join(lines)


def emit_python(api: Api) -> str:
    """Render Python using only the normalized representation."""

    models = [_model(definition) for definition in _ordered_schema_definitions(api)]
    aliases = _property_aliases(api)
    methods: list[str] = []
    emitted_names: set[str] = set()
    for operation in api.operations:
        name, rendered = _method(operation, async_method=False)
        if name in emitted_names:
            raise ValueError(f"Operations have a generated-name collision: {name}")
        emitted_names.add(name)
        methods.append(rendered)
    for operation in api.operations:
        if operation.operation_id not in ASYNC_OPERATIONS:
            continue
        name, rendered = _method(operation, async_method=True)
        if name in emitted_names:
            raise ValueError(f"Operations have a generated-name collision: {name}")
        emitted_names.add(name)
        methods.append(rendered)

    return "\n".join(
        [
            '"""Generated from the Custom Tools projection of openapi/public-v1.json. Do not edit by hand."""',
            "",
            "from __future__ import annotations",
            "",
            "from typing import Any, Literal, TypeAlias, cast",
            "from typing_extensions import NotRequired, TypedDict",
            "from urllib.parse import quote",
            "",
            "from tamarind.http import HTTPClient",
            "",
            f"OPENAPI_SERVER_URL = {api.server_url!r}",
            f"OPENAPI_SHA256 = {api.source_sha256!r}",
            "",
            "def _segment(value: str) -> str:",
            "    return quote(value, safe='')",
            "",
            *aliases,
            "",
            *models,
            "",
            "class GeneratedCustomToolsTransport:",
            "    def __init__(self, client: HTTPClient):",
            "        self._client = client",
            "",
            "\n\n".join(methods),
            "",
        ]
    )


def generate(document: dict[str, object]) -> str:
    return emit_python(normalize(project_custom_tools(document)))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("spec", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    document = json.loads(args.spec.read_text(encoding="utf-8"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(generate(document), encoding="utf-8")


if __name__ == "__main__":
    main()
