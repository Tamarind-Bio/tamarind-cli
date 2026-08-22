from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

from tamarind_codegen.custom_tools import normalize
from tamarind_codegen.custom_tools.project import project_custom_tools


def test_cli_projects_custom_tools_from_the_complete_public_spec() -> None:
    root = Path(__file__).resolve().parents[1]
    document = json.loads((root / "openapi/public-v1.json").read_text())
    projected = project_custom_tools(document)

    assert len(projected["paths"]) < len(document["paths"])
    assert all(
        "custom-tools" in operation["tags"]
        for path_item in projected["paths"].values()
        for method, operation in path_item.items()
        if method in {"delete", "get", "patch", "post", "put"}
    )
    assert "PublicCustomTool" in projected["components"]["schemas"]
    assert "PublicPipeline" not in projected["components"]["schemas"]


def test_projection_resolves_local_path_item_references() -> None:
    root = Path(__file__).resolve().parents[1]
    document = json.loads((root / "openapi/public-v1.json").read_text())
    path = "/custom-tools/{name}"
    path_item = document["paths"][path]
    document["components"].setdefault("pathItems", {})["CustomToolItem"] = path_item
    document["paths"][path] = {"$ref": "#/components/pathItems/CustomToolItem"}

    projected = project_custom_tools(document)

    assert set(projected["paths"][path]) == {"delete", "get", "patch"}


def test_projection_rejects_unsupported_path_item_references() -> None:
    root = Path(__file__).resolve().parents[1]
    document = json.loads((root / "openapi/public-v1.json").read_text())
    document["paths"]["/custom-tools/{name}"] = {"$ref": "https://example.com/path-item.json"}

    with pytest.raises(ValueError, match="local components/pathItems"):
        project_custom_tools(document)


