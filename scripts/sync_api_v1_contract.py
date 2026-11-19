#!/usr/bin/env python3
"""Vendor the Tamarind API v1 contract and regenerate its typed client.

The contract is ``documentation/api-redesign/openapi-v1.yaml`` in tamarind-website
(the v1 API served at ``https://api.tamarind.bio``). It is unrelated to
``openapi/public-v1.json``, the older Custom Tools spec.

Sync (after the contract changes)::

    git -C ../tamarind-website fetch origin ashok/api-v1-spec
    git -C ../tamarind-website show <sha>:documentation/api-redesign/openapi-v1.yaml > /tmp/v1.yaml
    uv run --extra dev python scripts/sync_api_v1_contract.py /tmp/v1.yaml \
        --source-checkout ../tamarind-website --source-commit <sha>

Check (CI)::

    uv run --extra dev python scripts/sync_api_v1_contract.py --check

The vendored YAML is byte-identical to the producer's file, and the client is
generated from it as it is: a generator warning (a skipped part of the contract)
fails both sync and check.
"""

from __future__ import annotations

import argparse
import filecmp
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory
from typing import Any

import yaml

from sync_custom_tools_contract import EXPECTED_REPOSITORY, _verify_committed_source

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_PATH = "documentation/api-redesign/openapi-v1.yaml"
GENERATOR = "openapi-python-client==0.28.4"
SPEC = Path("openapi/api-v1.yaml")
LOCK = Path("openapi/api-v1.lock.json")
CONFIG = Path("openapi/api-v1-openapi-python-client.json")
TARGET = Path("src/tamarind/v1/_generated")
METADATA = Path("src/tamarind/v1/_contract.py")
LOCK_KEYS = {
    "artifactSha256",
    "generator",
    "schemaVersion",
    "sourceCommit",
    "sourcePath",
    "sourceRepository",
}
HTTP_METHODS = {"get", "put", "post", "delete", "patch", "head", "options", "trace"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("source", type=Path, nargs="?")
    parser.add_argument("--check", action="store_true", help="verify the vendored client only")
    parser.add_argument("--source-checkout", type=Path)
    parser.add_argument("--source-repository", default=EXPECTED_REPOSITORY)
    parser.add_argument("--source-commit")
    parser.add_argument("--source-path", default=EXPECTED_PATH)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()

    if args.check:
        check(args.root)
        return
    if args.source is None or args.source_checkout is None or args.source_commit is None:
        parser.error("sync needs SOURCE, --source-checkout and --source-commit")
    sync(
        args.root,
        args.source.read_bytes(),
        checkout=args.source_checkout,
        repository=args.source_repository,
        commit=args.source_commit,
        path=args.source_path,
    )


def sync(
    root: Path, raw: bytes, *, checkout: Path, repository: str, commit: str, path: str
) -> None:
    if repository != EXPECTED_REPOSITORY or path != EXPECTED_PATH:
        raise SystemExit("unsupported API v1 producer")
    if len(commit) != 40 or any(character not in "0123456789abcdef" for character in commit):
        raise SystemExit("source commit must be a full lowercase Git SHA")
    _verify_committed_source(checkout, commit, path, raw)
    document = load_contract(raw)
    lock = {
        "artifactSha256": sha256(raw).hexdigest(),
        "generator": GENERATOR,
        "schemaVersion": 1,
        "sourceCommit": commit,
        "sourcePath": path,
        "sourceRepository": repository,
    }
    with TemporaryDirectory(dir=root) as directory:
        generated = generate(root, document, Path(directory))
        (root / SPEC).write_bytes(raw)
        (root / LOCK).write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n")
        target = root / TARGET
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(generated, target)
        (root / METADATA).write_text(contract_metadata(document))


def check(root: Path) -> None:
    raw = (root / SPEC).read_bytes()
    lock = json.loads((root / LOCK).read_text())
    if set(lock) != LOCK_KEYS or lock["schemaVersion"] != 1:
        raise SystemExit(f"{LOCK} has an unsupported shape")
    if lock["generator"] != GENERATOR:
        raise SystemExit("API v1 client does not use the pinned generator")
    if lock["sourceRepository"] != EXPECTED_REPOSITORY or lock["sourcePath"] != EXPECTED_PATH:
        raise SystemExit("unsupported API v1 producer")
    if sha256(raw).hexdigest() != lock["artifactSha256"]:
        raise SystemExit(f"{SPEC} does not match its provenance lock")
    document = load_contract(raw)
    with TemporaryDirectory(dir=root) as directory:
        generated = generate(root, document, Path(directory))
        differences = _differences(generated, root / TARGET)
    metadata = root / METADATA
    if not metadata.is_file() or metadata.read_text() != contract_metadata(document):
        differences.append(f"changed {METADATA}")
    if differences:
        listed = "\n  ".join(differences[:20])
        raise SystemExit(f"{TARGET} is stale; rerun scripts/sync_api_v1_contract.py:\n  {listed}")


def load_contract(raw: bytes) -> dict[str, Any]:
    document = yaml.safe_load(raw)
    if not isinstance(document, dict) or not str(document.get("openapi", "")).startswith("3.1"):
        raise SystemExit("API v1 contract must be an OpenAPI 3.1 document")
    if not isinstance(document.get("paths"), dict) or not document["paths"]:
        raise SystemExit("API v1 contract has no paths")
    return document


def operations(document: dict[str, Any]) -> list[tuple[str, str, dict[str, Any]]]:
    """Every (method, path, operation) in the contract, in document order."""
    found = []
    for path, item in document["paths"].items():
        for method, operation in item.items():
            if method in HTTP_METHODS and isinstance(operation, dict):
                found.append((method, path, operation))
    return found


def contract_metadata(document: dict[str, Any]) -> str:
    """What the generated request builders can't express, for the SDK to apply."""
    parameters = document.get("components", {}).get("parameters", {})
    comma_joined: dict[str, list[str]] = {}
    for _method, _path, operation in operations(document):
        for parameter in operation.get("parameters", []):
            if "$ref" in parameter:
                parameter = parameters[parameter["$ref"].rsplit("/", 1)[-1]]
            schema = parameter.get("schema", {})
            if (
                parameter.get("in") == "query"
                and parameter.get("explode") is False
                and parameter.get("style", "form") == "form"
                and schema.get("type") == "array"
            ):
                module = _snake(operation["operationId"])
                comma_joined.setdefault(module, []).append(parameter["name"])
    lines = [
        '"""Generated from openapi/api-v1.yaml by scripts/sync_api_v1_contract.py. Do not edit."""',
        "",
        "# Query parameters the contract declares `style: form, explode: false`, by generated",
        "# module: a list goes on the wire as one comma-joined value (`status=Running,Complete`).",
        "# The generated request builders send repeated keys instead, which the API reads as",
        "# only the last value.",
        "COMMA_JOINED_QUERY: dict[str, frozenset[str]] = {",
    ]
    for module in sorted(comma_joined):
        names = ", ".join(json.dumps(name) for name in sorted(comma_joined[module]))
        lines.append(f"    {json.dumps(module)}: frozenset({{{names}}}),")
    lines.append("}")
    return "\n".join(lines) + "\n"


def _snake(name: str) -> str:
    return "".join(f"_{c.lower()}" if c.isupper() else c for c in name).lstrip("_")


def generate(root: Path, document: dict[str, Any], staging: Path) -> Path:
    spec = staging / "api-v1.json"
    spec.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n")
    output = staging / "generated"
    completed = subprocess.run(
        [
            "openapi-python-client",
            "generate",
            "--path",
            str(spec),
            "--config",
            str(root / CONFIG),
            "--meta",
            "none",
            "--output-path",
            str(output),
            "--overwrite",
        ],
        check=True,
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    # A warning means the generator skipped part of the contract; never vendor that.
    if "Warning" in completed.stdout or "WARNING" in completed.stdout:
        raise SystemExit(f"openapi-python-client skipped part of the contract:\n{completed.stdout}")
    cache = output / ".ruff_cache"
    if cache.exists():
        shutil.rmtree(cache)
    return output


def _differences(expected: Path, actual: Path) -> list[str]:
    if not actual.is_dir():
        return [f"missing {actual}"]
    found: list[str] = []
    _compare(filecmp.dircmp(expected, actual, ignore=[".ruff_cache", "__pycache__"]), "", found)
    return found


def _compare(comparison: filecmp.dircmp[str], prefix: str, found: list[str]) -> None:
    found.extend(f"missing {prefix}{name}" for name in comparison.left_only)
    found.extend(f"unexpected {prefix}{name}" for name in comparison.right_only)
    _, mismatch, errors = filecmp.cmpfiles(
        comparison.left, comparison.right, comparison.common_files, shallow=False
    )
    found.extend(f"changed {prefix}{name}" for name in mismatch + errors)
    for name, sub in comparison.subdirs.items():
        _compare(sub, f"{prefix}{name}/", found)


if __name__ == "__main__":
    main()
