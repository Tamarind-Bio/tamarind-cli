from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest
import respx

from tamarind import Tamarind
from tamarind.errors import CustomToolBuildFailedError, CustomToolUploadError

BASE = "https://api.test/"
UPLOAD = "https://uploads.test/source.zip"


def _tool(
    *, updated: str = "2026-08-15T00:00:00Z", source: bool = False, error: str | None = None
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
        "connectionError": error,
        "published": False,
        "autoPublish": False,
        "defaultVersion": None,
        "createdAt": "2026-08-15T00:00:00Z",
        "updatedAt": updated,
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
def test_build_composes_upload_finalize_poll_deploy_and_version(tmp_path: Path) -> None:
    _source(tmp_path)
    tool_reads = respx.get(f"{BASE}custom-tools/example").mock(
        side_effect=[
            httpx.Response(200, json=_tool()),
            httpx.Response(200, json=_tool()),
            httpx.Response(200, json=_tool(updated="2026-08-15T00:00:01Z", source=True)),
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
        return_value=httpx.Response(202, json={"versionName": "v1", "path": "building"})
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
    assert json.loads(deploy.calls.last.request.content) == {}
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
