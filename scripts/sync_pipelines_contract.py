#!/usr/bin/env python3
"""Project and vendor the typed Pipelines read contract from tamarind-website."""

from __future__ import annotations

import argparse
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory
from sync_custom_tools_contract import (
    EXPECTED_REPOSITORY,
    _load_contract,
    _verify_committed_source,
)

EXPECTED_PATH = "backend/app/public_api/openapi/public-v1.generated.json"
PIPELINE_PATHS = (
    "/pipelines/runs/{run_id}",
    "/pipelines/runs/{run_id}/node-runs/{node_run_id}/molecules",
)
EXPECTED_OPERATIONS = {"getRun", "listNodeRunMolecules"}


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
    raw = args.source.read_bytes()
    _verify_committed_source(args.source_checkout, args.source_commit, args.source_path, raw)
    projected = _project_contract(_load_contract(raw))
    projected_raw = (json.dumps(projected, indent=2, sort_keys=True) + "\n").encode()

    spec_path = args.root / "openapi/pipelines-v1.json"
    lock_path = args.root / "openapi/pipelines-v1.lock.json"
    target = args.root / "src/tamarind/pipelines/_generated"
    with TemporaryDirectory(dir=args.root) as directory:
        staging = Path(directory)
        staged_spec = staging / "pipelines-v1.json"
        staged_lock = staging / "pipelines-v1.lock.json"
        generated = staging / "generated"
        staged_spec.write_bytes(projected_raw)
        staged_lock.write_text(
            json.dumps(
                {
                    "artifactSha256": sha256(projected_raw).hexdigest(),
                    "generator": "openapi-python-client==0.28.4",
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
        subprocess.run(
            [
                "openapi-python-client",
                "generate",
                "--path",
                str(staged_spec),
                "--config",
                str(args.root / "openapi/pipelines-openapi-python-client.json"),
                "--meta",
                "none",
                "--output-path",
                str(generated),
                "--overwrite",
            ],
            check=True,
            cwd=args.root,
        )
        cache = generated / ".ruff_cache"
        if cache.exists():
            shutil.rmtree(cache)
        _replace(staged_spec, spec_path)
        _replace(staged_lock, lock_path)
        _replace(generated, target)


def _project_contract(document: dict[str, object]) -> dict[str, object]:
    paths = document.get("paths")
    if not isinstance(paths, dict) or any(path not in paths for path in PIPELINE_PATHS):
        raise SystemExit("producer contract is missing a required Pipelines path")

    selected_paths = {path: deepcopy(paths[path]) for path in PIPELINE_PATHS}
    operation_ids = {
        operation.get("operationId")
        for path_item in selected_paths.values()
        if isinstance(path_item, dict)
        for operation in path_item.values()
        if isinstance(operation, dict) and "responses" in operation
    }
    if operation_ids != EXPECTED_OPERATIONS:
        raise SystemExit("producer contract has unexpected Pipelines operations")

    components = document.get("components")
    if not isinstance(components, dict):
        raise SystemExit("producer contract has no components")
    projected_components: dict[str, dict[str, object]] = {}
    pending = list(_refs(selected_paths))
    visited: set[str] = set()
    while pending:
        ref = pending.pop()
        if ref in visited:
            continue
        visited.add(ref)
        parts = ref.split("/")
        if len(parts) != 4 or parts[:2] != ["#", "components"]:
            raise SystemExit(f"unsupported contract reference: {ref}")
        category, name = parts[2], parts[3]
        category_values = components.get(category)
        if not isinstance(category_values, dict) or name not in category_values:
            raise SystemExit(f"unresolved contract reference: {ref}")
        value = deepcopy(category_values[name])
        projected_components.setdefault(category, {})[name] = value
        pending.extend(_refs(value))

    projected = {
        "openapi": document.get("openapi"),
        "info": deepcopy(document.get("info")),
        "servers": deepcopy(document.get("servers")),
        "paths": selected_paths,
        "components": projected_components,
    }
    _validate_projection(projected)
    return projected


def _validate_provenance(repository: str, commit: str, path: str) -> None:
    if repository != EXPECTED_REPOSITORY or path != EXPECTED_PATH:
        raise SystemExit("unsupported Pipelines producer")
    if len(commit) != 40 or any(character not in "0123456789abcdef" for character in commit):
        raise SystemExit("source commit must be a full lowercase Git SHA")


def _refs(value: object) -> set[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        for key, member in value.items():
            if key == "$ref" and isinstance(member, str):
                found.add(member)
            else:
                found.update(_refs(member))
    elif isinstance(value, list):
        for member in value:
            found.update(_refs(member))
    return found


def _validate_projection(document: dict[str, object]) -> None:
    paths = document.get("paths")
    if not isinstance(paths, dict) or tuple(paths) != PIPELINE_PATHS:
        raise SystemExit("Pipelines projection contains unexpected paths")
    if any(not path.startswith("/pipelines/") for path in paths):
        raise SystemExit("Pipelines projection escaped its API namespace")


def _replace(source: Path, target: Path) -> None:
    if target.is_dir():
        shutil.rmtree(target)
    elif target.exists():
        target.unlink()
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        shutil.copytree(source, target)
    else:
        shutil.copyfile(source, target)


if __name__ == "__main__":
    main()
