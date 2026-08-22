"""Generated from the Custom Tools projection of openapi/public-v1.json. Do not edit by hand."""

from __future__ import annotations

from typing import Any, Literal, TypeAlias, cast
from typing_extensions import NotRequired, TypedDict
from urllib.parse import quote

from tamarind.http import HTTPClient

OPENAPI_SERVER_URL = "https://app.tamarind.bio/api/"
OPENAPI_SHA256 = "38276abb99cf166a4c19290e854333221959c981be92041d32cea05fbfe1672f"


def _segment(value: str) -> str:
    return quote(value, safe="")


GpuType: TypeAlias = Literal["None", "T4", "L4", "L40S", "A10", "A100"]
MemorySize: TypeAlias = Literal[
    "8Gi", "12Gi", "24Gi", "32Gi", "48Gi", "64Gi", "90Gi", "96Gi", "180Gi"
]

PublicBuildError = TypedDict(
    "PublicBuildError",
    {
        "code": str,
        "message": str,
    },
)
PublicBuildEvent = TypedDict(
    "PublicBuildEvent",
    {
        "message": str,
        "timestamp": int,
    },
)
PublicVersionStatus: TypeAlias = Literal["Queued", "Running", "Complete", "Stopped"]
PublicBuildLogPage = TypedDict(
    "PublicBuildLogPage",
    {
        "error": PublicBuildError | None,
        "items": list[PublicBuildEvent],
        "nextCursor": str | None,
        "status": PublicVersionStatus,
    },
)
PublicVersion = TypedDict(
    "PublicVersion",
    {
        "completedAt": str | None,
        "createdAt": str,
        "error": PublicBuildError | None,
        "name": str,
        "origin": str,
        "sourceDigest": str | None,
        "sourceRevision": str,
        "startedAt": str,
        "status": PublicVersionStatus,
        "terminal": bool,
    },
)
PublicBuildResult = TypedDict(
    "PublicBuildResult",
    {
        "action": Literal["build", "reuse_image", "unchanged"],
        "version": PublicVersion,
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
PublicCreateVersionRequest = TypedDict(
    "PublicCreateVersionRequest",
    {
        "expectedSourceDigest": str,
        "uploadId": str,
    },
)
PublicCustomToolStatus: TypeAlias = Literal["Draft", "Building", "Deployed"]
PublicCustomTool = TypedDict(
    "PublicCustomTool",
    {
        "autoPublish": bool,
        "canBuild": bool,
        "canEdit": bool,
        "cpu": int,
        "createdAt": str,
        "defaultVersion": str | None,
        "description": str,
        "displayName": str,
        "estTime": str,
        "functions": list[str],
        "generation": str,
        "gpuType": GpuType,
        "hasSource": bool,
        "homeDiskGi": int,
        "maxRuntimeSeconds": int | None,
        "memory": MemorySize,
        "name": str,
        "paperUrl": str,
        "published": bool,
        "sourceDigest": str | None,
        "status": PublicCustomToolStatus,
        "tags": list[str],
        "updatedAt": str,
    },
)
PublicCustomToolPage = TypedDict(
    "PublicCustomToolPage",
    {
        "items": list[PublicCustomTool],
        "nextCursor": str | None,
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
PublicUploadSession = TypedDict(
    "PublicUploadSession",
    {
        "expiresAt": str,
        "maxBytes": int,
        "uploadHeaders": dict[str, str],
        "uploadId": str,
        "uploadMethod": Literal["PUT"],
        "uploadUrl": str,
    },
)
PublicVersionPage = TypedDict(
    "PublicVersionPage",
    {
        "items": list[PublicVersion],
        "nextCursor": str | None,
    },
)


class GeneratedCustomToolsTransport:
    def __init__(self, client: HTTPClient):
        self._client = client

    def list_custom_tools(
        self,
        status: PublicCustomToolStatus | None = None,
        published: bool | None = None,
        limit: int | None = None,
        cursor: str | None = None,
        *,
        timeout: float | None = None,
    ) -> PublicCustomToolPage:
        response = self._client.request(
            "GET",
            "custom-tools",
            params={"status": status, "published": published, "limit": limit, "cursor": cursor},
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

    def delete_custom_tool(self, name: str, if_match: str, *, timeout: float | None = None) -> None:
        self._client.request(
            "DELETE",
            f"custom-tools/{_segment(name)}",
            headers={"If-Match": if_match},
            timeout=timeout,
        )
        return None

    def get_custom_tool(self, name: str, *, timeout: float | None = None) -> PublicCustomTool:
        response = self._client.request(
            "GET",
            f"custom-tools/{_segment(name)}",
            timeout=timeout,
        )
        return cast(PublicCustomTool, response.json())

    def update_custom_tool(
        self,
        name: str,
        if_match: str,
        body: PublicUpdateCustomToolRequest,
        *,
        timeout: float | None = None,
    ) -> PublicCustomTool:
        response = self._client.request(
            "PATCH",
            f"custom-tools/{_segment(name)}",
            headers={"If-Match": if_match},
            json=body,
            timeout=timeout,
        )
        return cast(PublicCustomTool, response.json())

    def create_custom_tool_upload(
        self, name: str, if_match: str, *, timeout: float | None = None
    ) -> PublicUploadSession:
        response = self._client.request(
            "POST",
            f"custom-tools/{_segment(name)}/uploads",
            headers={"If-Match": if_match},
            timeout=timeout,
        )
        return cast(PublicUploadSession, response.json())

    def list_custom_tool_versions(
        self,
        name: str,
        status: PublicVersionStatus | None = None,
        limit: int | None = None,
        cursor: str | None = None,
        *,
        timeout: float | None = None,
    ) -> PublicVersionPage:
        response = self._client.request(
            "GET",
            f"custom-tools/{_segment(name)}/versions",
            params={"status": status, "limit": limit, "cursor": cursor},
            timeout=timeout,
        )
        return cast(PublicVersionPage, response.json())

    def build_custom_tool_version(
        self,
        name: str,
        if_match: str,
        body: PublicCreateVersionRequest,
        *,
        timeout: float | None = None,
    ) -> PublicBuildResult:
        response = self._client.request(
            "POST",
            f"custom-tools/{_segment(name)}/versions",
            headers={"If-Match": if_match},
            json=body,
            timeout=timeout,
        )
        return cast(PublicBuildResult, response.json())

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
        self, name: str, version_name: str, if_match: str, *, timeout: float | None = None
    ) -> PublicVersion:
        response = self._client.request(
            "POST",
            f"custom-tools/{_segment(name)}/versions/{_segment(version_name)}/cancel",
            headers={"If-Match": if_match},
            timeout=timeout,
        )
        return cast(PublicVersion, response.json())

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
        self, name: str, version_name: str, if_match: str, *, timeout: float | None = None
    ) -> PublicCustomTool:
        response = self._client.request(
            "POST",
            f"custom-tools/{_segment(name)}/versions/{_segment(version_name)}/publish",
            headers={"If-Match": if_match},
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
