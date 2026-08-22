#!/usr/bin/env python3
"""Check that the vendored contract matches its immutable backend provenance lock."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import re


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    spec = root / "openapi" / "custom-tools-v1.json"
    lock = json.loads((root / "openapi" / "custom-tools-v1.lock.json").read_text())
    if lock != {
        "artifactSha256": lock.get("artifactSha256"),
        "schemaVersion": 1,
        "sourceCommit": lock.get("sourceCommit"),
        "sourcePath": "backend/app/public_api/openapi/custom-tools-v1.generated.json",
        "sourceRepository": "Tamarind-Bio/tamarind-website",
    }:
        raise SystemExit("custom-tools-v1.lock.json has an unsupported shape or source")
    if re.fullmatch(r"[0-9a-f]{40}", str(lock["sourceCommit"])) is None:
        raise SystemExit("sourceCommit must be a full immutable Git commit SHA")
    actual = sha256(spec.read_bytes()).hexdigest()
    if actual != lock["artifactSha256"]:
        raise SystemExit(
            "custom-tools-v1.json does not match its provenance lock: "
            f"expected {lock['artifactSha256']}, got {actual}"
        )


if __name__ == "__main__":
    main()
