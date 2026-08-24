#!/usr/bin/env python3
"""Vendor the backend-owned slice and regenerate with the pinned mature generator."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
from typing import NoReturn
from urllib.parse import unquote, urlsplit

EXPECTED_REPOSITORY = "Tamarind-Bio/tamarind-website"
EXPECTED_PATH = "backend/app/public_api/openapi/custom-tools-v1.generated.json"
_PATH_SEGMENT = re.compile(r"(?:[A-Za-z0-9_-]+|\{[A-Za-z_][A-Za-z0-9_]*\})")
_MALFORMED_ESCAPE = re.compile(r"%(?![0-9A-Fa-f]{2})")


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
    document = _load_contract(raw)
    _validate_contract(document)

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
        _verify_generated_facade(args.root, generated, staged_metadata, staging)
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


def _is_custom_tools_path(path: object) -> bool:
    if not isinstance(path, str):
        return False
    segments = path.split("/")
    return (
        len(segments) >= 2
        and segments[:2] == ["", "custom-tools"]
        and all(_PATH_SEGMENT.fullmatch(segment) for segment in segments[2:])
    )


def _validate_contract(document: dict[str, object]) -> str:
    paths = document.get("paths")
    if (
        not isinstance(paths, dict)
        or not paths
        or not all(_is_custom_tools_path(path) for path in paths)
    ):
        raise SystemExit("source is not the dedicated Custom Tools artifact")
    return _default_server_url(document)


def _reject_json_constant(value: str) -> NoReturn:
    raise ValueError(f"non-standard JSON constant {value!r}")


def _object_without_duplicate_members(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for name, member in pairs:
        if name in value:
            raise ValueError(f"duplicate JSON object member {name!r}")
        value[name] = member
    return value


def _load_contract(raw: bytes) -> dict[str, object]:
    parsed = json.loads(
        raw,
        parse_constant=_reject_json_constant,
        object_pairs_hook=_object_without_duplicate_members,
    )
    if not isinstance(parsed, dict):
        raise ValueError("Custom Tools contract must be a JSON object")
    return parsed


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


def _default_server_url(document: dict[str, object]) -> str:
    servers = document.get("servers")
    if not isinstance(servers, list) or not servers or not isinstance(servers[0], dict):
        raise SystemExit("Custom Tools contract must declare a default server")
    server = servers[0].get("url")
    if not isinstance(server, str) or not server:
        raise SystemExit("Custom Tools contract default server must be a non-empty URL")
    if any(ord(character) <= 32 or ord(character) == 127 for character in server):
        raise SystemExit(
            "Custom Tools contract default server must be a usable absolute HTTP(S) URL"
        )
    try:
        parsed = urlsplit(server)
        port = parsed.port
    except ValueError:
        raise SystemExit(
            "Custom Tools contract default server must be a usable absolute HTTP(S) URL"
        ) from None
    if (
        parsed.scheme != "https"
        or parsed.hostname is None
        or port == 0
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or "%" in parsed.netloc
        or "{" in server
        or "}" in server
        or _MALFORMED_ESCAPE.search(server)
    ):
        raise SystemExit(
            "Custom Tools contract default server must be a usable absolute HTTP(S) URL"
        )
    for segment in parsed.path.split("/"):
        decoded = unquote(segment)
        if (
            decoded in {".", ".."}
            or any(delimiter in decoded for delimiter in "/\\?#")
            or any(ord(character) <= 32 or ord(character) == 127 for character in decoded)
        ):
            raise SystemExit(
                "Custom Tools contract default server must be a usable absolute HTTP(S) URL"
            )
    return server


def _contract_metadata(document: dict[str, object]) -> str:
    server = _validate_contract(document)
    return (
        '"""Generated metadata from the backend-owned Custom Tools contract."""\n\n'
        f"OPENAPI_SERVER_URL = {server!r}\n"
    )


def _verify_generated_facade(root: Path, generated: Path, metadata: Path, staging: Path) -> None:
    import_root = staging / "facade-import"
    package = import_root / "tamarind"
    shutil.copytree(
        root / "src/tamarind",
        package,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    generated_target = package / "custom_tools/_generated"
    shutil.rmtree(generated_target)
    shutil.copytree(generated, generated_target)
    shutil.copyfile(metadata, package / "custom_tools/_contract.py")
    environment = os.environ.copy()
    python_path = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = str(import_root) + (os.pathsep + python_path if python_path else "")
    # Importing the adapter catches removed modules and models, but not a regenerated
    # endpoint whose operation still exists with a changed call signature. Exercise every
    # adapter method while replacing only the HTTP boundary so contract synchronization
    # fails before an incompatible generated package is installed.
    probe = r"""
import asyncio
from types import SimpleNamespace

from tamarind.custom_tools.transport import GeneratedCustomToolsTransport


class ProbeTransport(GeneratedCustomToolsTransport):
    def __init__(self):
        self._client = SimpleNamespace(
            request=lambda **_kwargs: SimpleNamespace(status_code=204)
        )

    def _sync(self, _operation, _kwargs, _timeout=None):
        return {}

    async def _async(self, _operation, _kwargs, _timeout=None):
        return {}


transport = ProbeTransport()
transport.list_custom_tools()
transport.create_custom_tool({"name": "contract-probe"})
transport.delete_custom_tool("contract-probe", "generation")
transport.get_custom_tool("contract-probe")
transport.update_custom_tool("contract-probe", "generation", {})
transport.create_custom_tool_upload("contract-probe", "generation")
transport.list_custom_tool_versions("contract-probe", "generation")
transport.build_custom_tool_version(
    "contract-probe",
    "generation",
    {
        "uploadId": "upload",
        "expectedSourceDigest": "sha256:" + "0" * 64,
    },
)
transport.get_custom_tool_version("contract-probe", "v1", "generation")
transport.cancel_custom_tool_build("contract-probe", "v1", "generation")
transport.list_custom_tool_build_logs("contract-probe", "v1", "generation")
transport.publish_custom_tool_version("contract-probe", "v1", "generation")


async def exercise_async_facade():
    await transport.get_custom_tool_version_async(
        "contract-probe", "v1", "generation"
    )
    await transport.list_custom_tool_build_logs_async(
        "contract-probe", "v1", "generation"
    )


asyncio.run(exercise_async_facade())
"""
    subprocess.run(
        [sys.executable, "-c", probe],
        check=True,
        cwd=staging,
        env=environment,
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
    except BaseException:
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
