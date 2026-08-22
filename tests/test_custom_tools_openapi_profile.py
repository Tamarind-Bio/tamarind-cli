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
                {"name": "trace", "in": "header", "schema": {"type": "string"}}
            ),
            "only path and query parameters are supported",
        ),
        (lambda document: document.update({"webhooks": {}}), "webhooks are not supported"),
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
