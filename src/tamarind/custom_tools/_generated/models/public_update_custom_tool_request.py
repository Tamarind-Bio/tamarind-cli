from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..models.public_update_custom_tool_request_gpu_type_type_0 import (
    PublicUpdateCustomToolRequestGpuTypeType0,
)
from ..models.public_update_custom_tool_request_memory_type_0 import (
    PublicUpdateCustomToolRequestMemoryType0,
)
from ..types import UNSET, Unset

T = TypeVar("T", bound="PublicUpdateCustomToolRequest")


@_attrs_define
class PublicUpdateCustomToolRequest:
    """
    Attributes:
        auto_publish (bool | None | Unset):
        cpu (int | None | Unset):
        description (None | str | Unset):
        display_name (None | str | Unset):
        est_time (None | str | Unset):
        functions (list[str] | None | Unset):
        gpu_type (None | PublicUpdateCustomToolRequestGpuTypeType0 | Unset):
        home_disk_gi (int | None | Unset):
        memory (None | PublicUpdateCustomToolRequestMemoryType0 | Unset):
        paper_url (None | str | Unset):
        tags (list[str] | None | Unset):
    """

    auto_publish: bool | None | Unset = UNSET
    cpu: int | None | Unset = UNSET
    description: None | str | Unset = UNSET
    display_name: None | str | Unset = UNSET
    est_time: None | str | Unset = UNSET
    functions: list[str] | None | Unset = UNSET
    gpu_type: None | PublicUpdateCustomToolRequestGpuTypeType0 | Unset = UNSET
    home_disk_gi: int | None | Unset = UNSET
    memory: None | PublicUpdateCustomToolRequestMemoryType0 | Unset = UNSET
    paper_url: None | str | Unset = UNSET
    tags: list[str] | None | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        auto_publish: bool | None | Unset
        if isinstance(self.auto_publish, Unset):
            auto_publish = UNSET
        else:
            auto_publish = self.auto_publish

        cpu: int | None | Unset
        if isinstance(self.cpu, Unset):
            cpu = UNSET
        else:
            cpu = self.cpu

        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        display_name: None | str | Unset
        if isinstance(self.display_name, Unset):
            display_name = UNSET
        else:
            display_name = self.display_name

        est_time: None | str | Unset
        if isinstance(self.est_time, Unset):
            est_time = UNSET
        else:
            est_time = self.est_time

        functions: list[str] | None | Unset
        if isinstance(self.functions, Unset):
            functions = UNSET
        elif isinstance(self.functions, list):
            functions = self.functions

        else:
            functions = self.functions

        gpu_type: None | str | Unset
        if isinstance(self.gpu_type, Unset):
            gpu_type = UNSET
        elif isinstance(self.gpu_type, PublicUpdateCustomToolRequestGpuTypeType0):
            gpu_type = self.gpu_type.value
        else:
            gpu_type = self.gpu_type

        home_disk_gi: int | None | Unset
        if isinstance(self.home_disk_gi, Unset):
            home_disk_gi = UNSET
        else:
            home_disk_gi = self.home_disk_gi

        memory: None | str | Unset
        if isinstance(self.memory, Unset):
            memory = UNSET
        elif isinstance(self.memory, PublicUpdateCustomToolRequestMemoryType0):
            memory = self.memory.value
        else:
            memory = self.memory

        paper_url: None | str | Unset
        if isinstance(self.paper_url, Unset):
            paper_url = UNSET
        else:
            paper_url = self.paper_url

        tags: list[str] | None | Unset
        if isinstance(self.tags, Unset):
            tags = UNSET
        elif isinstance(self.tags, list):
            tags = self.tags

        else:
            tags = self.tags

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if auto_publish is not UNSET:
            field_dict["autoPublish"] = auto_publish
        if cpu is not UNSET:
            field_dict["cpu"] = cpu
        if description is not UNSET:
            field_dict["description"] = description
        if display_name is not UNSET:
            field_dict["displayName"] = display_name
        if est_time is not UNSET:
            field_dict["estTime"] = est_time
        if functions is not UNSET:
            field_dict["functions"] = functions
        if gpu_type is not UNSET:
            field_dict["gpuType"] = gpu_type
        if home_disk_gi is not UNSET:
            field_dict["homeDiskGi"] = home_disk_gi
        if memory is not UNSET:
            field_dict["memory"] = memory
        if paper_url is not UNSET:
            field_dict["paperUrl"] = paper_url
        if tags is not UNSET:
            field_dict["tags"] = tags

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_auto_publish(data: object) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        auto_publish = _parse_auto_publish(d.pop("autoPublish", UNSET))

        def _parse_cpu(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        cpu = _parse_cpu(d.pop("cpu", UNSET))

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_display_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        display_name = _parse_display_name(d.pop("displayName", UNSET))

        def _parse_est_time(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        est_time = _parse_est_time(d.pop("estTime", UNSET))

        def _parse_functions(data: object) -> list[str] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                functions_type_0 = cast(list[str], data)

                return functions_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[str] | None | Unset, data)

        functions = _parse_functions(d.pop("functions", UNSET))

        def _parse_gpu_type(
            data: object,
        ) -> None | PublicUpdateCustomToolRequestGpuTypeType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                gpu_type_type_0 = PublicUpdateCustomToolRequestGpuTypeType0(data)

                return gpu_type_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | PublicUpdateCustomToolRequestGpuTypeType0 | Unset, data)

        gpu_type = _parse_gpu_type(d.pop("gpuType", UNSET))

        def _parse_home_disk_gi(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        home_disk_gi = _parse_home_disk_gi(d.pop("homeDiskGi", UNSET))

        def _parse_memory(
            data: object,
        ) -> None | PublicUpdateCustomToolRequestMemoryType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                memory_type_0 = PublicUpdateCustomToolRequestMemoryType0(data)

                return memory_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | PublicUpdateCustomToolRequestMemoryType0 | Unset, data)

        memory = _parse_memory(d.pop("memory", UNSET))

        def _parse_paper_url(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        paper_url = _parse_paper_url(d.pop("paperUrl", UNSET))

        def _parse_tags(data: object) -> list[str] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                tags_type_0 = cast(list[str], data)

                return tags_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[str] | None | Unset, data)

        tags = _parse_tags(d.pop("tags", UNSET))

        public_update_custom_tool_request = cls(
            auto_publish=auto_publish,
            cpu=cpu,
            description=description,
            display_name=display_name,
            est_time=est_time,
            functions=functions,
            gpu_type=gpu_type,
            home_disk_gi=home_disk_gi,
            memory=memory,
            paper_url=paper_url,
            tags=tags,
        )

        return public_update_custom_tool_request
