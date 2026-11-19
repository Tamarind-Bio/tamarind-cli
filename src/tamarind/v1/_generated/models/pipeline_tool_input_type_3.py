from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..models.pipeline_tool_input_type_3_kind import PipelineToolInputType3Kind

T = TypeVar("T", bound="PipelineToolInputType3")


@_attrs_define
class PipelineToolInputType3:
    """
    Attributes:
        group_id (str):
        kind (PipelineToolInputType3Kind):
    """

    group_id: str
    kind: PipelineToolInputType3Kind

    def to_dict(self) -> dict[str, Any]:
        group_id = self.group_id

        kind = self.kind.value

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "groupId": group_id,
                "kind": kind,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        group_id = d.pop("groupId")

        kind = PipelineToolInputType3Kind(d.pop("kind"))

        pipeline_tool_input_type_3 = cls(
            group_id=group_id,
            kind=kind,
        )

        return pipeline_tool_input_type_3
