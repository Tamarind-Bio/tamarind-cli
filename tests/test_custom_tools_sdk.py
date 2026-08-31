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
    APIError,
    CustomToolBuildFailedError,
    CustomToolGitHubAuthorizationRequiredError,
    CustomToolGitHubConnectionFailedError,
    CustomToolGitHubConnectionTimeoutError,
    CustomToolNotFoundError,
    CustomToolUploadError,
    StaleCustomToolError,
    TamarindError,
    ValidationError,
)

BASE = "https://api.test/"
UPLOAD = "https://uploads.test/source.zip"
VERSION_ID = "ver_opaque"


@pytest.mark.parametrize("value", [10**400, -(10**400)])
def test_custom_tool_timeouts_reject_integers_outside_the_float_range(value: int) -> None:
    with pytest.raises(ValidationError, match="finite number greater than zero"):
        resources._positive_finite_number(value, "timeout")


def test_numbered_version_names_are_not_accepted_as_sdk_selectors() -> None:
    with pytest.raises(ValidationError, match="opaque Version.id"):
        resources._require_opaque_version_id("v1")

    assert resources._require_opaque_version_id(VERSION_ID) == VERSION_ID


def _tool(
    *,
    generation: str = "generation-1",
    source_digest: str | None = None,
    source: bool = False,
) -> dict:
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


def _version(
    *,
    status: str = "Running",
    terminal: bool | None = None,
    error: str | None = None,
    source_digest: str = "sha256:" + "a" * 64,
) -> dict:
    return {
        "id": VERSION_ID,
        "name": "v1",
        "sourceRevision": "a" * 40,
        "sourceDigest": source_digest,
        "status": status,
        "origin": "build",
        "createdAt": "2026-08-15T00:00:00Z",
        "startedAt": "2026-08-15T00:00:00Z",
        "completedAt": "2026-08-15T00:01:00Z" if status in {"Complete", "Stopped"} else None,
        "terminal": status in {"Complete", "Stopped"} if terminal is None else terminal,
        "error": {"code": "build_failed", "message": error} if error else None,
    }


def _github_connection(
    *,
    status: str = "connecting",
    error: str | None = None,
    commit: str | None = None,
) -> dict:
    connected = status != "disconnected"
    return {
        "repo": "acme/example" if connected else None,
        "branch": "main" if connected else None,
        "commit": commit if connected else None,
        "autoPublish": connected,
        "status": status,
        "error": error if connected else None,
    }


def _github_authorization_problem(*, action: object | None = None) -> dict:
    return {
        "type": "https://app.tamarind.bio/errors/github_authorization_required",
        "title": "GitHub authorization required",
        "status": 403,
        "code": "github_authorization_required",
        "detail": "Authorize the Tamarind GitHub App, then resume the connection.",
        "action": action
        if action is not None
        else {
            "type": "authorize_github",
            "authorizationUrl": "https://github.com/apps/tamarind-bio/installations/new?state=opaque",
            "resumeToken": "r" * 43,
            "expiresAt": "2026-08-29T18:00:00Z",
        },
    }


def _source(root: Path) -> None:
    (root / "config.json").write_text(json.dumps({"displayName": "Example", "inputs": []}))
    (root / "Dockerfile").write_text("FROM python:3.12-slim\n")
    (root / "run.sh").write_text("#!/bin/sh\ntrue\n")


def _archive_digest(root: Path) -> str:
    return build_source_tree_archive(inspect_source_tree(root)).digest


def test_transport_bridge_preserves_generated_kwargs_and_sibling_headers() -> None:
    from tamarind.custom_tools.transport import _http_kwargs

    generated = {
        "method": "patch",
        "url": "/custom-tools/example",
        "headers": {
            "If-Match": '"opaque-validator"',
            "Content-Type": "application/json",
        },
    }

    forwarded = _http_kwargs(generated)

    assert generated["headers"] == {
        "If-Match": '"opaque-validator"',
        "Content-Type": "application/json",
    }
    assert forwarded["path"] == "/custom-tools/example"
    assert "url" not in forwarded
    assert forwarded["headers"] == {
        "X-Tamarind-If-Match": '"opaque-validator"',
        "Content-Type": "application/json",
    }


@respx.mock
def test_create_list_and_update_wrap_public_routes() -> None:
    create = respx.post(f"{BASE}custom-tools").mock(return_value=httpx.Response(201, json=_tool()))
    listed_route = respx.get(f"{BASE}custom-tools").mock(
        return_value=httpx.Response(200, json={"items": [_tool()], "nextCursor": "tools-page-2"})
    )
    respx.get(f"{BASE}custom-tools/example").mock(
        return_value=httpx.Response(200, json=_tool(), headers={"ETag": '"opaque-validator"'})
    )
    update = respx.patch(f"{BASE}custom-tools/example").mock(
        return_value=httpx.Response(200, json={**_tool(), "description": "updated"})
    )

    with Tamarind(api_key="key", api_base=BASE) as client:
        tool = client.custom_tools.create("example")
        page = client.custom_tools.list(limit=1)
        listed = page.items
        changed = tool.update(description="updated")

    assert json.loads(create.calls.last.request.content) == {"name": "example"}
    assert listed[0].name == "example"
    assert page.next_cursor == "tools-page-2"
    assert listed_route.calls.last.request.url.params["limit"] == "1"
    assert json.loads(update.calls.last.request.content) == {"description": "updated"}
    assert update.calls.last.request.headers["X-Tamarind-If-Match"] == '"opaque-validator"'
    assert "If-Match" not in update.calls.last.request.headers
    assert changed.description == "updated"


@respx.mock
def test_delete_uses_the_tool_etag() -> None:
    respx.get(f"{BASE}custom-tools/example").mock(
        return_value=httpx.Response(200, json=_tool(), headers={"ETag": '"opaque-validator"'})
    )
    delete = respx.delete(f"{BASE}custom-tools/example").mock(return_value=httpx.Response(204))

    with Tamarind(api_key="key", api_base=BASE) as client:
        client.custom_tools.get("example").delete()

    assert delete.calls.last.request.headers["X-Tamarind-If-Match"] == '"opaque-validator"'
    assert "If-Match" not in delete.calls.last.request.headers


