from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest
import respx

from tamarind import Tamarind
from tamarind.custom_tools import BuildEvent
from tamarind.custom_tools import resources
from tamarind.errors import (
    CustomToolBuildFailedError,
    CustomToolBuildTimeoutError,
    CustomToolUploadError,
    ExitCode,
    TamarindError,
    ValidationError,
)


BASE = "https://api.test/"
UPLOAD = "https://uploads.test/source.zip"


def _tool(*, generation: str = "generation-1") -> dict:
    return {
        "name": "example",
        "generation": generation,
        "displayName": "Example",
        "description": "",
        "functions": [],
        "status": "Draft",
        "gpuType": "None",
        "memory": "8Gi",
        "cpu": 1,
        "homeDiskGi": 20,
        "maxRuntimeSeconds": None,
        "hasSource": False,
        "sourceDigest": None,
        "published": False,
        "autoPublish": False,
        "estTime": "1:30:00",
        "paperUrl": "https://example.com/paper",
        "tags": ["structure"],
        "defaultVersion": None,
        "createdAt": "2026-08-15T00:00:00Z",
        "updatedAt": "2026-08-15T00:00:00Z",
        "canEdit": True,
        "canBuild": True,
    }


def _version(*, status: str = "Running", terminal: bool = False, error: dict | None = None) -> dict:
    return {
        "name": "v1",
        "sourceRevision": "a" * 40,
        "sourceDigest": "sha256:" + "b" * 64,
        "status": status,
        "origin": "Build",
        "createdAt": "2026-08-15T00:00:00Z",
        "startedAt": "2026-08-15T00:00:00Z",
        "completedAt": "2026-08-15T00:01:00Z" if terminal else None,
        "terminal": terminal,
        "error": error,
    }


def _source(root: Path) -> None:
    (root / "config.json").write_text(json.dumps({"displayName": "Example", "inputs": []}))
    (root / "Dockerfile").write_text("FROM python:3.12-slim\n")
    (root / "run.sh").write_text("#!/bin/sh\ntrue\n")


@respx.mock
def test_collection_get_list_and_update_use_resource_generation() -> None:
    respx.get(f"{BASE}custom-tools/example").mock(return_value=httpx.Response(200, json=_tool()))
    list_route = respx.get(f"{BASE}custom-tools").mock(
        return_value=httpx.Response(200, json={"items": [_tool()], "nextCursor": "next"})
    )
    update_route = respx.patch(f"{BASE}custom-tools/example").mock(
        return_value=httpx.Response(200, json={**_tool(), "description": "updated"})
    )

    with Tamarind(api_key="key", api_base=BASE) as client:
        tool = client.custom_tools.get("example")
        page = client.custom_tools.list(status="Draft", published=False, limit=10)
        updated = tool.update(description="updated")

    assert page.items == (tool,)
    assert page.next_cursor == "next"
    assert list_route.calls.last.request.url.params["status"] == "Draft"
    assert list_route.calls.last.request.url.params["published"] == "false"
    assert update_route.calls.last.request.headers["If-Match"] == "generation-1"
    assert json.loads(update_route.calls.last.request.content) == {"description": "updated"}
    assert updated.description == "updated"
    assert updated.est_time == "1:30:00"
    assert updated.paper_url == "https://example.com/paper"
    assert updated.tags == ("structure",)


@respx.mock
def test_build_uploads_exact_archive_then_creates_version(tmp_path: Path) -> None:
    _source(tmp_path)
    respx.get(f"{BASE}custom-tools/example").mock(return_value=httpx.Response(200, json=_tool()))
    upload_session_route = respx.post(f"{BASE}custom-tools/example/uploads").mock(
        return_value=httpx.Response(
            201,
            json={
                "uploadId": "upload-1",
                "uploadUrl": UPLOAD,
                "uploadMethod": "PUT",
                "uploadHeaders": {
                    "Content-Type": "application/zip",
                    "x-amz-meta-upload": "source",
                },
                "expiresAt": "2026-08-15T01:00:00Z",
                "maxBytes": 1_000_000,
            },
        )
    )
    upload_route = respx.put(UPLOAD).mock(return_value=httpx.Response(200))
    build_route = respx.post(f"{BASE}custom-tools/example/versions").mock(
        return_value=httpx.Response(202, json={"action": "build", "version": _version()})
    )

    with Tamarind(api_key="key", api_base=BASE) as client:
        result = client.custom_tools.get("example").build(tmp_path)

    uploaded = upload_route.calls.last.request.content
    body = json.loads(build_route.calls.last.request.content)
    assert upload_route.calls.last.request.headers["Content-Type"] == "application/zip"
    assert upload_route.calls.last.request.headers["x-amz-meta-upload"] == "source"
    assert upload_session_route.calls.last.request.headers["If-Match"] == "generation-1"
    assert body["uploadId"] == "upload-1"
    assert body["expectedSourceDigest"].startswith("sha256:")
    assert build_route.calls.last.request.headers["If-Match"] == "generation-1"
    assert uploaded.startswith(b"PK")
    assert result.action == "build"
    assert result.version.name == "v1"
    assert result.version.tool_generation == "generation-1"


