#!/usr/bin/env python3
"""Verify the exact backend artifact, generator pin, and immutable provenance lock."""

from hashlib import sha256
import json
from pathlib import Path

from sync_custom_tools_contract import _contract_metadata


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
    expected_metadata = _contract_metadata(json.loads(spec.read_text()))
    metadata = root / "src/tamarind/custom_tools/_contract.py"
    if metadata.read_text() != expected_metadata:
        raise SystemExit("runtime contract metadata is stale")

    pipelines_spec = root / "openapi/pipelines-v1.json"
    pipelines_lock = json.loads((root / "openapi/pipelines-v1.lock.json").read_text())
    if set(pipelines_lock) != expected or pipelines_lock["schemaVersion"] != 1:
        raise SystemExit("pipelines-v1.lock.json has an unsupported shape")
    if pipelines_lock["generator"] != "openapi-python-client==0.28.4":
        raise SystemExit("Pipelines client does not use the pinned generator")
    if pipelines_lock["sourceRepository"] != "Tamarind-Bio/tamarind-website" or pipelines_lock[
        "sourcePath"
    ] != "backend/app/public_api/openapi/public-v1.generated.json":
        raise SystemExit("unsupported Pipelines producer")
    if sha256(pipelines_spec.read_bytes()).hexdigest() != pipelines_lock["artifactSha256"]:
        raise SystemExit("pipelines-v1.json does not match its provenance lock")


if __name__ == "__main__":
    main()
