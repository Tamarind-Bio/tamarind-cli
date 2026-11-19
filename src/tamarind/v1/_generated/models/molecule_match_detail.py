from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.molecule_match_detail_axis import MoleculeMatchDetailAxis

T = TypeVar("T", bound="MoleculeMatchDetail")


@_attrs_define
class MoleculeMatchDetail:
    """
    Attributes:
        axis (MoleculeMatchDetailAxis):
        key (str):
        tool (None | str):
        value (None | str):
    """

    axis: MoleculeMatchDetailAxis
    key: str
    tool: None | str
    value: None | str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        axis = self.axis.value

        key = self.key

        tool: None | str
        tool = self.tool

        value: None | str
        value = self.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "axis": axis,
                "key": key,
                "tool": tool,
                "value": value,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        axis = MoleculeMatchDetailAxis(d.pop("axis"))

        key = d.pop("key")

        def _parse_tool(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        tool = _parse_tool(d.pop("tool"))

        def _parse_value(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        value = _parse_value(d.pop("value"))

        molecule_match_detail = cls(
            axis=axis,
            key=key,
            tool=tool,
            value=value,
        )

        molecule_match_detail.additional_properties = d
        return molecule_match_detail

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
