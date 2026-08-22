from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import json
import subprocess
import sys


def test_openapi_extraction_decodes_schema_reference_tokens(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    source = tmp_path / "public.json"
    output = tmp_path / "custom-tools.json"
    source.write_text(
        json.dumps(
            {
                "openapi": "3.1.0",
                "info": {"title": "test", "version": "1"},
                "paths": {
                    "/custom-tools": {
                        "get": {
                            "operationId": "listCustomTools",
                            "responses": {
                                "200": {
                                    "description": "ok",
                                    "content": {
                                        "application/json": {
                                            "schema": {
                                                "$ref": "#/components/schemas/Escaped~1Schema"
                                            }
                                        }
                                    },
                                }
                            },
                        }
                    }
                },
                "components": {
                    "schemas": {"Escaped/Schema": {"type": "string"}},
                    "securitySchemes": {},
                },
            }
        )
    )

    subprocess.run(
        [
            sys.executable,
            str(root / "scripts/extract_custom_tools_openapi.py"),
            str(source),
            str(output),
        ],
        check=True,
    )

    assert set(json.loads(output.read_text())["components"]["schemas"]) == {"Escaped/Schema"}


def test_openapi_extraction_uses_the_public_path_boundary(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    operation = {
        "operationId": "listCustomTools",
        "parameters": [{"$ref": "#/components/parameters/OptionalTrace"}],
        "responses": {
            "200": {
                "description": "ok",
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/PublicCustomTool"},
                        "example": {
                            "$ref": "#/components/schemas/NotASchema",
                            "component": {"$ref": "#/components/responses/NotAComponent"},
                            "security": [{"mode": "strict"}],
                        },
                        "x-example-data": {"$ref": "#/components/schemas/NotASchema"},
                    }
                },
            },
            "default": {"$ref": "#/components/responses/Error"},
        },
    }
    spec = {
        "openapi": "3.1.0",
        "info": {"title": "test", "version": "1"},
        "servers": [{"url": "https://app.tamarind.bio/api"}],
        "security": [{"ApiKey": []}],
        "paths": {
            "/custom-tools": {
                "get": operation,
                "post": {
                    "operationId": "createCustomTool",
                    "requestBody": {"$ref": "#/components/requestBodies/CreateBodyAlias"},
                    "responses": {"201": {"$ref": "#/components/responses/CreateSuccess"}},
                },
                "patch": {
                    "operationId": "optionalCustomToolAction",
                    "requestBody": {"$ref": "#/components/requestBodies/OptionalBody"},
                    "responses": {"204": {"description": "done"}},
                },
            },
            "/custom-tools/{name}": {
                "parameters": [{"$ref": "#/components/parameters/ToolName"}],
                "get": {
                    **operation,
                    "operationId": "getCustomTool",
                    "parameters": [{"$ref": "#/components/parameters/CanonicalToolName"}],
                },
            },
            "/custom-tools/{name}/versions": {"$ref": "#/components/pathItems/ToolVersionsAlias"},
            "/custom-tools-preview": {"get": operation},
            "/molecules": {"get": operation},
        },
        "components": {
            "responses": {
                "Error": {
                    "description": "problem",
                    "content": {
                        "application/problem+json": {
                            "schema": {"$ref": "#/components/schemas/PublicProblem"}
                        }
                    },
                },
                "CreateSuccess": {
                    "description": "created",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/CreateResultAlias"}
                        }
                    },
                },
                "UnrelatedSuccess": {
                    "description": "unrelated",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/UnrelatedModel"}
                        }
                    },
                },
            },
            "securitySchemes": {
                "ApiKey": {"type": "apiKey", "in": "header", "name": "x-api-key"},
                "UnrelatedAuth": {"type": "http", "scheme": "bearer"},
            },
            "requestBodies": {
                "CreateBodyAlias": {"$ref": "#/components/requestBodies/CreateBody"},
                "CreateBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/CreatePayload"}
                        }
                    },
                },
                "UnusedBody": {"content": {"application/json": {"schema": {"type": "string"}}}},
                "OptionalBody": {
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/CreatePayload"}
                        }
                    }
                },
            },
            "pathItems": {
                "ToolVersionsAlias": {"$ref": "#/components/pathItems/ToolVersions"},
                "ToolVersions": {
                    "parameters": [{"$ref": "#/components/parameters/ToolName"}],
                    "get": {
                        "operationId": "listVersions",
                        "responses": {"204": {"description": "empty"}},
                    },
                },
                "UnusedPath": {"get": operation},
            },
            "parameters": {
                "ToolName": {
                    "in": "path",
                    "name": "name",
                    "required": True,
                    "schema": {"type": "string"},
                },
                "CanonicalToolName": {
                    "in": "path",
                    "name": "name",
                    "required": True,
                    "schema": {"enum": ["canonical"]},
                },
                "Unused": {
                    "in": "query",
                    "name": "unused",
                    "schema": {"type": "string"},
                },
                "OptionalTrace": {
                    "in": "header",
                    "name": "X-Trace",
                    "schema": {
                        "type": "string",
                        "default": {"$ref": "#/components/responses/NotAComponent"},
                    },
                },
            },
            "schemas": {
                "CreatePayload": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "name": {
                            "type": "string",
                            "default": {"$ref": "#/components/schemas/NotASchema"},
                            "example": {"$ref": "#/components/responses/NotAComponent"},
                        }
                    },
                    "required": ["name"],
                },
                "CreateResult": {
                    "additionalProperties": False,
                    "type": "object",
                    "properties": {"id": {"type": "string"}},
                    "required": ["id"],
                },
                "PublicCustomTool": {
                    "type": "object",
                    "properties": {
                        "gpuType": {
                            "type": "string",
                            "enum": ["None", "T4", "L4", "L40S", "A10", "A100"],
                        },
                        "memory": {
                            "type": "string",
                            "enum": [
                                "8Gi",
                                "12Gi",
                                "24Gi",
                                "32Gi",
                                "48Gi",
                                "64Gi",
                                "90Gi",
                                "96Gi",
                                "180Gi",
                            ],
                        },
                    },
                    "required": ["gpuType", "memory"],
                },
                "CreateResultAlias": {"$ref": "#/components/schemas/CreateResult"},
                "PublicProblem": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string"},
                        "title": {"type": "string"},
                        "status": {"type": "integer"},
                        "code": {"type": "string"},
                    },
                    "required": ["type", "title", "status", "code"],
                },
                "UnrelatedModel": {"type": "string"},
            },
        },
    }
    source = tmp_path / "public.json"
    sliced_path = tmp_path / "custom-tools.json"
    source.write_text(json.dumps(spec))

    subprocess.run(
        [
            sys.executable,
            str(root / "scripts/extract_custom_tools_openapi.py"),
            str(source),
            str(sliced_path),
        ],
        check=True,
    )
    sliced = json.loads(sliced_path.read_text())

    assert set(sliced["paths"]) == {
        "/custom-tools",
        "/custom-tools/{name}",
        "/custom-tools/{name}/versions",
    }
    assert sliced["paths"]["/custom-tools/{name}"]["parameters"] == [
        {"$ref": "#/components/parameters/ToolName"}
    ]
    assert set(sliced["components"]["parameters"]) == {
        "CanonicalToolName",
        "OptionalTrace",
        "ToolName",
    }
    assert set(sliced["components"]["requestBodies"]) == {
        "CreateBody",
        "CreateBodyAlias",
        "OptionalBody",
    }
    assert set(sliced["components"]["pathItems"]) == {"ToolVersions", "ToolVersionsAlias"}
    assert set(sliced["components"]["schemas"]) == {
        "CreatePayload",
        "CreateResult",
        "CreateResultAlias",
        "PublicCustomTool",
        "PublicProblem",
    }
    assert set(sliced["components"]["responses"]) == {"CreateSuccess", "Error"}
    assert set(sliced["components"]["securitySchemes"]) == {"ApiKey"}

    generated = tmp_path / "generated.py"
    subprocess.run(
        [
            sys.executable,
            str(root / "scripts/generate_custom_tools_transport.py"),
            str(sliced_path),
            str(generated),
        ],
        check=True,
    )
    generated_text = generated.read_text()
    assert "OPENAPI_SERVER_URL = 'https://app.tamarind.bio/api/'" in generated_text
    assert "GpuType: TypeAlias = Literal[" in generated_text
    assert "'A100'" in generated_text
    assert "MemorySize: TypeAlias = Literal[" in generated_text
    assert "def get_custom_tool(self, name: Literal['canonical']" in generated_text
    assert "x_trace: str | None = None" in generated_text
    assert "headers={'X-Trace': x_trace}" in generated_text
    assert "f'custom-tools/{_segment(name)}'" in generated_text
    assert "def create_custom_tool(self, body: CreatePayload" in generated_text
    assert "json=body" in generated_text
    assert ") -> CreateResultAlias:" in generated_text
    assert generated_text.index("class CreateResult(TypedDict):") < generated_text.index(
        "CreateResultAlias: TypeAlias = CreateResult"
    )
    assert (
        "def optional_custom_tool_action(self, body: CreatePayload | None = None" in generated_text
    )
    assert "if body is None:" in generated_text
    assert "def list_versions(self, name: str" in generated_text
    assert ") -> None:" in generated_text
    assert "return None" in generated_text

    extension_response = deepcopy(sliced)
    extension_response["components"]["schemas"]["CreateResult"].pop("additionalProperties", None)
    extension_response_path = tmp_path / "extension-response.json"
    extension_response_output = tmp_path / "extension-response.py"
    extension_response_path.write_text(json.dumps(extension_response))
    subprocess.run(
        [
            sys.executable,
            str(root / "scripts/generate_custom_tools_transport.py"),
            str(extension_response_path),
            str(extension_response_output),
        ],
        check=True,
    )
    extension_text = extension_response_output.read_text()
    assert "class CreateResult(Protocol):" in extension_text
    assert "def __getitem__(self, key: str) -> Any" in extension_text

    alias_chain = deepcopy(sliced)
    alias_chain["components"]["schemas"].update(
        {
            "AAlias": {"$ref": "#/components/schemas/ZAlias"},
            "ZAlias": {"type": "string"},
        }
    )
    alias_chain_path = tmp_path / "alias-chain.json"
    alias_chain_output = tmp_path / "alias-chain.py"
    alias_chain_path.write_text(json.dumps(alias_chain))
    subprocess.run(
        [
            sys.executable,
            str(root / "scripts/generate_custom_tools_transport.py"),
            str(alias_chain_path),
            str(alias_chain_output),
        ],
        check=True,
    )
    alias_text = alias_chain_output.read_text()
    assert alias_text.index("ZAlias: TypeAlias = str") < alias_text.index(
        "AAlias: TypeAlias = ZAlias"
    )

    unsupported_contracts: list[tuple[dict[str, object], str]] = []

    divergent_mutation_alias = deepcopy(sliced)
    divergent_mutation_alias["components"]["schemas"].update(
        {
            "PublicCreateCustomToolRequest": {
                "type": "object",
                "additionalProperties": False,
                "properties": {"gpuType": {"enum": ["A100"], "type": "string"}},
            },
            "PublicUpdateCustomToolRequest": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "gpuType": {
                        "anyOf": [
                            {"enum": ["A100"], "type": "string"},
                            {"type": "null"},
                        ]
                    }
                },
            },
        }
    )
    unsupported_contracts.append(
        (divergent_mutation_alias, "Public alias GpuType has divergent mutation schemas")
    )

    path_servers = deepcopy(sliced)
    path_servers["paths"]["/custom-tools"]["servers"] = [{"url": "https://other.test"}]
    unsupported_contracts.append((path_servers, "Path-level servers"))

    operation_servers = deepcopy(sliced)
    operation_servers["paths"]["/custom-tools"]["get"]["servers"] = [{"url": "https://other.test"}]
    unsupported_contracts.append((operation_servers, "operation-level servers"))

    missing_server = deepcopy(sliced)
    missing_server["servers"] = []
    unsupported_contracts.append((missing_server, "Exactly one global OpenAPI server"))

    variable_server = deepcopy(sliced)
    variable_server["servers"] = [
        {
            "url": "https://{region}.tamarind.bio/api",
            "variables": {"region": {"default": "app"}},
        }
    ]
    unsupported_contracts.append((variable_server, "server variables and extensions"))

    custom_dialect = deepcopy(sliced)
    custom_dialect["jsonSchemaDialect"] = "https://example.test/custom-dialect"
    unsupported_contracts.append((custom_dialect, "Custom JSON Schema dialects"))

    openapi_30 = deepcopy(sliced)
    openapi_30["openapi"] = "3.0.3"
    unsupported_contracts.append((openapi_30, "Only OpenAPI 3.1"))

    unsupported_auth = deepcopy(sliced)
    unsupported_auth["components"]["securitySchemes"]["ApiKey"]["name"] = "Authorization"
    unsupported_contracts.append((unsupported_auth, "Exactly one x-api-key"))

    anonymous_auth = deepcopy(sliced)
    anonymous_auth["components"]["securitySchemes"] = {}
    anonymous_auth["security"] = [{}]
    unsupported_contracts.append((anonymous_auth, "Exactly one x-api-key"))

    multiple_successes = deepcopy(sliced)
    multiple_successes["paths"]["/custom-tools"]["get"]["responses"]["204"] = {
        "description": "empty"
    }
    unsupported_contracts.append((multiple_successes, "exactly one successful response"))

    nullable_optional_body = deepcopy(sliced)
    nullable_optional_body["components"]["requestBodies"]["OptionalBody"]["content"][
        "application/json"
    ]["schema"] = {
        "anyOf": [
            {"$ref": "#/components/schemas/CreatePayload"},
            {"type": "null"},
        ]
    }
    unsupported_contracts.append((nullable_optional_body, "nullable request body"))

    type_array_nullable_body = deepcopy(sliced)
    type_array_nullable_body["components"]["requestBodies"]["OptionalBody"]["content"][
        "application/json"
    ]["schema"] = {"type": ["object", "null"]}
    unsupported_contracts.append((type_array_nullable_body, "nullable request body"))

    enum_nullable_body = deepcopy(sliced)
    enum_nullable_body["components"]["requestBodies"]["OptionalBody"]["content"][
        "application/json"
    ]["schema"] = {"enum": ["value", None]}
    unsupported_contracts.append((enum_nullable_body, "nullable request body"))

    ref_sibling_nullable_body = deepcopy(sliced)
    ref_sibling_nullable_body["components"]["requestBodies"]["OptionalBody"]["content"][
        "application/json"
    ]["schema"] = {
        "$ref": "#/components/schemas/CreatePayload",
        "type": ["object", "null"],
    }
    unsupported_contracts.append((ref_sibling_nullable_body, "Schema reference siblings"))

    type_array_model = deepcopy(sliced)
    type_array_model["components"]["schemas"]["CreatePayload"]["properties"]["name"] = {
        "type": ["string", "null"]
    }
    type_array_path = tmp_path / "type-array.json"
    type_array_output = tmp_path / "type-array.py"
    type_array_path.write_text(json.dumps(type_array_model))
    subprocess.run(
        [
            sys.executable,
            str(root / "scripts/generate_custom_tools_transport.py"),
            str(type_array_path),
            str(type_array_output),
        ],
        check=True,
    )
    assert "name: str | None" in type_array_output.read_text()

    nullable_inline_object = deepcopy(sliced)
    nullable_inline_object["components"]["schemas"]["CreatePayload"]["properties"]["name"] = {
        "type": ["object", "null"],
        "properties": {"value": {"type": "string"}},
    }
    unsupported_contracts.append((nullable_inline_object, "inline object schemas"))

    all_of_model = deepcopy(sliced)
    all_of_model["components"]["schemas"]["CreatePayload"]["properties"]["name"] = {
        "allOf": [{"type": "string"}]
    }
    unsupported_contracts.append((all_of_model, "allOf schemas"))

    combinator_sibling_model = deepcopy(sliced)
    combinator_sibling_model["components"]["schemas"]["CreatePayload"]["properties"]["name"] = {
        "anyOf": [{"type": "string"}, {"type": "null"}],
        "type": "string",
    }
    unsupported_contracts.append((combinator_sibling_model, "anyOf schema siblings"))

    unconstrained_model = deepcopy(sliced)
    unconstrained_model["components"]["schemas"]["CreatePayload"]["properties"]["name"] = {}
    unsupported_contracts.append((unconstrained_model, "Unconstrained schemas"))

    opaque_alias_annotation = deepcopy(sliced)
    opaque_alias_annotation["components"]["schemas"]["OpaqueAlias"] = {
        "type": "string",
        "x-data": {"$ref": "#/components/schemas/OpaqueAlias"},
    }
    opaque_alias_path = tmp_path / "opaque-alias.json"
    opaque_alias_output = tmp_path / "opaque-alias.py"
    opaque_alias_path.write_text(json.dumps(opaque_alias_annotation))
    subprocess.run(
        [
            sys.executable,
            str(root / "scripts/generate_custom_tools_transport.py"),
            str(opaque_alias_path),
            str(opaque_alias_output),
        ],
        check=True,
    )

    ref_sibling_model = deepcopy(sliced)
    ref_sibling_model["components"]["schemas"]["CreatePayload"]["properties"]["name"] = {
        "$ref": "#/components/schemas/CreateResult",
        "type": "string",
    }
    unsupported_contracts.append((ref_sibling_model, "Schema reference siblings"))

    external_ref = deepcopy(sliced)
    external_ref["paths"]["/custom-tools"]["get"]["responses"]["200"]["content"][
        "application/json"
    ]["schema"] = {"$ref": "https://schemas.example/str"}
    unsupported_contracts.append((external_ref, "External schema references"))

    inconsistent_enum = deepcopy(sliced)
    inconsistent_enum["components"]["schemas"]["CreatePayload"]["properties"]["name"] = {
        "type": "string",
        "enum": ["ok", 1],
    }
    unsupported_contracts.append((inconsistent_enum, "Enum values conflict"))

    inconsistent_const = deepcopy(sliced)
    inconsistent_const["components"]["schemas"]["CreatePayload"]["properties"]["name"] = {
        "type": "integer",
        "const": "one",
    }
    unsupported_contracts.append((inconsistent_const, "Const value conflicts"))

    tuple_model = deepcopy(sliced)
    tuple_model["components"]["schemas"]["CreatePayload"]["properties"]["name"] = {
        "type": "array",
        "prefixItems": [{"type": "string"}, {"type": "integer"}],
    }
    unsupported_contracts.append((tuple_model, "prefixItems schemas"))

    inline_object_model = deepcopy(sliced)
    inline_object_model["components"]["schemas"]["CreatePayload"]["properties"]["name"] = {
        "type": "object",
        "properties": {"value": {"type": "string"}},
    }
    unsupported_contracts.append((inline_object_model, "inline object schemas"))

    extension_request = deepcopy(sliced)
    extension_request["components"]["schemas"]["CreatePayload"].pop("additionalProperties", None)
    unsupported_contracts.append((extension_request, "extension-bearing request object"))

    invalid_closed_field = deepcopy(sliced)
    invalid_closed_field["components"]["schemas"]["CreatePayload"]["properties"]["foo-bar"] = {
        "type": "string"
    }
    unsupported_contracts.append((invalid_closed_field, "Closed object property names"))

    keyword_closed_field = deepcopy(sliced)
    keyword_closed_field["components"]["schemas"]["CreatePayload"]["properties"]["from"] = {
        "type": "string"
    }
    unsupported_contracts.append((keyword_closed_field, "Closed object property names"))

    keyword_schema = deepcopy(sliced)
    keyword_schema["components"]["schemas"]["class"] = {"type": "string"}
    unsupported_contracts.append((keyword_schema, "Schema component names"))

    directional_model = deepcopy(sliced)
    directional_model["components"]["schemas"]["CreatePayload"]["properties"]["name"][
        "readOnly"
    ] = True
    unsupported_contracts.append((directional_model, "Directional properties"))

    nullable_parameter = deepcopy(sliced)
    nullable_parameter["paths"]["/custom-tools"]["get"]["parameters"].append(
        {
            "in": "query",
            "name": "nullable",
            "schema": {"type": ["string", "null"]},
        }
    )
    unsupported_contracts.append((nullable_parameter, "Nullable wire parameter"))

    pattern_extension_request = deepcopy(sliced)
    pattern_extension_request["components"]["schemas"]["CreatePayload"]["patternProperties"] = {
        "^x-": {"type": "string"}
    }
    unsupported_contracts.append((pattern_extension_request, "extension-bearing request object"))

    nested_pattern_request = deepcopy(sliced)
    nested_pattern_request["components"]["schemas"]["CreatePayload"]["properties"]["nested"] = {
        "$ref": "#/components/schemas/NestedPayload"
    }
    nested_pattern_request["components"]["schemas"]["NestedPayload"] = {
        "type": "object",
        "additionalProperties": False,
        "properties": {"name": {"type": "string"}},
        "patternProperties": {"^x-": {"type": "string"}},
    }
    unsupported_contracts.append((nested_pattern_request, "extension-bearing request object"))

    keyword_parameter = deepcopy(sliced)
    keyword_parameter["paths"]["/custom-tools"]["get"]["parameters"].append(
        {"in": "query", "name": "from", "schema": {"type": "string"}}
    )
    unsupported_contracts.append((keyword_parameter, "parameter name"))

    colliding_parameters = deepcopy(sliced)
    colliding_parameters["paths"]["/custom-tools"]["get"]["parameters"].extend(
        [
            {"in": "query", "name": "foo-bar", "schema": {"type": "string"}},
            {"in": "header", "name": "foo_bar", "schema": {"type": "string"}},
        ]
    )
    unsupported_contracts.append((colliding_parameters, "colliding parameter names"))

    invalid_operation_name = deepcopy(sliced)
    invalid_operation_name["paths"]["/custom-tools"]["get"]["operationId"] = "123"
    unsupported_contracts.append((invalid_operation_name, "Operation name"))

    required_nullable_body = deepcopy(nullable_optional_body)
    required_nullable_body["components"]["requestBodies"]["OptionalBody"]["required"] = True
    unsupported_contracts.append((required_nullable_body, "nullable request body"))

    unsupported_request_media = deepcopy(sliced)
    unsupported_request_media["components"]["requestBodies"]["OptionalBody"]["content"] = {
        "text/plain": {"schema": {"type": "string"}}
    }
    unsupported_contracts.append((unsupported_request_media, "unsupported request content"))

    unsupported_path_style = deepcopy(sliced)
    unsupported_path_style["components"]["parameters"]["ToolName"]["style"] = "label"
    unsupported_contracts.append((unsupported_path_style, "Unsupported path parameter style"))

    integer_path = deepcopy(sliced)
    integer_path["components"]["parameters"]["CanonicalToolName"]["schema"] = {"type": "integer"}
    unsupported_contracts.append((integer_path, "Non-string path parameter"))

    boolean_header = deepcopy(sliced)
    boolean_header["components"]["parameters"]["OptionalTrace"]["schema"] = {"type": "boolean"}
    unsupported_contracts.append((boolean_header, "Non-string header parameter"))

    allow_reserved_query = deepcopy(sliced)
    allow_reserved_query["paths"]["/custom-tools"]["get"]["parameters"].append(
        {
            "in": "query",
            "name": "raw",
            "allowReserved": True,
            "schema": {"type": "string"},
        }
    )
    unsupported_contracts.append((allow_reserved_query, "Unsupported allowReserved"))

    success_headers = deepcopy(sliced)
    success_headers["paths"]["/custom-tools"]["get"]["responses"]["200"]["headers"] = {
        "ETag": {"schema": {"type": "string"}}
    }
    unsupported_contracts.append((success_headers, "unsupported success headers"))

    invalid_error_contract = deepcopy(sliced)
    invalid_error_contract["components"]["responses"]["Error"]["content"][
        "application/problem+json"
    ]["schema"] = {"type": "object", "properties": {"detail": {"type": "string"}}}
    unsupported_contracts.append((invalid_error_contract, "unsupported error response contract"))

    structured_query = deepcopy(sliced)
    structured_query["paths"]["/custom-tools"]["get"]["parameters"].append(
        {
            "in": "query",
            "name": "filter",
            "style": "deepObject",
            "explode": True,
            "schema": {"type": "object"},
        }
    )
    unsupported_contracts.append((structured_query, "Structured query parameter"))

    structured_header = deepcopy(sliced)
    structured_header["paths"]["/custom-tools"]["get"]["parameters"].append(
        {
            "in": "header",
            "name": "X-Values",
            "schema": {"type": "array", "items": {"type": "string"}},
        }
    )
    unsupported_contracts.append((structured_header, "Structured header parameter"))

    for index, (unsupported, expected_error) in enumerate(unsupported_contracts):
        unsupported_path = tmp_path / f"unsupported-{index}.json"
        unsupported_path.write_text(json.dumps(unsupported))
        result = subprocess.run(
            [
                sys.executable,
                str(root / "scripts/generate_custom_tools_transport.py"),
                str(unsupported_path),
                str(tmp_path / f"unsupported-{index}.py"),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
        assert expected_error in result.stderr


def test_generated_transport_matches_committed_openapi(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    generated = tmp_path / "generated.py"
    subprocess.run(
        [
            sys.executable,
            str(root / "scripts/generate_custom_tools_transport.py"),
            str(root / "openapi/custom-tools-v1.json"),
            str(generated),
        ],
        check=True,
    )
    subprocess.run([sys.executable, "-m", "ruff", "format", str(generated)], check=True)

    assert generated.read_text() == (root / "src/tamarind/custom_tools/generated.py").read_text()


def test_openapi_extraction_rejects_unsupported_custom_tools_operations(
    tmp_path: Path,
) -> None:
    root = Path(__file__).resolve().parents[1]
    source = tmp_path / "public.json"
    output = tmp_path / "custom-tools.json"
    source.write_text(
        json.dumps(
            {
                "openapi": "3.1.0",
                "info": {"title": "test", "version": "1"},
                "paths": {
                    "/custom-tools": {
                        "head": {
                            "operationId": "inspectCustomTools",
                            "responses": {"204": {"description": "ok"}},
                        }
                    }
                },
                "components": {},
            }
        )
    )

    result = subprocess.run(
        [
            sys.executable,
            str(root / "scripts/extract_custom_tools_openapi.py"),
            str(source),
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "Unsupported Custom Tools HTTP methods" in result.stderr


def test_openapi_slice_has_no_dangling_schema_references() -> None:
    root = Path(__file__).resolve().parents[1]
    spec = json.loads((root / "openapi/custom-tools-v1.json").read_text())
    schemas = spec["components"]["schemas"]
    missing: set[str] = set()

    def visit(node: object) -> None:
        if isinstance(node, dict):
            ref = node.get("$ref")
            if isinstance(ref, str) and ref.startswith("#/components/schemas/"):
                name = ref.rsplit("/", 1)[-1]
                if name not in schemas:
                    missing.add(name)
            for value in node.values():
                visit(value)
        elif isinstance(node, list):
            for value in node:
                visit(value)

    visit(spec)
    assert not missing


def test_version_routes_use_numbered_version_handles() -> None:
    root = Path(__file__).resolve().parents[1]
    spec = json.loads((root / "openapi/custom-tools-v1.json").read_text())
    readable_paths = (
        "/custom-tools/{name}/versions/{version_name}",
        "/custom-tools/{name}/versions/{version_name}/logs",
    )

    for path in readable_paths:
        parameters = spec["paths"][path]["get"]["parameters"]
        version = next(item for item in parameters if item["name"] == "version_name")
        assert version["schema"]["pattern"] == "^v[1-9][0-9]*$"
