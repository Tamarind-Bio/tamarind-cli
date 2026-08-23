#!/usr/bin/env python3
"""Vendor a backend-produced contract, record provenance, and regenerate transport code."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

from generate_custom_tools_transport import write_generated_transport
from tamarind_codegen.custom_tools.json_loader import load_json_document
from tamarind_codegen.custom_tools.profile import validate_profile
from tamarind_codegen.custom_tools.project import project_custom_tools


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--source-repository", required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument(
        "--source-path",
        default="backend/app/public_api/openapi/public-v1.generated.json#tag=custom-tools",
    )
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()

    raw = args.source.read_bytes()
    document = load_json_document(raw)
    projection = project_custom_tools(document)
    validate_profile(projection)
    projected = (json.dumps(projection, indent=2, sort_keys=True) + "\n").encode()

    spec_path = args.root / "openapi" / "public-v1.json"
    lock_path = args.root / "openapi" / "public-v1.lock.json"
    generated_path = args.root / "src" / "tamarind" / "custom_tools" / "generated.py"
    spec_path.parent.mkdir(parents=True, exist_ok=True)
    spec_path.write_bytes(projected)
    lock_path.write_text(
        json.dumps(
            {
                "artifactSha256": sha256(projected).hexdigest(),
                "schemaVersion": 1,
                "sourceCommit": args.source_commit,
                "sourcePath": args.source_path,
                "sourceRepository": args.source_repository,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    write_generated_transport(projection, generated_path)


if __name__ == "__main__":
    main()
