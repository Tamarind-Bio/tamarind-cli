from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="AssayEstimate")


@_attrs_define
class AssayEstimate:
    """
    Attributes:
        assay_type (str):
        cost_per_sequence_usd (float | None): Null when `estimatedCostUsd` is.
        estimated_cost_usd (float | None): Null when the lab prices this order on request. `note` says so.
        note (str): What this figure is. It is an estimate, not a quote: Tamarind confirms the final price before the
            order is approved.
        provider (str): The lab that gave the estimate.
        sequence_count (int):
        turnaround (None | str): The assay type's usual turnaround, as text.
        turnaround_days (float | None): The lab's own figure for this order, when it gave one.
    """

    assay_type: str
    cost_per_sequence_usd: float | None
    estimated_cost_usd: float | None
    note: str
    provider: str
    sequence_count: int
    turnaround: None | str
    turnaround_days: float | None
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        assay_type = self.assay_type

        cost_per_sequence_usd: float | None
        cost_per_sequence_usd = self.cost_per_sequence_usd

        estimated_cost_usd: float | None
        estimated_cost_usd = self.estimated_cost_usd

        note = self.note

        provider = self.provider

        sequence_count = self.sequence_count

        turnaround: None | str
        turnaround = self.turnaround

        turnaround_days: float | None
        turnaround_days = self.turnaround_days

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "assayType": assay_type,
                "costPerSequenceUsd": cost_per_sequence_usd,
                "estimatedCostUsd": estimated_cost_usd,
                "note": note,
                "provider": provider,
                "sequenceCount": sequence_count,
                "turnaround": turnaround,
                "turnaroundDays": turnaround_days,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        assay_type = d.pop("assayType")

        def _parse_cost_per_sequence_usd(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        cost_per_sequence_usd = _parse_cost_per_sequence_usd(d.pop("costPerSequenceUsd"))

        def _parse_estimated_cost_usd(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        estimated_cost_usd = _parse_estimated_cost_usd(d.pop("estimatedCostUsd"))

        note = d.pop("note")

        provider = d.pop("provider")

        sequence_count = d.pop("sequenceCount")

        def _parse_turnaround(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        turnaround = _parse_turnaround(d.pop("turnaround"))

        def _parse_turnaround_days(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        turnaround_days = _parse_turnaround_days(d.pop("turnaroundDays"))

        assay_estimate = cls(
            assay_type=assay_type,
            cost_per_sequence_usd=cost_per_sequence_usd,
            estimated_cost_usd=estimated_cost_usd,
            note=note,
            provider=provider,
            sequence_count=sequence_count,
            turnaround=turnaround,
            turnaround_days=turnaround_days,
        )

        assay_estimate.additional_properties = d
        return assay_estimate

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
