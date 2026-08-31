"""Command contract tests for the unified ``tamarind custom-tools`` surface."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from typer.testing import CliRunner

from tamarind.cli.main import State, app
from tamarind.custom_tools.resources import BuildError, BuildLogPage, BuildEvent, Page
from tamarind.custom_tools._generated.models.public_build_result_action import (
    PublicBuildResultAction,
)
from tamarind.custom_tools.transport import (
    GpuType,
    MemorySize,
    PublicCustomToolStatus,
    PublicVersionStatus,
)
from tamarind.errors import CustomToolBuildTimeoutError


runner = CliRunner()
ENV = {
    "TAMARIND_API_KEY": "test-key",
    "TAMARIND_API_BASE": "https://api.test/",
}
VERSION_ID = "df82ad10-2639-4576-a117-46ec736b9f52"


def _tool(**overrides):
    values = {
        "name": "fold-local",
        "generation": "generation-1",
        "display_name": "Fold Local",
        "description": "A local folding tool",
        "functions": ("structure-prediction",),
        "status": PublicCustomToolStatus.DEPLOYED,
        "gpu_type": GpuType.A10,
        "memory": MemorySize.VALUE_2,
        "cpu": 4,
        "home_disk_gi": 20,
        "max_runtime_seconds": 3600,
        "has_source": True,
        "source_digest": "sha256:abc",
        "published": True,
        "auto_publish": False,
        "est_time": "5m",
        "paper_url": "",
        "tags": ("folding",),
        "default_version": "v3",
        "created_at": "2026-08-30T00:00:00Z",
        "updated_at": "2026-08-31T00:00:00Z",
        "can_edit": True,
        "can_build": True,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


class FakeVersion:
    def __init__(self, *, terminal: bool = False, status=PublicVersionStatus.RUNNING):
        self.id = VERSION_ID
        self.name = "v3"
        self.source_revision = "revision-3"
        self.source_digest = "sha256:abc"
        self.status = status
        self.terminal = terminal
        self.origin = "upload"
        self.created_at = "2026-08-31T00:00:00Z"
        self.started_at = "2026-08-31T00:00:01Z"
        self.completed_at = None
        self.error = None
        self.tool_name = "fold-local"
        self.tool_generation = "generation-1"
        self.monitor_args = None
        self.cancelled = False
        self.published = False

    def monitor(self, **kwargs):
        self.monitor_args = kwargs
        self.status = PublicVersionStatus.COMPLETE
        self.terminal = True
        self.completed_at = "2026-08-31T00:05:00Z"
        return self

    def logs(self, *, cursor=None):
        assert cursor == "cursor-1"
        return BuildLogPage(
            items=(BuildEvent(message="building", timestamp=123),),
            status=self.status,
            next_cursor="cursor-2",
            error=BuildError(code="notice", message="still working"),
        )

    def cancel(self):
        self.cancelled = True
        return self

    def publish(self):
        self.published = True
        return _tool(default_version=self.name)


class FakeTool:
    def __init__(self, version: FakeVersion):
        self._version = version
        self.built = None
        self.deleted = False

    def __getattr__(self, name):
        return getattr(_tool(), name)

    def get_version(self, version_id):
        assert version_id == VERSION_ID
        return self._version

    def versions(self, **kwargs):
        return Page((self._version,), next_cursor="next-versions")

    def build(self, folder: Path, *, idempotency_key=None):
        self.built = (folder, idempotency_key)
        return SimpleNamespace(action=PublicBuildResultAction.BUILD, version=self._version)

    def update(self, **kwargs):
        self.updated = kwargs
        return self

    def delete(self):
        self.deleted = True


class FakeCustomTools:
    def __init__(self, tool: FakeTool):
        self.tool = tool
        self.get_names = []
        self.created = None

    def list(self, **kwargs):
        return Page((self.tool,), next_cursor="next-tools")

    def get(self, name):
        self.get_names.append(name)
        return self.tool

    def create(self, name, **kwargs):
        self.created = (name, kwargs)
        return self.tool


class FakeSDK:
    def __init__(self):
        self.version = FakeVersion()
        self.custom_tools = FakeCustomTools(FakeTool(self.version))

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return None


def _install_sdk(monkeypatch) -> FakeSDK:
    sdk = FakeSDK()
    monkeypatch.setattr(State, "sdk_client", lambda _state: sdk)
    return sdk


def test_list_is_machine_readable_and_preserves_cursor(monkeypatch):
    _install_sdk(monkeypatch)

    result = runner.invoke(app, ["--json", "custom-tools", "list"], env=ENV)

    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    assert payload["items"][0]["name"] == "fold-local"
    assert payload["items"][0]["gpuType"] == "A10"
    assert payload["nextCursor"] == "next-tools"


def test_build_waits_through_sdk_and_returns_opaque_version_id(monkeypatch, tmp_path):
    sdk = _install_sdk(monkeypatch)
    (tmp_path / "Dockerfile").write_text("FROM scratch\n")

    result = runner.invoke(
        app,
        [
            "--json",
            "custom-tools",
            "build",
            "fold-local",
            str(tmp_path),
            "--idempotency-key",
            "release-1",
            "--wait",
            "--timeout",
            "9",
            "--poll-interval",
            "0.5",
        ],
        env=ENV,
    )

    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    assert payload["action"] == "build"
    assert payload["version"]["id"] == VERSION_ID
    assert payload["version"]["status"] == "Complete"
    assert sdk.custom_tools.tool.built == (tmp_path.resolve(), "release-1")
    assert sdk.version.monitor_args["timeout"] == 9
    assert sdk.version.monitor_args["interval"] == 0.5
    assert sdk.version.monitor_args["on_event"] is None


def test_version_wait_reattaches_by_opaque_id(monkeypatch):
    sdk = _install_sdk(monkeypatch)

    result = runner.invoke(
        app,
        ["--json", "custom-tools", "version", "fold-local", VERSION_ID, "--wait"],
        env=ENV,
    )

    assert result.exit_code == 0, result.stdout
    assert json.loads(result.stdout)["terminal"] is True
    assert sdk.custom_tools.get_names == ["fold-local"]


def test_build_wait_error_keeps_durable_reattachment_handle(monkeypatch, tmp_path):
    sdk = _install_sdk(monkeypatch)
    (tmp_path / "Dockerfile").write_text("FROM scratch\n")

    def timeout(**_kwargs):
        raise CustomToolBuildTimeoutError("local wait expired")

    sdk.version.monitor = timeout
    result = runner.invoke(
        app,
        ["--json", "custom-tools", "build", "fold-local", str(tmp_path), "--wait"],
        env=ENV,
    )

    assert isinstance(result.exception, CustomToolBuildTimeoutError)
    assert result.exception.detail == {
        "toolName": "fold-local",
        "versionId": VERSION_ID,
        "versionName": "v3",
        "action": "build",
    }


def test_logs_return_resume_cursor(monkeypatch):
    _install_sdk(monkeypatch)

    result = runner.invoke(
        app,
        [
            "--json",
            "custom-tools",
            "logs",
            "fold-local",
            VERSION_ID,
            "--cursor",
            "cursor-1",
        ],
        env=ENV,
    )

    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    assert payload["items"] == [{"message": "building", "timestamp": 123}]
    assert payload["nextCursor"] == "cursor-2"


def test_cancel_requires_explicit_confirmation_in_json_mode(monkeypatch):
    sdk = _install_sdk(monkeypatch)

    refused = runner.invoke(
        app, ["--json", "custom-tools", "cancel", "fold-local", VERSION_ID], env=ENV
    )
    allowed = runner.invoke(
        app,
        ["--json", "custom-tools", "cancel", "fold-local", VERSION_ID, "--yes"],
        env=ENV,
    )

    assert refused.exit_code == 2
    assert sdk.version.cancelled is True
    assert allowed.exit_code == 0, allowed.stdout


def test_delete_requires_explicit_confirmation_in_json_mode(monkeypatch):
    sdk = _install_sdk(monkeypatch)

    refused = runner.invoke(app, ["--json", "custom-tools", "delete", "fold-local"], env=ENV)
    allowed = runner.invoke(
        app, ["--json", "custom-tools", "delete", "fold-local", "--yes"], env=ENV
    )

    assert refused.exit_code == 2
    assert allowed.exit_code == 0, allowed.stdout
    assert json.loads(allowed.stdout) == {"ok": True, "name": "fold-local"}
    assert sdk.custom_tools.tool.deleted is True


def test_local_validation_uses_stable_validation_exit_code(tmp_path):
    result = runner.invoke(
        app, ["--json", "custom-tools", "validate", str(tmp_path)], env=ENV
    )

    assert result.exit_code == 5
    payload = json.loads(result.stdout)
    assert payload["valid"] is False
    assert payload["errors"][0]["code"] == "required_file_missing"