def test_generated_property_aliases_follow_referenced_components(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    document = json.loads((root / "openapi/public-v1.json").read_text())
    custom_tool = document["components"]["schemas"]["PublicCustomTool"]
    create_tool = document["components"]["schemas"]["PublicCreateCustomToolRequest"]
    update_tool = document["components"]["schemas"]["PublicUpdateCustomToolRequest"]
    gpu_schema = custom_tool["properties"]["gpuType"]
    document["components"]["schemas"]["SharedGpuType"] = gpu_schema
    for model in (custom_tool, create_tool, update_tool):
        model["properties"]["gpuType"] = {"$ref": "#/components/schemas/SharedGpuType"}
    spec = tmp_path / "referenced-alias.json"
    generated = tmp_path / "generated_referenced_alias.py"
    spec.write_text(json.dumps(document), encoding="utf-8")

    subprocess.run(
        [
            sys.executable,
            str(root / "scripts/generate_custom_tools_transport.py"),
            str(spec),
            str(generated),
        ],
        check=True,
    )
    source = generated.read_text(encoding="utf-8")

    assert source.index("SharedGpuType: TypeAlias") < source.index("GpuType: TypeAlias")
    subprocess.run([sys.executable, str(generated)], check=True)


def test_property_aliases_ignore_documentation_metadata(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    document = json.loads((root / "openapi/public-v1.json").read_text())
    custom_tool = document["components"]["schemas"]["PublicCustomTool"]
    custom_tool["properties"]["gpuType"]["description"] = "GPU requested by the tool"
    spec = tmp_path / "documented_alias.json"
    generated = tmp_path / "generated_documented_alias.py"
    spec.write_text(json.dumps(document), encoding="utf-8")

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


def test_generated_models_preserve_non_identifier_wire_keys(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    document = json.loads((root / "openapi/public-v1.json").read_text(encoding="utf-8"))
    model = document["components"]["schemas"]["PublicCreateCustomToolRequest"]
    model["properties"]["K"] = {"type": "string"}
    spec = tmp_path / "unicode-property.json"
    generated = tmp_path / "generated_unicode_property.py"
    spec.write_text(json.dumps(document), encoding="utf-8")

    subprocess.run(
        [
            sys.executable,
            str(root / "scripts/generate_custom_tools_transport.py"),
            str(spec),
            str(generated),
        ],
        check=True,
    )

    assert "'K': NotRequired[str]" in generated.read_text(encoding="utf-8")


def test_generated_models_reject_nfkc_ambiguous_schema_names(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    document = json.loads((root / "openapi/public-v1.json").read_text(encoding="utf-8"))
    document["components"]["schemas"]["K"] = {"type": "string"}
    document["components"]["schemas"]["PublicCustomTool"]["properties"]["ambiguous"] = {
        "$ref": "#/components/schemas/K"
    }
    spec = tmp_path / "unicode-schema.json"
    generated = tmp_path / "generated_unicode_schema.py"
    spec.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(subprocess.CalledProcessError):
        subprocess.run(
            [
                sys.executable,
                str(root / "scripts/generate_custom_tools_transport.py"),
                str(spec),
                str(generated),
            ],
            check=True,
            capture_output=True,
        )


@pytest.mark.parametrize("name", ["str", "int", "float", "bool", "list", "dict"])
def test_generated_models_reject_names_that_shadow_annotation_builtins(
    tmp_path: Path, name: str
) -> None:
    root = Path(__file__).resolve().parents[1]
    document = json.loads((root / "openapi/public-v1.json").read_text(encoding="utf-8"))
    document["components"]["schemas"][name] = {"type": "string"}
    document["components"]["schemas"]["PublicCustomTool"]["properties"]["shadowed"] = {
        "$ref": f"#/components/schemas/{name}"
    }
    spec = tmp_path / "shadowed-builtin.json"
    generated = tmp_path / "generated_shadowed_builtin.py"
    spec.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(subprocess.CalledProcessError):
        subprocess.run(
            [
                sys.executable,
                str(root / "scripts/generate_custom_tools_transport.py"),
                str(spec),
                str(generated),
            ],
            check=True,
            capture_output=True,
        )


def test_current_openapi_normalizes_to_the_expected_surface() -> None:
    root = Path(__file__).resolve().parents[1]
    api = normalize(project_custom_tools(json.loads((root / "openapi/public-v1.json").read_text())))

    assert len(api.schemas) == 15
    assert {operation.operation_id for operation in api.operations} == {
        "cancelCustomToolBuild",
        "createCustomTool",
        "createCustomToolUpload",
        "deleteCustomTool",
        "buildCustomToolVersion",
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
            str(root / "openapi/public-v1.json"),
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
            str(root / "openapi/public-v1.json"),
            str(generated),
        ],
        check=True,
    )
    module_spec = importlib.util.spec_from_file_location("generated_transport", generated)
    assert module_spec is not None and module_spec.loader is not None
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)

    assert module.OPENAPI_SERVER_URL == "https://app.tamarind.bio/api/"
    assert hasattr(module.GeneratedCustomToolsTransport, "build_custom_tool_version")
    assert hasattr(module.GeneratedCustomToolsTransport, "delete_custom_tool")
    assert hasattr(module.GeneratedCustomToolsTransport, "get_custom_tool_version_async")


def test_generated_optional_fields_have_runtime_typed_dict_metadata() -> None:
    from tamarind.custom_tools.generated import PublicCreateCustomToolRequest

    assert PublicCreateCustomToolRequest.__required_keys__ == frozenset({"name"})
    assert PublicCreateCustomToolRequest.__optional_keys__ == frozenset(
        {"cpu", "description", "displayName", "gpuType", "memory"}
    )


def test_generated_aliases_follow_schema_dependency_order(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    document = json.loads((root / "openapi/public-v1.json").read_text())
    schemas = document["components"]["schemas"]
    document["components"]["schemas"] = {
        "PublicVersionList": {
            "type": "array",
            "items": {"$ref": "#/components/schemas/PublicVersion"},
        },
        **schemas,
    }
    build_result = document["components"]["schemas"]["PublicBuildResult"]
    build_result["properties"]["versions"] = {"$ref": "#/components/schemas/PublicVersionList"}
    build_result["required"].append("versions")
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
    document = json.loads((root / "openapi/public-v1.json").read_text())
    for path in (
        "/custom-tools/{name}/versions/{version_name}",
        "/custom-tools/{name}/versions/{version_name}/logs",
    ):
        parameters = document["paths"][path]["get"]["parameters"]
        version = next(item for item in parameters if item["name"] == "version_name")
        assert version["schema"]["pattern"] == "^v[1-9][0-9]*$"
