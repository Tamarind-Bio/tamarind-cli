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
    source_digest: str | None = None,
    source: bool = False,
) -> dict:
    return {
        "name": "example",
        "generation": "generation-1",
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
        "sourceDigest": source_digest
        if source_digest is not None
        else "sha256:" + "a" * 64
        if source
        else None,
        "published": False,
        "autoPublish": False,
        "estTime": "",
        "paperUrl": "",
        "tags": [],
        "defaultVersion": None,
        "createdAt": "2026-08-15T00:00:00Z",
        "updatedAt": "2026-08-15T00:00:00Z",
        "canEdit": True,
        "canBuild": True,
    }


def _version(*, status: str = "Running", error: str | None = None) -> dict:
    return {
        "name": "v1",
        "sourceRevision": "a" * 40,
        "sourceDigest": "sha256:" + "a" * 64,
        "status": status,
        "origin": "build",
        "createdAt": "2026-08-15T00:00:00Z",
        "startedAt": "2026-08-15T00:00:00Z",
        "completedAt": "2026-08-15T00:01:00Z" if status in {"Complete", "Stopped"} else None,
        "terminal": status in {"Complete", "Stopped"},
        "error": {"code": "build_failed", "message": error} if error else None,
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
    assert update.calls.last.request.headers["If-Match"] == "generation-1"
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
def test_non_custom_tool_route_with_matching_segment_keeps_generic_404() -> None:
    from tamarind.errors import NotFoundError

    respx.get(f"{BASE}catalog/tools/custom-tools/schema").mock(
        return_value=httpx.Response(404, json={"detail": "Not Found"})
    )

    with Tamarind(api_key="key", api_base=BASE) as client:
        with pytest.raises(NotFoundError) as raised:
            client._http.get_json("catalog/tools/custom-tools/schema")

    assert not isinstance(raised.value, CustomToolNotFoundError)


@respx.mock
def test_build_uploads_archive_and_starts_version_atomically(tmp_path: Path) -> None:
    _source(tmp_path)
    digest = _archive_digest(tmp_path)
    respx.get(f"{BASE}custom-tools/example").mock(return_value=httpx.Response(200, json=_tool()))
    create_upload = respx.post(f"{BASE}custom-tools/example/uploads").mock(
        return_value=httpx.Response(
            201,
            json={
                "uploadId": "upload-1",
                "uploadUrl": UPLOAD,
                "uploadMethod": "PUT",
                "uploadHeaders": {"Content-Type": "application/zip"},
                "expiresAt": "2026-08-15T00:15:00Z",
                "maxBytes": 1024,
            },
        )
    )
    upload = respx.put(UPLOAD).mock(return_value=httpx.Response(200))
    build = respx.post(f"{BASE}custom-tools/example/versions").mock(
        return_value=httpx.Response(202, json={"action": "build", "version": _version()})
    )

    with Tamarind(api_key="key", api_base=BASE) as client:
        version = client.custom_tools.get("example").build(tmp_path)

    assert upload.calls.last.request.content.startswith(b"PK")
    assert upload.calls.last.request.headers["Content-Type"] == "application/zip"
    assert create_upload.calls.last.request.headers["If-Match"] == "generation-1"
    assert build.calls.last.request.headers["If-Match"] == "generation-1"
    assert json.loads(build.calls.last.request.content) == {
        "uploadId": "upload-1",
        "expectedSourceDigest": digest,
    }
    assert version.name == "v1"


def test_build_caps_archive_at_the_server_source_limit(tmp_path: Path, monkeypatch) -> None:
    _source(tmp_path)
    observed_limit = None

    class Transport:
        def create_custom_tool_upload(self, _name, _generation):
            return {"uploadUrl": UPLOAD, "uploadId": "upload-1"}

    def capture_limit(_tree, *, max_bytes):
        nonlocal observed_limit
        observed_limit = max_bytes
        raise CustomToolUploadError("stop after observing limit")

    monkeypatch.setattr(resources, "build_source_tree_archive", capture_limit)
    collection = resources.CustomTools(Transport())  # type: ignore[arg-type]
    tool = type("Tool", (), {"name": "example", "generation": "generation-1"})()

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
        def create_custom_tool_upload(self, _name, _generation):
            events.append("session")
            raise RuntimeError("session failed")

    def build_archive(_tree, *, max_bytes):
        assert max_bytes == resources.MAX_TOOL_SOURCE_BYTES
        events.append("archive")
        return Archive()

    monkeypatch.setattr(resources, "build_source_tree_archive", build_archive)
    collection = resources.CustomTools(Transport())  # type: ignore[arg-type]
    tool = type("Tool", (), {"name": "example", "generation": "generation-1"})()

    with pytest.raises(RuntimeError, match="session failed"):
        collection._build(  # type: ignore[arg-type]
            tool,
            resources.inspect_source_tree(tmp_path),
            source_timeout=1,
            poll_interval=0.1,
        )

    assert events == ["archive", "session", "close"]


@respx.mock
def test_build_fails_closed_when_generation_changes(tmp_path: Path) -> None:
    _source(tmp_path)
    respx.get(f"{BASE}custom-tools/example").mock(return_value=httpx.Response(200, json=_tool()))
    respx.post(f"{BASE}custom-tools/example/uploads").mock(
        return_value=httpx.Response(
            201,
            json={
                "uploadId": "upload-1",
                "uploadUrl": UPLOAD,
                "uploadMethod": "PUT",
                "uploadHeaders": {},
                "expiresAt": "2026-08-15T00:15:00Z",
                "maxBytes": 1024,
            },
        )
    )
    respx.put(UPLOAD).mock(return_value=httpx.Response(200))
    build = respx.post(f"{BASE}custom-tools/example/versions").mock(
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
    with Tamarind(api_key="key", api_base=BASE) as client:
        with pytest.raises(StaleCustomToolError, match="refresh and retry"):
            client.custom_tools.get("example").build(tmp_path)

    assert build.calls.last.request.headers["If-Match"] == "generation-1"


@respx.mock
def test_version_logs_cancel_and_publish_use_version_routes() -> None:
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
                "nextCursor": None,
                "error": None,
            },
        )
    )
    cancel = respx.post(f"{BASE}custom-tools/example/versions/v1/cancel").mock(
        return_value=httpx.Response(200, json=_version(status="Stopped", error="cancelled by user"))
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

    assert cancel.calls.last.request.headers["If-Match"] == "generation-1"
    assert publish.calls.last.request.headers["If-Match"] == "generation-1"


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
        asyncio.run(version._monitor(timeout=1.0, interval=0.1, on_event=lambda _event: None))

    assert refreshed is False


def test_monitor_maps_http_request_timeout_to_build_timeout() -> None:
    async def timed_out_request():
        try:
            raise httpx.ReadTimeout("request timed out")
        except httpx.TimeoutException as exc:
            raise resources.TamarindError("network error") from exc

    with pytest.raises(resources.CustomToolBuildTimeoutError, match="monitoring timed out"):
        asyncio.run(resources._await_with_timeout(timed_out_request(), 1.0))


def test_monitor_without_callback_does_not_fetch_logs(monkeypatch) -> None:
    async def logs(*_args, **_kwargs):
        raise AssertionError("logs must not be fetched without an event callback")

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


def test_monitor_without_callback_polls_until_complete(monkeypatch) -> None:
    refreshes = 0

    async def logs(*_args, **_kwargs):
        raise AssertionError("logs must not be fetched without an event callback")

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
    assert refreshes == 2


def test_monitor_delivers_logs_written_during_terminal_refresh(monkeypatch) -> None:
    first = resources.BuildEvent("building", 1)
    final = resources.BuildEvent("complete", 2)
    trailing = resources.BuildEvent("image pushed", 3)
    pages = iter(
        (
            resources.BuildLogPage(items=(first,), status="RUNNING", next_cursor="cursor-1"),
            resources.BuildLogPage(items=(final,), status="SUCCEEDED", next_cursor="cursor-2"),
            resources.BuildLogPage(items=(trailing,), status="SUCCEEDED"),
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
    assert delivered == [first, final, trailing]


def test_monitor_rechecks_deadline_after_terminal_log_callback(monkeypatch) -> None:
    ticks = iter((0.0, 0.1, 1.1))
    monkeypatch.setattr(resources, "_clock", lambda: next(ticks))

    async def logs(*_args, **_kwargs):
        return resources.BuildLogPage(
            items=(resources.BuildEvent("complete", 1),), status="SUCCEEDED"
        )

    monkeypatch.setattr(resources.Version, "_logs_async", logs)
    version = resources.Version(
        name="v1",
        source_revision="a" * 40,
        status="Complete",
        origin="build",
        started_at="2026-08-15T00:00:00Z",
        completed_at="2026-08-15T00:01:00Z",
        duration_seconds=60,
        error=None,
        tool_name="example",
        _collection=None,  # type: ignore[arg-type]
    )

    with pytest.raises(resources.CustomToolBuildTimeoutError, match="monitoring timed out"):
        asyncio.run(version._monitor(timeout=1.0, interval=0.1, on_event=lambda _event: None))


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
