#!/usr/bin/env python3
"""Check that the vendored contract matches its immutable backend provenance lock."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

from tamarind_codegen.custom_tools.provenance import validate_source_provenance


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    spec = root / "openapi" / "public-v1.json"
    lock = json.loads((root / "openapi" / "public-v1.lock.json").read_text())
    expected_fields = {
        "artifactSha256",
        "schemaVersion",
        "sourceCommit",
        "sourcePath",
        "sourceRepository",
    }
    if not isinstance(lock, dict) or set(lock) != expected_fields or lock.get("schemaVersion") != 1:
        raise SystemExit("public-v1.lock.json has an unsupported shape or source")
    try:
        validate_source_provenance(
            lock["sourceRepository"],
            lock["sourceCommit"],
            lock["sourcePath"],
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    actual = sha256(spec.read_bytes()).hexdigest()
    if actual != lock["artifactSha256"]:
        raise SystemExit(
            "public-v1.json does not match its provenance lock: "
            f"expected {lock['artifactSha256']}, got {actual}"
        )


if __name__ == "__main__":
    main()
