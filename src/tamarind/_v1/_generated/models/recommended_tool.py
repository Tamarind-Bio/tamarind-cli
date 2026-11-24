from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="RecommendedTool")


@_attrs_define
class RecommendedTool:
    """One tool, in recommended order. The ORDER is the recommendation.

    Attributes:
        display_name (str): The catalog's display name.
        preconditions (list[str]): What has to hold for this recommendation to stand, in prose. Empty when none is
            stated.
        reason (str): Why this tool, in prose.
        tool_id (str): The tool to run, as named by the tool catalogue.
    """

    display_name: str
    preconditions: list[str]
    reason: str
    tool_id: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        display_name = self.display_name

        preconditions = self.preconditions

        reason = self.reason

        tool_id = self.tool_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "displayName": display_name,
                "preconditions": preconditions,
                "reason": reason,
                "toolId": tool_id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        display_name = d.pop("displayName")

        preconditions = cast(list[str], d.pop("preconditions"))

        reason = d.pop("reason")

        tool_id = d.pop("toolId")

        recommended_tool = cls(
            display_name=display_name,
            preconditions=preconditions,
            reason=reason,
            tool_id=tool_id,
        )

        recommended_tool.additional_properties = d
        return recommended_tool

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
