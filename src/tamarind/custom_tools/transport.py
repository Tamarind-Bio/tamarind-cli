"""Handwritten facade adapter over the pinned openapi-python-client output."""

from __future__ import annotations

from typing import Any, NamedTuple, TypeAlias, cast

from tamarind.custom_tools._generated.client import Client as GeneratedClient
from tamarind.custom_tools._generated.models.public_create_custom_tool_request import (
    PublicCreateCustomToolRequest as CreateModel,
)
from tamarind.custom_tools._generated.models.public_create_version_request import (
    PublicCreateVersionRequest as CreateVersionModel,
)
from tamarind.custom_tools._generated.models.public_custom_tool_gputype import (
    PublicCustomToolGputype as GeneratedGpuType,
)
from tamarind.custom_tools._generated.models.public_custom_tool_memory import (
    PublicCustomToolMemory as GeneratedMemorySize,
)
from tamarind.custom_tools._generated.models.public_custom_tool_status import (
    PublicCustomToolStatus as GeneratedToolStatus,
)
from tamarind.custom_tools._generated.models.public_update_custom_tool_request import (
    PublicUpdateCustomToolRequest as UpdateModel,
)
from tamarind.custom_tools._generated.models.public_version_status import (
    PublicVersionStatus as GeneratedVersionStatus,
)
from tamarind.errors import TamarindError
from tamarind.http import HTTPClient

from ._generated.api.custom_tools import (
    build_custom_tool_version,
    cancel_custom_tool_build,
    create_custom_tool,
    create_custom_tool_upload,
    delete_custom_tool,
    get_custom_tool,
    get_custom_tool_version,
    list_custom_tool_build_logs,
    list_custom_tool_versions,
    list_custom_tools,
    publish_custom_tool_version,
    update_custom_tool,
)

GpuType: TypeAlias = GeneratedGpuType
MemorySize: TypeAlias = GeneratedMemorySize
PublicCustomToolStatus: TypeAlias = GeneratedToolStatus
PublicVersionStatus: TypeAlias = GeneratedVersionStatus
PublicCreateCustomToolRequest: TypeAlias = dict[str, Any]
PublicUpdateCustomToolRequest: TypeAlias = dict[str, Any]
PublicCreateVersionRequest: TypeAlias = dict[str, Any]
PublicCustomTool: TypeAlias = dict[str, Any]
PublicVersion: TypeAlias = dict[str, Any]
PublicBuildResult: TypeAlias = dict[str, Any]
PublicBuildLogPage: TypeAlias = dict[str, Any]


class _Operation(NamedTuple):
    endpoint: Any
    success_status: int


_LIST_CUSTOM_TOOLS = _Operation(list_custom_tools, 200)
_CREATE_CUSTOM_TOOL = _Operation(create_custom_tool, 201)
_GET_CUSTOM_TOOL = _Operation(get_custom_tool, 200)
_UPDATE_CUSTOM_TOOL = _Operation(update_custom_tool, 200)
_CREATE_CUSTOM_TOOL_UPLOAD = _Operation(create_custom_tool_upload, 201)
_LIST_CUSTOM_TOOL_VERSIONS = _Operation(list_custom_tool_versions, 200)
_BUILD_CUSTOM_TOOL_VERSION = _Operation(build_custom_tool_version, 202)
_GET_CUSTOM_TOOL_VERSION = _Operation(get_custom_tool_version, 200)
_CANCEL_CUSTOM_TOOL_BUILD = _Operation(cancel_custom_tool_build, 200)
_LIST_CUSTOM_TOOL_BUILD_LOGS = _Operation(list_custom_tool_build_logs, 200)
_PUBLISH_CUSTOM_TOOL_VERSION = _Operation(publish_custom_tool_version, 200)

_MODEL_OPERATIONS = (
    _LIST_CUSTOM_TOOLS,
    _CREATE_CUSTOM_TOOL,
    _GET_CUSTOM_TOOL,
    _UPDATE_CUSTOM_TOOL,
    _CREATE_CUSTOM_TOOL_UPLOAD,
    _LIST_CUSTOM_TOOL_VERSIONS,
    _BUILD_CUSTOM_TOOL_VERSION,
    _GET_CUSTOM_TOOL_VERSION,
    _CANCEL_CUSTOM_TOOL_BUILD,
    _LIST_CUSTOM_TOOL_BUILD_LOGS,
    _PUBLISH_CUSTOM_TOOL_VERSION,
)


