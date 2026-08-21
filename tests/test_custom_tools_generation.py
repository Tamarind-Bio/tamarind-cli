from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys


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


def test_openapi_artifact_matches_pinned_provenance() -> None:
    root = Path(__file__).resolve().parents[1]
    artifact = root / "openapi/custom-tools-v1.json"
    provenance = json.loads((root / "openapi/custom-tools-v1.provenance.json").read_text())

    assert provenance["repository"] == "Tamarind-Bio/tamarind-website"
    assert len(provenance["revision"]) == 40
    assert provenance["path"] == "backend/app/public_api/openapi/custom-tools-v1.generated.json"
    # Git may check text files out with platform-native line endings. The
    # provenance digest is over the canonical LF bytes stored in Git.
    canonical = artifact.read_text().replace("\r\n", "\n").encode()
    assert hashlib.sha256(canonical).hexdigest() == provenance["sha256"]


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


def test_all_version_routes_require_numbered_handles() -> None:
    root = Path(__file__).resolve().parents[1]
    spec = json.loads((root / "openapi/custom-tools-v1.json").read_text())
    for path, item in spec["paths"].items():
        if "{version_name}" not in path:
            continue
        for operation in item.values():
            if not isinstance(operation, dict) or "parameters" not in operation:
                continue
            version = next(
                value for value in operation["parameters"] if value["name"] == "version_name"
            )
            assert version["schema"]["pattern"] == r"^v[1-9][0-9]*$"
