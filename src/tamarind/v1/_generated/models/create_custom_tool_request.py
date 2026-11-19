from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..models.create_custom_tool_request_gputype import CreateCustomToolRequestGputype
from ..models.create_custom_tool_request_memory import CreateCustomToolRequestMemory
from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateCustomToolRequest")


@_attrs_define
class CreateCustomToolRequest:
    """
    Attributes:
        name (str): A unique lowercase name containing letters, numbers, and hyphens.
        cpu (int | Unset): Number of CPU cores allocated to each run. Defaults to 1. Default: 1.
        description (str | Unset): Short explanation of the tool. Defaults to an empty string. Default: ''.
        display_name (str | Unset): Human-readable name shown in the UI. Defaults to an empty string. Default: ''.
        gpu_type (CreateCustomToolRequestGputype | Unset): GPU allocated to each run: "None", T4, L4, L40S, or A100.
            Defaults to "None". A10 is retired: it is still accepted and runs on L4. Default:
            CreateCustomToolRequestGputype.NONE.
        memory (CreateCustomToolRequestMemory | Unset): Memory allocated to each run. Defaults to "8Gi". Default:
            CreateCustomToolRequestMemory.VALUE_0.
    """

    name: str
    cpu: int | Unset = 1
    description: str | Unset = ""
    display_name: str | Unset = ""
    gpu_type: CreateCustomToolRequestGputype | Unset = CreateCustomToolRequestGputype.NONE
    memory: CreateCustomToolRequestMemory | Unset = CreateCustomToolRequestMemory.VALUE_0

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        cpu = self.cpu

        description = self.description

        display_name = self.display_name

        gpu_type: str | Unset = UNSET
        if not isinstance(self.gpu_type, Unset):
            gpu_type = self.gpu_type.value

        memory: str | Unset = UNSET
        if not isinstance(self.memory, Unset):
            memory = self.memory.value

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "name": name,
            }
        )
        if cpu is not UNSET:
            field_dict["cpu"] = cpu
        if description is not UNSET:
            field_dict["description"] = description
        if display_name is not UNSET:
            field_dict["displayName"] = display_name
        if gpu_type is not UNSET:
            field_dict["gpuType"] = gpu_type
        if memory is not UNSET:
            field_dict["memory"] = memory

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        cpu = d.pop("cpu", UNSET)

        description = d.pop("description", UNSET)

        display_name = d.pop("displayName", UNSET)

        _gpu_type = d.pop("gpuType", UNSET)
        gpu_type: CreateCustomToolRequestGputype | Unset
        if isinstance(_gpu_type, Unset):
            gpu_type = UNSET
        else:
            gpu_type = CreateCustomToolRequestGputype(_gpu_type)

        _memory = d.pop("memory", UNSET)
        memory: CreateCustomToolRequestMemory | Unset
        if isinstance(_memory, Unset):
            memory = UNSET
        else:
            memory = CreateCustomToolRequestMemory(_memory)

        create_custom_tool_request = cls(
            name=name,
            cpu=cpu,
            description=description,
            display_name=display_name,
            gpu_type=gpu_type,
            memory=memory,
        )

        return create_custom_tool_request