@respx.mock
def test_delete_requires_the_contract_no_content_status() -> None:
    respx.get(f"{BASE}custom-tools/example").mock(
        return_value=httpx.Response(200, json=_tool(), headers={"ETag": '"opaque-validator"'})
    )
    respx.delete(f"{BASE}custom-tools/example").mock(return_value=httpx.Response(202))

    with Tamarind(api_key="key", api_base=BASE) as client:
        with pytest.raises(TamarindError, match="generated contract"):
            client.custom_tools.get("example").delete()


@respx.mock
def test_github_connection_primary_happy_path() -> None:
    tool_route = respx.get(f"{BASE}custom-tools/example").mock(
        side_effect=[
            httpx.Response(200, json=_tool(), headers={"ETag": '"selected-validator"'}),
            httpx.Response(200, json=_tool(), headers={"ETag": '"current-validator"'}),
            httpx.Response(200, json=_tool(), headers={"ETag": '"current-validator"'}),
            httpx.Response(200, json=_tool(), headers={"ETag": '"current-validator"'}),
        ]
    )
    connect = respx.post(f"{BASE}custom-tools/example/github").mock(
        return_value=httpx.Response(202, json=_github_connection())
    )
    connection_route = respx.get(f"{BASE}custom-tools/example/github").mock(
        return_value=httpx.Response(
            200,
            json=_github_connection(status="connected", commit="a" * 40),
        )
    )
    disconnect = respx.delete(f"{BASE}custom-tools/example/github").mock(
        return_value=httpx.Response(204)
    )

    with Tamarind(api_key="key", api_base=BASE) as client:
        tool = client.custom_tools.get("example")
        pending = tool.connect_github("acme/example", branch="main", auto_publish=True)
        connected = pending.monitor(timeout=1, interval=0.001)
        current = tool.github_connection()
        tool.refresh().disconnect_github()

    assert pending.status == "connecting"
    assert connected.status == "connected"
    assert connected.commit == "a" * 40
    assert current is not None and current.repo == "acme/example"
    assert json.loads(connect.calls.last.request.content) == {
        "repo": "acme/example",
        "branch": "main",
        "autoPublish": True,
    }
    assert connect.calls.last.request.headers["X-Tamarind-If-Match"] == '"selected-validator"'
    assert disconnect.calls.last.request.headers["X-Tamarind-If-Match"] == '"current-validator"'
    assert tool_route.call_count == 4
    assert connection_route.call_count == 2


@respx.mock
def test_github_disconnect_preserves_the_selected_tool_etag() -> None:
    tool_route = respx.get(f"{BASE}custom-tools/example").mock(
        return_value=httpx.Response(200, json=_tool(), headers={"ETag": '"selected-validator"'})
    )
    disconnect = respx.delete(f"{BASE}custom-tools/example/github").mock(
        return_value=httpx.Response(
            412,
            json={
                "type": "https://app.tamarind.bio/errors/precondition_failed",
                "title": "Precondition failed",
                "status": 412,
                "code": "precondition_failed",
                "detail": "refresh and retry",
            },
        )
    )

    with Tamarind(api_key="key", api_base=BASE) as client:
        tool = client.custom_tools.get("example")
        with pytest.raises(StaleCustomToolError, match="refresh and retry"):
            tool.disconnect_github()

    assert tool_route.call_count == 1
    assert disconnect.calls.last.request.headers["X-Tamarind-If-Match"] == '"selected-validator"'


@respx.mock
def test_github_connection_authorization_can_resume_the_exact_request() -> None:
    respx.get(f"{BASE}custom-tools/example").mock(
        return_value=httpx.Response(200, json=_tool(), headers={"ETag": '"current-validator"'})
    )
    connect = respx.post(f"{BASE}custom-tools/example/github").mock(
        side_effect=[
            httpx.Response(403, json=_github_authorization_problem()),
            httpx.Response(202, json=_github_connection()),
        ]
    )

    with Tamarind(api_key="key", api_base=BASE) as client:
        tool = client.custom_tools.get("example")
        with pytest.raises(CustomToolGitHubAuthorizationRequiredError) as raised:
            tool.connect_github("acme/example", branch="release", auto_publish=True)

        authorization = raised.value
        assert authorization.authorization_url.startswith("https://github.com/apps/")
        assert authorization.resume_token == "r" * 43
        assert authorization.expires_at == "2026-08-29T18:00:00Z"
        connection = authorization.resume()

    assert connection.status == "connecting"
    assert connect.call_count == 2
    assert json.loads(connect.calls[0].request.content) == {
        "repo": "acme/example",
        "branch": "release",
        "autoPublish": True,
    }
    assert json.loads(connect.calls[1].request.content) == {
        "repo": "acme/example",
        "branch": "release",
        "autoPublish": True,
        "authorizationToken": "r" * 43,
    }
    assert all(
        call.request.headers["X-Tamarind-If-Match"] == '"current-validator"'
        for call in connect.calls
    )


