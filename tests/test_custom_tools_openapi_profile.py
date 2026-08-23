from __future__ import annotations

from copy import deepcopy

import pytest

from tamarind_codegen.custom_tools import ProfileViolation, normalize, validate_profile


def _document() -> dict:
    return {
        "openapi": "3.1.0",
        "info": {"title": "Custom Tools", "version": "1.0"},
        "servers": [{"url": "https://app.tamarind.bio/api"}],
        "security": [{"ApiKeyAuth": []}],
        "paths": {
            "/custom-tools/{name}": {
                "parameters": [
                    {
                        "name": "name",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"},
                    }
                ],
                "get": {
                    "operationId": "getCustomTool",
                    "summary": "Get a Custom Tool",
                    "parameters": [
                        {
                            "name": "includeVersions",
                            "in": "query",
                            "schema": {"type": "boolean", "default": False},
                        }
                    ],
                    "responses": {
                        "200": {"$ref": "#/components/responses/CustomToolResponse"},
                        "404": {"description": "Not found"},
                    },
                },
                "patch": {
                    "operationId": "updateCustomTool",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/UpdateCustomTool"}
                            }
                        },
                    },
                    "responses": {"200": {"$ref": "#/components/responses/CustomToolResponse"}},
                },
            }
        },
        "components": {
            "securitySchemes": {
                "ApiKeyAuth": {"type": "apiKey", "in": "header", "name": "x-api-key"}
            },
            "schemas": {
                "CustomTool": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["name", "status"],
                    "properties": {
                        "name": {"type": "string", "minLength": 1, "maxLength": 64},
                        "status": {"type": "string", "enum": ["Draft", "Deployed"]},
                        "sourceRef": {
                            "anyOf": [
                                {"type": "string", "pattern": "^[0-9a-f]{40}$"},
                                {"type": "null"},
                            ]
                        },
                    },
                },
                "UpdateCustomTool": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {"displayName": {"type": "string", "default": "Untitled"}},
                },
            },
            "responses": {
                "CustomToolResponse": {
                    "description": "A Custom Tool",
                    "content": {
                        "application/json": {"schema": {"$ref": "#/components/schemas/CustomTool"}}
                    },
                }
            },
        },
    }


def test_profile_accepts_the_documented_subset() -> None:
    validate_profile(_document())


