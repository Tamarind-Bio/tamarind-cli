from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="Estimate")


@_attrs_define
class Estimate:
    """A job's or a batch's runtime and cost, before running: exactly what today's estimator
    returns, the same figures the submit budget gate checks. No ranges, elapsed time or
    per-stage breakdown yet; fields are added (which isn't a breaking change) when the
    estimator produces them.

        Attributes:
            job_count (int): How many jobs this would create, including fan-out. For a batch over 500 rows, the count for
                its first 500 rows scaled to all of them.
            notes (list[str]): Caveats a user should see, such as that a batch was priced from its first 500 rows. Empty
                when there are none.
            per_job_runtime_seconds (float | None): The estimated runtime of one job, averaged across a batch. Null means
                unknown, when the estimator has no runtime for the tool; it is never 0 for that.
            weighted_hours (float | None): The total weighted (compute) hours, the figure your budget is checked against at
                submit, at the low-priority price when the request sets `lowPriority`, and for a batch over 500 rows scaled from
                its first 500. Null on the Free tier, with a note saying so.
    """

    job_count: int
    notes: list[str]
    per_job_runtime_seconds: float | None
    weighted_hours: float | None
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        job_count = self.job_count

        notes = self.notes

        per_job_runtime_seconds: float | None
        per_job_runtime_seconds = self.per_job_runtime_seconds

        weighted_hours: float | None
        weighted_hours = self.weighted_hours

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "jobCount": job_count,
                "notes": notes,
                "perJobRuntimeSeconds": per_job_runtime_seconds,
                "weightedHours": weighted_hours,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        job_count = d.pop("jobCount")

        notes = cast(list[str], d.pop("notes"))

        def _parse_per_job_runtime_seconds(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        per_job_runtime_seconds = _parse_per_job_runtime_seconds(d.pop("perJobRuntimeSeconds"))

        def _parse_weighted_hours(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        weighted_hours = _parse_weighted_hours(d.pop("weightedHours"))

        estimate = cls(
            job_count=job_count,
            notes=notes,
            per_job_runtime_seconds=per_job_runtime_seconds,
            weighted_hours=weighted_hours,
        )

        estimate.additional_properties = d
        return estimate

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
