from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

from tamarind_codegen.custom_tools import ProfileViolation, normalize, validate_profile
from tamarind_codegen.custom_tools.json_loader import load_json_document
from tamarind_codegen.custom_tools.project import project_custom_tools


def _producer_checkout(tmp_path: Path, source: bytes) -> tuple[Path, Path, str]:
    checkout = tmp_path / "producer"
    artifact = checkout / "backend/app/public_api/openapi/public-v1.generated.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_bytes(source)
    commands = [
        ["git", "init", str(checkout)],
        ["git", "-C", str(checkout), "config", "user.name", "Contract Test"],
        ["git", "-C", str(checkout), "config", "user.email", "contract@example.com"],
        [
            "git",
            "-C",
            str(checkout),
            "remote",
            "add",
            "origin",
            "https://github.com/Tamarind-Bio/tamarind-website.git",
        ],
        ["git", "-C", str(checkout), "add", "."],
        ["git", "-C", str(checkout), "commit", "-m", "Add contract"],
    ]
    for command in commands:
        subprocess.run(command, check=True, capture_output=True)
    commit = subprocess.run(
        ["git", "-C", str(checkout), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    return checkout, artifact, commit


def test_cli_projection_is_idempotent_for_the_vendored_custom_tools_spec() -> None:
    root = Path(__file__).resolve().parents[1]
    document = json.loads((root / "openapi/public-v1.json").read_text())
    projected = project_custom_tools(document)

    assert projected == document
    assert all(
        "custom-tools" in operation["tags"]
        for path_item in projected["paths"].values()
        for method, operation in path_item.items()
        if method in {"delete", "get", "patch", "post", "put"}
    )
    assert "PublicCustomTool" in projected["components"]["schemas"]
    assert "PublicPipeline" not in projected["components"]["schemas"]


def test_contract_entrypoints_reject_duplicate_json_members(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    checkout, spec, commit = _producer_checkout(tmp_path, b'{"openapi":"3.1.0","openapi":"3.1.1"}')

    with pytest.raises(ValueError, match="duplicate JSON object member"):
        load_json_document(spec.read_bytes())

    commands = [
        [sys.executable, str(root / "scripts/validate_custom_tools_openapi.py"), str(spec)],
        [
            sys.executable,
            str(root / "scripts/generate_custom_tools_transport.py"),
            str(spec),
            str(tmp_path / "generated.py"),
        ],
        [
            sys.executable,
            str(root / "scripts/sync_custom_tools_contract.py"),
            str(spec),
            "--source-checkout",
            str(checkout),
            "--source-repository",
            "Tamarind-Bio/tamarind-website",
            "--source-commit",
            commit,
            "--root",
            str(tmp_path / "sync-root"),
        ],
    ]
    for command in commands:
        result = subprocess.run(command, capture_output=True, text=True)
        assert result.returncode != 0
        assert "duplicate JSON object member" in result.stderr


@pytest.mark.parametrize(
    "raw",
    [
        '{"value":1e400}',
        '{"value":NaN}',
        '{"value":1e-400}',
        '{"value":-1e-400}',
        '{"value":0.123456789012345678901}',
        '{"value":9007199254740993.0}',
    ],
)
def test_strict_contract_loader_rejects_unrepresentable_numbers(raw: str) -> None:
    with pytest.raises(ValueError):
        load_json_document(raw)


def test_projection_removes_unrelated_operations_from_a_complete_spec() -> None:
    root = Path(__file__).resolve().parents[1]
    document = json.loads((root / "openapi/public-v1.json").read_text())
    document["paths"]["/health"] = {
        "get": {
            "operationId": "health",
            "responses": {"200": {"description": "ok"}},
            "tags": ["system"],
        }
    }

    projected = project_custom_tools(document)

    assert "/health" not in projected["paths"]
    assert len(projected["paths"]) < len(document["paths"])


@pytest.mark.parametrize("tags", ["not-custom-tools-extra", ["custom-tools", 1]])
def test_projection_rejects_malformed_operation_tags(tags: object) -> None:
    root = Path(__file__).resolve().parents[1]
    document = json.loads((root / "openapi/public-v1.json").read_text())
    document["paths"]["/custom-tools/{name}"]["get"]["tags"] = tags

    with pytest.raises(ValueError, match="tags must be an array of strings"):
        project_custom_tools(document)


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


def test_projection_preserves_tagged_unsupported_methods_for_profile_rejection() -> None:
    root = Path(__file__).resolve().parents[1]
    document = json.loads((root / "openapi/public-v1.json").read_text())
    operation = document["paths"]["/custom-tools/{name}"]["get"].copy()
    operation["operationId"] = "headCustomTool"
    document["paths"]["/custom-tools/{name}"]["head"] = operation

    projected = project_custom_tools(document)

    assert "head" in projected["paths"]["/custom-tools/{name}"]
    with pytest.raises(ProfileViolation, match="path item fields are not supported"):
        validate_profile(projected)


def test_projection_preserves_path_semantics_for_profile_rejection() -> None:
    root = Path(__file__).resolve().parents[1]
    document = json.loads((root / "openapi/public-v1.json").read_text())
    document["paths"]["/custom-tools/{name}"]["servers"] = [{"url": "https://other.example/api"}]

    projected = project_custom_tools(document)

    assert "servers" in projected["paths"]["/custom-tools/{name}"]
    with pytest.raises(ProfileViolation, match="path item fields are not supported"):
        validate_profile(projected)


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

    module_spec = importlib.util.spec_from_file_location("generated_unicode_property", generated)
    assert module_spec is not None and module_spec.loader is not None
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)

    assert "K" in module.PublicCreateCustomToolRequest.__annotations__


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


@pytest.mark.parametrize(
    "name",
    [
        "str",
        "int",
        "float",
        "bool",
        "list",
        "dict",
        "quote",
        "HTTPClient",
        "TypedDict",
        "GeneratedCustomToolsTransport",
    ],
)
def test_generated_models_reject_names_owned_by_the_emitter(tmp_path: Path, name: str) -> None:
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


@pytest.mark.parametrize("name", ["GpuType", "MemorySize"])
def test_generated_models_reject_names_that_shadow_property_aliases(
    tmp_path: Path, name: str
) -> None:
    root = Path(__file__).resolve().parents[1]
    document = json.loads((root / "openapi/public-v1.json").read_text(encoding="utf-8"))
    document["components"]["schemas"][name] = {"type": "string"}
    document["components"]["schemas"]["PublicCustomTool"]["properties"]["shadowed"] = {
        "$ref": f"#/components/schemas/{name}"
    }
    spec = tmp_path / "shadowed-property-alias.json"
    generated = tmp_path / "generated_shadowed_property_alias.py"
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

    assert generated.read_text() == (root / "src/tamarind/custom_tools/generated.py").read_text()


def test_contract_sync_writes_the_canonical_generated_transport(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    checkout, source, commit = _producer_checkout(
        tmp_path, (root / "openapi/public-v1.json").read_bytes()
    )
    subprocess.run(
        [
            sys.executable,
            str(root / "scripts/sync_custom_tools_contract.py"),
            str(source),
            "--source-checkout",
            str(checkout),
            "--source-repository",
            "Tamarind-Bio/tamarind-website",
            "--source-commit",
            commit,
            "--root",
            str(tmp_path),
        ],
        check=True,
    )

    assert (tmp_path / "src/tamarind/custom_tools/generated.py").read_text() == (
        root / "src/tamarind/custom_tools/generated.py"
    ).read_text()


def test_contract_sync_leaves_committed_artifacts_unchanged_when_generation_fails(
    tmp_path: Path,
) -> None:
    root = Path(__file__).resolve().parents[1]
    document = json.loads((root / "openapi/public-v1.json").read_text())
    first_operation = next(
        operation
        for path_item in document["paths"].values()
        for method, operation in path_item.items()
        if method in {"delete", "get", "patch", "post", "put"}
    )
    first_operation["operationId"] = "123"
    source = tmp_path / "invalid.json"
    source_bytes = json.dumps(document).encode()
    checkout, source, commit = _producer_checkout(tmp_path, source_bytes)
    targets = {
        "openapi/public-v1.json": "old spec\n",
        "openapi/public-v1.lock.json": "old lock\n",
        "src/tamarind/custom_tools/generated.py": "old generated\n",
    }
    for relative, content in targets.items():
        target = tmp_path / "root" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(root / "scripts/sync_custom_tools_contract.py"),
            str(source),
            "--source-checkout",
            str(checkout),
            "--source-repository",
            "Tamarind-Bio/tamarind-website",
            "--source-commit",
            commit,
            "--root",
            str(tmp_path / "root"),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    for relative, content in targets.items():
        assert (tmp_path / "root" / relative).read_text() == content


@pytest.mark.parametrize(
    ("argument", "value", "message"),
    [
        ("--source-repository", "Tamarind-Bio/website", "source repository"),
        ("--source-path", "backend/openapi.json", "source path"),
        ("--source-commit", "abc123", "source commit"),
        ("--source-commit", "A" * 40, "source commit"),
        ("--source-commit", "g" * 40, "source commit"),
    ],
)
def test_contract_sync_rejects_invalid_provenance_before_writing_outputs(
    tmp_path: Path,
    argument: str,
    value: str,
    message: str,
) -> None:
    root = Path(__file__).resolve().parents[1]
    targets = {
        "openapi/public-v1.json": "old spec\n",
        "openapi/public-v1.lock.json": "old lock\n",
        "src/tamarind/custom_tools/generated.py": "old generated\n",
    }
    for relative, content in targets.items():
        target = tmp_path / "root" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    command = [
        sys.executable,
        str(root / "scripts/sync_custom_tools_contract.py"),
        str(root / "openapi/public-v1.json"),
        "--source-checkout",
        str(root),
        "--source-repository",
        "Tamarind-Bio/tamarind-website",
        "--source-commit",
        "a" * 40,
        "--root",
        str(tmp_path / "root"),
        argument,
        value,
    ]

    result = subprocess.run(command, capture_output=True, text=True)

    assert result.returncode != 0
    assert message in result.stderr
    for relative, content in targets.items():
        assert (tmp_path / "root" / relative).read_text() == content


@pytest.mark.parametrize("mismatch", ["commit", "artifact", "origin"])
def test_contract_sync_verifies_the_checked_out_backend_before_writing(
    tmp_path: Path, mismatch: str
) -> None:
    root = Path(__file__).resolve().parents[1]
    source_bytes = (root / "openapi/public-v1.json").read_bytes()
    checkout, source, commit = _producer_checkout(tmp_path, source_bytes)
    if mismatch == "commit":
        commit = "0" * 40
    elif mismatch == "artifact":
        source.write_bytes(source_bytes + b"\n")
    else:
        subprocess.run(
            ["git", "-C", str(checkout), "remote", "set-url", "origin", "https://example.com/x"],
            check=True,
        )
    output_root = tmp_path / "output"

    result = subprocess.run(
        [
            sys.executable,
            str(root / "scripts/sync_custom_tools_contract.py"),
            str(source),
            "--source-checkout",
            str(checkout),
            "--source-repository",
            "Tamarind-Bio/tamarind-website",
            "--source-commit",
            commit,
            "--root",
            str(output_root),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert not output_root.exists()


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
