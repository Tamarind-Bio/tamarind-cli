"""Generated from openapi/custom-tools-v1.json. Do not edit by hand."""

from __future__ import annotations

from typing import Any, Literal, TypeAlias, TypedDict, cast
from typing_extensions import NotRequired
from urllib.parse import quote

from tamarind.http import HTTPClient

OPENAPI_SHA256 = "0a2b91ce20bca7d992f892fd31920d6691fe7888b48fdfc56bbb59b5421eb8d3"


def _segment(value: str) -> str:
    return quote(value, safe="")


PublicCustomToolStatus: TypeAlias = Literal["Draft", "Building", "Deployed"]
PublicVersionStatus: TypeAlias = Literal["Queued", "Running", "Complete", "Stopped"]


class PublicBuildError(TypedDict):
    code: str
    message: str


class PublicBuildEvent(TypedDict):
    message: str
    timestamp: int


class PublicBuildLogPage(TypedDict):
    error: PublicBuildError | None
    items: list[PublicBuildEvent]
    nextCursor: str | None
    status: PublicVersionStatus


class PublicBuildResult(TypedDict):
    action: Literal["build", "reuse_image", "unchanged"]
    version: PublicVersion


class PublicCreateCustomToolRequest(TypedDict):
    cpu: NotRequired[int]
    description: NotRequired[str]
    displayName: NotRequired[str]
    gpuType: NotRequired[Literal["None", "T4", "L4", "L40S", "A10", "A100"]]
    memory: NotRequired[
        Literal["8Gi", "12Gi", "24Gi", "32Gi", "48Gi", "64Gi", "90Gi", "96Gi", "180Gi"]
    ]
    name: str


class PublicCreateVersionRequest(TypedDict):
    expectedSourceDigest: str
    uploadId: str


class PublicCustomTool(TypedDict):
    autoPublish: bool
    canBuild: bool
    canEdit: bool
    cpu: int
    createdAt: str
    defaultVersion: str | None
    description: str
    displayName: str
    estTime: str
    functions: list[str]
    generation: str
    gpuType: Literal["None", "T4", "L4", "L40S", "A10", "A100"]
    hasSource: bool
    homeDiskGi: int
    maxRuntimeSeconds: int | None
    memory: Literal["8Gi", "12Gi", "24Gi", "32Gi", "48Gi", "64Gi", "90Gi", "96Gi", "180Gi"]
    name: str
    paperUrl: str
    published: bool
    sourceDigest: str | None
    status: PublicCustomToolStatus
    tags: list[str]
    updatedAt: str


class PublicCustomToolPage(TypedDict):
    items: list[PublicCustomTool]
    nextCursor: str | None


class PublicProblem(TypedDict):
    code: str
    detail: NotRequired[str | None]
    errors: NotRequired[list[dict[str, Any]] | None]
    status: int
    title: str
    type: str


class PublicUpdateCustomToolRequest(TypedDict):
    autoPublish: NotRequired[bool | None]
    cpu: NotRequired[int | None]
    description: NotRequired[str | None]
    displayName: NotRequired[str | None]
    estTime: NotRequired[str | None]
    functions: NotRequired[list[str] | None]
    gpuType: NotRequired[Literal["None", "T4", "L4", "L40S", "A10", "A100"] | None]
    homeDiskGi: NotRequired[int | None]
    memory: NotRequired[
        Literal["8Gi", "12Gi", "24Gi", "32Gi", "48Gi", "64Gi", "90Gi", "96Gi", "180Gi"] | None
    ]
    paperUrl: NotRequired[str | None]
    tags: NotRequired[list[str] | None]


class PublicUploadSession(TypedDict):
    expiresAt: str
    maxBytes: int
    uploadHeaders: dict[str, str]
    uploadId: str
    uploadMethod: Literal["PUT"]
    uploadUrl: str


class PublicVersion(TypedDict):
    completedAt: str | None
    createdAt: str
    error: PublicBuildError | None
    name: str
    origin: str
    sourceDigest: str | None
    sourceRevision: str
    startedAt: str
    status: PublicVersionStatus
    terminal: bool


class PublicVersionPage(TypedDict):
    items: list[PublicVersion]
    nextCursor: str | None


class GeneratedCustomToolsTransport:
    def __init__(self, client: HTTPClient):
        self._client = client

    def fork(self) -> GeneratedCustomToolsTransport:
        return GeneratedCustomToolsTransport(self._client.fork())

    def close(self) -> None:
        self._client.close()

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
