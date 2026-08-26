from __future__ import annotations

import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


def test_vendored_contract_is_the_dedicated_backend_artifact() -> None:
    from sync_custom_tools_contract import _is_custom_tools_path

    document = json.loads((ROOT / "openapi/public-v1.json").read_text())
    assert document["paths"]
    assert all(_is_custom_tools_path(path) for path in document["paths"])
    assert all("/generations/" not in path for path in document["paths"])
    conditional_operations = {
        ("/custom-tools/{name}", "delete"),
        ("/custom-tools/{name}", "patch"),
        ("/custom-tools/{name}/versions", "post"),
        ("/custom-tools/{name}/versions/{version}:cancel", "post"),
        ("/custom-tools/{name}/versions/{version}:publish", "post"),
    }
    for path, item in document["paths"].items():
        for method, operation in item.items():
            if not isinstance(operation, dict):
                continue
            headers = [
                parameter
                for parameter in operation.get("parameters", [])
                if parameter.get("in") == "header"
            ]
            expected = ["If-Match"] if (path, method) in conditional_operations else []
            assert [header["name"] for header in headers] == expected
            assert all(header["required"] is True for header in headers)

    serialized = json.dumps(document)
    assert "X-Tamarind-If-Match" not in serialized
    assert "X-Tamarind-Tool-Generation" not in serialized


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


def test_transport_declares_the_success_status_of_every_model_operation() -> None:
    from tamarind.custom_tools.transport import _MODEL_OPERATIONS

    document = json.loads((ROOT / "openapi/public-v1.json").read_text())
    expected: dict[str, int] = {}
    for path_item in document["paths"].values():
        for operation in path_item.values():
            if not isinstance(operation, dict) or operation["operationId"] == "deleteCustomTool":
                continue
            name = re.sub(r"(?<!^)(?=[A-Z])", "_", operation["operationId"]).lower()
            success_statuses = [
                int(status) for status in operation["responses"] if status.startswith("2")
            ]
            assert len(success_statuses) == 1
            expected[name] = success_statuses[0]

    described = {
        operation.endpoint.__name__.rsplit(".", 1)[-1]: operation.success_status
        for operation in _MODEL_OPERATIONS
    }
    assert described == expected


def test_generator_is_exactly_pinned() -> None:
    pyproject = (ROOT / "pyproject.toml").read_text()
    lock = json.loads((ROOT / "openapi/public-v1.lock.json").read_text())
    assert '"openapi-python-client==0.28.4"' in pyproject
    assert lock["generator"] == "openapi-python-client==0.28.4"


def test_sync_rejects_duplicate_json_members() -> None:
    from sync_custom_tools_contract import _load_contract

    with pytest.raises(ValueError, match="duplicate JSON object member 'paths'"):
        _load_contract(b'{"paths": {}, "paths": {}}')


@pytest.mark.parametrize(
    ("path", "accepted"),
    [
        ("/custom-tools", True),
        ("/custom-tools/example", True),
        ("/custom-tools-admin", False),
        ("/custom-tool", False),
        ("/custom-tools/../admin", False),
        ("/custom-tools/%2e%2e/admin", False),
        ("/custom-tools/%ZZ", False),
        ("/custom-tools//admin", False),
        ("/custom-tools/admin;scope=all", False),
        ("/custom-tools/admin?scope=all", False),
        ("/custom-tools/admin#fragment", False),
        (r"/custom-tools/admin\escape", False),
        ("/custom-tools/{valid_name}", True),
        ("/custom-tools/{valid_name}:publish", True),
        ("/custom-tools/{invalid-name}", False),
        ("/custom-tools/{valid_name}:9invalid", False),
    ],
)
def test_dedicated_artifact_requires_the_custom_tools_path_segment(
    path: str, accepted: bool
) -> None:
    from sync_custom_tools_contract import _is_custom_tools_path

    assert _is_custom_tools_path(path) is accepted


