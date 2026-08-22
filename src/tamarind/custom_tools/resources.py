"""Resource API composed from the existing Custom Tools lifecycle.

There is intentionally no BuildRequest resource or repair protocol here.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
import math
from pathlib import Path
import time
from typing import Awaitable, BinaryIO, Callable, Generic, TypeVar, cast

import httpx

from tamarind.custom_tools.generated import (
    GeneratedCustomToolsTransport,
    GpuType,
    MemorySize,
    PublicBuildLogPage,
    PublicCreateCustomToolRequest,
    PublicCreateVersionRequest,
    PublicCustomTool,
    PublicCustomToolStatus,
    PublicUpdateCustomToolRequest,
    PublicVersion,
    PublicVersionStatus,
)
from tamarind.custom_tools.packaging import (
    MAX_TOOL_SOURCE_BYTES,
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
    next_cursor: str | None = None


@dataclass(frozen=True)
class BuildError:
    code: str
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


@dataclass
class _LogProgress:
    """Own log-resume state without letting it control Version polling."""

    cursor: str | None = None
    delivered_cursor: str | None = None
    delivered_at_cursor: int = 0

    def consume(self, page: BuildLogPage) -> tuple[BuildEvent, ...]:
        requested_cursor = self.cursor
        if requested_cursor == self.delivered_cursor:
            events = page.items[self.delivered_at_cursor :]
        else:
            events = page.items
        next_cursor = page.next_cursor if page.next_cursor is not None else requested_cursor
        if next_cursor == requested_cursor:
            self.delivered_cursor = requested_cursor
            self.delivered_at_cursor = max(self.delivered_at_cursor, len(page.items))
        else:
            self.delivered_cursor = None
            self.delivered_at_cursor = 0
        self.cursor = next_cursor
        return events


@dataclass(frozen=True)
class CustomTool:
    name: str
    generation: str
    display_name: str
    description: str
    functions: tuple[str, ...]
    status: PublicCustomToolStatus
    gpu_type: GpuType
    memory: MemorySize
    cpu: int
    home_disk_gi: int
    max_runtime_seconds: int | None
    has_source: bool
    source_digest: str | None
    published: bool
    auto_publish: bool
    est_time: str
    paper_url: str
    tags: tuple[str, ...]
    default_version: str | None
    created_at: str
    updated_at: str
    can_edit: bool
    can_build: bool
    _collection: "CustomTools" = field(repr=False, compare=False)

    def refresh(self) -> "CustomTool":
        return self._refresh(request_timeout=None)

    def _refresh(self, *, request_timeout: float | None) -> "CustomTool":
        return self._collection._get(self.name, request_timeout=request_timeout)

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
        return self._collection._update(self.name, self.generation, body)

    def validate(self, folder: str | Path) -> ValidationReport:
        return validate_folder(folder)

    def build(
        self,
        folder: str | Path,
        *,
        source_timeout: float = 180.0,
    ) -> "Version":
        """Upload the deterministic archive and start its server-owned build Version."""
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
        return self._collection._build(self, tree, source_timeout=source_timeout)

    def get_version(self, name: str) -> "Version":
        return self._collection._get_version(self.name, name)

    def versions(
        self,
        *,
        status: PublicVersionStatus | None = None,
        limit: int = 50,
        cursor: str | None = None,
    ) -> Page["Version"]:
        return self._collection._versions(self.name, status=status, limit=limit, cursor=cursor)


@dataclass(frozen=True)
class Version:
    name: str
    source_revision: str
    source_digest: str | None
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
        generation = self._collection.get(self.tool_name).generation
        wire = self._collection._transport.cancel_custom_tool_build(
            self.tool_name, self.name, generation
        )
        return _version_from_wire(self._collection, self.tool_name, wire)

    def publish(self) -> CustomTool:
        generation = self._collection.get(self.tool_name).generation
        wire = self._collection._transport.publish_custom_tool_version(
            self.tool_name, self.name, generation
        )
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
        logs = _LogProgress() if on_event is not None else None
        current = self

        def remaining_budget() -> float | None:
            if deadline is None:
                return None
            remaining = deadline - _clock()
            if remaining <= 0:
                raise CustomToolBuildTimeoutError(
                    f"Custom Tool Version {self.tool_name}/{self.name} monitoring timed out "
                    f"while status is {current.status}"
                )
            return remaining

        async def deliver_log_page(version: Version) -> bool:
            if logs is None or on_event is None:
                return False
            requested_cursor = logs.cursor
            remaining = remaining_budget()
            page = await _await_with_timeout(
                version._logs_async(cursor=requested_cursor, request_timeout=remaining), remaining
            )
            for event in logs.consume(page):
                on_event(event)
                remaining_budget()
            remaining_budget()
            return page.next_cursor is not None and page.next_cursor != requested_cursor

        while not current.terminal:
            if logs is not None:
                await deliver_log_page(current)
            remaining = remaining_budget()
            current = await _await_with_timeout(
                current._refresh_async(request_timeout=remaining), remaining
            )
            if not current.terminal:
                remaining = remaining_budget()
                await asyncio.sleep(interval if remaining is None else min(interval, remaining))

        while await deliver_log_page(current):
            pass
        return _require_success(current)


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
        return self._get(name, request_timeout=None)

    def _get(self, name: str, *, request_timeout: float | None) -> CustomTool:
        return _tool_from_wire(self, self._transport.get_custom_tool(name, timeout=request_timeout))

    def list(
        self,
        *,
        status: PublicCustomToolStatus | None = None,
        published: bool | None = None,
        limit: int = 50,
        cursor: str | None = None,
    ) -> Page[CustomTool]:
        wire = self._transport.list_custom_tools(
            status=status,
            published=published,
            limit=limit,
            cursor=cursor,
        )
        return Page(
            items=tuple(_tool_from_wire(self, item) for item in wire["items"]),
            next_cursor=wire["nextCursor"],
        )

    def _update(
        self, name: str, generation: str, body: PublicUpdateCustomToolRequest
    ) -> CustomTool:
        return _tool_from_wire(self, self._transport.update_custom_tool(name, generation, body))

    def _build(self, tool: CustomTool, tree: SourceTree, *, source_timeout: float) -> Version:
        timeout, _ = _validate_monitor_options(timeout=source_timeout, interval=1.0)
        archive = build_source_tree_archive(tree, max_bytes=MAX_TOOL_SOURCE_BYTES)
        try:
            session = self._transport.create_custom_tool_upload(tool.name, tool.generation)
            if archive.size > session["maxBytes"]:
                raise CustomToolUploadError(
                    f"Source archive is {archive.size} bytes but the upload session allows "
                    f"at most {session['maxBytes']} bytes."
                )
            _upload_archive(
                session["uploadUrl"],
                archive.content(),
                method=session.get("uploadMethod", "PUT"),
                headers=session.get("uploadHeaders", {}),
                timeout=self._upload_timeout,
            )
            result = self._transport.build_custom_tool_version(
                tool.name,
                tool.generation,
                cast(
                    PublicCreateVersionRequest,
                    {
                        "uploadId": session["uploadId"],
                        "expectedSourceDigest": archive.digest,
                    },
                ),
                timeout=timeout,
            )
        finally:
            archive.close()
        return _version_from_wire(self, tool.name, result["version"])

    def _versions(
        self,
        tool_name: str,
        *,
        status: PublicVersionStatus | None,
        limit: int,
        cursor: str | None,
        request_timeout: float | None = None,
    ) -> Page[Version]:
        wire = self._transport.list_custom_tool_versions(
            tool_name,
            status=status,
            limit=limit,
            cursor=cursor,
            timeout=request_timeout,
        )
        return Page(
            items=tuple(_version_from_wire(self, tool_name, item) for item in wire["items"]),
            next_cursor=wire["nextCursor"],
        )

    def _get_version(
        self, tool_name: str, version_name: str, *, request_timeout: float | None = None
    ) -> Version:
        wire = self._transport.get_custom_tool_version(
            tool_name, version_name, timeout=request_timeout
        )
        return _version_from_wire(self, tool_name, wire)


def _upload_archive(
    url: str, data: BinaryIO, *, method: str, headers: dict[str, str], timeout: float
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
        generation=wire["generation"],
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
        source_digest=wire["sourceDigest"],
        published=wire["published"],
        auto_publish=wire["autoPublish"],
        est_time=wire["estTime"],
        paper_url=wire["paperUrl"],
        tags=tuple(wire["tags"]),
        default_version=wire["defaultVersion"],
        created_at=wire["createdAt"],
        updated_at=wire["updatedAt"],
        can_edit=wire["canEdit"],
        can_build=wire["canBuild"],
        _collection=collection,
    )


def _version_from_wire(collection: CustomTools, tool_name: str, wire: PublicVersion) -> Version:
    error = wire["error"]
    completed_at = wire["completedAt"]
    duration_seconds = None
    if completed_at is not None:
        started = datetime.fromisoformat(wire["startedAt"].replace("Z", "+00:00"))
        completed = datetime.fromisoformat(completed_at.replace("Z", "+00:00"))
        duration_seconds = max(0, int((completed - started).total_seconds()))
    return Version(
        name=wire["name"],
        source_revision=wire["sourceRevision"],
        source_digest=wire["sourceDigest"],
        status=wire["status"],
        origin=wire["origin"],
        started_at=wire["startedAt"],
        completed_at=completed_at,
        duration_seconds=duration_seconds,
        error=BuildError(error["code"], error["message"]) if error else None,
        tool_name=tool_name,
        _collection=collection,
    )


def _log_page_from_wire(wire: PublicBuildLogPage) -> BuildLogPage:
    error = wire["error"]
    return BuildLogPage(
        items=tuple(BuildEvent(item["message"], item["timestamp"]) for item in wire["items"]),
        next_cursor=wire["nextCursor"],
        status=wire["status"],
        error=BuildError(error["code"], error["message"]) if error else None,
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
    except TamarindError as exc:
        if isinstance(exc.__cause__, httpx.TimeoutException):
            raise CustomToolBuildTimeoutError("Custom Tool build monitoring timed out") from None
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
