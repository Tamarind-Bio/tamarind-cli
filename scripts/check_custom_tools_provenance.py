#!/usr/bin/env python3
"""Verify the exact backend artifact, generator pin, and immutable provenance lock."""

from hashlib import sha256
import json
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    spec = root / "openapi/public-v1.json"
    lock = json.loads((root / "openapi/public-v1.lock.json").read_text())
    expected = {
        "artifactSha256",
        "generator",
        "schemaVersion",
        "sourceCommit",
        "sourcePath",
        "sourceRepository",
    }
    if set(lock) != expected or lock["schemaVersion"] != 2:
        raise SystemExit("public-v1.lock.json has an unsupported shape")
    if lock["generator"] != "openapi-python-client==0.28.4":
        raise SystemExit("generated client does not use the pinned generator")
    if lock["sourceRepository"] != "Tamarind-Bio/tamarind-website" or lock["sourcePath"] != (
        "backend/app/public_api/openapi/custom-tools-v1.generated.json"
    ):
        raise SystemExit("unsupported Custom Tools producer")
    if sha256(spec.read_bytes()).hexdigest() != lock["artifactSha256"]:
        raise SystemExit("public-v1.json does not match its provenance lock")


if __name__ == "__main__":
    main()
