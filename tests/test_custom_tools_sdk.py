from __future__ import annotations

import asyncio
import json
from pathlib import Path

import httpx
import pytest
import respx

from tamarind import Tamarind
from tamarind.custom_tools import resources
from tamarind.custom_tools.packaging import build_source_tree_archive, inspect_source_tree
from tamarind.errors import (
    CustomToolBuildFailedError,
    CustomToolNotFoundError,
    CustomToolUploadError,
    StaleCustomToolError,
)

BASE = "https://api.test/"
UPLOAD = "https://uploads.test/source.zip"


def _tool(
    *,
    source_hash: str = "",
    source_ref: str | None = None,
    source: bool = False,
    error: str | None = None,
) -> dict:
    return {
        "name": "example",
        "displayName": "Example",
        "description": "",
        "functions": [],
        "status": "Draft",
        "gpuType": "None",
        "memory": "8Gi",
        "cpu": 1,
        "homeDiskGi": 20,
        "maxRuntimeSeconds": None,
        "hasSource": source,
        "sourceHash": source_hash,
        "sourceRef": source_ref if source_ref is not None else "a" * 40 if source else None,
        "connectionError": error,
        "published": False,
        "autoPublish": False,
        "defaultVersion": None,
        "createdAt": "2026-08-15T00:00:00Z",
        "updatedAt": "2026-08-15T00:00:00Z",
        "canEdit": True,
        "canDeploy": True,
    }


def _version(*, status: str = "Running", error: str | None = None) -> dict:
    return {
        "versionName": "v1",
        "ref": "a" * 40,
        "status": status,
        "origin": "build",
        "buildStartedAt": "2026-08-15T00:00:00Z",
        "buildCompletedAt": "2026-08-15T00:01:00Z" if status in {"Complete", "Stopped"} else None,
        "buildDurationSeconds": 60 if status in {"Complete", "Stopped"} else None,
        "errorMessage": error,
    }


def _source(root: Path) -> None:
    (root / "config.json").write_text(json.dumps({"displayName": "Example", "inputs": []}))
    (root / "Dockerfile").write_text("FROM python:3.12-slim\n")
    (root / "run.sh").write_text("#!/bin/sh\ntrue\n")


def _archive_digest(root: Path) -> str:
    return build_source_tree_archive(inspect_source_tree(root)).digest


@respx.mock
def test_create_list_and_update_wrap_public_routes() -> None:
    create = respx.post(f"{BASE}custom-tools").mock(return_value=httpx.Response(201, json=_tool()))
    respx.get(f"{BASE}custom-tools").mock(
        return_value=httpx.Response(200, json={"items": [_tool()]})
    )
    update = respx.patch(f"{BASE}custom-tools/example").mock(
        return_value=httpx.Response(200, json={**_tool(), "description": "updated"})
    )

    with Tamarind(api_key="key", api_base=BASE) as client:
        tool = client.custom_tools.create("example")
        listed = client.custom_tools.list().items
        changed = tool.update(description="updated")

    assert json.loads(create.calls.last.request.content) == {"name": "example"}
    assert listed[0].name == "example"
    assert json.loads(update.calls.last.request.content) == {"description": "updated"}
    assert "If-Match" not in update.calls.last.request.headers
    assert changed.description == "updated"


@respx.mock
def test_custom_tools_transport_owns_plain_404_classification() -> None:
    respx.get(f"{BASE}custom-tools/missing").mock(
        return_value=httpx.Response(404, json={"detail": "Not Found"})
    )

    with Tamarind(api_key="key", api_base=BASE) as client:
        with pytest.raises(CustomToolNotFoundError, match="Not Found"):
            client.custom_tools.get("missing")


