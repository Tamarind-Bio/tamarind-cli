from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.custom_tool_detail_gputype import CustomToolDetailGputype
from ..models.custom_tool_detail_memory import CustomToolDetailMemory
from ..models.custom_tool_status import CustomToolStatus

if TYPE_CHECKING:
    from ..models.custom_tool_version import CustomToolVersion


T = TypeVar("T", bound="CustomToolDetail")


@_attrs_define
class CustomToolDetail:
    """
    Attributes:
        auto_publish (bool):
        can_build (bool):
        can_edit (bool):
        cpu (int):
        created_at (datetime.datetime):
        default_version (None | str): The version used by default, such as `v3`. Null when no version is published.
        description (str):
        display_name (str):
        est_time (str):
        etag (str): Opaque SDK-managed validator for this Tool snapshot.
        functions (list[str]):
        gpu_type (CustomToolDetailGputype): The GPU each run gets. Never `A10` in a response, because A10 is retired and
            reads back as `L4`.
        has_source (bool):
        home_disk_gi (int):
        max_runtime_seconds (int | None): Maximum runtime for a tool run, in seconds. Null means no tool-specific limit.
        memory (CustomToolDetailMemory):
        name (str):
        paper_url (str):
        published (bool):
        serves_models (bool): As on `CustomTool`.
        source_digest (None | str): SHA-256 digest of the current source archive after it has been admitted for a build.
            Null when the current source is unbuilt, absent, or hidden.
        status (CustomToolStatus): Today's custom tool statuses.
        tags (list[str]):
        trainable (bool): As on `CustomTool`.
        updated_at (datetime.datetime):
        version (CustomToolVersion | None): The requested version, or the latest version when no version was requested.
    """

    auto_publish: bool
    can_build: bool
    can_edit: bool
    cpu: int
    created_at: datetime.datetime
    default_version: None | str
    description: str
    display_name: str
    est_time: str
    etag: str
    functions: list[str]
    gpu_type: CustomToolDetailGputype
    has_source: bool
    home_disk_gi: int
    max_runtime_seconds: int | None
    memory: CustomToolDetailMemory
    name: str
    paper_url: str
    published: bool
    serves_models: bool
    source_digest: None | str
    status: CustomToolStatus
    tags: list[str]
    trainable: bool
    updated_at: datetime.datetime
    version: CustomToolVersion | None
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.custom_tool_version import CustomToolVersion

        auto_publish = self.auto_publish

        can_build = self.can_build

        can_edit = self.can_edit

        cpu = self.cpu

        created_at = self.created_at.isoformat()

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

        serves_models = self.serves_models

        source_digest: None | str
        source_digest = self.source_digest

        status = self.status.value

        tags = self.tags

        trainable = self.trainable

        updated_at = self.updated_at.isoformat()

        version: dict[str, Any] | None
        if isinstance(self.version, CustomToolVersion):
            version = self.version.to_dict()
        else:
            version = self.version

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
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
                "servesModels": serves_models,
                "sourceDigest": source_digest,
                "status": status,
                "tags": tags,
                "trainable": trainable,
                "updatedAt": updated_at,
                "version": version,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.custom_tool_version import CustomToolVersion

        d = dict(src_dict)
        auto_publish = d.pop("autoPublish")

        can_build = d.pop("canBuild")

        can_edit = d.pop("canEdit")

        cpu = d.pop("cpu")

        created_at = isoparse(d.pop("createdAt"))

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

        gpu_type = CustomToolDetailGputype(d.pop("gpuType"))

        has_source = d.pop("hasSource")

        home_disk_gi = d.pop("homeDiskGi")

        def _parse_max_runtime_seconds(data: object) -> int | None:
            if data is None:
                return data
            return cast(int | None, data)

        max_runtime_seconds = _parse_max_runtime_seconds(d.pop("maxRuntimeSeconds"))

        memory = CustomToolDetailMemory(d.pop("memory"))

        name = d.pop("name")

        paper_url = d.pop("paperUrl")

        published = d.pop("published")

        serves_models = d.pop("servesModels")

        def _parse_source_digest(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        source_digest = _parse_source_digest(d.pop("sourceDigest"))

        status = CustomToolStatus(d.pop("status"))

        tags = cast(list[str], d.pop("tags"))

        trainable = d.pop("trainable")

        updated_at = isoparse(d.pop("updatedAt"))

        def _parse_version(data: object) -> CustomToolVersion | None:
            if data is None:
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                version_type_0 = CustomToolVersion.from_dict(data)

                return version_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(CustomToolVersion | None, data)

        version = _parse_version(d.pop("version"))

        custom_tool_detail = cls(
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
            serves_models=serves_models,
            source_digest=source_digest,
            status=status,
            tags=tags,
            trainable=trainable,
            updated_at=updated_at,
            version=version,
        )

        custom_tool_detail.additional_properties = d
        return custom_tool_detail

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