class GeneratedCustomToolsTransport:
    """Expose the generated endpoint semantics through Tamarind's shared HTTP/error boundary."""

    def __init__(self, client: HTTPClient):
        self._client = client
        self._parser = GeneratedClient(base_url=client.base_url)

    def _sync(
        self, operation: _Operation, kwargs: dict[str, Any], timeout: float | None = None
    ) -> Any:
        response = self._client.request(timeout=timeout, **_http_kwargs(kwargs))
        return self._parse(operation, response)

    async def _async(
        self, operation: _Operation, kwargs: dict[str, Any], timeout: float | None = None
    ) -> Any:
        response = await self._client.request_async(timeout=timeout, **_http_kwargs(kwargs))
        return self._parse(operation, response)

    def _parse(self, operation: _Operation, response: Any) -> dict[str, Any]:
        if response.status_code != operation.success_status:
            raise TamarindError("Custom Tools response did not match the generated contract")
        try:
            parsed = operation.endpoint._parse_response(client=self._parser, response=response)
        except (AttributeError, KeyError, TypeError, ValueError) as exc:
            raise TamarindError(
                "Custom Tools response did not match the generated contract"
            ) from exc
        if parsed is None or not hasattr(parsed, "to_dict"):
            raise TamarindError("Custom Tools response did not match the generated contract")
        return cast(dict[str, Any], parsed.to_dict())

    def list_custom_tools(
        self,
        status: PublicCustomToolStatus | None = None,
        published: bool | None = None,
        limit: int | None = None,
        cursor: str | None = None,
        *,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        return self._sync(
            _LIST_CUSTOM_TOOLS,
            list_custom_tools._get_kwargs(
                status=GeneratedToolStatus(status) if status is not None else None,
                published=published,
                limit=50 if limit is None else limit,
                cursor=cursor,
            ),
            timeout,
        )

    def create_custom_tool(
        self, body: PublicCreateCustomToolRequest, *, timeout: float | None = None
    ) -> PublicCustomTool:
        return self._sync(
            _CREATE_CUSTOM_TOOL,
            create_custom_tool._get_kwargs(body=CreateModel.from_dict(body)),
            timeout,
        )

    def delete_custom_tool(
        self, name: str, generation: str, *, timeout: float | None = None
    ) -> None:
        response = self._client.request(
            timeout=timeout,
            **_http_kwargs(delete_custom_tool._get_kwargs(name, if_match=_etag(generation))),
        )
        if response.status_code != 204:
            raise TamarindError("Custom Tools response did not match the generated contract")

    def get_custom_tool(self, name: str, *, timeout: float | None = None) -> PublicCustomTool:
        return self._sync(_GET_CUSTOM_TOOL, get_custom_tool._get_kwargs(name), timeout)

    def update_custom_tool(
        self,
        name: str,
        generation: str,
        body: PublicUpdateCustomToolRequest,
        *,
        timeout: float | None = None,
    ) -> PublicCustomTool:
        return self._sync(
            _UPDATE_CUSTOM_TOOL,
            update_custom_tool._get_kwargs(
                name, body=UpdateModel.from_dict(body), if_match=_etag(generation)
            ),
            timeout,
        )

    def create_custom_tool_upload(
        self, name: str, generation: str, *, timeout: float | None = None
    ) -> dict[str, Any]:
        return self._sync(
            _CREATE_CUSTOM_TOOL_UPLOAD,
            create_custom_tool_upload._get_kwargs(name, generation),
            timeout,
        )

    def list_custom_tool_versions(
        self,
        name: str,
        generation: str,
        status: PublicVersionStatus | None = None,
        limit: int | None = None,
        cursor: str | None = None,
        *,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        return self._sync(
            _LIST_CUSTOM_TOOL_VERSIONS,
            list_custom_tool_versions._get_kwargs(
                name,
                generation,
                status=GeneratedVersionStatus(status) if status is not None else None,
                limit=50 if limit is None else limit,
                cursor=cursor,
            ),
            timeout,
        )

    def build_custom_tool_version(
        self,
        name: str,
        generation: str,
        body: PublicCreateVersionRequest,
        *,
        timeout: float | None = None,
    ) -> PublicBuildResult:
        return self._sync(
            _BUILD_CUSTOM_TOOL_VERSION,
            build_custom_tool_version._get_kwargs(
                name, generation, body=CreateVersionModel.from_dict(body)
            ),
            timeout,
        )

    def get_custom_tool_version(
        self, name: str, version_name: str, generation: str, *, timeout: float | None = None
    ) -> PublicVersion:
        return self._sync(
            _GET_CUSTOM_TOOL_VERSION,
            get_custom_tool_version._get_kwargs(name, generation, version_name),
            timeout,
        )

    def cancel_custom_tool_build(
        self, name: str, version_name: str, generation: str, *, timeout: float | None = None
    ) -> PublicVersion:
        return self._sync(
            _CANCEL_CUSTOM_TOOL_BUILD,
            cancel_custom_tool_build._get_kwargs(name, generation, version_name),
            timeout,
        )

    def list_custom_tool_build_logs(
        self,
        name: str,
        version_name: str,
        generation: str,
        cursor: str | None = None,
        *,
        timeout: float | None = None,
    ) -> PublicBuildLogPage:
        return self._sync(
            _LIST_CUSTOM_TOOL_BUILD_LOGS,
            list_custom_tool_build_logs._get_kwargs(name, generation, version_name, cursor=cursor),
            timeout,
        )

    def publish_custom_tool_version(
        self, name: str, version_name: str, generation: str, *, timeout: float | None = None
    ) -> PublicCustomTool:
        return self._sync(
            _PUBLISH_CUSTOM_TOOL_VERSION,
            publish_custom_tool_version._get_kwargs(name, generation, version_name),
            timeout,
        )

    async def get_custom_tool_version_async(
        self, name: str, version_name: str, generation: str, *, timeout: float | None = None
    ) -> PublicVersion:
        return await self._async(
            _GET_CUSTOM_TOOL_VERSION,
            get_custom_tool_version._get_kwargs(name, generation, version_name),
            timeout,
        )

    async def list_custom_tool_build_logs_async(
        self,
        name: str,
        version_name: str,
        generation: str,
        cursor: str | None = None,
        *,
        timeout: float | None = None,
    ) -> PublicBuildLogPage:
        return await self._async(
            _LIST_CUSTOM_TOOL_BUILD_LOGS,
            list_custom_tool_build_logs._get_kwargs(name, generation, version_name, cursor=cursor),
            timeout,
        )


def _etag(generation: str) -> str:
    return f'"{generation}"'


def _http_kwargs(kwargs: dict[str, Any]) -> dict[str, Any]:
    values = dict(kwargs)
    values["path"] = values.pop("url")
    return cast(dict[str, Any], values)