@respx.mock
def test_versions_retain_parent_generation_for_refresh_and_cancellation() -> None:
    respx.get(f"{BASE}custom-tools/example").mock(
        return_value=httpx.Response(200, json=_tool(generation="generation-1"))
    )
    respx.get(f"{BASE}custom-tools/example/versions").mock(
        return_value=httpx.Response(200, json={"items": [_version()], "nextCursor": None})
    )
    respx.get(f"{BASE}custom-tools/example/versions/v1").mock(
        return_value=httpx.Response(200, json=_version())
    )
    cancel_route = respx.post(f"{BASE}custom-tools/example/versions/v1/cancel").mock(
        return_value=httpx.Response(200, json=_version(status="Stopped", terminal=True))
    )

    with Tamarind(api_key="key", api_base=BASE) as client:
        tool = client.custom_tools.get("example")
        listed = tool.versions().items[0]
        fetched = tool.get_version("v1")
        refreshed = fetched.refresh()
        cancelled = refreshed.cancel()

    assert listed.tool_generation == "generation-1"
    assert fetched.tool_generation == "generation-1"
    assert refreshed.tool_generation == "generation-1"
    assert cancelled.tool_generation == "generation-1"
    assert cancel_route.calls.last.request.headers["If-Match"] == "generation-1"


