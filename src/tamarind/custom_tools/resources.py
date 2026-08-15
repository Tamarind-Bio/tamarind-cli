"""Handwritten resource API over the generated Custom Tools transport."""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from pathlib import Path
import time
from typing import Callable, Generic, Literal, TypeVar, cast

import httpx

from tamarind.custom_tools.generated import (
    GeneratedCustomToolsTransport,
    PublicBuildLogPage,
    PublicCreateCustomToolRequest,
    PublicCustomTool,
    PublicCustomToolStatus,
    PublicUpdateCustomToolRequest,
    PublicVersion,
    PublicVersionStatus,
)
from tamarind.custom_tools.packaging import SourceArchive, build_archive
from tamarind.custom_tools.validation import ValidationReport, validate_folder
from tamarind.errors import (
    CustomToolBuildFailedError,
    CustomToolBuildTimeoutError,
    CustomToolUploadError,
    TamarindError,
    ValidationError,
)


T = TypeVar("T")
BuildAction = Literal["build", "reuse_image", "unchanged"]
EventCallback = Callable[["BuildEvent"], None]


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
class BuildLogPage(Page[BuildEvent]):
    status: PublicVersionStatus = "Launching"
    error: BuildError | None = None


@dataclass(frozen=True)
class BuildResult:
    action: BuildAction
    version: "Version"


@dataclass(frozen=True)
class CustomTool:
    name: str
    generation: str
    display_name: str
    description: str
    functions: tuple[str, ...]
    status: PublicCustomToolStatus
    gpu_type: str
    memory: str
    cpu: int
    home_disk_gi: int
    max_runtime_seconds: int | None
    has_source: bool
    source_digest: str | None
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
        gpu_type: str | None | _Unset = _UNSET,
        memory: str | None | _Unset = _UNSET,
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
            PublicUpdateCustomToolRequest,
            {key: value for key, value in values.items() if value is not _UNSET},
        )
        return self._collection._update(self.name, self.generation, body)

    def validate(self, folder: str | Path) -> ValidationReport:
        return validate_folder(folder)

    def build(self, folder: str | Path) -> BuildResult:
        report = self.validate(folder)
        if not report.valid:
            raise ValidationError("Custom Tool source validation failed", detail=report)
        return self._collection._build(self, build_archive(folder))

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
    created_at: str
    started_at: str
    completed_at: str | None
    terminal: bool
    error: BuildError | None
    tool_name: str
    _collection: "CustomTools" = field(repr=False, compare=False)

    def refresh(self) -> "Version":
        return self._collection._get_version(self.tool_name, self.name)

    def logs(self, *, cursor: str | None = None) -> BuildLogPage:
        return self._logs(cursor=cursor, request_timeout=None)

    def _logs(self, *, cursor: str | None, request_timeout: float | None) -> BuildLogPage:
        wire = self._collection._transport.list_custom_tool_build_logs(
            self.tool_name,
            self.name,
            cursor=cursor,
            timeout=request_timeout,
        )
        return _log_page_from_wire(wire)

    def cancel(self) -> "Version":
        wire = self._collection._transport.cancel_custom_tool_build(self.tool_name, self.name)
        return _version_from_wire(self._collection, self.tool_name, wire)

    def monitor(
        self,
        *,
        timeout: float | None,
        interval: float = 2.0,
        on_event: EventCallback | None = None,
    ) -> "Version":
        _validate_monitor_options(timeout=timeout, interval=interval)
        deadline = None if timeout is None else time.monotonic() + timeout
        cursor: str | None = None
        current = self

        while True:
            if current.terminal:
                return _require_success(current)
            remaining = None if deadline is None else deadline - time.monotonic()
            if remaining is not None and remaining <= 0:
                raise CustomToolBuildTimeoutError(
                    f"Custom Tool Version {self.tool_name}/{self.name} was still {current.status} after {timeout:g}s"
                )

            try:
                page = current._logs(cursor=cursor, request_timeout=remaining)
            except TamarindError as exc:
                if (
                    type(exc) is TamarindError
                    and deadline is not None
                    and time.monotonic() >= deadline
                ):
                    raise CustomToolBuildTimeoutError(
                        f"Custom Tool Version {self.tool_name}/{self.name} did not return logs "
                        f"before the {timeout:g}s deadline"
                    ) from exc
                raise
            if page.next_cursor is not None:
                cursor = page.next_cursor
            if on_event is not None:
                for event in page.items:
                    on_event(event)

            if page.status in ("Complete", "Stopped"):
                return _require_success(current.refresh())

            remaining = None if deadline is None else deadline - time.monotonic()
            if remaining is not None and remaining <= 0:
                raise CustomToolBuildTimeoutError(
                    f"Custom Tool Version {self.tool_name}/{self.name} was still {page.status} after {timeout:g}s"
                )
            time.sleep(interval if remaining is None else min(interval, remaining))


