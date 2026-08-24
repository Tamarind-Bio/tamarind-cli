#!/usr/bin/env python3
"""Vendor the backend-owned slice and regenerate with the pinned mature generator."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory

EXPECTED_REPOSITORY = "Tamarind-Bio/tamarind-website"
EXPECTED_PATH = "backend/app/public_api/openapi/custom-tools-v1.generated.json"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--source-checkout", required=True, type=Path)
    parser.add_argument("--source-repository", required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--source-path", default=EXPECTED_PATH)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    _validate_provenance(args.source_repository, args.source_commit, args.source_path)
    checkout_file = args.source_checkout / args.source_path
    raw = args.source.read_bytes()
    if checkout_file.read_bytes() != raw:
        parser.error("source bytes do not match the declared producer checkout")
    document = json.loads(raw)
    if not document.get("paths") or not all(
        path.startswith("/custom-tools") for path in document["paths"]
    ):
        parser.error("source is not the dedicated Custom Tools artifact")

    spec_path = args.root / "openapi/public-v1.json"
    lock_path = args.root / "openapi/public-v1.lock.json"
    target = args.root / "src/tamarind/custom_tools/_generated"
    spec_path.write_bytes(raw)
    lock_path.write_text(
        json.dumps(
            {
                "artifactSha256": sha256(raw).hexdigest(),
                "generator": "openapi-python-client==0.28.4",
                "schemaVersion": 2,
                "sourceCommit": args.source_commit,
                "sourcePath": args.source_path,
                "sourceRepository": args.source_repository,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    with TemporaryDirectory() as directory:
        generated = Path(directory) / "generated"
        subprocess.run(
            [
                "openapi-python-client",
                "generate",
                "--path",
                str(spec_path),
                "--config",
                str(args.root / "openapi/openapi-python-client.json"),
                "--meta",
                "none",
                "--output-path",
                str(generated),
                "--overwrite",
            ],
            check=True,
            cwd=args.root,
        )
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(generated, target, ignore=shutil.ignore_patterns(".ruff_cache"))


def _validate_provenance(repository: str, commit: str, path: str) -> None:
    if repository != EXPECTED_REPOSITORY or path != EXPECTED_PATH:
        raise SystemExit("unsupported Custom Tools producer")
    if len(commit) != 40 or any(character not in "0123456789abcdef" for character in commit):
        raise SystemExit("source commit must be a full lowercase Git SHA")


if __name__ == "__main__":
    main()