@respx.mock
def test_custom_tools_not_found_classification_ignores_api_mount_prefix() -> None:
    prefixed_base = f"{BASE}api/"
    respx.get(f"{prefixed_base}custom-tools/example").mock(
        return_value=httpx.Response(200, json=_tool())
    )
    respx.get(f"{prefixed_base}custom-tools/example/versions/v1").mock(
        return_value=httpx.Response(404, json={"detail": "Not Found"})
    )

    with Tamarind(api_key="key", api_base=prefixed_base) as client:
        with pytest.raises(CustomToolNotFoundError, match="Not Found"):
            client.custom_tools.get("example").get_version("v1")


@respx.mock
def test_build_composes_upload_finalize_poll_deploy_and_version(tmp_path: Path) -> None:
    _source(tmp_path)
    source_hash = _archive_digest(tmp_path)
    tool_reads = respx.get(f"{BASE}custom-tools/example").mock(
        side_effect=[
            httpx.Response(200, json=_tool()),
            httpx.Response(200, json=_tool()),
            httpx.Response(200, json=_tool(source=True, source_hash=source_hash)),
        ]
    )
    respx.post(f"{BASE}custom-tools/example/uploads").mock(
        return_value=httpx.Response(
            201,
            json={
                "uploadId": "upload-1",
                "uploadUrl": UPLOAD,
                "uploadMethod": "PUT",
                "uploadHeaders": {"Content-Type": "application/zip"},
                "expiresIn": 900,
            },
        )
    )
    upload = respx.put(UPLOAD).mock(return_value=httpx.Response(200))
    finalize = respx.post(f"{BASE}custom-tools/example/uploads/upload-1/finalize").mock(
        return_value=httpx.Response(202, json={"status": "processing"})
    )
    deploy = respx.post(f"{BASE}custom-tools/example/deploy").mock(
        return_value=httpx.Response(
            202, json={"versionName": "v1", "ref": "a" * 40, "path": "building"}
        )
    )
    respx.get(f"{BASE}custom-tools/example/versions", params={"limit": "50"}).mock(
        return_value=httpx.Response(200, json={"items": []})
    )
    respx.get(f"{BASE}custom-tools/example/versions/v1").mock(
        return_value=httpx.Response(200, json=_version())
    )

    with Tamarind(api_key="key", api_base=BASE) as client:
        version = client.custom_tools.get("example").build(tmp_path, poll_interval=0.001)

    assert tool_reads.call_count == 3
    assert upload.calls.last.request.content.startswith(b"PK")
    assert upload.calls.last.request.headers["Content-Type"] == "application/zip"
    assert finalize.called
    assert json.loads(deploy.calls.last.request.content) == {"expectedSourceRef": "a" * 40}
    assert version.name == "v1"
    assert not respx.calls.last.request.url.path.endswith("/versions")


@respx.mock
def test_build_surfaces_background_extraction_error(tmp_path: Path) -> None:
    _source(tmp_path)
    respx.get(f"{BASE}custom-tools/example").mock(
        side_effect=[
            httpx.Response(200, json=_tool()),
            httpx.Response(200, json=_tool()),
            httpx.Response(200, json=_tool(error="bad archive")),
        ]
    )
    respx.post(f"{BASE}custom-tools/example/uploads").mock(
        return_value=httpx.Response(
            201, json={"uploadId": "upload-1", "uploadUrl": UPLOAD, "expiresIn": 900}
        )
    )
    respx.put(UPLOAD).mock(return_value=httpx.Response(200))
    respx.post(f"{BASE}custom-tools/example/uploads/upload-1/finalize").mock(
        return_value=httpx.Response(202, json={"status": "processing"})
    )

    with Tamarind(api_key="key", api_base=BASE) as client:
        with pytest.raises(CustomToolUploadError, match="bad archive"):
            client.custom_tools.get("example").build(tmp_path, poll_interval=0.001)


