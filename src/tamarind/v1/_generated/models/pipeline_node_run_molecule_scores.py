from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="PipelineNodeRunMoleculeScores")


@_attrs_define
class PipelineNodeRunMoleculeScores:
    """Per-tool scores keyed by tool, e.g. `{"protenix": {"ipSAE_AB": 0.62, "pDockQ_AB": 0.41}}`. Metric names are case-
    sensitive. To THRESHOLD or RANK on one of these, use `GET /molecules?nodeRunId=` with
    `filter=protenix.ipSAE_AB:gte:0.5` and `sortBy=protenix.ipSAE_AB` — this endpoint returns them but does not filter
    or sort by them.

    """

    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        pipeline_node_run_molecule_scores = cls()

        pipeline_node_run_molecule_scores.additional_properties = d
        return pipeline_node_run_molecule_scores

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
