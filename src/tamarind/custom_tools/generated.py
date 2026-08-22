"""Generated from openapi/custom-tools-v1.json. Do not edit by hand."""

from __future__ import annotations

from typing import Any, Literal, TypeAlias, TypedDict, cast
from typing_extensions import NotRequired
from urllib.parse import quote

from tamarind.http import HTTPClient

OPENAPI_SERVER_URL = "https://app.tamarind.bio/api/"
OPENAPI_SHA256 = "5e7ca70dcd863b84be1bc0060a0bd718eebf128a756f9da371741bb27e24d69d"


def _segment(value: str) -> str:
    return quote(value, safe="")


GpuType: TypeAlias = Literal["None", "T4", "L4", "L40S", "A10", "A100"]
MemorySize: TypeAlias = Literal[
    "8Gi", "12Gi", "24Gi", "32Gi", "48Gi", "64Gi", "90Gi", "96Gi", "180Gi"
]

PublicBuildEvent = TypedDict(
    "PublicBuildEvent",
    {
        "message": str,
        "timestamp": int,
    },
)
PublicBuildLogPage = TypedDict(
    "PublicBuildLogPage",
    {
        "buildStatus": str,
        "errorMessage": NotRequired[str | None],
        "logs": list[PublicBuildEvent],
        "nextCursor": NotRequired[str | None],
    },
)
PublicCreateCustomToolRequest = TypedDict(
    "PublicCreateCustomToolRequest",
    {
        "cpu": NotRequired[int],
        "description": NotRequired[str],
        "displayName": NotRequired[str],
        "gpuType": NotRequired[GpuType],
        "memory": NotRequired[MemorySize],
        "name": str,
    },
)
PublicToolStatus: TypeAlias = Literal["Draft", "Building", "Deployed"]
PublicCustomTool = TypedDict(
    "PublicCustomTool",
    {
        "autoPublish": bool,
        "canDeploy": bool,
        "canEdit": bool,
        "connectionError": str | None,
        "cpu": int,
        "createdAt": str,
        "defaultVersion": str | None,
        "description": str,
        "displayName": str,
        "functions": list[str],
        "gpuType": GpuType,
        "hasSource": bool,
        "homeDiskGi": int,
        "maxRuntimeSeconds": int | None,
        "memory": MemorySize,
        "name": str,
        "published": bool,
        "sourceHash": str,
        "sourceRef": str | None,
        "status": PublicToolStatus,
        "updatedAt": str,
    },
)
PublicCustomToolPage = TypedDict(
    "PublicCustomToolPage",
    {
        "items": list[PublicCustomTool],
    },
)
PublicDeployRequest = TypedDict(
    "PublicDeployRequest",
    {
        "carryForwardFromVersion": NotRequired[str | None],
        "expectedSourceRef": NotRequired[str | None],
    },
)
PublicDeployResult = TypedDict(
    "PublicDeployResult",
    {
        "path": Literal["noop", "saved", "building"],
        "ref": str,
        "versionName": str | None,
    },
)
PublicProblem = TypedDict(
    "PublicProblem",
    {
        "code": str,
        "detail": NotRequired[str | None],
        "errors": NotRequired[list[dict[str, Any]] | None],
        "status": int,
        "title": str,
        "type": str,
    },
)
PublicStatus = TypedDict(
    "PublicStatus",
    {
        "status": str,
    },
)
PublicUpdateCustomToolRequest = TypedDict(
    "PublicUpdateCustomToolRequest",
    {
        "autoPublish": NotRequired[bool | None],
        "cpu": NotRequired[int | None],
        "description": NotRequired[str | None],
        "displayName": NotRequired[str | None],
        "estTime": NotRequired[str | None],
        "functions": NotRequired[list[str] | None],
        "gpuType": NotRequired[GpuType | None],
        "homeDiskGi": NotRequired[int | None],
        "memory": NotRequired[MemorySize | None],
        "paperUrl": NotRequired[str | None],
        "tags": NotRequired[list[str] | None],
    },
)
PublicUploadFinalized = TypedDict(
    "PublicUploadFinalized",
    {
        "status": Literal["processing"],
    },
)
PublicUploadSession = TypedDict(
    "PublicUploadSession",
    {
        "expiresIn": int,
        "uploadHeaders": NotRequired[dict[str, str]],
        "uploadId": str,
        "uploadMethod": NotRequired[Literal["PUT"]],
        "uploadUrl": str,
    },
)
PublicVersionOrigin: TypeAlias = Literal["tamarind", "build", "save", "github", "rollback"]
PublicVersionStatus: TypeAlias = Literal["Queued", "Running", "Complete", "Stopped"]
PublicVersion = TypedDict(
    "PublicVersion",
    {
        "buildCompletedAt": str | None,
        "buildDurationSeconds": int | None,
        "buildStartedAt": str,
        "errorMessage": str | None,
        "origin": PublicVersionOrigin,
        "ref": str,
        "status": PublicVersionStatus,
        "versionName": str,
    },
)
PublicVersionPage = TypedDict(
    "PublicVersionPage",
    {
        "items": list[PublicVersion],
    },
)


