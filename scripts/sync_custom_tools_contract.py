#!/usr/bin/env python3
"""Vendor the backend-owned slice and regenerate with the pinned mature generator."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
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
    raw = args.source.read_bytes()
    _verify_committed_source(args.source_checkout, args.source_commit, args.source_path, raw)
    document = json.loads(raw)
    if not document.get("paths") or not all(
        path.startswith("/custom-tools") for path in document["paths"]
    ):
        parser.error("source is not the dedicated Custom Tools artifact")

    spec_path = args.root / "openapi/public-v1.json"
    lock_path = args.root / "openapi/public-v1.lock.json"
    metadata_path = args.root / "src/tamarind/custom_tools/_contract.py"
    target = args.root / "src/tamarind/custom_tools/_generated"
    with TemporaryDirectory(dir=args.root) as directory:
        staging = Path(directory)
        staged_spec = staging / "public-v1.json"
        staged_lock = staging / "public-v1.lock.json"
        staged_metadata = staging / "_contract.py"
        generated = staging / "generated"
        staged_spec.write_bytes(raw)
        staged_lock.write_text(
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
        staged_metadata.write_text(_contract_metadata(document))
        subprocess.run(
            [
                "openapi-python-client",
                "generate",
                "--path",
                str(staged_spec),
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
        cache = generated / ".ruff_cache"
        if cache.exists():
            shutil.rmtree(cache)
        _install_staged(
            staging,
            (
                (staged_spec, spec_path),
                (staged_lock, lock_path),
                (staged_metadata, metadata_path),
                (generated, target),
            ),
        )


def _validate_provenance(repository: str, commit: str, path: str) -> None:
    if repository != EXPECTED_REPOSITORY or path != EXPECTED_PATH:
        raise SystemExit("unsupported Custom Tools producer")
    if len(commit) != 40 or any(character not in "0123456789abcdef" for character in commit):
        raise SystemExit("source commit must be a full lowercase Git SHA")


def _verify_committed_source(checkout: Path, commit: str, path: str, raw: bytes) -> None:
    resolved = _git(checkout, "rev-parse", "--verify", f"{commit}^{{commit}}").decode().strip()
    if resolved != commit:
        raise SystemExit("source commit does not resolve exactly in the producer checkout")
    origin = _git(checkout, "remote", "get-url", "origin").decode().strip()
    if _repository_slug(origin) != EXPECTED_REPOSITORY:
        raise SystemExit("producer checkout origin does not match the declared repository")
    if _git(checkout, "show", f"{commit}:{path}") != raw:
        raise SystemExit("source bytes do not match the artifact at the declared commit")


def _git(checkout: Path, *arguments: str) -> bytes:
    try:
        return subprocess.run(
            ["git", "-C", str(checkout), *arguments],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ).stdout
    except subprocess.CalledProcessError as exc:
        message = exc.stderr.decode(errors="replace").strip()
        raise SystemExit(f"cannot verify producer Git provenance: {message}") from None


def _repository_slug(origin: str) -> str:
    normalized = origin.removesuffix(".git")
    for prefix in ("git@github.com:", "https://github.com/", "ssh://git@github.com/"):
        if normalized.startswith(prefix):
            return normalized.removeprefix(prefix)
    return ""


def _contract_metadata(document: dict[str, object]) -> str:
    servers = document.get("servers")
    if not isinstance(servers, list) or not servers or not isinstance(servers[0], dict):
        raise SystemExit("Custom Tools contract must declare a default server")
    server = servers[0].get("url")
    if not isinstance(server, str) or not server:
        raise SystemExit("Custom Tools contract default server must be a non-empty URL")
    return (
        '"""Generated metadata from the backend-owned Custom Tools contract."""\n\n'
        f"OPENAPI_SERVER_URL = {server.rstrip('/') + '/'!r}\n"
    )


def _install_staged(staging: Path, replacements: tuple[tuple[Path, Path], ...]) -> None:
    backups: list[tuple[Path, Path]] = []
    installed: list[Path] = []
    try:
        for index, (_, destination) in enumerate(replacements):
            if destination.exists():
                backup = staging / f"backup-{index}"
                os.replace(destination, backup)
                backups.append((backup, destination))
        for source, destination in replacements:
            os.replace(source, destination)
            installed.append(destination)
    except Exception:
        for destination in reversed(installed):
            _remove(destination)
        for backup, destination in reversed(backups):
            os.replace(backup, destination)
        raise


def _remove(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


if __name__ == "__main__":
    main()