def test_build_caps_archive_at_the_server_source_limit(tmp_path: Path, monkeypatch) -> None:
    _source(tmp_path)
    observed_limit = None

    class Transport:
        def create_custom_tool_upload(self, _name):
            return {"uploadUrl": UPLOAD, "uploadId": "upload-1"}

    def capture_limit(_tree, *, max_bytes):
        nonlocal observed_limit
        observed_limit = max_bytes
        raise CustomToolUploadError("stop after observing limit")

    monkeypatch.setattr(resources, "build_source_tree_archive", capture_limit)
    collection = resources.CustomTools(Transport())  # type: ignore[arg-type]
    tool = type("Tool", (), {"name": "example"})()

    with pytest.raises(CustomToolUploadError, match="observing limit"):
        collection._build(  # type: ignore[arg-type]
            tool,
            resources.inspect_source_tree(tmp_path),
            source_timeout=1,
            poll_interval=0.1,
        )

    assert observed_limit == resources.MAX_TOOL_SOURCE_BYTES


def test_build_constructs_archive_before_creating_upload_session(
    tmp_path: Path, monkeypatch
) -> None:
    _source(tmp_path)
    events: list[str] = []

    class Archive:
        digest = "sha256:test"

        def content(self):
            raise AssertionError("upload must not start in this lifecycle test")

        def close(self):
            events.append("close")

    class Transport:
        def create_custom_tool_upload(self, _name):
            events.append("session")
            raise RuntimeError("session failed")

    def build_archive(_tree, *, max_bytes):
        assert max_bytes == resources.MAX_TOOL_SOURCE_BYTES
        events.append("archive")
        return Archive()

    monkeypatch.setattr(resources, "build_source_tree_archive", build_archive)
    collection = resources.CustomTools(Transport())  # type: ignore[arg-type]
    tool = type("Tool", (), {"name": "example"})()

    with pytest.raises(RuntimeError, match="session failed"):
        collection._build(  # type: ignore[arg-type]
            tool,
            resources.inspect_source_tree(tmp_path),
            source_timeout=1,
            poll_interval=0.1,
        )

    assert events == ["archive", "session", "close"]


@respx.mock
def test_build_tracks_queued_deploy_by_source_ref(tmp_path: Path) -> None:
    _source(tmp_path)
    source_hash = _archive_digest(tmp_path)
    respx.get(f"{BASE}custom-tools/example").mock(
        side_effect=[
            httpx.Response(200, json=_tool()),
            httpx.Response(200, json=_tool(source=True, source_hash=source_hash)),
        ]
    )
    respx.post(f"{BASE}custom-tools/example/uploads").mock(
        return_value=httpx.Response(
            201,
            json={"uploadId": "upload-1", "uploadUrl": UPLOAD, "expiresIn": 900},
        )
    )
    respx.put(UPLOAD).mock(return_value=httpx.Response(200))
    respx.post(f"{BASE}custom-tools/example/uploads/upload-1/finalize").mock(
        return_value=httpx.Response(202, json={"status": "processing"})
    )
    respx.post(f"{BASE}custom-tools/example/deploy").mock(
        return_value=httpx.Response(
            202, json={"versionName": None, "ref": "a" * 40, "path": "noop"}
        )
    )
    versions = respx.get(f"{BASE}custom-tools/example/versions", params={"limit": "50"}).mock(
        side_effect=[
            httpx.Response(200, json={"items": []}),
            httpx.Response(200, json={"items": []}),
            httpx.Response(200, json={"items": [_version()]}),
        ]
    )

    with Tamarind(api_key="key", api_base=BASE) as client:
        version = client.custom_tools.get("example").build(tmp_path, poll_interval=0.001)

    assert version.name == "v1"
    assert versions.call_count == 3