class GeneratedCustomToolsTransport:
    def __init__(self, client: HTTPClient):
        self._client = client

    def list_custom_tools(self, *, timeout: float | None = None) -> PublicCustomToolPage:
        response = self._client.request(
            "GET",
            "custom-tools",
            timeout=timeout,
        )
        return cast(PublicCustomToolPage, response.json())

    def create_custom_tool(
        self, body: PublicCreateCustomToolRequest, *, timeout: float | None = None
    ) -> PublicCustomTool:
        response = self._client.request(
            "POST",
            "custom-tools",
            json=body,
            timeout=timeout,
        )
        return cast(PublicCustomTool, response.json())

    def get_custom_tool(self, name: str, *, timeout: float | None = None) -> PublicCustomTool:
        response = self._client.request(
            "GET",
            f"custom-tools/{_segment(name)}",
            timeout=timeout,
        )
        return cast(PublicCustomTool, response.json())

    def update_custom_tool(
        self, name: str, body: PublicUpdateCustomToolRequest, *, timeout: float | None = None
    ) -> PublicCustomTool:
        response = self._client.request(
            "PATCH",
            f"custom-tools/{_segment(name)}",
            json=body,
            timeout=timeout,
        )
        return cast(PublicCustomTool, response.json())

    def deploy_custom_tool(
        self, name: str, body: PublicDeployRequest | None = None, *, timeout: float | None = None
    ) -> PublicDeployResult:
        if body is None:
            response = self._client.request(
                "POST",
                f"custom-tools/{_segment(name)}/deploy",
                timeout=timeout,
            )
        else:
            response = self._client.request(
                "POST",
                f"custom-tools/{_segment(name)}/deploy",
                json=body,
                timeout=timeout,
            )
        return cast(PublicDeployResult, response.json())

    def create_custom_tool_upload(
        self, name: str, *, timeout: float | None = None
    ) -> PublicUploadSession:
        response = self._client.request(
            "POST",
            f"custom-tools/{_segment(name)}/uploads",
            timeout=timeout,
        )
        return cast(PublicUploadSession, response.json())

    def finalize_custom_tool_upload(
        self, name: str, upload_id: str, *, timeout: float | None = None
    ) -> PublicUploadFinalized:
        response = self._client.request(
            "POST",
            f"custom-tools/{_segment(name)}/uploads/{_segment(upload_id)}/finalize",
            timeout=timeout,
        )
        return cast(PublicUploadFinalized, response.json())

    def list_custom_tool_versions(
        self, name: str, limit: int | None = None, *, timeout: float | None = None
    ) -> PublicVersionPage:
        response = self._client.request(
            "GET",
            f"custom-tools/{_segment(name)}/versions",
            params={"limit": limit},
            timeout=timeout,
        )
        return cast(PublicVersionPage, response.json())

    def get_custom_tool_version(
        self, name: str, version_name: str, *, timeout: float | None = None
    ) -> PublicVersion:
        response = self._client.request(
            "GET",
            f"custom-tools/{_segment(name)}/versions/{_segment(version_name)}",
            timeout=timeout,
        )
        return cast(PublicVersion, response.json())

    def cancel_custom_tool_build(
        self, name: str, version_name: str, *, timeout: float | None = None
    ) -> PublicStatus:
        response = self._client.request(
            "POST",
            f"custom-tools/{_segment(name)}/versions/{_segment(version_name)}/cancel",
            timeout=timeout,
        )
        return cast(PublicStatus, response.json())

    def list_custom_tool_build_logs(
        self,
        name: str,
        version_name: str,
        cursor: str | None = None,
        *,
        timeout: float | None = None,
    ) -> PublicBuildLogPage:
        response = self._client.request(
            "GET",
            f"custom-tools/{_segment(name)}/versions/{_segment(version_name)}/logs",
            params={"cursor": cursor},
            timeout=timeout,
        )
        return cast(PublicBuildLogPage, response.json())

    def publish_custom_tool_version(
        self, name: str, version_name: str, *, timeout: float | None = None
    ) -> PublicCustomTool:
        response = self._client.request(
            "POST",
            f"custom-tools/{_segment(name)}/versions/{_segment(version_name)}/publish",
            timeout=timeout,
        )
        return cast(PublicCustomTool, response.json())

    async def get_custom_tool_version_async(
        self, name: str, version_name: str, *, timeout: float | None = None
    ) -> PublicVersion:
        response = await self._client.request_async(
            "GET",
            f"custom-tools/{_segment(name)}/versions/{_segment(version_name)}",
            timeout=timeout,
        )
        return cast(PublicVersion, response.json())

    async def list_custom_tool_build_logs_async(
        self,
        name: str,
        version_name: str,
        cursor: str | None = None,
        *,
        timeout: float | None = None,
    ) -> PublicBuildLogPage:
        response = await self._client.request_async(
            "GET",
            f"custom-tools/{_segment(name)}/versions/{_segment(version_name)}/logs",
            params={"cursor": cursor},
            timeout=timeout,
        )
        return cast(PublicBuildLogPage, response.json())
