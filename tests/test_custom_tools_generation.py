from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

from tamarind_codegen.custom_tools import normalize


def test_openapi_extraction_keeps_only_the_custom_tools_dependency_closure(
    tmp_path: Path,
) -> None:
    root = Path(__file__).resolve().parents[1]
    source = tmp_path / "public.json"
    output = tmp_path / "custom-tools.json"
    source.write_text(
        json.dumps(
            {
                "openapi": "3.1.0",
                "jsonSchemaDialect": "https://json-schema.org/draft/2020-12/schema",
                "info": {"title": "test", "version": "1"},
                "servers": [{"url": "https://app.tamarind.bio/api"}],
                "security": [{"ApiKey": []}],
                "paths": {
                    "/custom-tools": {
                        "get": {
                            "operationId": "listCustomTools",
                            "responses": {
                                "200": {"$ref": "#/components/responses/ToolResponse"},
                                "default": {"$ref": "#/components/responses/Error"},
                            },
                        }
                    },
                    "/custom-tools-preview": {
                        "get": {
                            "operationId": "previewCustomTools",
                            "responses": {"200": {"description": "preview"}},
                        }
                    },
                    "/jobs": {
                        "get": {
                            "operationId": "listJobs",
                            "responses": {"200": {"description": "jobs"}},
                        }
                    },
                },
                "components": {
                    "securitySchemes": {
                        "ApiKey": {"type": "apiKey", "in": "header", "name": "x-api-key"},
                        "Unused": {"type": "http", "scheme": "bearer"},
                    },
                    "responses": {
                        "ToolResponse": {
                            "description": "ok",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Tool"}
                                }
                            },
                        },
                        "Error": {
                            "description": "error",
                            "content": {
                                "application/problem+json": {
                                    "schema": {"$ref": "#/components/schemas/Nested"}
                                }
                            },
                        },
                        "Unused": {"description": "unused"},
                    },
                    "schemas": {
                        "Tool": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "default": {"$ref": "#/components/schemas/Nested"},
                            },
                            "required": ["name", "default"],
                        },
                        "Nested": {"type": "string"},
                        "Unused": {"type": "string"},
                    },
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

    sliced = json.loads(output.read_text())
    assert set(sliced["paths"]) == {"/custom-tools"}
    assert sliced["jsonSchemaDialect"] == "https://json-schema.org/draft/2020-12/schema"
    assert set(sliced["components"]["responses"]) == {"Error", "ToolResponse"}
    assert set(sliced["components"]["schemas"]) == {"Nested", "Tool"}
    assert set(sliced["components"]["securitySchemes"]) == {"ApiKey"}
    assert normalize(sliced).operations[0].operation_id == "listCustomTools"


def test_openapi_extraction_consumes_and_merges_path_item_components(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    source = tmp_path / "public.json"
    output = tmp_path / "custom-tools.json"
    source.write_text(
        json.dumps(
            {
                "openapi": "3.1.0",
                "info": {"title": "test", "version": "1"},
                "servers": [{"url": "https://app.tamarind.bio/api"}],
                "security": [{"ApiKey": []}],
                "paths": {
                    "/custom-tools": {
                        "$ref": "#/components/pathItems/CustomTools",
                        "post": {
                            "operationId": "createCustomTool",
                            "responses": {"201": {"description": "created"}},
                        },
                    }
                },
                "components": {
                    "pathItems": {
                        "CustomTools": {
                            "get": {
                                "operationId": "listCustomTools",
                                "responses": {"200": {"description": "ok"}},
                            }
                        }
                    },
                    "securitySchemes": {
                        "ApiKey": {"type": "apiKey", "in": "header", "name": "x-api-key"}
                    },
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

    sliced = json.loads(output.read_text())
    assert "pathItems" not in sliced["components"]
    assert {operation.operation_id for operation in normalize(sliced).operations} == {
        "createCustomTool",
        "listCustomTools",
    }


def test_openapi_extraction_rejects_conflicting_path_item_siblings(tmp_path: Path) -> None:
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
                        "$ref": "#/components/pathItems/CustomTools",
                        "get": {
                            "operationId": "replacement",
                            "responses": {"200": {"description": "replacement"}},
                        },
                    }
                },
                "components": {
                    "pathItems": {
                        "CustomTools": {
                            "get": {
                                "operationId": "listCustomTools",
                                "responses": {"200": {"description": "ok"}},
                            }
                        }
                    }
                },
            }
        )
    )

    with pytest.raises(subprocess.CalledProcessError):
        subprocess.run(
            [
                sys.executable,
                str(root / "scripts/extract_custom_tools_openapi.py"),
                str(source),
                str(output),
            ],
            check=True,
            capture_output=True,
        )


