"""Generated from openapi/custom-tools-v1.json. Do not edit by hand."""

from __future__ import annotations

from typing import Any, Literal, Protocol, TypeAlias, TypedDict, cast, overload
from typing_extensions import NotRequired
from urllib.parse import quote

from tamarind.http import HTTPClient

OPENAPI_SHA256 = "5e7ca70dcd863b84be1bc0060a0bd718eebf128a756f9da371741bb27e24d69d"


def _segment(value: str) -> str:
    return quote(value, safe="")


GpuType: TypeAlias = Literal["None", "T4", "L4", "L40S", "A10", "A100"]
MemorySize: TypeAlias = Literal[
    "8Gi", "12Gi", "24Gi", "32Gi", "48Gi", "64Gi", "90Gi", "96Gi", "180Gi"
]


class PublicBuildEvent(Protocol):
    @overload
    def __getitem__(self, key: Literal["message"]) -> str: ...
    @overload
    def __getitem__(self, key: Literal["timestamp"]) -> int: ...
    @overload
    def __getitem__(self, key: str) -> Any: ...
    def get(self, key: str, default: Any = None) -> Any: ...


class PublicBuildLogPage(Protocol):
    @overload
    def __getitem__(self, key: Literal["buildStatus"]) -> str: ...
    @overload
    def __getitem__(self, key: Literal["errorMessage"]) -> str | None: ...
    @overload
    def __getitem__(self, key: Literal["logs"]) -> list[PublicBuildEvent]: ...
    @overload
    def __getitem__(self, key: Literal["nextCursor"]) -> str | None: ...
    @overload
    def __getitem__(self, key: str) -> Any: ...
    def get(self, key: str, default: Any = None) -> Any: ...


class PublicCreateCustomToolRequest(TypedDict):
    cpu: NotRequired[int]
    description: NotRequired[str]
    displayName: NotRequired[str]
    gpuType: NotRequired[Literal["None", "T4", "L4", "L40S", "A10", "A100"]]
    memory: NotRequired[
        Literal["8Gi", "12Gi", "24Gi", "32Gi", "48Gi", "64Gi", "90Gi", "96Gi", "180Gi"]
    ]
    name: str


class PublicCustomTool(Protocol):
    @overload
    def __getitem__(self, key: Literal["autoPublish"]) -> bool: ...
    @overload
    def __getitem__(self, key: Literal["canDeploy"]) -> bool: ...
    @overload
    def __getitem__(self, key: Literal["canEdit"]) -> bool: ...
    @overload
    def __getitem__(self, key: Literal["connectionError"]) -> str | None: ...
    @overload
    def __getitem__(self, key: Literal["cpu"]) -> int: ...
    @overload
    def __getitem__(self, key: Literal["createdAt"]) -> str: ...
    @overload
    def __getitem__(self, key: Literal["defaultVersion"]) -> str | None: ...
    @overload
    def __getitem__(self, key: Literal["description"]) -> str: ...
    @overload
    def __getitem__(self, key: Literal["displayName"]) -> str: ...
    @overload
    def __getitem__(self, key: Literal["functions"]) -> list[str]: ...
    @overload
    def __getitem__(
        self, key: Literal["gpuType"]
    ) -> Literal["None", "T4", "L4", "L40S", "A10", "A100"]: ...
    @overload
    def __getitem__(self, key: Literal["hasSource"]) -> bool: ...
    @overload
    def __getitem__(self, key: Literal["homeDiskGi"]) -> int: ...
    @overload
    def __getitem__(self, key: Literal["maxRuntimeSeconds"]) -> int | None: ...
    @overload
    def __getitem__(
        self, key: Literal["memory"]
    ) -> Literal["8Gi", "12Gi", "24Gi", "32Gi", "48Gi", "64Gi", "90Gi", "96Gi", "180Gi"]: ...
    @overload
    def __getitem__(self, key: Literal["name"]) -> str: ...
    @overload
    def __getitem__(self, key: Literal["published"]) -> bool: ...
    @overload
    def __getitem__(self, key: Literal["sourceHash"]) -> str: ...
    @overload
    def __getitem__(self, key: Literal["sourceRef"]) -> str | None: ...
    @overload
    def __getitem__(self, key: Literal["status"]) -> PublicToolStatus: ...
    @overload
    def __getitem__(self, key: Literal["updatedAt"]) -> str: ...
    @overload
    def __getitem__(self, key: str) -> Any: ...
    def get(self, key: str, default: Any = None) -> Any: ...


