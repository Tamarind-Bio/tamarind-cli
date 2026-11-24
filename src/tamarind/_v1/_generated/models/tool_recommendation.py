from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.tool_recommendation_abstain_reason_type_1 import ToolRecommendationAbstainReasonType1
from ..models.tool_recommendation_abstain_reason_type_2_type_1 import (
    ToolRecommendationAbstainReasonType2Type1,
)
from ..models.tool_recommendation_abstain_reason_type_3_type_1 import (
    ToolRecommendationAbstainReasonType3Type1,
)

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
            abstain_reason (None | ToolRecommendationAbstainReasonType1 | ToolRecommendationAbstainReasonType2Type1 |
                ToolRecommendationAbstainReasonType3Type1): Why no tool was recommended; null when one was. `needs_more_detail`,
                `summary` names the missing fact (which interface this is, say); answer it and ask again.
                `not_available_to_your_account`, the tools that fit aren't available to you.
            retryable (bool): Whether asking again may give a recommendation, after adding the missing detail for
                `needs_more_detail` or unchanged for a transient failure. False when a tool was recommended.
            summary (str): A short explanation of the ranking, for a person to read. It also carries the caveats: whether
                the benchmark had measured your target, whether anything measured this kind of task at all, and what the service
                could not establish.
            tools (list[RecommendedTool]): Ranked best-first, and only the tools worth running — usually two to four, not
                the whole catalogue. Empty when `abstain` is true.
    """

    abstain: bool
    abstain_reason: (
        None
        | ToolRecommendationAbstainReasonType1
        | ToolRecommendationAbstainReasonType2Type1
        | ToolRecommendationAbstainReasonType3Type1
    )
    retryable: bool
    summary: str
    tools: list[RecommendedTool]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        abstain = self.abstain

        abstain_reason: None | str
        if isinstance(self.abstain_reason, ToolRecommendationAbstainReasonType1):
            abstain_reason = self.abstain_reason.value
        elif isinstance(self.abstain_reason, ToolRecommendationAbstainReasonType2Type1):
            abstain_reason = self.abstain_reason.value
        elif isinstance(self.abstain_reason, ToolRecommendationAbstainReasonType3Type1):
            abstain_reason = self.abstain_reason.value
        else:
            abstain_reason = self.abstain_reason

        retryable = self.retryable

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
                "abstainReason": abstain_reason,
                "retryable": retryable,
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

        def _parse_abstain_reason(
            data: object,
        ) -> (
            None
            | ToolRecommendationAbstainReasonType1
            | ToolRecommendationAbstainReasonType2Type1
            | ToolRecommendationAbstainReasonType3Type1
        ):
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                abstain_reason_type_1 = ToolRecommendationAbstainReasonType1(data)

                return abstain_reason_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            try:
                if not isinstance(data, str):
                    raise TypeError()
                abstain_reason_type_2_type_1 = ToolRecommendationAbstainReasonType2Type1(data)

                return abstain_reason_type_2_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            try:
                if not isinstance(data, str):
                    raise TypeError()
                abstain_reason_type_3_type_1 = ToolRecommendationAbstainReasonType3Type1(data)

                return abstain_reason_type_3_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(
                None
                | ToolRecommendationAbstainReasonType1
                | ToolRecommendationAbstainReasonType2Type1
                | ToolRecommendationAbstainReasonType3Type1,
                data,
            )

        abstain_reason = _parse_abstain_reason(d.pop("abstainReason"))

        retryable = d.pop("retryable")

        summary = d.pop("summary")

        tools = []
        _tools = d.pop("tools")
        for tools_item_data in _tools:
            tools_item = RecommendedTool.from_dict(tools_item_data)

            tools.append(tools_item)

        tool_recommendation = cls(
            abstain=abstain,
            abstain_reason=abstain_reason,
            retryable=retryable,
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