@pytest.mark.parametrize(
    "action",
    [
        {},
        {
            "type": "open_browser",
            "authorizationUrl": "https://github.com/apps/tamarind-bio/installations/new",
            "resumeToken": "r" * 43,
            "expiresAt": "2026-08-29T18:00:00Z",
        },
        {
            "type": "authorize_github",
            "authorizationUrl": "javascript:alert(1)",
            "resumeToken": "r" * 43,
            "expiresAt": "2026-08-29T18:00:00Z",
        },
        {
            "type": "authorize_github",
            "authorizationUrl": "https://github.com/apps/tamarind-bio/installations/new",
            "resumeToken": "short",
            "expiresAt": "2026-08-29T18:00:00Z",
        },
        {
            "type": "authorize_github",
            "authorizationUrl": "https://github.com/apps/tamarind-bio/installations/new",
            "resumeToken": "r" * 43,
            "expiresAt": "not-a-timestamp",
        },
        {
            "type": "authorize_github",
            "authorizationUrl": "https://github.com/apps/tamarind-bio/installations/new",
            "resumeToken": "r" * 43,
            "expiresAt": "2026-08-29T18:00:00Z",
            "unexpected": True,
        },
    ],
)
@respx.mock
def test_github_connection_rejects_malformed_authorization_actions(action: object) -> None:
    respx.get(f"{BASE}custom-tools/example").mock(
        return_value=httpx.Response(200, json=_tool(), headers={"ETag": '"validator"'})
    )
    respx.post(f"{BASE}custom-tools/example/github").mock(
        return_value=httpx.Response(403, json=_github_authorization_problem(action=action))
    )

    with Tamarind(api_key="key", api_base=BASE) as client:
        with pytest.raises(APIError) as raised:
            client.custom_tools.get("example").connect_github("acme/example")

    assert raised.value.status_code == 403
    assert not isinstance(raised.value, CustomToolGitHubAuthorizationRequiredError)


@respx.mock
def test_github_connection_returns_none_when_disconnected() -> None:
    respx.get(f"{BASE}custom-tools/example").mock(return_value=httpx.Response(200, json=_tool()))
    respx.get(f"{BASE}custom-tools/example/github").mock(
        return_value=httpx.Response(200, json=_github_connection(status="disconnected"))
    )

    with Tamarind(api_key="key", api_base=BASE) as client:
        assert client.custom_tools.get("example").github_connection() is None


@respx.mock
def test_github_connection_rejects_a_tool_name_reused_during_the_read() -> None:
    replaced = False

    def read_tool(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, json=_tool(generation="generation-2" if replaced else "generation-1")
        )

    def read_connection(_request: httpx.Request) -> httpx.Response:
        nonlocal replaced
        replaced = True
        return httpx.Response(200, json=_github_connection(status="connected", commit="a" * 40))

    respx.get(f"{BASE}custom-tools/example").mock(side_effect=read_tool)
    respx.get(f"{BASE}custom-tools/example/github").mock(side_effect=read_connection)

    with Tamarind(api_key="key", api_base=BASE) as client:
        tool = client.custom_tools.get("example")
        with pytest.raises(StaleCustomToolError, match="different generation"):
            tool.github_connection()


@respx.mock
def test_github_connection_surfaces_failed_materialization() -> None:
    respx.get(f"{BASE}custom-tools/example").mock(
        return_value=httpx.Response(200, json=_tool(), headers={"ETag": '"validator"'})
    )
    respx.post(f"{BASE}custom-tools/example/github").mock(
        return_value=httpx.Response(202, json=_github_connection())
    )
    respx.get(f"{BASE}custom-tools/example/github").mock(
        return_value=httpx.Response(
            200,
            json=_github_connection(status="failed", error="clone failed"),
        )
    )

    with Tamarind(api_key="key", api_base=BASE) as client:
        connection = client.custom_tools.get("example").connect_github("acme/example")
        with pytest.raises(CustomToolGitHubConnectionFailedError, match="clone failed") as raised:
            connection.monitor(timeout=1, interval=0.001)

    assert raised.value.detail is not None


@respx.mock
def test_github_connection_failed_without_detail_uses_the_documented_fallback() -> None:
    respx.get(f"{BASE}custom-tools/example").mock(
        return_value=httpx.Response(200, json=_tool(), headers={"ETag": '"validator"'})
    )
    respx.post(f"{BASE}custom-tools/example/github").mock(
        return_value=httpx.Response(202, json=_github_connection())
    )
    respx.get(f"{BASE}custom-tools/example/github").mock(
        return_value=httpx.Response(200, json=_github_connection(status="failed", error=None))
    )

    with Tamarind(api_key="key", api_base=BASE) as client:
        connection = client.custom_tools.get("example").connect_github("acme/example")
        with pytest.raises(CustomToolGitHubConnectionFailedError, match="unknown error"):
            connection.monitor(timeout=1, interval=0.001)


@respx.mock
def test_github_connect_maps_a_stale_tool_etag() -> None:
    respx.get(f"{BASE}custom-tools/example").mock(
        return_value=httpx.Response(200, json=_tool(), headers={"ETag": '"stale-validator"'})
    )
    respx.post(f"{BASE}custom-tools/example/github").mock(
        return_value=httpx.Response(
            412,
            json={
                "type": "https://app.tamarind.bio/errors/precondition_failed",
                "title": "Precondition failed",
                "status": 412,
                "code": "precondition_failed",
                "detail": "refresh and retry",
            },
        )
    )

    with Tamarind(api_key="key", api_base=BASE) as client:
        with pytest.raises(StaleCustomToolError, match="refresh and retry"):
            client.custom_tools.get("example").connect_github("acme/example")


def test_github_connection_monitor_enforces_the_deadline() -> None:
    class Collection:
        async def _github_connection_async(self, *_args, **_kwargs):
            await asyncio.sleep(1)
            raise AssertionError("deadline did not cancel the request")

    connection = resources.GitHubConnection(
        repo="acme/example",
        branch="main",
        commit=None,
        auto_publish=False,
        status="connecting",
        error=None,
        tool_name="example",
        tool_generation="generation-1",
        _collection=Collection(),  # type: ignore[arg-type]
    )

    with pytest.raises(CustomToolGitHubConnectionTimeoutError, match="timed out"):
        connection.monitor(timeout=0.001, interval=0.001)


@pytest.mark.parametrize(
    "wire",
    [
        {**_github_connection(status="connected"), "repo": 42},
        {**_github_connection(status="connected"), "autoPublish": "yes"},
        {**_github_connection(status="disconnected"), "repo": "acme/example"},
        _github_connection(status="connected", error="stale error"),
    ],
)
@respx.mock
def test_github_connection_rejects_malformed_contract_responses(wire: dict) -> None:
    respx.get(f"{BASE}custom-tools/example").mock(return_value=httpx.Response(200, json=_tool()))
    respx.get(f"{BASE}custom-tools/example/github").mock(
        return_value=httpx.Response(200, json=wire)
    )

    with Tamarind(api_key="key", api_base=BASE) as client:
        with pytest.raises(TamarindError, match="generated contract"):
            client.custom_tools.get("example").github_connection()


