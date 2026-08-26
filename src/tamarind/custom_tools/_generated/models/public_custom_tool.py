from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..models.public_custom_tool_gputype import PublicCustomToolGputype
from ..models.public_custom_tool_memory import PublicCustomToolMemory
from ..models.public_custom_tool_status import PublicCustomToolStatus

T = TypeVar("T", bound="PublicCustomTool")


@_attrs_define
class PublicCustomTool:
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
        functions (list[str]):
        generation (str): The immutable lifetime identity of this Tool name. Clients use the Tool's quoted `ETag` with
            standard `If-Match`; versions remain numbered handles such as `v3`.
        gpu_type (PublicCustomToolGputype):
        has_source (bool):
        home_disk_gi (int):
        max_runtime_seconds (int | None): Maximum runtime for a tool run, in seconds. Null means no tool-specific limit.
        memory (PublicCustomToolMemory):
        name (str):
        paper_url (str):
        published (bool):
        source_digest (None | str): SHA-256 digest of the current source archive after it has been admitted for a build.
            Null when the current source is unbuilt, absent, or hidden.
        status (PublicCustomToolStatus):
        tags (list[str]):
        updated_at (str):
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
    functions: list[str]
    generation: str
    gpu_type: PublicCustomToolGputype
    has_source: bool
    home_disk_gi: int
    max_runtime_seconds: int | None
    memory: PublicCustomToolMemory
    name: str
    paper_url: str
    published: bool
    source_digest: None | str
    status: PublicCustomToolStatus
    tags: list[str]
    updated_at: str

    def to_dict(self) -> dict[str, Any]:
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

        functions = self.functions

        generation = self.generation

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
                "functions": functions,
                "generation": generation,
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
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
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

        functions = cast(list[str], d.pop("functions"))

        generation = d.pop("generation")

        gpu_type = PublicCustomToolGputype(d.pop("gpuType"))

        has_source = d.pop("hasSource")

        home_disk_gi = d.pop("homeDiskGi")

        def _parse_max_runtime_seconds(data: object) -> int | None:
            if data is None:
                return data
            return cast(int | None, data)

        max_runtime_seconds = _parse_max_runtime_seconds(d.pop("maxRuntimeSeconds"))

        memory = PublicCustomToolMemory(d.pop("memory"))

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

        public_custom_tool = cls(
            auto_publish=auto_publish,
            can_build=can_build,
            can_edit=can_edit,
            cpu=cpu,
            created_at=created_at,
            default_version=default_version,
            description=description,
            display_name=display_name,
            est_time=est_time,
            functions=functions,
            generation=generation,
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
        )

        return public_custom_tool