def test_normalize_produces_an_openapi_free_ir() -> None:
    api = normalize(_document())

    assert api.server_url == "https://app.tamarind.bio/api/"
    assert [schema.name for schema in api.schemas] == ["CustomTool", "UpdateCustomTool"]

    custom_tool = api.schemas[0].schema
    assert custom_tool.kind == "object"
    assert [field.wire_name for field in custom_tool.fields] == ["name", "status", "sourceRef"]
    assert custom_tool.fields[2].schema.kind == "string"
    assert custom_tool.fields[2].schema.nullable is True

    get_tool = api.operations[0]
    assert (get_tool.method, get_tool.path, get_tool.operation_id) == (
        "GET",
        "/custom-tools/{name}",
        "getCustomTool",
    )
    assert [(parameter.wire_name, parameter.location) for parameter in get_tool.parameters] == [
        ("name", "path"),
        ("includeVersions", "query"),
    ]
    assert get_tool.parameters[1].schema.has_default is True
    assert get_tool.parameters[1].schema.default is False
    assert get_tool.responses[0].schema is not None
    assert get_tool.responses[0].schema.reference == "CustomTool"

    update_tool = api.operations[1]
    assert update_tool.request_body is not None
    assert update_tool.request_body.schema.reference == "UpdateCustomTool"


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (
            lambda document: document["components"]["schemas"]["CustomTool"]["properties"].update(
                {"remote": {"$ref": "https://example.com/schema.json"}}
            ),
            "schema references must target local component schemas",
        ),
        (
            lambda document: document["components"]["schemas"]["CustomTool"]["properties"].update(
                {"choice": {"oneOf": [{"type": "string"}, {"type": "integer"}]}}
            ),
            "schema composition is not supported",
        ),
        (
            lambda document: document["paths"]["/custom-tools/{name}"]["get"]["parameters"].append(
                {"name": "trace", "in": "cookie", "schema": {"type": "string"}}
            ),
            "only header, path and query parameters are supported",
        ),
        (
            lambda document: document["paths"]["/custom-tools/{name}"]["get"]["parameters"].append(
                {"name": "empty", "in": "query", "required": True, "schema": {"type": "null"}}
            ),
            "parameters must use scalar schemas",
        ),
        (
            lambda document: document["paths"]["/custom-tools/{name}"]["get"]["parameters"].append(
                {
                    "name": "many",
                    "in": "query",
                    "schema": {"type": "array", "items": {"type": "string"}},
                }
            ),
            "parameters must use scalar schemas",
        ),
        (
            lambda document: document["paths"]["/custom-tools/{name}"]["parameters"][0].update(
                {"schema": {"type": "integer"}}
            ),
            "path parameters must use string schemas",
        ),
        (
            lambda document: document["paths"]["/custom-tools/{name}"]["get"]["parameters"].append(
                {
                    "name": "x-retry-count",
                    "in": "header",
                    "schema": {"type": "integer"},
                }
            ),
            "header parameters must use string schemas",
        ),
        (
            lambda document: document["paths"]["/custom-tools/{name}"]["patch"]["requestBody"][
                "content"
            ]["application/json"].update({"schema": {"type": "null"}}),
            "request bodies must use non-null schemas",
        ),
        (
            lambda document: document["paths"]["/custom-tools/{name}"]["patch"]["requestBody"][
                "content"
            ]["application/json"].update(
                {
                    "schema": {
                        "type": "object",
                        "properties": {"name": {"type": "string"}},
                    }
                }
            ),
            "structured object schemas must be named components",
        ),
        (
            lambda document: document["components"]["schemas"]["CustomTool"]["properties"].update(
                {
                    "inline": {
                        "type": "object",
                        "properties": {"value": {"type": "string"}},
                    }
                }
            ),
            "structured object schemas must be named components",
        ),
        (
            lambda document: document["components"]["schemas"].update(
                {
                    "InlineItems": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {"value": {"type": "string"}},
                        },
                    }
                }
            ),
            "structured object schemas must be named components",
        ),
        (
            lambda document: document["paths"]["/custom-tools/{name}"]["get"][
                "responses"
            ].__setitem__(
                "200",
                {
                    "description": "Inline object",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {"value": {"type": "string"}},
                            }
                        }
                    },
                },
            ),
            "structured object schemas must be named components",
        ),
        *(
            (
                lambda document, additional=additional: document["components"]["schemas"][
                    "CustomTool"
                ].__setitem__("additionalProperties", additional),
                "object schemas with properties must set additionalProperties to false",
            )
            for additional in (True, {"type": "string"})
        ),
        (
            lambda document: document["components"]["schemas"]["CustomTool"].pop(
                "additionalProperties"
            ),
            "object schemas with properties must set additionalProperties to false",
        ),
        (
            lambda document: document["components"]["schemas"].__setitem__(
                "CustomTool",
                {
                    "anyOf": [
                        document["components"]["schemas"]["CustomTool"],
                        {"type": "null"},
                    ]
                },
            ),
            "named object schemas cannot be nullable",
        ),
        (
            lambda document: document["components"]["schemas"].update(
                {"Empty": {"type": "object", "additionalProperties": False}}
            ),
            "closed empty object schemas are not supported",
        ),
        (
            lambda document: document["paths"]["/custom-tools/{name}"]["get"]["responses"].update(
                {"201": {"description": "Also successful"}}
            ),
            "exactly one successful response is required",
        ),
        (
            lambda document: document.update({"webhooks": {}}),
            "document fields are not supported",
        ),
        (
            lambda document: document.update(
                {"jsonSchemaDialect": "https://example.com/custom-dialect"}
            ),
            "only the standard OpenAPI and JSON Schema dialects are supported",
        ),
        (
            lambda document: document["info"].update({"contact": {"name": "Support"}}),
            "info fields are not supported",
        ),
        (
            lambda document: document["servers"][0].update({"variables": {}}),
            "server fields are not supported",
        ),
        (
            lambda document: document["components"].update({"callbacks": {}}),
            "components fields are not supported",
        ),
        (
            lambda document: document["components"]["securitySchemes"]["ApiKeyAuth"].update(
                {"scheme": "bearer"}
            ),
            "security scheme fields are not supported",
        ),
        (
            lambda document: document["paths"]["/custom-tools/{name}"].update({"trace": {}}),
            "path item fields are not supported",
        ),
        (
            lambda document: document["paths"]["/custom-tools/{name}"]["get"]["parameters"][
                0
            ].update({"style": "deepObject"}),
            "non-default parameter style is not supported",
        ),
        (
            lambda document: document["paths"]["/custom-tools/{name}"]["get"]["parameters"][
                0
            ].update({"explode": False}),
            "non-default parameter explode is not supported",
        ),
        (
            lambda document: document["paths"]["/custom-tools/{name}"]["get"]["parameters"][
                0
            ].update({"allowReserved": True}),
            "allowReserved parameters are not supported",
        ),
        (
            lambda document: document["components"]["schemas"]["CustomTool"]["properties"].update(
                {"tags": {"type": "array", "items": {"type": "string"}, "uniqueItems": True}}
            ),
            "schema keywords are not supported",
        ),
        (
            lambda document: document["paths"]["/custom-tools/{name}"]["get"].update(
                {"servers": [{"url": "https://other.example/api"}]}
            ),
            "operation fields are not supported",
        ),
        (
            lambda document: document["paths"]["/custom-tools/{name}"]["patch"][
                "requestBody"
            ].update({"encoding": {}}),
            "request body fields are not supported",
        ),
        (
            lambda document: document["components"]["responses"]["CustomToolResponse"].update(
                {"headers": {"x-request-id": {"schema": {"type": "string"}}}}
            ),
            "response fields are not supported",
        ),
        (
            lambda document: document["components"]["responses"]["CustomToolResponse"]["content"][
                "application/json"
            ].update({"encoding": {}}),
            "media type fields are not supported",
        ),
        (
            lambda document: document["components"]["schemas"]["CustomTool"]["properties"].update(
                {"shape": {"type": "object", "const": {"x": 1}}}
            ),
            "must be a JSON scalar",
        ),
        (
            lambda document: document["components"]["schemas"]["CustomTool"]["properties"].update(
                {"choice": {"type": "string", "enum": ["a", "b"], "const": "a"}}
            ),
            "schemas cannot combine enum and const",
        ),
        (
            lambda document: document["components"]["schemas"]["CustomTool"]["properties"].update(
                {"ratio": {"type": "number", "enum": [1.5]}}
            ),
            "number enums cannot be represented faithfully",
        ),
        (
            lambda document: document["components"]["schemas"]["CustomTool"]["properties"].update(
                {"ratio": {"type": "number", "enum": [1]}}
            ),
            "number enums cannot be represented faithfully",
        ),
        (
            lambda document: document["components"]["schemas"]["CustomTool"]["properties"].update(
                {"ratio": {"type": "number", "const": 1.5}}
            ),
            "number consts cannot be represented faithfully",
        ),
        (
            lambda document: document["components"]["schemas"]["CustomTool"]["properties"].update(
                {"ratio": {"type": "number", "const": 1}}
            ),
            "number consts cannot be represented faithfully",
        ),
        (
            lambda document: document["paths"]["/custom-tools/{name}"]["get"]["parameters"][
                0
            ].update({"required": "yes"}),
            "must be a boolean",
        ),
        (
            lambda document: document["paths"]["/custom-tools/{name}"]["get"]["parameters"].append(
                {
                    "name": "includeVersions",
                    "in": "query",
                    "schema": {"type": "boolean"},
                }
            ),
            "duplicate parameter",
        ),
        (
            lambda document: document["components"]["schemas"]["CustomTool"]["properties"].update(
                {
                    "brokenNullable": {
                        "anyOf": [
                            {"type": "string"},
                            {"type": "null", "const": "not-null"},
                        ]
                    }
                }
            ),
            "nullable branch must be exactly",
        ),
        (
            lambda document: document["paths"]["/custom-tools/{name}"]["get"]["responses"][
                "200"
            ].update({"description": "override"}),
            "reference siblings are not supported",
        ),
    ],
)
def test_profile_rejects_unsupported_constructs(mutate, message: str) -> None:
    document = deepcopy(_document())
    mutate(document)

    with pytest.raises(ProfileViolation, match=message):
        validate_profile(document)