@respx.mock
def test_refresh_rejects_a_reused_tool_name() -> None:
    route = respx.get(f"{BASE}custom-tools/example").mock(
        side_effect=[
            httpx.Response(200, json=_tool()),
            httpx.Response(200, json=_tool(generation="generation-2")),
        ]
    )

    with Tamarind(api_key="key", api_base=BASE) as client:
        selected = client.custom_tools.get("example")
        with pytest.raises(StaleCustomToolError, match="different generation"):
            selected.refresh()

    assert route.call_count == 2


@pytest.mark.parametrize("operation", ["get_version", "versions"])
@respx.mock
def test_tool_scoped_version_reads_reject_a_reused_tool_name(operation: str) -> None:
    tool_route = respx.get(f"{BASE}custom-tools/example").mock(
        side_effect=[
            httpx.Response(200, json=_tool()),
            httpx.Response(200, json=_tool(generation="generation-2")),
        ]
    )
    if operation == "get_version":
        respx.get(f"{BASE}custom-tools/example/versions/{VERSION_ID}").mock(
            return_value=httpx.Response(200, json=_version())
        )
    else:
        respx.get(f"{BASE}custom-tools/example/versions").mock(
            return_value=httpx.Response(200, json={"items": [_version()], "nextCursor": None})
        )

    with Tamarind(api_key="key", api_base=BASE) as client:
        selected = client.custom_tools.get("example")
        with pytest.raises(StaleCustomToolError, match="different generation"):
            if operation == "get_version":
                selected.get_version(VERSION_ID)
            else:
                selected.versions()

    assert tool_route.call_count == 2


@respx.mock
def test_custom_tools_transport_owns_plain_404_classification() -> None:
    respx.get(f"{BASE}custom-tools/missing").mock(
        return_value=httpx.Response(404, json={"detail": "Not Found"})
    )

    with Tamarind(api_key="key", api_base=BASE) as client:
        with pytest.raises(CustomToolNotFoundError, match="Not Found"):
            client.custom_tools.get("missing")


@respx.mock
def test_generated_response_shape_failures_use_the_sdk_error_boundary() -> None:
    respx.get(f"{BASE}custom-tools/broken").mock(
        return_value=httpx.Response(200, json={"name": "broken"})
    )

    with Tamarind(api_key="key", api_base=BASE) as client:
        with pytest.raises(TamarindError, match="generated contract") as raised:
            client.custom_tools.get("broken")

    assert isinstance(raised.value.__cause__, KeyError)


@pytest.mark.parametrize("status_code", [201, 202, 206, 299])
def test_every_model_operation_rejects_undocumented_2xx_problem_responses(
    status_code: int,
) -> None:
    from tamarind.custom_tools.transport import (
        GeneratedCustomToolsTransport,
        _MODEL_OPERATIONS,
    )
    from tamarind.http import HTTPClient

    problem = {
        "code": "unexpected_success",
        "status": status_code,
        "title": "Unexpected success",
        "type": "https://api.test/problems/unexpected-success",
    }

    with HTTPClient(api_key="key", base_url=BASE) as client:
        transport = GeneratedCustomToolsTransport(client)
        for operation in _MODEL_OPERATIONS:
            if status_code == operation.success_status:
                continue
            response = httpx.Response(status_code, json=problem)
            with pytest.raises(TamarindError, match="generated contract"):
                transport._parse(operation, response)


@respx.mock
def test_malformed_nested_build_errors_use_the_sdk_error_boundary() -> None:
    malformed = _version()
    malformed["error"] = "not-an-error-object"
    respx.get(f"{BASE}custom-tools/example").mock(
        return_value=httpx.Response(200, json=_tool(), headers={"ETag": '"opaque-validator"'})
    )
    respx.get(f"{BASE}custom-tools/example/versions/{VERSION_ID}").mock(
        return_value=httpx.Response(200, json=malformed)
    )

    with Tamarind(api_key="key", api_base=BASE) as client:
        with pytest.raises(TamarindError, match="generated contract"):
            client.custom_tools.get("example").get_version(VERSION_ID)


@respx.mock
def test_custom_tools_not_found_classification_ignores_api_mount_prefix() -> None:
    prefixed_base = f"{BASE}api/"
    respx.get(f"{prefixed_base}custom-tools/example").mock(
        return_value=httpx.Response(200, json=_tool())
    )
    respx.get(f"{prefixed_base}custom-tools/example/versions/{VERSION_ID}").mock(
        return_value=httpx.Response(404, json={"detail": "Not Found"})
    )

    with Tamarind(api_key="key", api_base=prefixed_base) as client:
        with pytest.raises(CustomToolNotFoundError, match="Not Found"):
            client.custom_tools.get("example").get_version(VERSION_ID)


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
    respx.get(f"{BASE}custom-tools/example").mock(
        return_value=httpx.Response(200, json=_tool(), headers={"ETag": '"opaque-validator"'})
    )
    upload_session = respx.post(f"{BASE}custom-tools/example/uploads").mock(
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
        return_value=httpx.Response(
            202,
            json={"action": "reuse_image", "version": _version(source_digest=digest)},
            headers={"ETag": '"version-etag"', "Location": f"./versions/{VERSION_ID}"},
        )
    )

    with Tamarind(api_key="key", api_base=BASE) as client:
        result = client.custom_tools.get("example").build(tmp_path, idempotency_key="release-1")

    assert upload.calls.last.request.content.startswith(b"PK")
    assert upload.calls.last.request.headers["Content-Type"] == "application/zip"
    assert upload.calls.last.request.headers["Content-Length"] == str(
        len(upload.calls.last.request.content)
    )
    assert "X-Tamarind-Tool-Generation" not in upload_session.calls.last.request.headers
    assert build.calls.last.request.headers["X-Tamarind-If-Match"] == '"opaque-validator"'
    assert "If-Match" not in build.calls.last.request.headers
    assert build.calls.last.request.headers["Idempotency-Key"] == "release-1"
    assert json.loads(build.calls.last.request.content) == {
        "uploadId": "upload-1",
        "expectedSourceDigest": digest,
    }
    assert result.action == "reuse_image"
    assert result.version.id == VERSION_ID
    assert result.version._etag == '"version-etag"'
    assert result.version.name == "v1"
    assert result.version.source_digest == digest