@respx.mock
def test_build_ignores_old_version_with_the_same_source_ref(tmp_path: Path) -> None:
    _source(tmp_path)
    source_hash = _archive_digest(tmp_path)
    respx.get(f"{BASE}custom-tools/example").mock(
        side_effect=[
            httpx.Response(200, json=_tool()),
            httpx.Response(200, json=_tool(source=True, source_hash=source_hash)),
        ]
    )
    respx.post(f"{BASE}custom-tools/example/uploads").mock(
        return_value=httpx.Response(
            201, json={"uploadId": "upload-1", "uploadUrl": UPLOAD, "expiresIn": 900}
        )
    )
    respx.put(UPLOAD).mock(return_value=httpx.Response(200))
    respx.post(f"{BASE}custom-tools/example/uploads/upload-1/finalize").mock(
        return_value=httpx.Response(202, json={"status": "processing"})
    )
    respx.post(f"{BASE}custom-tools/example/deploy").mock(
        return_value=httpx.Response(
            202, json={"versionName": None, "ref": "a" * 40, "path": "building"}
        )
    )
    old = _version()
    new = {**_version(), "versionName": "v2"}
    respx.get(f"{BASE}custom-tools/example/versions", params={"limit": "50"}).mock(
        side_effect=[
            httpx.Response(200, json={"items": [old]}),
            httpx.Response(200, json={"items": [old]}),
            httpx.Response(200, json={"items": [new, old]}),
        ]
    )

    with Tamarind(api_key="key", api_base=BASE) as client:
        version = client.custom_tools.get("example").build(tmp_path, poll_interval=0.001)

    assert version.name == "v2"


@respx.mock
def test_build_fails_closed_when_selected_source_changes_before_deploy(tmp_path: Path) -> None:
    _source(tmp_path)
    source_hash = _archive_digest(tmp_path)
    respx.get(f"{BASE}custom-tools/example").mock(
        side_effect=[
            httpx.Response(200, json=_tool()),
            httpx.Response(200, json=_tool(source=True, source_hash=source_hash)),
        ]
    )
    respx.post(f"{BASE}custom-tools/example/uploads").mock(
        return_value=httpx.Response(
            201, json={"uploadId": "upload-1", "uploadUrl": UPLOAD, "expiresIn": 900}
        )
    )
    respx.put(UPLOAD).mock(return_value=httpx.Response(200))
    respx.post(f"{BASE}custom-tools/example/uploads/upload-1/finalize").mock(
        return_value=httpx.Response(202, json={"status": "processing"})
    )
    deploy = respx.post(f"{BASE}custom-tools/example/deploy").mock(
        return_value=httpx.Response(
            409,
            json={
                "type": "https://app.tamarind.bio/errors/custom_tool_source_changed",
                "title": "Custom Tool source changed",
                "status": 409,
                "code": "custom_tool_source_changed",
                "detail": "refresh and retry",
            },
        )
    )
    respx.get(f"{BASE}custom-tools/example/versions", params={"limit": "50"}).mock(
        return_value=httpx.Response(200, json={"items": []})
    )

    with Tamarind(api_key="key", api_base=BASE) as client:
        with pytest.raises(StaleCustomToolError, match="refresh and retry"):
            client.custom_tools.get("example").build(tmp_path, poll_interval=0.001)

    assert json.loads(deploy.calls.last.request.content) == {"expectedSourceRef": "a" * 40}


@respx.mock
def test_version_logs_cancel_and_publish_use_version_routes() -> None:
    respx.get(f"{BASE}custom-tools/example").mock(return_value=httpx.Response(200, json=_tool()))
    respx.get(f"{BASE}custom-tools/example/versions/v1").mock(
        side_effect=[
            httpx.Response(200, json=_version()),
            httpx.Response(200, json=_version(status="Stopped", error="cancelled by user")),
        ]
    )
    respx.get(f"{BASE}custom-tools/example/versions/v1/logs").mock(
        return_value=httpx.Response(
            200,
            json={
                "buildStatus": "Running",
                "logs": [{"message": "building", "timestamp": 1}],
                "nextCursor": None,
                "errorMessage": None,
            },
        )
    )
    cancel = respx.post(f"{BASE}custom-tools/example/versions/v1/cancel").mock(
        return_value=httpx.Response(200, json={"status": "cancelled"})
    )
    publish = respx.post(f"{BASE}custom-tools/example/versions/v1/publish").mock(
        return_value=httpx.Response(
            200, json={**_tool(source=True), "published": True, "defaultVersion": "v1"}
        )
    )

    with Tamarind(api_key="key", api_base=BASE) as client:
        version = client.custom_tools.get("example").get_version("v1")
        assert version.logs().items[0].message == "building"
        assert version.cancel().status == "Stopped"
        assert version.publish().default_version == "v1"

    assert cancel.called and publish.called