def test_operation_parameters_override_path_parameters() -> None:
    document = _document()
    document["paths"]["/custom-tools/{name}"]["get"]["parameters"].append(
        {
            "name": "name",
            "in": "path",
            "required": True,
            "description": "Operation-specific description",
            "schema": {"type": "string", "pattern": "^[a-z0-9-]+$"},
        }
    )

    operation = normalize(document).operations[0]

    assert (
        len([parameter for parameter in operation.parameters if parameter.wire_name == "name"]) == 1
    )
    assert operation.parameters[0].description == "Operation-specific description"


def test_explicit_empty_response_content_is_bodyless() -> None:
    document = _document()
    responses = document["paths"]["/custom-tools/{name}"]["get"]["responses"]
    responses.pop("200")
    responses["204"] = {
        "description": "No content",
        "content": {},
    }

    api = normalize(document)

    response = next(item for item in api.operations[0].responses if item.status == "204")
    assert response.schema is None


def test_nullable_schema_preserves_inner_annotations() -> None:
    document = _document()
    document["components"]["schemas"]["CustomTool"]["properties"]["sourceRef"] = {
        "anyOf": [
            {"type": "string", "description": "Source revision", "default": "pending"},
            {"type": "null"},
        ]
    }

    source_ref = normalize(document).schemas[0].schema.fields[2].schema

    assert source_ref.description == "Source revision"
    assert source_ref.has_default is True
    assert source_ref.default == "pending"
