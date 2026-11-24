from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="ToolFacetsFunctionsItem")


@_attrs_define
class ToolFacetsFunctionsItem:
    """
    Attributes:
        description (None | str): The curated taxonomy's description; null when it has none.
        label (str): The curated taxonomy's label for this value; `name` when the taxonomy doesn't define it.
        name (str):
        tool_count (int): How many tools you can see with this value, what the filter returns. Every value the curated
            taxonomy defines is listed, so this can be 0.
    """

    description: None | str
    label: str
    name: str
    tool_count: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        description: None | str
        description = self.description

        label = self.label

        name = self.name

        tool_count = self.tool_count

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "description": description,
                "label": label,
                "name": name,
                "toolCount": tool_count,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_description(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        description = _parse_description(d.pop("description"))

        label = d.pop("label")

        name = d.pop("name")

        tool_count = d.pop("toolCount")

        tool_facets_functions_item = cls(
            description=description,
            label=label,
            name=name,
            tool_count=tool_count,
        )

        tool_facets_functions_item.additional_properties = d
        return tool_facets_functions_item

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