@respx.mock
def test_build_rejects_archive_larger_than_upload_session_limit(tmp_path: Path) -> None:
    _source(tmp_path)
    respx.get(f"{BASE}custom-tools/example").mock(
        return_value=httpx.Response(200, json=_tool(), headers={"ETag": '"opaque-validator"'})
    )
    respx.post(f"{BASE}custom-tools/example/uploads").mock(
        return_value=httpx.Response(
            201,
            json={
                "uploadId": "upload-1",
                "uploadUrl": UPLOAD,
                "uploadMethod": "PUT",
                "uploadHeaders": {},
                "expiresAt": "2026-08-15T00:15:00Z",
                "maxBytes": 1,
            },
        )
    )
    upload = respx.put(UPLOAD).mock(return_value=httpx.Response(200))

    with Tamarind(api_key="key", api_base=BASE) as client:
        with pytest.raises(CustomToolUploadError, match="upload session allows at most 1 bytes"):
            client.custom_tools.get("example").build(tmp_path)

    assert not upload.called


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("uploadId", 1),
        ("uploadUrl", 1),
        ("uploadUrl", "http://localhost:8000/source.zip"),
        ("uploadUrl", "http://uploads.test/source.zip"),
        ("uploadMethod", "POST"),
        ("uploadHeaders", {"Content-Type": 1}),
        ("expiresAt", 1),
        ("maxBytes", "1024"),
        ("maxBytes", True),
        ("maxBytes", -1),
    ],
)
@respx.mock
def test_build_rejects_malformed_upload_session_scalars(
    tmp_path: Path, field: str, value: object
) -> None:
    _source(tmp_path)
    session: dict[str, object] = {
        "uploadId": "upload-1",
        "uploadUrl": UPLOAD,
        "uploadMethod": "PUT",
        "uploadHeaders": {},
        "expiresAt": "2026-08-15T00:15:00Z",
        "maxBytes": 1024,
    }
    session[field] = value
    respx.get(f"{BASE}custom-tools/example").mock(return_value=httpx.Response(200, json=_tool()))
    respx.post(f"{BASE}custom-tools/example/uploads").mock(
        return_value=httpx.Response(201, json=session)
    )
    upload = respx.put(UPLOAD).mock(return_value=httpx.Response(200))

    with Tamarind(api_key="key", api_base=BASE) as client:
        with pytest.raises(TamarindError, match="generated contract"):
            client.custom_tools.get("example").build(tmp_path)

    assert not upload.called


@respx.mock
def test_version_pages_preserve_and_accept_cursors() -> None:
    respx.get(f"{BASE}custom-tools/example").mock(return_value=httpx.Response(200, json=_tool()))
    versions = respx.get(f"{BASE}custom-tools/example/versions").mock(
        return_value=httpx.Response(
            200,
            json={"items": [_version()], "nextCursor": "versions-page-2"},
        )
    )

    with Tamarind(api_key="key", api_base=BASE) as client:
        page = client.custom_tools.get("example").versions(
            status="Running",
            limit=1,
            cursor="versions-page-1",
        )

    assert page.next_cursor == "versions-page-2"
    assert page.items[0].source_digest == "sha256:" + "a" * 64
    assert dict(versions.calls.last.request.url.params) == {
        "status": "Running",
        "limit": "1",
        "cursor": "versions-page-1",
    }


@respx.mock
def test_list_operations_preserve_an_explicit_zero_limit() -> None:
    tools = respx.get(f"{BASE}custom-tools").mock(
        return_value=httpx.Response(200, json={"items": [], "nextCursor": None})
    )
    respx.get(f"{BASE}custom-tools/example").mock(return_value=httpx.Response(200, json=_tool()))
    versions = respx.get(f"{BASE}custom-tools/example/versions").mock(
        return_value=httpx.Response(200, json={"items": [], "nextCursor": None})
    )

    with Tamarind(api_key="key", api_base=BASE) as client:
        client.custom_tools.list(limit=0)
        client.custom_tools.get("example").versions(limit=0)

    assert tools.calls.last.request.url.params["limit"] == "0"
    assert versions.calls.last.request.url.params["limit"] == "0"


@respx.mock
def test_version_preserves_wire_timestamps_and_stable_error_code() -> None:
    failed = _version(status="Stopped", error="Docker build failed")
    respx.get(f"{BASE}custom-tools/example").mock(return_value=httpx.Response(200, json=_tool()))
    respx.get(f"{BASE}custom-tools/example/versions/{VERSION_ID}").mock(
        return_value=httpx.Response(200, json=failed)
    )

    with Tamarind(api_key="key", api_base=BASE) as client:
        version = client.custom_tools.get("example").get_version(VERSION_ID)

    assert version.created_at == failed["createdAt"]
    assert version.started_at == failed["startedAt"]
    assert version.completed_at == failed["completedAt"]
    assert version.error is not None
    assert version.error.code == "build_failed"
    assert version.error.message == "Docker build failed"


@respx.mock
def test_version_preserves_the_server_terminal_marker() -> None:
    respx.get(f"{BASE}custom-tools/example").mock(return_value=httpx.Response(200, json=_tool()))
    respx.get(f"{BASE}custom-tools/example/versions/{VERSION_ID}").mock(
        return_value=httpx.Response(200, json=_version(status="Running", terminal=True))
    )

    with Tamarind(api_key="key", api_base=BASE) as client:
        version = client.custom_tools.get("example").get_version(VERSION_ID)

    assert version.terminal is True


