from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.pipeline_estimate_breakdown_item import PipelineEstimateBreakdownItem


T = TypeVar("T", bound="PipelineEstimate")


@_attrs_define
class PipelineEstimate:
    """A pipeline run's cost, before running, as today's pipeline estimator returns it. It has no runtime; one is added
    when the estimator produces it.

        Attributes:
            assumptions (list[str]): What the estimate takes for granted: chiefly that every molecule passes every filter.
                Empty when there is nothing to state.
            breakdown (list[PipelineEstimateBreakdownItem]): One entry per node.
            estimate_failed (bool): True when the run could not be priced. The figures are then not a quote, and a zero is
                not a free run.
            job_count (int): How many jobs the run would create.
            weighted_hours (float): The total weighted (compute) hours, the figure your budget is checked against at submit.
    """

    assumptions: list[str]
    breakdown: list[PipelineEstimateBreakdownItem]
    estimate_failed: bool
    job_count: int
    weighted_hours: float
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        assumptions = self.assumptions

        breakdown = []
        for breakdown_item_data in self.breakdown:
            breakdown_item = breakdown_item_data.to_dict()
            breakdown.append(breakdown_item)

        estimate_failed = self.estimate_failed

        job_count = self.job_count

        weighted_hours = self.weighted_hours

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "assumptions": assumptions,
                "breakdown": breakdown,
                "estimateFailed": estimate_failed,
                "jobCount": job_count,
                "weightedHours": weighted_hours,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.pipeline_estimate_breakdown_item import PipelineEstimateBreakdownItem

        d = dict(src_dict)
        assumptions = cast(list[str], d.pop("assumptions"))

        breakdown = []
        _breakdown = d.pop("breakdown")
        for breakdown_item_data in _breakdown:
            breakdown_item = PipelineEstimateBreakdownItem.from_dict(breakdown_item_data)

            breakdown.append(breakdown_item)

        estimate_failed = d.pop("estimateFailed")

        job_count = d.pop("jobCount")

        weighted_hours = d.pop("weightedHours")

        pipeline_estimate = cls(
            assumptions=assumptions,
            breakdown=breakdown,
            estimate_failed=estimate_failed,
            job_count=job_count,
            weighted_hours=weighted_hours,
        )

        pipeline_estimate.additional_properties = d
        return pipeline_estimate

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
