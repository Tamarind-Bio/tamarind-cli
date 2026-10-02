from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..models.public_custom_tool_detail_gputype import PublicCustomToolDetailGputype
from ..models.public_custom_tool_detail_memory import PublicCustomToolDetailMemory
from ..models.public_custom_tool_status import PublicCustomToolStatus

if TYPE_CHECKING:
    from ..models.public_version import PublicVersion


T = TypeVar("T", bound="PublicCustomToolDetail")


@_attrs_define
class PublicCustomToolDetail:
    """
    Attributes:
        auto_publish (bool):
        can_build (bool):
        can_edit (bool):
        cpu (int):
        created_at (str):
        default_version (None | str): The version used by default, such as `v3`. Null when no version is published.
        description (str):
        display_name (str):
        est_time (str):
        etag (str): Opaque SDK-managed validator for this Tool snapshot.
        functions (list[str]):
        gpu_type (PublicCustomToolDetailGputype):
        has_source (bool):
        home_disk_gi (int):
        max_runtime_seconds (int | None): Maximum runtime for a tool run, in seconds. Null means no tool-specific limit.
        memory (PublicCustomToolDetailMemory):
        name (str):
        paper_url (str):
        published (bool):
        source_digest (None | str): SHA-256 digest of the current source archive after it has been admitted for a build.
            Null when the current source is unbuilt, absent, or hidden.
        status (PublicCustomToolStatus):
        tags (list[str]):
        updated_at (str):
        version (None | PublicVersion): The requested version, or the latest version when no version was requested.
    """

    auto_publish: bool
    can_build: bool
    can_edit: bool
    cpu: int
    created_at: str
    default_version: None | str
    description: str
    display_name: str
    est_time: str
    etag: str
    functions: list[str]
    gpu_type: PublicCustomToolDetailGputype
    has_source: bool
    home_disk_gi: int
    max_runtime_seconds: int | None
    memory: PublicCustomToolDetailMemory
    name: str
    paper_url: str
    published: bool
    source_digest: None | str
    status: PublicCustomToolStatus
    tags: list[str]
    updated_at: str
    version: None | PublicVersion

    def to_dict(self) -> dict[str, Any]:
        from ..models.public_version import PublicVersion

        auto_publish = self.auto_publish

        can_build = self.can_build

        can_edit = self.can_edit

        cpu = self.cpu

        created_at = self.created_at

        default_version: None | str
        default_version = self.default_version

        description = self.description

        display_name = self.display_name

        est_time = self.est_time

        etag = self.etag

        functions = self.functions

        gpu_type = self.gpu_type.value

        has_source = self.has_source

        home_disk_gi = self.home_disk_gi

        max_runtime_seconds: int | None
        max_runtime_seconds = self.max_runtime_seconds

        memory = self.memory.value

        name = self.name

        paper_url = self.paper_url

        published = self.published

        source_digest: None | str
        source_digest = self.source_digest

        status = self.status.value

        tags = self.tags

        updated_at = self.updated_at

        version: dict[str, Any] | None
        if isinstance(self.version, PublicVersion):
            version = self.version.to_dict()
        else:
            version = self.version

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "autoPublish": auto_publish,
                "canBuild": can_build,
                "canEdit": can_edit,
                "cpu": cpu,
                "createdAt": created_at,
                "defaultVersion": default_version,
                "description": description,
                "displayName": display_name,
                "estTime": est_time,
                "etag": etag,
                "functions": functions,
                "gpuType": gpu_type,
                "hasSource": has_source,
                "homeDiskGi": home_disk_gi,
                "maxRuntimeSeconds": max_runtime_seconds,
                "memory": memory,
                "name": name,
                "paperUrl": paper_url,
                "published": published,
                "sourceDigest": source_digest,
                "status": status,
                "tags": tags,
                "updatedAt": updated_at,
                "version": version,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.public_version import PublicVersion

        d = dict(src_dict)
        auto_publish = d.pop("autoPublish")

        can_build = d.pop("canBuild")

        can_edit = d.pop("canEdit")

        cpu = d.pop("cpu")

        created_at = d.pop("createdAt")

        def _parse_default_version(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        default_version = _parse_default_version(d.pop("defaultVersion"))

        description = d.pop("description")

        display_name = d.pop("displayName")

        est_time = d.pop("estTime")

        etag = d.pop("etag")

        functions = cast(list[str], d.pop("functions"))

        gpu_type = PublicCustomToolDetailGputype(d.pop("gpuType"))

        has_source = d.pop("hasSource")

        home_disk_gi = d.pop("homeDiskGi")

        def _parse_max_runtime_seconds(data: object) -> int | None:
            if data is None:
                return data
            return cast(int | None, data)

        max_runtime_seconds = _parse_max_runtime_seconds(d.pop("maxRuntimeSeconds"))

        memory = PublicCustomToolDetailMemory(d.pop("memory"))

        name = d.pop("name")

        paper_url = d.pop("paperUrl")

        published = d.pop("published")

        def _parse_source_digest(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        source_digest = _parse_source_digest(d.pop("sourceDigest"))

        status = PublicCustomToolStatus(d.pop("status"))

        tags = cast(list[str], d.pop("tags"))

        updated_at = d.pop("updatedAt")

        def _parse_version(data: object) -> None | PublicVersion:
            if data is None:
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                version_type_0 = PublicVersion.from_dict(data)

                return version_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | PublicVersion, data)

        version = _parse_version(d.pop("version"))

        public_custom_tool_detail = cls(
            auto_publish=auto_publish,
            can_build=can_build,
            can_edit=can_edit,
            cpu=cpu,
            created_at=created_at,
            default_version=default_version,
            description=description,
            display_name=display_name,
            est_time=est_time,
            etag=etag,
            functions=functions,
            gpu_type=gpu_type,
            has_source=has_source,
            home_disk_gi=home_disk_gi,
            max_runtime_seconds=max_runtime_seconds,
            memory=memory,
            name=name,
            paper_url=paper_url,
            published=published,
            source_digest=source_digest,
            status=status,
            tags=tags,
            updated_at=updated_at,
            version=version,
        )

        return public_custom_tool_detail