@pytest.mark.parametrize(
    "server",
    [
        "https://example.test/api/",
        "https://example.test/api//",
    ],
)
def test_contract_metadata_preserves_the_declared_server(server: str) -> None:
    from sync_custom_tools_contract import _contract_metadata

    assert _contract_metadata(
        {
            "paths": {"/custom-tools": {}},
            "servers": [{"url": server}],
        }
    ) == (
        '"""Generated metadata from the backend-owned Custom Tools contract."""\n\n'
        f"OPENAPI_SERVER_URL = {server!r}\n"
    )


@pytest.mark.parametrize(
    "server",
    [
        "/api",
        "http://localhost:8000/api",
        "http://example.test/api",
        "ftp://example.test/api",
        "https:///api",
        "https://user:secret@example.test/api",
        "https://example.test/api?tenant=one",
        "https://example.test/api#fragment",
        "https://example.test/api/../admin",
        "https://example.test/api/%2e%2e/admin",
        "https://example.test/api/%ZZ",
        "https://example.test/api path",
        "https://example.test/{base}",
        "https://example.test:0/api",
    ],
)
def test_contract_metadata_rejects_an_unusable_default_server(server: str) -> None:
    from sync_custom_tools_contract import _contract_metadata

    with pytest.raises(SystemExit, match="usable absolute HTTP"):
        _contract_metadata(
            {
                "paths": {"/custom-tools": {}},
                "servers": [{"url": server}],
            }
        )


def test_sync_provenance_reads_the_declared_git_object(tmp_path: Path) -> None:
    from sync_custom_tools_contract import EXPECTED_PATH, _verify_committed_source

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
    import sync_custom_tools_contract as sync

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


def test_contract_install_restores_the_previous_generation_when_interrupted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import sync_custom_tools_contract as sync

    staging = tmp_path / "staging"
    staging.mkdir()
    destinations = tuple(tmp_path / name for name in ("spec", "lock", "metadata", "generated"))
    staged = tuple(staging / name for name in ("spec", "lock", "metadata", "generated"))
    for path in destinations + staged:
        path.write_text(f"{path.parent.name}:{path.name}")
    previous = [path.read_text() for path in destinations]

    real_replace = sync.os.replace
    install_calls = 0

    def interrupt_during_install(source: Path, destination: Path) -> None:
        nonlocal install_calls
        if source in staged:
            install_calls += 1
            if install_calls == 2:
                raise KeyboardInterrupt
        real_replace(source, destination)

    monkeypatch.setattr(sync.os, "replace", interrupt_during_install)
    with pytest.raises(KeyboardInterrupt):
        sync._install_staged(staging, tuple(zip(staged, destinations, strict=True)))

    assert [path.read_text() for path in destinations] == previous


def test_contract_sync_rejects_a_generated_package_incompatible_with_the_facade(
    tmp_path: Path,
) -> None:
    from sync_custom_tools_contract import _verify_generated_facade

    staging = tmp_path / "staging"
    generated = staging / "generated"
    staging.mkdir()
    source = ROOT / "src/tamarind/custom_tools/_generated"
    shutil.copytree(source, generated)
    (generated / "models/public_version.py").unlink()

    with pytest.raises(subprocess.CalledProcessError):
        _verify_generated_facade(
            ROOT,
            generated,
            ROOT / "src/tamarind/custom_tools/_contract.py",
            staging,
        )


def test_contract_sync_exercises_generated_endpoint_signatures(
    tmp_path: Path,
) -> None:
    from sync_custom_tools_contract import _verify_generated_facade

    staging = tmp_path / "staging"
    generated = staging / "generated"
    staging.mkdir()
    source = ROOT / "src/tamarind/custom_tools/_generated"
    shutil.copytree(source, generated)
    endpoint = generated / "api/custom_tools/list_custom_tool_versions.py"
    original = endpoint.read_text()
    mutated = original.replace(
        "    name: str,\n    *,",
        "    name: str,\n    required_probe: str,\n    *,",
        1,
    )
    assert mutated != original
    endpoint.write_text(mutated)

    with pytest.raises(subprocess.CalledProcessError):
        _verify_generated_facade(
            ROOT,
            generated,
            ROOT / "src/tamarind/custom_tools/_contract.py",
            staging,
        )