@respx.mock
def test_terminal_failure_raises_typed_error() -> None:
    respx.get(f"{BASE}custom-tools/example").mock(return_value=httpx.Response(200, json=_tool()))
    respx.get(f"{BASE}custom-tools/example/versions/v1").mock(
        return_value=httpx.Response(
            200, json=_version(status="Stopped", error="Docker build failed")
        )
    )

    with Tamarind(api_key="key", api_base=BASE) as client:
        version = client.custom_tools.get("example").get_version("v1")
        with pytest.raises(CustomToolBuildFailedError, match="Docker build failed"):
            version.monitor(timeout=1)


def test_monitor_recomputes_the_deadline_after_log_poll(monkeypatch) -> None:
    ticks = iter((0.0, 0.1, 1.1))
    monkeypatch.setattr(resources, "_clock", lambda: next(ticks))
    refreshed = False

    async def logs(*_args, **_kwargs):
        return resources.BuildLogPage(items=(), status="RUNNING")

    async def refresh(*_args, **_kwargs):
        nonlocal refreshed
        refreshed = True
        raise AssertionError("refresh must not start after the deadline")

    monkeypatch.setattr(resources.Version, "_logs_async", logs)
    monkeypatch.setattr(resources.Version, "_refresh_async", refresh)
    version = resources.Version(
        name="v1",
        source_revision="a" * 40,
        status="Running",
        origin="build",
        started_at="2026-08-15T00:00:00Z",
        completed_at=None,
        duration_seconds=None,
        error=None,
        tool_name="example",
        _collection=None,  # type: ignore[arg-type]
    )

    with pytest.raises(resources.CustomToolBuildTimeoutError):
        asyncio.run(version._monitor(timeout=1.0, interval=0.1, on_event=None))

    assert refreshed is False


def test_monitor_refreshes_version_after_empty_advancing_log_cursor(monkeypatch) -> None:
    requested_cursors: list[str | None] = []

    async def logs(_version, *, cursor, **_kwargs):
        requested_cursors.append(cursor)
        return resources.BuildLogPage(items=(), status="SUCCEEDED", next_cursor="advanced")

    async def refresh(version, **_kwargs):
        return resources.Version(
            name=version.name,
            source_revision=version.source_revision,
            status="Complete",
            origin=version.origin,
            started_at=version.started_at,
            completed_at="2026-08-15T00:01:00Z",
            duration_seconds=60,
            error=version.error,
            tool_name=version.tool_name,
            _collection=version._collection,
        )

    monkeypatch.setattr(resources.Version, "_logs_async", logs)
    monkeypatch.setattr(resources.Version, "_refresh_async", refresh)
    version = resources.Version(
        name="v1",
        source_revision="a" * 40,
        status="Running",
        origin="build",
        started_at="2026-08-15T00:00:00Z",
        completed_at=None,
        duration_seconds=None,
        error=None,
        tool_name="example",
        _collection=None,  # type: ignore[arg-type]
    )

    completed = asyncio.run(version._monitor(timeout=1.0, interval=0.1, on_event=None))

    assert completed.status == "Complete"
    assert requested_cursors == [None, "advanced"]