def test_property_aliases_ignore_documentation_metadata(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    document = json.loads((root / "openapi/custom-tools-v1.json").read_text())
    custom_tool = document["components"]["schemas"]["PublicCustomTool"]
    custom_tool["properties"]["gpuType"]["description"] = "GPU requested by the tool"
    spec = tmp_path / "documented_alias.json"
    generated = tmp_path / "generated_documented_alias.py"
    spec.write_text(json.dumps(document))

    subprocess.run(
        [
            sys.executable,
            str(root / "scripts/generate_custom_tools_transport.py"),
            str(spec),
            str(generated),
        ],
        check=True,
    )

    assert "GpuType: TypeAlias = Literal[" in generated.read_text()


def test_current_openapi_normalizes_to_the_expected_surface() -> None:
    root = Path(__file__).resolve().parents[1]
    api = normalize(json.loads((root / "openapi/custom-tools-v1.json").read_text()))

    assert len(api.schemas) == 17
    assert {operation.operation_id for operation in api.operations} == {
        "cancelCustomToolBuild",
        "createCustomTool",
        "createCustomToolUpload",
        "deployCustomTool",
        "finalizeCustomToolUpload",
        "getCustomTool",
        "getCustomToolVersion",
        "listCustomToolBuildLogs",
        "listCustomTools",
        "listCustomToolVersions",
        "publishCustomToolVersion",
        "updateCustomTool",
    }


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


def test_generated_transport_is_importable(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    generated = tmp_path / "generated_transport.py"
    subprocess.run(
        [
            sys.executable,
            str(root / "scripts/generate_custom_tools_transport.py"),
            str(root / "openapi/custom-tools-v1.json"),
            str(generated),
        ],
        check=True,
    )
    module_spec = importlib.util.spec_from_file_location("generated_transport", generated)
    assert module_spec is not None and module_spec.loader is not None
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)

    assert module.OPENAPI_SERVER_URL == "https://app.tamarind.bio/api/"
    assert hasattr(module.GeneratedCustomToolsTransport, "deploy_custom_tool")
    assert hasattr(module.GeneratedCustomToolsTransport, "get_custom_tool_version_async")


def test_generated_aliases_follow_schema_dependency_order(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    document = json.loads((root / "openapi/custom-tools-v1.json").read_text())
    schemas = document["components"]["schemas"]
    document["components"]["schemas"] = {
        "PublicVersionList": {
            "type": "array",
            "items": {"$ref": "#/components/schemas/PublicVersion"},
        },
        **schemas,
    }
    spec = tmp_path / "forward_alias.json"
    generated = tmp_path / "generated_forward_alias.py"
    spec.write_text(json.dumps(document))
    subprocess.run(
        [
            sys.executable,
            str(root / "scripts/generate_custom_tools_transport.py"),
            str(spec),
            str(generated),
        ],
        check=True,
    )

    module_spec = importlib.util.spec_from_file_location("generated_forward_alias", generated)
    assert module_spec is not None and module_spec.loader is not None
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)

    assert module.PublicVersionList == list[module.PublicVersion]


def test_version_routes_use_numbered_version_handles() -> None:
    root = Path(__file__).resolve().parents[1]
    document = json.loads((root / "openapi/custom-tools-v1.json").read_text())
    for path in (
        "/custom-tools/{name}/versions/{version_name}",
        "/custom-tools/{name}/versions/{version_name}/logs",
    ):
        parameters = document["paths"][path]["get"]["parameters"]
        version = next(item for item in parameters if item["name"] == "version_name")
        assert version["schema"]["pattern"] == "^v[1-9][0-9]*$"
