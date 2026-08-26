"""Resource API composed from the existing Custom Tools lifecycle.

There is intentionally no BuildRequest resource or repair protocol here.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
import math
from pathlib import Path
import re
import time
from typing import Awaitable, BinaryIO, Callable, Generic, TypeAlias, TypeVar, cast

import httpx

from tamarind.custom_tools._generated.models.public_build_result_action import (
    PublicBuildResultAction,
)

from tamarind.custom_tools.transport import (
    GeneratedCustomToolsTransport,
    GpuType,
    MemorySize,
    PublicBuildResult,
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
    StaleCustomToolError,
    TamarindError,
    ValidationError,
)
from tamarind.http import DEFAULT_TIMEOUT

T = TypeVar("T")
EventCallback = Callable[["BuildEvent"], None]
BuildAction: TypeAlias = PublicBuildResultAction
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
    status: PublicVersionStatus
    next_cursor: str | None = None
    error: BuildError | None = None


@dataclass(frozen=True)
class BuildResult:
    """Outcome of one build submission and the resulting durable Version."""

    action: BuildAction
    version: "Version"


@dataclass(frozen=True)
class _UploadSession:
    upload_id: str
    upload_url: str
    upload_method: str
    upload_headers: dict[str, str]
    expires_at: str
    max_bytes: int


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
    _etag: str | None = field(repr=False, compare=False)
    _collection: "CustomTools" = field(repr=False, compare=False)

    def refresh(self) -> "CustomTool":
        return self._refresh(request_timeout=None)

    def _refresh(self, *, request_timeout: float | None) -> "CustomTool":
        return self._collection._current_tool(
            self.name,
            self.generation,
            request_timeout=request_timeout,
        )

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
        return self._collection._update(self, body)

    def delete(self) -> None:
        """Delete this exact tool generation and release its name for reuse."""
        self._collection._delete(self)

    def validate(self, folder: str | Path) -> ValidationReport:
        return validate_folder(folder)

    def build(
        self,
        folder: str | Path,
        *,
        idempotency_key: str | None = None,
        source_timeout: float = 180.0,
    ) -> BuildResult:
        """Upload source and return what the server did plus the durable Version."""
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
            self,
            tree,
            idempotency_key=idempotency_key,
            source_timeout=source_timeout,
        )

    def get_version(self, version_id: str) -> "Version":
        """Get one exact Version by its opaque ``id``."""
        return self._collection._get_version_for_tool(self, _require_opaque_version_id(version_id))

    def versions(
        self,
        *,
        status: PublicVersionStatus | None = None,
        limit: int = 50,
        cursor: str | None = None,
    ) -> Page["Version"]:
        return self._collection._versions(
            self,
            status=status,
            limit=limit,
            cursor=cursor,
        )


@dataclass(frozen=True)
class Version:
    id: str
    name: str
    source_revision: str | None
    source_digest: str | None
    status: PublicVersionStatus
    terminal: bool
    origin: str
    created_at: str
    started_at: str
    completed_at: str | None
    error: BuildError | None
    tool_name: str
    tool_generation: str
    _collection: "CustomTools" = field(repr=False, compare=False)
    _etag: str | None = field(default=None, repr=False, compare=False)

    def refresh(self) -> "Version":
        return self._refresh(request_timeout=None)

    def _refresh(self, *, request_timeout: float | None) -> "Version":
        wire = self._collection._transport.get_custom_tool_version(
            self.tool_name,
            self.id,
            timeout=request_timeout,
        )
        return _version_from_wire(self._collection, self.tool_name, self.tool_generation, wire)

    async def _refresh_async(self, *, request_timeout: float | None) -> "Version":
        wire = await self._collection._transport.get_custom_tool_version_async(
            self.tool_name,
            self.id,
            timeout=request_timeout,
        )
        return _version_from_wire(self._collection, self.tool_name, self.tool_generation, wire)

    def logs(self, *, cursor: str | None = None) -> BuildLogPage:
        return self._logs(cursor=cursor, request_timeout=None)

    def _logs(self, *, cursor: str | None, request_timeout: float | None) -> BuildLogPage:
        wire = self._collection._transport.list_custom_tool_build_logs(
            self.tool_name,
            self.id,
            cursor=cursor,
            timeout=request_timeout,
        )
        return _log_page_from_wire(wire)

    async def _logs_async(
        self, *, cursor: str | None, request_timeout: float | None
    ) -> BuildLogPage:
        wire = await self._collection._transport.list_custom_tool_build_logs_async(
            self.tool_name,
            self.id,
            cursor=cursor,
            timeout=request_timeout,
        )
        return _log_page_from_wire(wire)

    def cancel(self) -> "Version":
        return self._collection._cancel_version(self)

    def publish(self) -> CustomTool:
        return self._collection._publish_version(self)

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

        async def await_with_budget(
            start: Callable[[float | None], Awaitable[T]],
        ) -> T:
            remaining = remaining_budget()
            result = await _await_with_timeout(start(remaining), remaining)
            remaining_budget()
            return result

        async def deliver_log_page(version: Version) -> bool:
            if logs is None or on_event is None:
                return False
            requested_cursor = logs.cursor
            page = await await_with_budget(
                lambda remaining: version._logs_async(
                    cursor=requested_cursor, request_timeout=remaining
                )
            )
            for event in logs.consume(page):
                on_event(event)
                remaining_budget()
            remaining_budget()
            return page.next_cursor is not None and page.next_cursor != requested_cursor

        while not current.terminal:
            if logs is not None:
                await deliver_log_page(current)
            current = await await_with_budget(
                lambda remaining: current._refresh_async(request_timeout=remaining)
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

    def _current_tool(
        self,
        tool_name: str,
        expected_generation: str,
        *,
        request_timeout: float | None = None,
    ) -> CustomTool:
        current = self._get(tool_name, request_timeout=request_timeout)
        if current.generation != expected_generation:
            raise StaleCustomToolError(
                f"Custom Tool {tool_name!r} now refers to a different generation; "
                "fetch it again explicitly to select the replacement."
            )
        return current

    def _validator(self, tool: CustomTool) -> str:
        if tool._etag is not None:
            return tool._etag
        current = self._current_tool(tool.name, tool.generation)
        if current.updated_at != tool.updated_at:
            raise StaleCustomToolError(
                f"Custom Tool {tool.name!r} changed since it was listed; "
                "fetch it again before mutating it."
            )
        if current._etag is None:
            raise TamarindError("Custom Tools response did not include the required ETag")
        return current._etag

    def _update(self, tool: CustomTool, body: PublicUpdateCustomToolRequest) -> CustomTool:
        return _tool_from_wire(
            self,
            self._transport.update_custom_tool(tool.name, self._validator(tool), body),
        )

    def _delete(self, tool: CustomTool) -> None:
        self._transport.delete_custom_tool(tool.name, self._validator(tool))

    def _build(
        self,
        tool: CustomTool,
        tree: SourceTree,
        *,
        idempotency_key: str | None,
        source_timeout: float,
    ) -> BuildResult:
        timeout, _ = _validate_monitor_options(timeout=source_timeout, interval=1.0)
        archive = build_source_tree_archive(tree, max_bytes=MAX_TOOL_SOURCE_BYTES)
        try:
            session = _upload_session_from_wire(
                self._transport.create_custom_tool_upload(tool.name)
            )
            if archive.size > session.max_bytes:
                raise CustomToolUploadError(
                    f"Source archive is {archive.size} bytes but the upload session allows "
                    f"at most {session.max_bytes} bytes."
                )
            _upload_archive(
                session.upload_url,
                archive.content(),
                size=archive.size,
                method=session.upload_method,
                headers=session.upload_headers,
                timeout=self._upload_timeout,
            )
            result = self._transport.build_custom_tool_version(
                tool.name,
                self._validator(tool),
                cast(
                    PublicCreateVersionRequest,
                    {
                        "uploadId": session.upload_id,
                        "expectedSourceDigest": archive.digest,
                    },
                ),
                idempotency_key=idempotency_key,
                timeout=timeout,
            )
        finally:
            archive.close()
        return _build_result_from_wire(self, tool.name, tool.generation, result)

    def _versions(
        self,
        tool: CustomTool,
        *,
        status: PublicVersionStatus | None,
        limit: int,
        cursor: str | None,
        request_timeout: float | None = None,
    ) -> Page[Version]:
        wire = self._transport.list_custom_tool_versions(
            tool.name,
            status=status,
            limit=limit,
            cursor=cursor,
            timeout=request_timeout,
        )
        self._current_tool(
            tool.name,
            tool.generation,
            request_timeout=request_timeout,
        )
        return Page(
            items=tuple(
                _version_from_wire(self, tool.name, tool.generation, item) for item in wire["items"]
            ),
            next_cursor=wire["nextCursor"],
        )

    def _get_version_for_tool(
        self,
        tool: CustomTool,
        version_id: str,
        *,
        request_timeout: float | None = None,
    ) -> Version:
        version = self._get_version(
            tool.name,
            tool.generation,
            version_id,
            request_timeout=request_timeout,
        )
        self._current_tool(
            tool.name,
            tool.generation,
            request_timeout=request_timeout,
        )
        return version

    def _get_version(
        self,
        tool_name: str,
        tool_generation: str,
        version_id: str,
        *,
        request_timeout: float | None = None,
    ) -> Version:
        wire = self._transport.get_custom_tool_version(
            tool_name,
            version_id,
            timeout=request_timeout,
        )
        return _version_from_wire(self, tool_name, tool_generation, wire)

    def _version_validator(self, version: Version) -> str:
        if version._etag is not None:
            return version._etag
        current = self._get_version(version.tool_name, version.tool_generation, version.id)
        if current.id != version.id:
            raise StaleCustomToolError(
                f"Custom Tool Version {version.tool_name}/{version.name} changed identity; fetch it again."
            )
        if current._etag is None:
            raise TamarindError("Custom Tools response did not include the required Version ETag")
        return current._etag

    def _cancel_version(self, version: Version) -> Version:
        wire = self._transport.cancel_custom_tool_build(
            version.tool_name,
            version.id,
            self._version_validator(version),
        )
        return _version_from_wire(self, version.tool_name, version.tool_generation, wire)

    def _publish_version(self, version: Version) -> CustomTool:
        tool = self._current_tool(
            version.tool_name,
            version.tool_generation,
        )
        wire = self._transport.publish_custom_tool_version(
            version.tool_name,
            version.id,
            self._validator(tool),
        )
        return _tool_from_wire(self, wire)


def _upload_session_from_wire(wire: object) -> _UploadSession:
    if not isinstance(wire, dict):
        raise TamarindError("Custom Tools response did not match the generated contract")

    upload_id = wire.get("uploadId")
    upload_url = wire.get("uploadUrl")
    upload_method = wire.get("uploadMethod")
    upload_headers = wire.get("uploadHeaders")
    expires_at = wire.get("expiresAt")
    max_bytes = wire.get("maxBytes")
    if (
        not isinstance(upload_id, str)
        or not isinstance(upload_url, str)
        or upload_method != "PUT"
        or not isinstance(upload_headers, dict)
        or not all(
            isinstance(key, str) and isinstance(value, str) for key, value in upload_headers.items()
        )
        or not isinstance(expires_at, str)
        or type(max_bytes) is not int
        or max_bytes < 0
    ):
        raise TamarindError("Custom Tools response did not match the generated contract")
    try:
        parsed_upload_url = httpx.URL(upload_url)
    except httpx.InvalidURL:
        raise TamarindError("Custom Tools response did not match the generated contract") from None
    if parsed_upload_url.scheme != "https":
        raise TamarindError("Custom Tools response did not match the generated contract")
    return _UploadSession(
        upload_id=upload_id,
        upload_url=upload_url,
        upload_method=upload_method,
        upload_headers=cast(dict[str, str], upload_headers),
        expires_at=expires_at,
        max_bytes=max_bytes,
    )


def _upload_archive(
    url: str,
    data: BinaryIO,
    *,
    size: int,
    method: str,
    headers: dict[str, str],
    timeout: float,
) -> None:
    request_headers = dict(headers)
    if not any(name.lower() == "content-length" for name in request_headers):
        request_headers["Content-Length"] = str(size)
    try:
        response = httpx.request(
            method, url, content=data, headers=request_headers, timeout=timeout
        )
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
        status=PublicCustomToolStatus(wire["status"]),
        gpu_type=GpuType(wire["gpuType"]),
        memory=MemorySize(wire["memory"]),
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
        _etag=cast(str | None, wire.get("_etag")),
        _collection=collection,
    )


def _version_from_wire(
    collection: CustomTools, tool_name: str, tool_generation: str, wire: PublicVersion
) -> Version:
    terminal = wire["terminal"]
    if not isinstance(terminal, bool):
        raise TamarindError("Custom Tools response did not match the generated contract")
    return Version(
        id=wire["id"],
        name=wire["name"],
        source_revision=wire["sourceRevision"],
        source_digest=wire["sourceDigest"],
        status=PublicVersionStatus(wire["status"]),
        terminal=terminal,
        origin=wire["origin"],
        created_at=wire["createdAt"],
        started_at=wire["startedAt"],
        completed_at=wire["completedAt"],
        error=_build_error_from_wire(wire["error"]),
        tool_name=tool_name,
        tool_generation=tool_generation,
        _etag=cast(str | None, wire.get("_etag")),
        _collection=collection,
    )


def _build_result_from_wire(
    collection: CustomTools,
    tool_name: str,
    tool_generation: str,
    wire: PublicBuildResult,
) -> BuildResult:
    version = dict(wire["version"])
    if "_etag" in wire:
        version["_etag"] = wire["_etag"]
    return BuildResult(
        action=BuildAction(wire["action"]),
        version=_version_from_wire(collection, tool_name, tool_generation, version),
    )


def _log_page_from_wire(wire: PublicBuildLogPage) -> BuildLogPage:
    return BuildLogPage(
        items=tuple(BuildEvent(item["message"], item["timestamp"]) for item in wire["items"]),
        next_cursor=wire["nextCursor"],
        status=PublicVersionStatus(wire["status"]),
        error=_build_error_from_wire(wire["error"]),
    )


def _build_error_from_wire(error: object) -> BuildError | None:
    if error is None:
        return None
    if not isinstance(error, dict):
        raise TamarindError("Custom Tools response did not match the generated contract")
    code = error.get("code")
    message = error.get("message")
    if not isinstance(code, str) or not isinstance(message, str):
        raise TamarindError("Custom Tools response did not match the generated contract")
    return BuildError(code, message)


def _require_success(version: Version) -> Version:
    if version.status != "Complete":
        message = (
            version.error.message if version.error else f"build ended with status {version.status}"
        )
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
        if remaining is None:
            raise
        raise CustomToolBuildTimeoutError("Custom Tool build monitoring timed out") from None
    except TamarindError as exc:
        if remaining is not None and isinstance(exc.__cause__, httpx.TimeoutException):
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
    try:
        normalized = float(value)
    except OverflowError:
        raise ValidationError(f"{label} must be a finite number greater than zero") from None
    if not math.isfinite(normalized) or normalized <= 0:
        raise ValidationError(f"{label} must be a finite number greater than zero")
    return normalized


def _require_opaque_version_id(value: str) -> str:
    if re.fullmatch(r"v[1-9][0-9]*", value):
        raise ValidationError("get_version requires the opaque Version.id, not its numbered name")
    return value