def test_monitor_advances_log_progress_without_an_event_callback(monkeypatch) -> None:
    requested_cursors: list[str | None] = []
    refreshes = 0

    async def logs(_version, *, cursor, **_kwargs):
        requested_cursors.append(cursor)
        return resources.BuildLogPage(items=(), status="RUNNING", next_cursor="advanced")

    async def refresh(version, **_kwargs):
        nonlocal refreshes
        refreshes += 1
        status = "Complete" if refreshes == 2 else "Running"
        return resources.Version(
            name=version.name,
            source_revision=version.source_revision,
            status=status,
            origin=version.origin,
            started_at=version.started_at,
            completed_at="2026-08-15T00:01:00Z" if status == "Complete" else None,
            duration_seconds=60 if status == "Complete" else None,
            error=version.error,
            tool_name=version.tool_name,
            _collection=version._collection,
        )

    monkeypatch.setattr(resources.Version, "_logs_async", logs)
    monkeypatch.setattr(resources.Version, "_refresh_async", refresh)
    version = resources.Version(
        name="v1",
        source_revision="a" * 40,
        status="Running",
        origin="build",
        started_at="2026-08-15T00:00:00Z",
        completed_at=None,
        duration_seconds=None,
        error=None,
        tool_name="example",
        _collection=None,  # type: ignore[arg-type]
    )

    completed = asyncio.run(version._monitor(timeout=1.0, interval=0.001, on_event=None))

    assert completed.status == "Complete"
    assert requested_cursors == [None, "advanced", "advanced"]


def test_monitor_delivers_logs_written_during_terminal_refresh(monkeypatch) -> None:
    first = resources.BuildEvent("building", 1)
    final = resources.BuildEvent("complete", 2)
    pages = iter(
        (
            resources.BuildLogPage(items=(first,), status="RUNNING", next_cursor="cursor-1"),
            resources.BuildLogPage(items=(final,), status="SUCCEEDED", next_cursor="cursor-2"),
        )
    )

    async def logs(*_args, **_kwargs):
        return next(pages)

    async def refresh(version, **_kwargs):
        return resources.Version(
            name=version.name,
            source_revision=version.source_revision,
            status="Complete",
            origin=version.origin,
            started_at=version.started_at,
            completed_at="2026-08-15T00:01:00Z",
            duration_seconds=60,
            error=version.error,
            tool_name=version.tool_name,
            _collection=version._collection,
        )

    monkeypatch.setattr(resources.Version, "_logs_async", logs)
    monkeypatch.setattr(resources.Version, "_refresh_async", refresh)
    version = resources.Version(
        name="v1",
        source_revision="a" * 40,
        status="Running",
        origin="build",
        started_at="2026-08-15T00:00:00Z",
        completed_at=None,
        duration_seconds=None,
        error=None,
        tool_name="example",
        _collection=None,  # type: ignore[arg-type]
    )
    delivered: list[resources.BuildEvent] = []

    completed = asyncio.run(version._monitor(timeout=1.0, interval=0.1, on_event=delivered.append))

    assert completed.status == "Complete"
    assert delivered == [first, final]


def test_log_progress_deduplicates_cumulative_pages_without_a_cursor() -> None:
    first = resources.BuildEvent("first", 1)
    second = resources.BuildEvent("second", 2)
    progress = resources._LogProgress()

    assert progress.consume(resources.BuildLogPage(items=(first,), status="RUNNING")) == (first,)
    assert progress.consume(resources.BuildLogPage(items=(first, second), status="RUNNING")) == (
        second,
    )


def test_log_progress_treats_cursor_pages_as_incremental() -> None:
    first = resources.BuildEvent("first", 1)
    second = resources.BuildEvent("second", 2)
    progress = resources._LogProgress()

    assert progress.consume(
        resources.BuildLogPage(items=(first,), status="RUNNING", next_cursor="cursor-1")
    ) == (first,)
    assert progress.consume(
        resources.BuildLogPage(items=(second,), status="RUNNING", next_cursor="cursor-2")
    ) == (second,)


def test_log_progress_retains_and_deduplicates_a_terminal_cursor() -> None:
    first = resources.BuildEvent("first", 1)
    final = resources.BuildEvent("final", 2)
    progress = resources._LogProgress()

    assert progress.consume(
        resources.BuildLogPage(items=(first,), status="RUNNING", next_cursor="cursor-1")
    ) == (first,)
    assert progress.consume(resources.BuildLogPage(items=(final,), status="RUNNING")) == (final,)
    assert progress.cursor == "cursor-1"
    assert progress.consume(resources.BuildLogPage(items=(final,), status="RUNNING")) == ()
