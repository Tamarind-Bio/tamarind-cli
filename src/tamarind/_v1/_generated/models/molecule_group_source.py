from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="MoleculeGroupSource")


@_attrs_define
class MoleculeGroupSource:
    """`Group.source` — set when the group is a job's output.

    Attributes:
        job_id (None | str): The job's bare stored id, without the `job_` or `batch_` prefix `/jobs` uses.
        tool_name (None | str):
    """

    job_id: None | str
    tool_name: None | str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        job_id: None | str
        job_id = self.job_id

        tool_name: None | str
        tool_name = self.tool_name

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "jobId": job_id,
                "toolName": tool_name,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_job_id(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        job_id = _parse_job_id(d.pop("jobId"))

        def _parse_tool_name(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        tool_name = _parse_tool_name(d.pop("toolName"))

        molecule_group_source = cls(
            job_id=job_id,
            tool_name=tool_name,
        )

        molecule_group_source.additional_properties = d
        return molecule_group_source

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