@respx.mock
def test_build_archives_the_same_source_snapshot_that_passed_validation(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _source(tmp_path)
    respx.get(f"{BASE}custom-tools/example").mock(return_value=httpx.Response(200, json=_tool()))
    validate_source_tree = resources.validate_source_tree

    def mutate_after_validation(tree):
        report = validate_source_tree(tree)
        (tmp_path / "run.sh").write_text("#!/bin/sh\nchanged\n")
        return report

    monkeypatch.setattr(resources, "validate_source_tree", mutate_after_validation)

    with Tamarind(api_key="key", api_base=BASE) as client:
        with pytest.raises(CustomToolUploadError, match="changed after inspection"):
            client.custom_tools.get("example").build(tmp_path)


@respx.mock
def test_build_uses_configured_timeout_for_source_upload(tmp_path: Path) -> None:
    _source(tmp_path)
    respx.get(f"{BASE}custom-tools/example").mock(return_value=httpx.Response(200, json=_tool()))
    respx.post(f"{BASE}custom-tools/example/uploads").mock(
        return_value=httpx.Response(
            201,
            json={
                "uploadId": "upload-1",
                "uploadUrl": UPLOAD,
                "uploadMethod": "PUT",
                "uploadHeaders": {"Content-Type": "application/zip"},
                "expiresAt": "2026-08-15T01:00:00Z",
                "maxBytes": 1_000_000,
            },
        )
    )
    upload_route = respx.put(UPLOAD).mock(return_value=httpx.Response(200))
    respx.post(f"{BASE}custom-tools/example/versions").mock(
        return_value=httpx.Response(202, json={"action": "build", "version": _version()})
    )

    with Tamarind(api_key="key", api_base=BASE, timeout=0.25) as client:
        client.custom_tools.get("example").build(tmp_path)

    request_timeout = upload_route.calls.last.request.extensions["timeout"]
    assert request_timeout == {
        "connect": 0.25,
        "read": 0.25,
        "write": 0.25,
        "pool": 0.25,
    }


@respx.mock
def test_build_redacts_presigned_url_from_upload_failure(tmp_path: Path) -> None:
    _source(tmp_path)
    signed_url = f"{UPLOAD}?X-Amz-Signature=do-not-leak"
    respx.get(f"{BASE}custom-tools/example").mock(return_value=httpx.Response(200, json=_tool()))
    respx.post(f"{BASE}custom-tools/example/uploads").mock(
        return_value=httpx.Response(
            201,
            json={
                "uploadId": "upload-1",
                "uploadUrl": signed_url,
                "uploadMethod": "PUT",
                "uploadHeaders": {"Content-Type": "application/zip"},
                "expiresAt": "2026-08-15T01:00:00Z",
                "maxBytes": 1_000_000,
            },
        )
    )
    respx.put(signed_url).mock(return_value=httpx.Response(403))

    with Tamarind(api_key="key", api_base=BASE) as client:
        with pytest.raises(CustomToolUploadError) as raised:
            client.custom_tools.get("example").build(tmp_path)

    assert "403" in str(raised.value)
    assert "do-not-leak" not in str(raised.value)
    assert raised.value.__cause__ is None


@respx.mock
def test_monitor_advances_cursor_and_returns_terminal_version(monkeypatch) -> None:
    respx.get(f"{BASE}custom-tools/example").mock(return_value=httpx.Response(200, json=_tool()))
    version_route = respx.get(f"{BASE}custom-tools/example/versions/v1").mock(
        side_effect=[
            httpx.Response(200, json=_version()),
            httpx.Response(200, json=_version(status="Complete", terminal=True)),
        ]
    )
    logs_route = respx.get(f"{BASE}custom-tools/example/versions/v1/logs").mock(
        side_effect=[
            httpx.Response(
                200,
                json={
                    "status": "Running",
                    "items": [{"message": "building", "timestamp": 1}],
                    "nextCursor": "cursor-1",
                    "error": None,
                },
            ),
            httpx.Response(
                200,
                json={
                    "status": "Complete",
                    "items": [{"message": "done", "timestamp": 2}],
                    "nextCursor": None,
                    "error": None,
                },
            ),
        ]
    )
    monkeypatch.setattr("tamarind.custom_tools.resources.time.sleep", lambda _: None)

    with Tamarind(api_key="key", api_base=BASE) as client:
        initial = client.custom_tools.get("example")
        version = initial.get_version("v1")
        events: list[BuildEvent] = []
        final = version.monitor(timeout=10, interval=0.01, on_event=events.append)

    assert final.status == "Complete"
    assert [event.message for event in events] == ["building", "done"]
    assert logs_route.calls[1].request.url.params["cursor"] == "cursor-1"
    assert version_route.call_count == 2


@respx.mock
def test_monitor_does_not_replay_cumulative_events_without_a_cursor(monkeypatch) -> None:
    respx.get(f"{BASE}custom-tools/example").mock(return_value=httpx.Response(200, json=_tool()))
    respx.get(f"{BASE}custom-tools/example/versions/v1").mock(
        side_effect=[
            httpx.Response(200, json=_version()),
            httpx.Response(200, json=_version(status="Complete", terminal=True)),
        ]
    )
    respx.get(f"{BASE}custom-tools/example/versions/v1/logs").mock(
        side_effect=[
            httpx.Response(
                200,
                json={
                    "status": "Running",
                    "items": [{"message": "building", "timestamp": 1}],
                    "nextCursor": None,
                    "error": None,
                },
            ),
            httpx.Response(
                200,
                json={
                    "status": "Complete",
                    "items": [
                        {"message": "building", "timestamp": 1},
                        {"message": "done", "timestamp": 2},
                    ],
                    "nextCursor": None,
                    "error": None,
                },
            ),
        ]
    )
    monkeypatch.setattr("tamarind.custom_tools.resources.time.sleep", lambda _: None)

    with Tamarind(api_key="key", api_base=BASE) as client:
        version = client.custom_tools.get("example").get_version("v1")
        events: list[BuildEvent] = []
        version.monitor(timeout=10, interval=0.01, on_event=events.append)

    assert [event.message for event in events] == ["building", "done"]


@respx.mock
def test_monitor_does_not_replay_events_when_a_cursor_appears(monkeypatch) -> None:
    respx.get(f"{BASE}custom-tools/example").mock(return_value=httpx.Response(200, json=_tool()))
    respx.get(f"{BASE}custom-tools/example/versions/v1").mock(
        side_effect=[
            httpx.Response(200, json=_version()),
            httpx.Response(200, json=_version(status="Complete", terminal=True)),
        ]
    )
    respx.get(f"{BASE}custom-tools/example/versions/v1/logs").mock(
        side_effect=[
            httpx.Response(
                200,
                json={
                    "status": "Running",
                    "items": [{"message": "building", "timestamp": 1}],
                    "nextCursor": None,
                    "error": None,
                },
            ),
            httpx.Response(
                200,
                json={
                    "status": "Complete",
                    "items": [
                        {"message": "building", "timestamp": 1},
                        {"message": "done", "timestamp": 2},
                    ],
                    "nextCursor": "cursor-1",
                    "error": None,
                },
            ),
            httpx.Response(
                200,
                json={
                    "status": "Complete",
                    "items": [{"message": "published image", "timestamp": 3}],
                    "nextCursor": None,
                    "error": None,
                },
            ),
        ]
    )
    monkeypatch.setattr("tamarind.custom_tools.resources.time.sleep", lambda _: None)

    with Tamarind(api_key="key", api_base=BASE) as client:
        version = client.custom_tools.get("example").get_version("v1")
        events: list[BuildEvent] = []
        version.monitor(timeout=10, interval=0.01, on_event=events.append)

    assert [event.message for event in events] == ["building", "done", "published image"]


@respx.mock
def test_callback_exception_stops_monitoring_without_cancelling() -> None:
    respx.get(f"{BASE}custom-tools/example").mock(return_value=httpx.Response(200, json=_tool()))
    respx.get(f"{BASE}custom-tools/example/versions/v1").mock(
        return_value=httpx.Response(200, json=_version())
    )
    respx.get(f"{BASE}custom-tools/example/versions/v1/logs").mock(
        return_value=httpx.Response(
            200,
            json={
                "status": "Running",
                "items": [{"message": "building", "timestamp": 1}],
                "nextCursor": "cursor-1",
                "error": None,
            },
        )
    )
    cancel_route = respx.post(f"{BASE}custom-tools/example/versions/v1/cancel").mock(
        return_value=httpx.Response(200, json=_version(status="Stopped", terminal=True))
    )

    with Tamarind(api_key="key", api_base=BASE) as client:
        version = client.custom_tools.get("example").get_version("v1")
        with pytest.raises(RuntimeError, match="renderer failed"):
            version.monitor(
                timeout=10,
                on_event=lambda _event: (_ for _ in ()).throw(RuntimeError("renderer failed")),
            )

    assert not cancel_route.called


@respx.mock
def test_timeout_does_not_cancel_remote_build(monkeypatch) -> None:
    respx.get(f"{BASE}custom-tools/example").mock(return_value=httpx.Response(200, json=_tool()))
    respx.get(f"{BASE}custom-tools/example/versions/v1").mock(
        return_value=httpx.Response(200, json=_version())
    )
    respx.get(f"{BASE}custom-tools/example/versions/v1/logs").mock(
        return_value=httpx.Response(
            200,
            json={"status": "Running", "items": [], "nextCursor": "cursor", "error": None},
        )
    )
    cancel_route = respx.post(f"{BASE}custom-tools/example/versions/v1/cancel").mock(
        return_value=httpx.Response(200, json=_version(status="Stopped", terminal=True))
    )
    ticks = iter([0.0, 0.0, 2.0])
    monkeypatch.setattr("tamarind.custom_tools.resources.time.monotonic", lambda: next(ticks))

    with Tamarind(api_key="key", api_base=BASE) as client:
        version = client.custom_tools.get("example").get_version("v1")
        with pytest.raises(CustomToolBuildTimeoutError):
            version.monitor(timeout=1)

    assert not cancel_route.called
    assert CustomToolBuildTimeoutError.exit_code == ExitCode.TIMEOUT


@respx.mock
def test_monitor_caps_log_request_by_remaining_deadline(monkeypatch) -> None:
    respx.get(f"{BASE}custom-tools/example").mock(return_value=httpx.Response(200, json=_tool()))
    respx.get(f"{BASE}custom-tools/example/versions/v1").mock(
        return_value=httpx.Response(200, json=_version())
    )

    def logs(request: httpx.Request) -> httpx.Response:
        assert request.extensions["timeout"]["read"] <= 1
        return httpx.Response(
            200,
            json={"status": "Running", "items": [], "nextCursor": None, "error": None},
        )

    respx.get(f"{BASE}custom-tools/example/versions/v1/logs").mock(side_effect=logs)
    ticks = iter([0.0, 0.0, 2.0])
    monkeypatch.setattr("tamarind.custom_tools.resources.time.monotonic", lambda: next(ticks))

    with Tamarind(api_key="key", api_base=BASE) as client:
        version = client.custom_tools.get("example").get_version("v1")
        with pytest.raises(CustomToolBuildTimeoutError):
            version.monitor(timeout=1)


@respx.mock
def test_monitor_translates_request_timeout_at_deadline(monkeypatch) -> None:
    respx.get(f"{BASE}custom-tools/example").mock(return_value=httpx.Response(200, json=_tool()))
    respx.get(f"{BASE}custom-tools/example/versions/v1").mock(
        return_value=httpx.Response(200, json=_version())
    )
    ticks = iter([0.0, 0.0, 2.0])
    monkeypatch.setattr("tamarind.custom_tools.resources.time.monotonic", lambda: next(ticks))

    with Tamarind(api_key="key", api_base=BASE) as client:
        version = client.custom_tools.get("example").get_version("v1")
        monkeypatch.setattr(
            client.custom_tools._transport,
            "list_custom_tool_build_logs",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(TamarindError("request timed out")),
        )
        with pytest.raises(CustomToolBuildTimeoutError):
            version.monitor(timeout=1)


@respx.mock
def test_monitor_bounds_terminal_refresh_by_remaining_deadline(monkeypatch) -> None:
    respx.get(f"{BASE}custom-tools/example").mock(return_value=httpx.Response(200, json=_tool()))
    respx.get(f"{BASE}custom-tools/example/versions/v1").mock(
        return_value=httpx.Response(200, json=_version())
    )
    respx.get(f"{BASE}custom-tools/example/versions/v1/logs").mock(
        return_value=httpx.Response(
            200,
            json={
                "status": "Complete",
                "items": [],
                "nextCursor": None,
                "error": None,
            },
        )
    )
    ticks = iter([0.0, 0.0, 0.5, 2.0])
    monkeypatch.setattr("tamarind.custom_tools.resources.time.monotonic", lambda: next(ticks))

    with Tamarind(api_key="key", api_base=BASE) as client:
        version = client.custom_tools.get("example").get_version("v1")

        def terminal_refresh(*_args, **kwargs):
            assert kwargs["timeout"] == pytest.approx(0.5)
            raise TamarindError("request timed out")

        monkeypatch.setattr(
            client.custom_tools._transport,
            "get_custom_tool_version",
            terminal_refresh,
        )
        with pytest.raises(CustomToolBuildTimeoutError, match="terminal state"):
            version.monitor(timeout=1)


@respx.mock
def test_terminal_failure_raises_typed_error() -> None:
    failed = _version(
        status="Stopped",
        terminal=True,
        error={"code": "build_failed", "message": "Docker build failed"},
    )
    respx.get(f"{BASE}custom-tools/example").mock(return_value=httpx.Response(200, json=_tool()))
    respx.get(f"{BASE}custom-tools/example/versions/v1").mock(
        return_value=httpx.Response(200, json=failed)
    )

    with Tamarind(api_key="key", api_base=BASE) as client:
        version = client.custom_tools.get("example").get_version("v1")
        with pytest.raises(CustomToolBuildFailedError, match="Docker build failed"):
            version.monitor(timeout=10)

    assert CustomToolBuildFailedError.exit_code == ExitCode.JOB_FAILED


@respx.mock
def test_monitor_rejects_oversized_integer_timeout() -> None:
    respx.get(f"{BASE}custom-tools/example").mock(return_value=httpx.Response(200, json=_tool()))
    respx.get(f"{BASE}custom-tools/example/versions/v1").mock(
        return_value=httpx.Response(200, json=_version())
    )

    with Tamarind(api_key="key", api_base=BASE) as client:
        version = client.custom_tools.get("example").get_version("v1")
        with pytest.raises(ValidationError, match="monitor timeout"):
            version.monitor(timeout=10**1000)
