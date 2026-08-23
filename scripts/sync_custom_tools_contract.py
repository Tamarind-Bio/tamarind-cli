#!/usr/bin/env python3
"""Vendor a backend-produced contract, record provenance, and regenerate transport code."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from generate_custom_tools_transport import write_generated_transport
from tamarind_codegen.custom_tools.json_loader import load_json_document
from tamarind_codegen.custom_tools.profile import validate_profile
from tamarind_codegen.custom_tools.project import project_custom_tools
from tamarind_codegen.custom_tools.provenance import SOURCE_PATH, validate_source_provenance


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--source-repository", required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument(
        "--source-path",
        default=SOURCE_PATH,
    )
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()

    try:
        validate_source_provenance(
            args.source_repository,
            args.source_commit,
            args.source_path,
        )
    except ValueError as exc:
        parser.error(str(exc))

    raw = args.source.read_bytes()
    document = load_json_document(raw)
    projection = project_custom_tools(document)
    validate_profile(projection)
    projected = (json.dumps(projection, indent=2, sort_keys=True) + "\n").encode()

    spec_path = args.root / "openapi" / "public-v1.json"
    lock_path = args.root / "openapi" / "public-v1.lock.json"
    generated_path = args.root / "src" / "tamarind" / "custom_tools" / "generated.py"
    lock = (
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
        + "\n"
    )
    with TemporaryDirectory() as staging_dir:
        staged_generated = Path(staging_dir) / "generated.py"
        write_generated_transport(projection, staged_generated)
        generated = staged_generated.read_text(encoding="utf-8")

    spec_path.parent.mkdir(parents=True, exist_ok=True)
    generated_path.parent.mkdir(parents=True, exist_ok=True)
    spec_path.write_bytes(projected)
    lock_path.write_text(lock, encoding="utf-8")
    generated_path.write_text(generated, encoding="utf-8")


if __name__ == "__main__":
    main()
