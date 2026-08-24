from __future__ import annotations

import json
from pathlib import Path
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[1]


def test_vendored_contract_is_the_dedicated_backend_artifact() -> None:
    document = json.loads((ROOT / "openapi/public-v1.json").read_text())
    assert document["paths"]
    assert all(path.startswith("/custom-tools") for path in document["paths"])
    assert not any(
        parameter.get("name") == "If-Match"
        for path, item in document["paths"].items()
        if "/generations/{generation}/" in path
        for operation in item.values()
        if isinstance(operation, dict)
        for parameter in operation.get("parameters", [])
    )


def test_generated_client_contains_sync_async_endpoints_and_attrs_models() -> None:
    from tamarind.custom_tools._generated.api.custom_tools import get_custom_tool_version
    from tamarind.custom_tools._generated.models.public_version import PublicVersion

    assert callable(get_custom_tool_version.sync)
    assert callable(get_custom_tool_version.asyncio)
    assert callable(PublicVersion.from_dict)
    assert callable(PublicVersion.to_dict)


def test_public_wire_enums_are_the_generated_contract_types() -> None:
    from tamarind.custom_tools._generated.models.public_custom_tool_gputype import (
        PublicCustomToolGputype,
    )
    from tamarind.custom_tools._generated.models.public_custom_tool_memory import (
        PublicCustomToolMemory,
    )
    from tamarind.custom_tools._generated.models.public_custom_tool_status import (
        PublicCustomToolStatus,
    )
    from tamarind.custom_tools._generated.models.public_version_status import PublicVersionStatus
    from tamarind.custom_tools.transport import GpuType, MemorySize
    from tamarind.custom_tools.transport import PublicCustomToolStatus as ExportedToolStatus
    from tamarind.custom_tools.transport import PublicVersionStatus as ExportedVersionStatus

    assert GpuType is PublicCustomToolGputype
    assert MemorySize is PublicCustomToolMemory
    assert ExportedToolStatus is PublicCustomToolStatus
    assert ExportedVersionStatus is PublicVersionStatus


def test_generator_is_exactly_pinned() -> None:
    pyproject = (ROOT / "pyproject.toml").read_text()
    lock = json.loads((ROOT / "openapi/public-v1.lock.json").read_text())
    assert '"openapi-python-client==0.28.4"' in pyproject
    assert lock["generator"] == "openapi-python-client==0.28.4"


def test_sync_provenance_reads_the_declared_git_object(tmp_path: Path) -> None:
    from scripts.sync_custom_tools_contract import EXPECTED_PATH, _verify_committed_source

    artifact = tmp_path / EXPECTED_PATH
    artifact.parent.mkdir(parents=True)
    artifact.write_bytes(b"committed contract")
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "remote", "add", "origin", "https://github.com/Tamarind-Bio/tamarind-website.git"],
        cwd=tmp_path,
        check=True,
    )
    subprocess.run(["git", "add", EXPECTED_PATH], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "contract"], cwd=tmp_path, check=True)
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=tmp_path, check=True, capture_output=True, text=True
    ).stdout.strip()

    _verify_committed_source(tmp_path, commit, EXPECTED_PATH, b"committed contract")
    artifact.write_bytes(b"working tree contract")
    with pytest.raises(SystemExit, match="declared commit"):
        _verify_committed_source(tmp_path, commit, EXPECTED_PATH, b"working tree contract")


def test_contract_install_restores_the_previous_complete_generation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from scripts import sync_custom_tools_contract as sync

    staging = tmp_path / "staging"
    staging.mkdir()
    destinations = tuple(tmp_path / name for name in ("spec", "lock", "metadata", "generated"))
    staged = tuple(staging / name for name in ("spec", "lock", "metadata", "generated"))
    for path in destinations + staged:
        path.write_text(f"{path.parent.name}:{path.name}")
    previous = [path.read_text() for path in destinations]

    real_replace = sync.os.replace
    install_calls = 0

    def fail_during_install(source: Path, destination: Path) -> None:
        nonlocal install_calls
        if source in staged:
            install_calls += 1
            if install_calls == 2:
                raise OSError("injected install failure")
        real_replace(source, destination)

    monkeypatch.setattr(sync.os, "replace", fail_during_install)
    with pytest.raises(OSError, match="injected install failure"):
        sync._install_staged(staging, tuple(zip(staged, destinations, strict=True)))

    assert [path.read_text() for path in destinations] == previous