@respx.mock
def test_version_rejects_a_non_boolean_terminal_marker() -> None:
    malformed = _version(status="Running")
    malformed["terminal"] = "false"
    respx.get(f"{BASE}custom-tools/example").mock(return_value=httpx.Response(200, json=_tool()))
    respx.get(f"{BASE}custom-tools/example/versions/{VERSION_ID}").mock(
        return_value=httpx.Response(200, json=malformed)
    )

    with Tamarind(api_key="key", api_base=BASE) as client:
        with pytest.raises(TamarindError, match="generated contract"):
            client.custom_tools.get("example").get_version(VERSION_ID)


@respx.mock
def test_version_does_not_interpret_wire_timestamps() -> None:
    wire = {
        **_version(status="Complete"),
        "createdAt": "created by server",
        "startedAt": "started by server",
        "completedAt": "completed by server",
    }
    respx.get(f"{BASE}custom-tools/example").mock(return_value=httpx.Response(200, json=_tool()))
    respx.get(f"{BASE}custom-tools/example/versions/{VERSION_ID}").mock(
        return_value=httpx.Response(200, json=wire)
    )

    with Tamarind(api_key="key", api_base=BASE) as client:
        version = client.custom_tools.get("example").get_version(VERSION_ID)

    assert (version.created_at, version.started_at, version.completed_at) == (
        "created by server",
        "started by server",
        "completed by server",
    )


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
    tool = type("Tool", (), {"name": "example", "generation": "generation-1"})()

    with pytest.raises(CustomToolUploadError, match="observing limit"):
        collection._build(  # type: ignore[arg-type]
            tool,
            resources.inspect_source_tree(tmp_path),
            source_timeout=1,
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
    tool = type("Tool", (), {"name": "example", "generation": "generation-1"})()

    with pytest.raises(RuntimeError, match="session failed"):
        collection._build(  # type: ignore[arg-type]
            tool,
            resources.inspect_source_tree(tmp_path),
            source_timeout=1,
        )

    assert events == ["archive", "session", "close"]


@respx.mock
def test_build_fails_closed_when_generation_changes(tmp_path: Path) -> None:
    _source(tmp_path)
    respx.get(f"{BASE}custom-tools/example").mock(
        return_value=httpx.Response(200, json=_tool(), headers={"ETag": '"opaque-validator"'})
    )
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
    respx.post(f"{BASE}custom-tools/example/versions").mock(
        return_value=httpx.Response(
            412,
            json={
                "type": "https://app.tamarind.bio/errors/precondition_failed",
                "title": "Precondition failed",
                "status": 412,
                "code": "precondition_failed",
                "detail": "refresh and retry",
            },
        )
    )
    with Tamarind(api_key="key", api_base=BASE) as client:
        with pytest.raises(StaleCustomToolError, match="refresh and retry"):
            client.custom_tools.get("example").build(tmp_path)


@respx.mock
def test_version_logs_cancel_and_publish_use_version_routes() -> None:
    get_tool = respx.get(f"{BASE}custom-tools/example").mock(
        return_value=httpx.Response(200, json=_tool(), headers={"ETag": '"opaque-validator"'})
    )
    get_version = respx.get(f"{BASE}custom-tools/example/versions/{VERSION_ID}").mock(
        return_value=httpx.Response(200, json=_version(), headers={"ETag": '"version-etag"'})
    )
    logs = respx.get(f"{BASE}custom-tools/example/versions/{VERSION_ID}/logs").mock(
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
    cancel = respx.post(f"{BASE}custom-tools/example/versions/{VERSION_ID}:cancel").mock(
        return_value=httpx.Response(200, json=_version(status="Stopped", error="cancelled by user"))
    )
    publish = respx.post(f"{BASE}custom-tools/example/versions/{VERSION_ID}:publish").mock(
        return_value=httpx.Response(
            200, json={**_tool(source=True), "published": True, "defaultVersion": "v1"}
        )
    )

    with Tamarind(api_key="key", api_base=BASE) as client:
        version = client.custom_tools.get("example").get_version(VERSION_ID)
        assert version.logs().items[0].message == "building"
        assert version.cancel().status == "Stopped"
        assert version.publish().default_version == "v1"

    assert get_tool.call_count == 3
    assert cancel.calls.last.request.headers["X-Tamarind-If-Match"] == '"version-etag"'
    assert "If-Match" not in cancel.calls.last.request.headers
    assert publish.calls.last.request.headers["X-Tamarind-If-Match"] == '"opaque-validator"'
    assert "If-Match" not in publish.calls.last.request.headers
    for route in (get_version, logs, cancel, publish):
        assert "X-Tamarind-Tool-Generation" not in route.calls.last.request.headers


@respx.mock
def test_terminal_failure_raises_typed_error() -> None:
    respx.get(f"{BASE}custom-tools/example").mock(return_value=httpx.Response(200, json=_tool()))
    respx.get(f"{BASE}custom-tools/example/versions/{VERSION_ID}").mock(
        return_value=httpx.Response(
            200, json=_version(status="Stopped", error="Docker build failed")
        )
    )

    with Tamarind(api_key="key", api_base=BASE) as client:
        version = client.custom_tools.get("example").get_version(VERSION_ID)
        with pytest.raises(CustomToolBuildFailedError, match="Docker build failed"):
            version.monitor(timeout=1)


@respx.mock
def test_non_complete_terminal_version_raises_typed_error() -> None:
    respx.get(f"{BASE}custom-tools/example").mock(return_value=httpx.Response(200, json=_tool()))
    respx.get(f"{BASE}custom-tools/example/versions/{VERSION_ID}").mock(
        return_value=httpx.Response(200, json=_version(status="Running", terminal=True))
    )

    with Tamarind(api_key="key", api_base=BASE) as client:
        version = client.custom_tools.get("example").get_version(VERSION_ID)
        with pytest.raises(CustomToolBuildFailedError, match="status Running"):
            version.monitor(timeout=1)


def test_monitor_recomputes_the_deadline_after_log_poll(monkeypatch) -> None:
    ticks = iter((0.0, 0.1, 1.1))
    monkeypatch.setattr(resources, "_clock", lambda: next(ticks))
    refreshed = False

    async def logs(*_args, **_kwargs):
        return resources.BuildLogPage(items=(), status="Running")

    async def refresh(*_args, **_kwargs):
        nonlocal refreshed
        refreshed = True
        raise AssertionError("refresh must not start after the deadline")

    monkeypatch.setattr(resources.Version, "_logs_async", logs)
    monkeypatch.setattr(resources.Version, "_refresh_async", refresh)
    version = resources.Version(
        id=VERSION_ID,
        name="v1",
        source_revision="a" * 40,
        source_digest="sha256:" + "a" * 64,
        status="Running",
        terminal=False,
        origin="build",
        created_at="2026-08-15T00:00:00Z",
        started_at="2026-08-15T00:00:00Z",
        completed_at=None,
        error=None,
        tool_name="example",
        tool_generation="generation-1",
        _collection=None,  # type: ignore[arg-type]
    )

    with pytest.raises(resources.CustomToolBuildTimeoutError):
        asyncio.run(version._monitor(timeout=1.0, interval=0.1, on_event=lambda _event: None))

    assert refreshed is False


def test_monitor_does_not_dispatch_logs_after_the_deadline(monkeypatch) -> None:
    ticks = iter((0.0, 0.1, 1.1))
    monkeypatch.setattr(resources, "_clock", lambda: next(ticks))
    delivered: list[resources.BuildEvent] = []

    async def logs(*_args, **_kwargs):
        return resources.BuildLogPage(
            items=(resources.BuildEvent("too late", 1),), status="Running"
        )

    monkeypatch.setattr(resources.Version, "_logs_async", logs)
    version = resources.Version(
        id=VERSION_ID,
        name="v1",
        source_revision="a" * 40,
        source_digest="sha256:" + "a" * 64,
        status="Running",
        terminal=False,
        origin="build",
        created_at="2026-08-15T00:00:00Z",
        started_at="2026-08-15T00:00:00Z",
        completed_at=None,
        error=None,
        tool_name="example",
        tool_generation="generation-1",
        _collection=None,  # type: ignore[arg-type]
    )

    with pytest.raises(resources.CustomToolBuildTimeoutError):
        asyncio.run(version._monitor(timeout=1.0, interval=0.1, on_event=delivered.append))

    assert delivered == []


def test_monitor_maps_http_request_timeout_to_build_timeout() -> None:
    async def timed_out_request():
        try:
            raise httpx.ReadTimeout("request timed out")
        except httpx.TimeoutException as exc:
            raise resources.TamarindError("network error") from exc

    with pytest.raises(resources.CustomToolBuildTimeoutError, match="monitoring timed out"):
        asyncio.run(resources._await_with_timeout(timed_out_request(), 1.0))


def test_unbounded_monitor_preserves_transport_timeout() -> None:
    async def timed_out_request():
        try:
            raise httpx.ReadTimeout("request timed out")
        except httpx.TimeoutException as exc:
            raise resources.TamarindError("network error") from exc

    with pytest.raises(resources.TamarindError, match="network error"):
        asyncio.run(resources._await_with_timeout(timed_out_request(), None))


def test_monitor_without_callback_does_not_fetch_logs(monkeypatch) -> None:
    async def logs(*_args, **_kwargs):
        raise AssertionError("logs must not be fetched without an event callback")

    async def refresh(version, **_kwargs):
        return resources.Version(
            id=version.id,
            name=version.name,
            source_revision=version.source_revision,
            source_digest=version.source_digest,
            status="Complete",
            terminal=True,
            origin=version.origin,
            created_at=version.created_at,
            started_at=version.started_at,
            completed_at="2026-08-15T00:01:00Z",
            error=version.error,
            tool_name=version.tool_name,
            tool_generation=version.tool_generation,
            _collection=version._collection,
        )

    monkeypatch.setattr(resources.Version, "_logs_async", logs)
    monkeypatch.setattr(resources.Version, "_refresh_async", refresh)
    version = resources.Version(
        id=VERSION_ID,
        name="v1",
        source_revision="a" * 40,
        source_digest="sha256:" + "a" * 64,
        status="Running",
        terminal=False,
        origin="build",
        created_at="2026-08-15T00:00:00Z",
        started_at="2026-08-15T00:00:00Z",
        completed_at=None,
        error=None,
        tool_name="example",
        tool_generation="generation-1",
        _collection=None,  # type: ignore[arg-type]
    )

    completed = asyncio.run(version._monitor(timeout=1.0, interval=0.1, on_event=None))

    assert completed.status == "Complete"


def test_monitor_rechecks_deadline_after_terminal_refresh(monkeypatch) -> None:
    ticks = iter((0.0, 0.1, 1.1))
    monkeypatch.setattr(resources, "_clock", lambda: next(ticks))

    async def refresh(version, **_kwargs):
        return resources.Version(
            id=version.id,
            name=version.name,
            source_revision=version.source_revision,
            source_digest=version.source_digest,
            status="Complete",
            terminal=True,
            origin=version.origin,
            created_at=version.created_at,
            started_at=version.started_at,
            completed_at="2026-08-15T00:01:00Z",
            error=version.error,
            tool_name=version.tool_name,
            tool_generation=version.tool_generation,
            _collection=version._collection,
        )

    monkeypatch.setattr(resources.Version, "_refresh_async", refresh)
    version = resources.Version(
        id=VERSION_ID,
        name="v1",
        source_revision="a" * 40,
        source_digest="sha256:" + "a" * 64,
        status="Running",
        terminal=False,
        origin="build",
        created_at="2026-08-15T00:00:00Z",
        started_at="2026-08-15T00:00:00Z",
        completed_at=None,
        error=None,
        tool_name="example",
        tool_generation="generation-1",
        _collection=None,  # type: ignore[arg-type]
    )

    with pytest.raises(resources.CustomToolBuildTimeoutError, match="monitoring timed out"):
        asyncio.run(version._monitor(timeout=1.0, interval=0.1, on_event=None))


def test_monitor_without_callback_polls_until_complete(monkeypatch) -> None:
    refreshes = 0

    async def logs(*_args, **_kwargs):
        raise AssertionError("logs must not be fetched without an event callback")

    async def refresh(version, **_kwargs):
        nonlocal refreshes
        refreshes += 1
        status = "Complete" if refreshes == 2 else "Running"
        return resources.Version(
            id=version.id,
            name=version.name,
            source_revision=version.source_revision,
            source_digest=version.source_digest,
            status=status,
            terminal=status == "Complete",
            origin=version.origin,
            created_at=version.created_at,
            started_at=version.started_at,
            completed_at="2026-08-15T00:01:00Z" if status == "Complete" else None,
            error=version.error,
            tool_name=version.tool_name,
            tool_generation=version.tool_generation,
            _collection=version._collection,
        )

    monkeypatch.setattr(resources.Version, "_logs_async", logs)
    monkeypatch.setattr(resources.Version, "_refresh_async", refresh)
    version = resources.Version(
        id=VERSION_ID,
        name="v1",
        source_revision="a" * 40,
        source_digest="sha256:" + "a" * 64,
        status="Running",
        terminal=False,
        origin="build",
        created_at="2026-08-15T00:00:00Z",
        started_at="2026-08-15T00:00:00Z",
        completed_at=None,
        error=None,
        tool_name="example",
        tool_generation="generation-1",
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
            resources.BuildLogPage(items=(first,), status="Running", next_cursor="cursor-1"),
            resources.BuildLogPage(items=(final,), status="Complete", next_cursor="cursor-2"),
            resources.BuildLogPage(items=(trailing,), status="Complete"),
        )
    )

    async def logs(*_args, **_kwargs):
        return next(pages)

    async def refresh(version, **_kwargs):
        return resources.Version(
            id=version.id,
            name=version.name,
            source_revision=version.source_revision,
            source_digest=version.source_digest,
            status="Complete",
            terminal=True,
            origin=version.origin,
            created_at=version.created_at,
            started_at=version.started_at,
            completed_at="2026-08-15T00:01:00Z",
            error=version.error,
            tool_name=version.tool_name,
            tool_generation=version.tool_generation,
            _collection=version._collection,
        )

    monkeypatch.setattr(resources.Version, "_logs_async", logs)
    monkeypatch.setattr(resources.Version, "_refresh_async", refresh)
    version = resources.Version(
        id=VERSION_ID,
        name="v1",
        source_revision="a" * 40,
        source_digest="sha256:" + "a" * 64,
        status="Running",
        terminal=False,
        origin="build",
        created_at="2026-08-15T00:00:00Z",
        started_at="2026-08-15T00:00:00Z",
        completed_at=None,
        error=None,
        tool_name="example",
        tool_generation="generation-1",
        _collection=None,  # type: ignore[arg-type]
    )
    delivered: list[resources.BuildEvent] = []

    completed = asyncio.run(version._monitor(timeout=1.0, interval=0.1, on_event=delivered.append))

    assert completed.status == "Complete"
    assert delivered == [first, final, trailing]


def test_monitor_rechecks_deadline_after_terminal_log_fetch(monkeypatch) -> None:
    ticks = iter((0.0, 0.1, 1.1))
    monkeypatch.setattr(resources, "_clock", lambda: next(ticks))

    async def logs(*_args, **_kwargs):
        return resources.BuildLogPage(
            items=(resources.BuildEvent("complete", 1),), status="Complete"
        )

    monkeypatch.setattr(resources.Version, "_logs_async", logs)
    version = resources.Version(
        id=VERSION_ID,
        name="v1",
        source_revision="a" * 40,
        source_digest="sha256:" + "a" * 64,
        status="Complete",
        terminal=True,
        origin="build",
        created_at="2026-08-15T00:00:00Z",
        started_at="2026-08-15T00:00:00Z",
        completed_at="2026-08-15T00:01:00Z",
        error=None,
        tool_name="example",
        tool_generation="generation-1",
        _collection=None,  # type: ignore[arg-type]
    )

    with pytest.raises(resources.CustomToolBuildTimeoutError, match="monitoring timed out"):
        asyncio.run(version._monitor(timeout=1.0, interval=0.1, on_event=lambda _event: None))


def test_log_progress_deduplicates_cumulative_pages_without_a_cursor() -> None:
    first = resources.BuildEvent("first", 1)
    second = resources.BuildEvent("second", 2)
    progress = resources._LogProgress()

    assert progress.consume(resources.BuildLogPage(items=(first,), status="Running")) == (first,)
    assert progress.consume(resources.BuildLogPage(items=(first, second), status="Running")) == (
        second,
    )


def test_log_progress_treats_cursor_pages_as_incremental() -> None:
    first = resources.BuildEvent("first", 1)
    second = resources.BuildEvent("second", 2)
    progress = resources._LogProgress()

    assert progress.consume(
        resources.BuildLogPage(items=(first,), status="Running", next_cursor="cursor-1")
    ) == (first,)
    assert progress.consume(
        resources.BuildLogPage(items=(second,), status="Running", next_cursor="cursor-2")
    ) == (second,)


def test_log_progress_retains_and_deduplicates_a_terminal_cursor() -> None:
    first = resources.BuildEvent("first", 1)
    final = resources.BuildEvent("final", 2)
    progress = resources._LogProgress()

    assert progress.consume(
        resources.BuildLogPage(items=(first,), status="Running", next_cursor="cursor-1")
    ) == (first,)
    assert progress.consume(resources.BuildLogPage(items=(final,), status="Running")) == (final,)
    assert progress.cursor == "cursor-1"
    assert progress.consume(resources.BuildLogPage(items=(final,), status="Running")) == ()
