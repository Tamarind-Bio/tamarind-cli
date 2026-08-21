"""Resource API composed from the existing Custom Tools lifecycle.

There is intentionally no BuildRequest resource or repair protocol here.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
import math
from pathlib import Path
import time
from typing import Awaitable, Callable, Generic, TypeVar, cast

import httpx

from tamarind.custom_tools.generated import (
    GeneratedCustomToolsTransport,
    GpuType,
    MemorySize,
    PublicBuildLogPage,
    PublicCreateCustomToolRequest,
    PublicCustomTool,
    PublicToolStatus,
    PublicUpdateCustomToolRequest,
    PublicVersion,
    PublicVersionStatus,
)
from tamarind.custom_tools.packaging import (
    SourceTree,
    build_source_tree_archive,
    inspect_source_tree,
)
from tamarind.custom_tools.validation import (
    ValidationProblem,
    ValidationReport,
    validate_folder,
    validate_source_tree,
)
from tamarind.errors import (
    CustomToolBuildFailedError,
    CustomToolBuildTimeoutError,
    CustomToolUploadError,
    TamarindError,
    ValidationError,
)
from tamarind.http import DEFAULT_TIMEOUT

T = TypeVar("T")
EventCallback = Callable[["BuildEvent"], None]
_clock = time.monotonic


class _Unset:
    pass


_UNSET = _Unset()


@dataclass(frozen=True)
class Page(Generic[T]):
    items: tuple[T, ...]


@dataclass(frozen=True)
class BuildError:
    message: str


@dataclass(frozen=True)
class BuildEvent:
    message: str
    timestamp: int


@dataclass(frozen=True)
class BuildLogPage:
    items: tuple[BuildEvent, ...]
    status: str
    next_cursor: str | None = None
    error: BuildError | None = None


@dataclass(frozen=True)
class CustomTool:
    name: str
    display_name: str
    description: str
    functions: tuple[str, ...]
    status: PublicToolStatus
    gpu_type: GpuType
    memory: MemorySize
    cpu: int
    home_disk_gi: int
    max_runtime_seconds: int | None
    has_source: bool
    source_hash: str
    connection_error: str | None
    published: bool
    auto_publish: bool
    default_version: str | None
    created_at: str
    updated_at: str
    can_edit: bool
    can_build: bool
    _collection: "CustomTools" = field(repr=False, compare=False)

    def refresh(self) -> "CustomTool":
        return self._collection.get(self.name)

    def update(
        self,
        *,
        display_name: str | None | _Unset = _UNSET,
        description: str | None | _Unset = _UNSET,
        functions: list[str] | None | _Unset = _UNSET,
        gpu_type: GpuType | None | _Unset = _UNSET,
        memory: MemorySize | None | _Unset = _UNSET,
        cpu: int | None | _Unset = _UNSET,
        home_disk_gi: int | None | _Unset = _UNSET,
        auto_publish: bool | None | _Unset = _UNSET,
        est_time: str | None | _Unset = _UNSET,
        paper_url: str | None | _Unset = _UNSET,
        tags: list[str] | None | _Unset = _UNSET,
    ) -> "CustomTool":
        values = {
            "displayName": display_name,
            "description": description,
            "functions": functions,
            "gpuType": gpu_type,
            "memory": memory,
            "cpu": cpu,
            "homeDiskGi": home_disk_gi,
            "autoPublish": auto_publish,
            "estTime": est_time,
            "paperUrl": paper_url,
            "tags": tags,
        }
        body = cast(
            PublicUpdateCustomToolRequest, {k: v for k, v in values.items() if v is not _UNSET}
        )
        return self._collection._update(self.name, body)

    def validate(self, folder: str | Path) -> ValidationReport:
        return validate_folder(folder)

    def build(
        self,
        folder: str | Path,
        *,
        source_timeout: float = 180.0,
        poll_interval: float = 1.0,
    ) -> "Version":
        """Upload, finalize, deploy, and return the server-owned Version."""
        try:
            tree = inspect_source_tree(folder)
        except CustomToolUploadError as exc:
            report = ValidationReport(
                errors=(ValidationProblem(code="invalid_source_tree", path=".", message=str(exc)),)
            )
            raise ValidationError("Custom Tool source validation failed", detail=report) from None
        report = validate_source_tree(tree)
        if not report.valid:
            raise ValidationError("Custom Tool source validation failed", detail=report)
        return self._collection._build(
            self, tree, source_timeout=source_timeout, poll_interval=poll_interval
        )

    def get_version(self, name: str) -> "Version":
        return self._collection._get_version(self.name, name)

    def versions(self, *, limit: int = 50) -> Page["Version"]:
        return self._collection._versions(self.name, limit=limit)


@dataclass(frozen=True)
class Version:
    name: str
    source_revision: str
    status: PublicVersionStatus
    origin: str
    started_at: str
    completed_at: str | None
    duration_seconds: int | None
    error: BuildError | None
    tool_name: str
    _collection: "CustomTools" = field(repr=False, compare=False)

    @property
    def terminal(self) -> bool:
        return self.status in ("Complete", "Stopped")

    def refresh(self) -> "Version":
        return self._refresh(request_timeout=None)

    def _refresh(self, *, request_timeout: float | None) -> "Version":
        wire = self._collection._transport.get_custom_tool_version(
            self.tool_name, self.name, timeout=request_timeout
        )
        return _version_from_wire(self._collection, self.tool_name, wire)

    async def _refresh_async(self, *, request_timeout: float | None) -> "Version":
        wire = await self._collection._transport.get_custom_tool_version_async(
            self.tool_name, self.name, timeout=request_timeout
        )
        return _version_from_wire(self._collection, self.tool_name, wire)

    def logs(self, *, cursor: str | None = None) -> BuildLogPage:
        return self._logs(cursor=cursor, request_timeout=None)

    def _logs(self, *, cursor: str | None, request_timeout: float | None) -> BuildLogPage:
        wire = self._collection._transport.list_custom_tool_build_logs(
            self.tool_name, self.name, cursor=cursor, timeout=request_timeout
        )
        return _log_page_from_wire(wire)

    async def _logs_async(
        self, *, cursor: str | None, request_timeout: float | None
    ) -> BuildLogPage:
        wire = await self._collection._transport.list_custom_tool_build_logs_async(
            self.tool_name, self.name, cursor=cursor, timeout=request_timeout
        )
        return _log_page_from_wire(wire)

    def cancel(self) -> "Version":
        self._collection._transport.cancel_custom_tool_build(self.tool_name, self.name)
        return self.refresh()

    def publish(self) -> CustomTool:
        wire = self._collection._transport.publish_custom_tool_version(self.tool_name, self.name)
        return _tool_from_wire(self._collection, wire)

    def monitor(
        self, *, timeout: float | None, interval: float = 2.0, on_event: EventCallback | None = None
    ) -> "Version":
        timeout, interval = _validate_monitor_options(timeout=timeout, interval=interval)
        return asyncio.run(self._monitor(timeout=timeout, interval=interval, on_event=on_event))

    async def monitor_async(
        self, *, timeout: float | None, interval: float = 2.0, on_event: EventCallback | None = None
    ) -> "Version":
        timeout, interval = _validate_monitor_options(timeout=timeout, interval=interval)
        return await self._monitor(timeout=timeout, interval=interval, on_event=on_event)

    async def _monitor(
        self, *, timeout: float | None, interval: float, on_event: EventCallback | None
    ) -> "Version":
        deadline = None if timeout is None else _clock() + timeout
        cursor: str | None = None
        current = self
        while True:
            if current.terminal:
                return _require_success(current)
            remaining = None if deadline is None else deadline - _clock()
            if remaining is not None and remaining <= 0:
                raise CustomToolBuildTimeoutError(
                    f"Custom Tool Version {self.tool_name}/{self.name} is still {current.status}"
                )
            page = await _await_with_timeout(
                current._logs_async(cursor=cursor, request_timeout=remaining), remaining
            )
            if on_event is not None:
                for event in page.items:
                    on_event(event)
            cursor = page.next_cursor
            if cursor is not None:
                continue
            current = await _await_with_timeout(
                current._refresh_async(request_timeout=remaining), remaining
            )
            if current.terminal:
                return _require_success(current)
            await asyncio.sleep(interval if remaining is None else min(interval, remaining))


class CustomTools:
    """Organization-scoped Custom Tool collection."""

    def __init__(
        self, transport: GeneratedCustomToolsTransport, *, upload_timeout: float = DEFAULT_TIMEOUT
    ):
        self._transport = transport
        self._upload_timeout = upload_timeout

    def create(
        self,
        name: str,
        *,
        display_name: str = cast(str, _UNSET),
        description: str = cast(str, _UNSET),
        gpu_type: GpuType = cast(GpuType, _UNSET),
        memory: MemorySize = cast(MemorySize, _UNSET),
        cpu: int = cast(int, _UNSET),
    ) -> CustomTool:
        body: dict[str, object] = {"name": name}
        for key, value in (
            ("displayName", display_name),
            ("description", description),
            ("gpuType", gpu_type),
            ("memory", memory),
            ("cpu", cpu),
        ):
            if value is not _UNSET:
                body[key] = value
        return _tool_from_wire(
            self, self._transport.create_custom_tool(cast(PublicCreateCustomToolRequest, body))
        )

    def get(self, name: str) -> CustomTool:
        return _tool_from_wire(self, self._transport.get_custom_tool(name))

    def list(self) -> Page[CustomTool]:
        wire = self._transport.list_custom_tools()
        return Page(items=tuple(_tool_from_wire(self, item) for item in wire["items"]))

    def _update(self, name: str, body: PublicUpdateCustomToolRequest) -> CustomTool:
        return _tool_from_wire(self, self._transport.update_custom_tool(name, body))

    def _build(
        self, tool: CustomTool, tree: SourceTree, *, source_timeout: float, poll_interval: float
    ) -> Version:
        timeout, interval = _validate_monitor_options(
            timeout=source_timeout, interval=poll_interval
        )
        session = self._transport.create_custom_tool_upload(tool.name)
        archive = build_source_tree_archive(tree)
        _upload_archive(
            session["uploadUrl"],
            archive.data,
            method=session.get("uploadMethod", "PUT"),
            headers=session.get("uploadHeaders", {}),
            timeout=self._upload_timeout,
        )
        self._transport.finalize_custom_tool_upload(tool.name, session["uploadId"])
        _wait_for_source(
            tool,
            archive.digest,
            timeout=cast(float, timeout),
            interval=interval,
        )
        deployed = self._transport.deploy_custom_tool(tool.name)
        version_name = deployed["versionName"]
        if version_name is not None:
            return self._get_version(tool.name, version_name)
        return _wait_for_version_ref(
            self,
            tool.name,
            deployed["ref"],
            timeout=cast(float, timeout),
            interval=interval,
        )

    def _versions(self, tool_name: str, *, limit: int) -> Page[Version]:
        wire = self._transport.list_custom_tool_versions(tool_name, limit=limit)
        return Page(
            items=tuple(_version_from_wire(self, tool_name, item) for item in wire["items"])
        )

    def _get_version(
        self, tool_name: str, version_name: str, *, request_timeout: float | None = None
    ) -> Version:
        wire = self._transport.get_custom_tool_version(
            tool_name, version_name, timeout=request_timeout
        )
        return _version_from_wire(self, tool_name, wire)


def _wait_for_source(
    tool: CustomTool, source_hash: str, *, timeout: float, interval: float
) -> CustomTool:
    deadline = _clock() + timeout
    while True:
        current = tool.refresh()
        if current.source_hash == source_hash:
            return current
        if current.connection_error:
            raise CustomToolUploadError(f"Source extraction failed: {current.connection_error}")
        if _clock() >= deadline:
            raise CustomToolUploadError(
                f"Source extraction did not finish within {timeout:g} seconds"
            )
        time.sleep(min(interval, max(0.0, deadline - _clock())))


def _wait_for_version_ref(
    collection: CustomTools,
    tool_name: str,
    source_ref: str,
    *,
    timeout: float,
    interval: float,
) -> Version:
    deadline = _clock() + timeout
    while True:
        for version in collection._versions(tool_name, limit=50).items:
            if version.source_revision == source_ref:
                return version
        if _clock() >= deadline:
            raise CustomToolBuildTimeoutError(
                f"Custom Tool deploy {tool_name}@{source_ref[:12]} did not receive a numbered version "
                f"within {timeout:g} seconds"
            )
        time.sleep(min(interval, max(0.0, deadline - _clock())))


def _upload_archive(
    url: str, data: bytes, *, method: str, headers: dict[str, str], timeout: float
) -> None:
    try:
        response = httpx.request(method, url, content=data, headers=headers, timeout=timeout)
        response.raise_for_status()
    except httpx.TimeoutException:
        raise CustomToolUploadError(f"Source upload timed out after {timeout:g} seconds.") from None
    except httpx.HTTPStatusError as exc:
        raise CustomToolUploadError(
            f"Source upload failed with HTTP {exc.response.status_code}."
        ) from None
    except (httpx.RequestError, httpx.InvalidURL, httpx.StreamError) as exc:
        raise CustomToolUploadError(f"Source upload failed ({type(exc).__name__}).") from None


def _tool_from_wire(collection: CustomTools, wire: PublicCustomTool) -> CustomTool:
    return CustomTool(
        name=wire["name"],
        display_name=wire["displayName"],
        description=wire["description"],
        functions=tuple(wire["functions"]),
        status=wire["status"],
        gpu_type=wire["gpuType"],
        memory=wire["memory"],
        cpu=wire["cpu"],
        home_disk_gi=wire["homeDiskGi"],
        max_runtime_seconds=wire["maxRuntimeSeconds"],
        has_source=wire["hasSource"],
        source_hash=wire["sourceHash"],
        connection_error=wire["connectionError"],
        published=wire["published"],
        auto_publish=wire["autoPublish"],
        default_version=wire["defaultVersion"],
        created_at=wire["createdAt"],
        updated_at=wire["updatedAt"],
        can_edit=wire["canEdit"],
        can_build=wire["canDeploy"],
        _collection=collection,
    )


def _version_from_wire(collection: CustomTools, tool_name: str, wire: PublicVersion) -> Version:
    message = wire["errorMessage"]
    return Version(
        name=wire["versionName"],
        source_revision=wire["ref"],
        status=wire["status"],
        origin=wire["origin"],
        started_at=wire["buildStartedAt"],
        completed_at=wire["buildCompletedAt"],
        duration_seconds=wire["buildDurationSeconds"],
        error=BuildError(message) if message else None,
        tool_name=tool_name,
        _collection=collection,
    )


def _log_page_from_wire(wire: PublicBuildLogPage) -> BuildLogPage:
    message = wire.get("errorMessage")
    return BuildLogPage(
        items=tuple(BuildEvent(item["message"], item["timestamp"]) for item in wire["logs"]),
        next_cursor=wire.get("nextCursor"),
        status=wire["buildStatus"],
        error=BuildError(message) if message else None,
    )


def _require_success(version: Version) -> Version:
    if version.status == "Stopped":
        message = version.error.message if version.error else "build stopped"
        raise CustomToolBuildFailedError(
            f"Custom Tool Version {version.tool_name}/{version.name} failed: {message}",
            detail=version,
        )
    return version


async def _await_with_timeout(awaitable: Awaitable[T], remaining: float | None) -> T:
    try:
        return (
            await awaitable if remaining is None else await asyncio.wait_for(awaitable, remaining)
        )
    except asyncio.TimeoutError:
        raise CustomToolBuildTimeoutError("Custom Tool build monitoring timed out") from None
    except TamarindError:
        raise


def _validate_monitor_options(
    *, timeout: float | None, interval: float
) -> tuple[float | None, float]:
    normalized_interval = _positive_finite_number(interval, "monitor interval")
    normalized_timeout = (
        None if timeout is None else _positive_finite_number(timeout, "monitor timeout")
    )
    return normalized_timeout, normalized_interval


def _positive_finite_number(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValidationError(f"{label} must be a finite number greater than zero")
    normalized = float(value)
    if not math.isfinite(normalized) or normalized <= 0:
        raise ValidationError(f"{label} must be a finite number greater than zero")
    return normalized
