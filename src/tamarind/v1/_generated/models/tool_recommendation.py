from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.recommended_tool import RecommendedTool


T = TypeVar("T", bound="ToolRecommendation")


@_attrs_define
class ToolRecommendation:
    """A ranked recommendation, or a reasoned refusal to make one.

    `abstain` is a normal outcome, not an error: it means no tool could be defended
    for this request, and `summary` says why. Callers should handle it as an answer.

        Attributes:
            abstain (bool): `false` — `tools` is ranked, best first, and the first entry is what to run. `true` — no tool
                could be justified, `tools` is empty, and `summary` says what was missing. An abstention is an answer, not an
                error.
            summary (str): A short explanation of the ranking, for a person to read. It also carries the caveats: whether
                the benchmark had measured your target, whether anything measured this kind of task at all, and what the service
                could not establish.
            tools (list[RecommendedTool]): Ranked best-first, and only the tools worth running — usually two to four, not
                the whole catalogue. Empty when `abstain` is true.
    """

    abstain: bool
    summary: str
    tools: list[RecommendedTool]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        abstain = self.abstain

        summary = self.summary

        tools = []
        for tools_item_data in self.tools:
            tools_item = tools_item_data.to_dict()
            tools.append(tools_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "abstain": abstain,
                "summary": summary,
                "tools": tools,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.recommended_tool import RecommendedTool

        d = dict(src_dict)
        abstain = d.pop("abstain")

        summary = d.pop("summary")

        tools = []
        _tools = d.pop("tools")
        for tools_item_data in _tools:
            tools_item = RecommendedTool.from_dict(tools_item_data)

            tools.append(tools_item)

        tool_recommendation = cls(
            abstain=abstain,
            summary=summary,
            tools=tools,
        )

        tool_recommendation.additional_properties = d
        return tool_recommendation

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
