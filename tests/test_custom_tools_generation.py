from __future__ import annotations

from pathlib import Path
import json
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
