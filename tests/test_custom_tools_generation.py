from __future__ import annotations

from pathlib import Path
import json
import subprocess
import sys


def test_openapi_extraction_uses_the_public_path_boundary(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    operation = {
        "operationId": "listCustomTools",
        "responses": {"200": {"description": "ok"}},
    }
    spec = {
        "openapi": "3.1.0",
        "info": {"title": "test", "version": "1"},
        "paths": {
            "/custom-tools": {"get": operation},
            "/custom-tools/{name}": {"get": {**operation, "operationId": "getCustomTool"}},
            "/custom-tools-preview": {"get": operation},
            "/molecules": {"get": operation},
        },
        "components": {"schemas": {}, "responses": {}, "securitySchemes": {}},
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

    assert set(sliced["paths"]) == {"/custom-tools", "/custom-tools/{name}"}


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


def test_readable_version_routes_accept_queued_build_handles() -> None:
    root = Path(__file__).resolve().parents[1]
    spec = json.loads((root / "openapi/custom-tools-v1.json").read_text())
    readable_paths = (
        "/custom-tools/{name}/versions/{version_name}",
        "/custom-tools/{name}/versions/{version_name}/logs",
    )

    for path in readable_paths:
        parameters = spec["paths"][path]["get"]["parameters"]
        version = next(item for item in parameters if item["name"] == "version_name")
        assert "queued-" in version["schema"]["pattern"]
