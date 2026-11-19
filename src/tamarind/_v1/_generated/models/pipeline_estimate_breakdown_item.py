from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="PipelineEstimateBreakdownItem")


@_attrs_define
class PipelineEstimateBreakdownItem:
    """
    Attributes:
        job_count (int):
        kind (str): The node's kind, e.g. a tool, input or filter node.
        label (None | str): The node's display label, when it has one.
        molecules (int): Molecules entering the node.
        node (str): The node id.
        notes (list[str]): What this node's figures take for granted, such as an input with no molecules bound yet being
            counted as one.
        output_molecules (int): Molecules leaving the node.
        tool (None | str): The tool the node runs. Null for input and filter nodes.
        weighted_hours (float):
    """

    job_count: int
    kind: str
    label: None | str
    molecules: int
    node: str
    notes: list[str]
    output_molecules: int
    tool: None | str
    weighted_hours: float
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        job_count = self.job_count

        kind = self.kind

        label: None | str
        label = self.label

        molecules = self.molecules

        node = self.node

        notes = self.notes

        output_molecules = self.output_molecules

        tool: None | str
        tool = self.tool

        weighted_hours = self.weighted_hours

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "jobCount": job_count,
                "kind": kind,
                "label": label,
                "molecules": molecules,
                "node": node,
                "notes": notes,
                "outputMolecules": output_molecules,
                "tool": tool,
                "weightedHours": weighted_hours,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        job_count = d.pop("jobCount")

        kind = d.pop("kind")

        def _parse_label(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        label = _parse_label(d.pop("label"))

        molecules = d.pop("molecules")

        node = d.pop("node")

        notes = cast(list[str], d.pop("notes"))

        output_molecules = d.pop("outputMolecules")

        def _parse_tool(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        tool = _parse_tool(d.pop("tool"))

        weighted_hours = d.pop("weightedHours")

        pipeline_estimate_breakdown_item = cls(
            job_count=job_count,
            kind=kind,
            label=label,
            molecules=molecules,
            node=node,
            notes=notes,
            output_molecules=output_molecules,
            tool=tool,
            weighted_hours=weighted_hours,
        )

        pipeline_estimate_breakdown_item.additional_properties = d
        return pipeline_estimate_breakdown_item

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