class PublicCustomToolPage(Protocol):
    @overload
    def __getitem__(self, key: Literal["items"]) -> list[PublicCustomTool]: ...
    @overload
    def __getitem__(self, key: str) -> Any: ...
    def get(self, key: str, default: Any = None) -> Any: ...


class PublicDeployRequest(TypedDict):
    carryForwardFromVersion: NotRequired[str | None]
    expectedSourceRef: NotRequired[str | None]


class PublicDeployResult(Protocol):
    @overload
    def __getitem__(self, key: Literal["path"]) -> Literal["noop", "saved", "building"]: ...
    @overload
    def __getitem__(self, key: Literal["ref"]) -> str: ...
    @overload
    def __getitem__(self, key: Literal["versionName"]) -> str | None: ...
    @overload
    def __getitem__(self, key: str) -> Any: ...
    def get(self, key: str, default: Any = None) -> Any: ...


class PublicProblem(Protocol):
    @overload
    def __getitem__(self, key: Literal["code"]) -> str: ...
    @overload
    def __getitem__(self, key: Literal["detail"]) -> str | None: ...
    @overload
    def __getitem__(self, key: Literal["errors"]) -> list[dict[str, Any]] | None: ...
    @overload
    def __getitem__(self, key: Literal["status"]) -> int: ...
    @overload
    def __getitem__(self, key: Literal["title"]) -> str: ...
    @overload
    def __getitem__(self, key: Literal["type"]) -> str: ...
    @overload
    def __getitem__(self, key: str) -> Any: ...
    def get(self, key: str, default: Any = None) -> Any: ...


class PublicStatus(Protocol):
    @overload
    def __getitem__(self, key: Literal["status"]) -> str: ...
    @overload
    def __getitem__(self, key: str) -> Any: ...
    def get(self, key: str, default: Any = None) -> Any: ...


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


class PublicUploadFinalized(Protocol):
    @overload
    def __getitem__(self, key: Literal["status"]) -> Literal["processing"]: ...
    @overload
    def __getitem__(self, key: str) -> Any: ...
    def get(self, key: str, default: Any = None) -> Any: ...


class PublicUploadSession(Protocol):
    @overload
    def __getitem__(self, key: Literal["expiresIn"]) -> int: ...
    @overload
    def __getitem__(self, key: Literal["uploadHeaders"]) -> dict[str, str]: ...
    @overload
    def __getitem__(self, key: Literal["uploadId"]) -> str: ...
    @overload
    def __getitem__(self, key: Literal["uploadMethod"]) -> Literal["PUT"]: ...
    @overload
    def __getitem__(self, key: Literal["uploadUrl"]) -> str: ...
    @overload
    def __getitem__(self, key: str) -> Any: ...
    def get(self, key: str, default: Any = None) -> Any: ...


class PublicVersion(Protocol):
    @overload
    def __getitem__(self, key: Literal["buildCompletedAt"]) -> str | None: ...
    @overload
    def __getitem__(self, key: Literal["buildDurationSeconds"]) -> int | None: ...
    @overload
    def __getitem__(self, key: Literal["buildStartedAt"]) -> str: ...
    @overload
    def __getitem__(self, key: Literal["errorMessage"]) -> str | None: ...
    @overload
    def __getitem__(self, key: Literal["origin"]) -> PublicVersionOrigin: ...
    @overload
    def __getitem__(self, key: Literal["ref"]) -> str: ...
    @overload
    def __getitem__(self, key: Literal["status"]) -> PublicVersionStatus: ...
    @overload
    def __getitem__(self, key: Literal["versionName"]) -> str: ...
    @overload
    def __getitem__(self, key: str) -> Any: ...
    def get(self, key: str, default: Any = None) -> Any: ...


class PublicVersionPage(Protocol):
    @overload
    def __getitem__(self, key: Literal["items"]) -> list[PublicVersion]: ...
    @overload
    def __getitem__(self, key: str) -> Any: ...
    def get(self, key: str, default: Any = None) -> Any: ...


PublicToolStatus: TypeAlias = Literal["Draft", "Building", "Deployed"]
PublicVersionOrigin: TypeAlias = Literal["tamarind", "build", "save", "github", "rollback"]
PublicVersionStatus: TypeAlias = Literal["Queued", "Running", "Complete", "Stopped"]


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