class CustomTools:
    """Organization-scoped Custom Tool collection."""

    def __init__(self, transport: GeneratedCustomToolsTransport):
        self._transport = transport

    def create(
        self,
        name: str,
        *,
        display_name: str = "",
        description: str = "",
        gpu_type: str = "None",
        memory: str = "8Gi",
        cpu: int = 1,
    ) -> CustomTool:
        body = cast(
            PublicCreateCustomToolRequest,
            {
                "name": name,
                "displayName": display_name,
                "description": description,
                "gpuType": gpu_type,
                "memory": memory,
                "cpu": cpu,
            },
        )
        return _tool_from_wire(self, self._transport.create_custom_tool(body))

    def get(self, name: str) -> CustomTool:
        return _tool_from_wire(self, self._transport.get_custom_tool(name))

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
        self,
        name: str,
        generation: str,
        body: PublicUpdateCustomToolRequest,
    ) -> CustomTool:
        wire = self._transport.update_custom_tool(name, generation, body)
        return _tool_from_wire(self, wire)

    def _build(self, tool: CustomTool, archive: SourceArchive) -> BuildResult:
        session = self._transport.create_custom_tool_upload(tool.name)
        if archive.size > session["maxBytes"]:
            raise CustomToolUploadError(
                f"Source archive is {archive.size} bytes; upload limit is {session['maxBytes']} bytes"
            )
        _upload_archive(session["uploadUrl"], archive.data)
        wire = self._transport.build_custom_tool_version(
            tool.name,
            tool.generation,
            {
                "uploadId": session["uploadId"],
                "expectedSourceDigest": archive.digest,
            },
        )
        return BuildResult(
            action=wire["action"],
            version=_version_from_wire(self, tool.name, wire["version"]),
        )

    def _versions(
        self,
        tool_name: str,
        *,
        status: PublicVersionStatus | None,
        limit: int,
        cursor: str | None,
    ) -> Page[Version]:
        wire = self._transport.list_custom_tool_versions(
            tool_name,
            status=status,
            limit=limit,
            cursor=cursor,
        )
        return Page(
            items=tuple(_version_from_wire(self, tool_name, item) for item in wire["items"]),
            next_cursor=wire["nextCursor"],
        )

    def _get_version(self, tool_name: str, version_name: str) -> Version:
        wire = self._transport.get_custom_tool_version(tool_name, version_name)
        return _version_from_wire(self, tool_name, wire)


def _upload_archive(url: str, data: bytes) -> None:
    try:
        response = httpx.put(
            url,
            content=data,
            headers={"Content-Type": "application/zip"},
            timeout=120.0,
        )
        response.raise_for_status()
    except httpx.TimeoutException:
        raise CustomToolUploadError("Source upload timed out after 120 seconds.") from None
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
        default_version=wire["defaultVersion"],
        created_at=wire["createdAt"],
        updated_at=wire["updatedAt"],
        can_edit=wire["canEdit"],
        can_build=wire["canBuild"],
        _collection=collection,
    )


def _version_from_wire(
    collection: CustomTools,
    tool_name: str,
    wire: PublicVersion,
) -> Version:
    error = wire["error"]
    return Version(
        name=wire["name"],
        source_revision=wire["sourceRevision"],
        source_digest=wire["sourceDigest"],
        status=wire["status"],
        origin=wire["origin"],
        created_at=wire["createdAt"],
        started_at=wire["startedAt"],
        completed_at=wire["completedAt"],
        terminal=wire["terminal"],
        error=BuildError(**error) if error else None,
        tool_name=tool_name,
        _collection=collection,
    )


def _log_page_from_wire(wire: PublicBuildLogPage) -> BuildLogPage:
    error = wire["error"]
    return BuildLogPage(
        items=tuple(BuildEvent(**item) for item in wire["items"]),
        next_cursor=wire["nextCursor"],
        status=wire["status"],
        error=BuildError(**error) if error else None,
    )


def _require_success(version: Version) -> Version:
    if version.status == "Stopped":
        message = version.error.message if version.error else "build stopped"
        raise CustomToolBuildFailedError(
            f"Custom Tool Version {version.tool_name}/{version.name} failed: {message}",
            detail=version,
        )
    return version


def _validate_monitor_options(*, timeout: float | None, interval: float) -> None:
    if not math.isfinite(interval) or interval <= 0:
        raise ValidationError("monitor interval must be a finite number greater than zero")
    if timeout is not None and (not math.isfinite(timeout) or timeout <= 0):
        raise ValidationError("monitor timeout must be a finite number greater than zero")
