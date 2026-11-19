from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.me_limits_monthly_jobs_type_0 import MeLimitsMonthlyJobsType0


T = TypeVar("T", bound="MeLimits")


@_attrs_define
class MeLimits:
    """
    Attributes:
        max_batch_jobs (int): The most jobs one batch may hold (30,000).
        max_queued_jobs (int): The most jobs you may have queued at once (100,000).
        max_request_bytes (int): The largest request body the gateway accepts, 10 MiB (10,485,760 bytes).
        monthly_jobs (MeLimitsMonthlyJobsType0 | None): Null unless your tier is Free, the only tier with a monthly job
            cap.
        per_job_weighted_hours (float | None): The most a job's `weightedHoursBudget` may be, when your Premium
            organization pins a hard limit. Null when no such cap applies.
        requests_per_minute (int | None): This key's general allowance, in requests a minute (1,200). Polling has its
            own, 3,600 a minute (see "Rate limits" above). Null on a deployment that doesn't enforce per-key limits.
    """

    max_batch_jobs: int
    max_queued_jobs: int
    max_request_bytes: int
    monthly_jobs: MeLimitsMonthlyJobsType0 | None
    per_job_weighted_hours: float | None
    requests_per_minute: int | None
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.me_limits_monthly_jobs_type_0 import MeLimitsMonthlyJobsType0

        max_batch_jobs = self.max_batch_jobs

        max_queued_jobs = self.max_queued_jobs

        max_request_bytes = self.max_request_bytes

        monthly_jobs: dict[str, Any] | None
        if isinstance(self.monthly_jobs, MeLimitsMonthlyJobsType0):
            monthly_jobs = self.monthly_jobs.to_dict()
        else:
            monthly_jobs = self.monthly_jobs

        per_job_weighted_hours: float | None
        per_job_weighted_hours = self.per_job_weighted_hours

        requests_per_minute: int | None
        requests_per_minute = self.requests_per_minute

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "maxBatchJobs": max_batch_jobs,
                "maxQueuedJobs": max_queued_jobs,
                "maxRequestBytes": max_request_bytes,
                "monthlyJobs": monthly_jobs,
                "perJobWeightedHours": per_job_weighted_hours,
                "requestsPerMinute": requests_per_minute,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.me_limits_monthly_jobs_type_0 import MeLimitsMonthlyJobsType0

        d = dict(src_dict)
        max_batch_jobs = d.pop("maxBatchJobs")

        max_queued_jobs = d.pop("maxQueuedJobs")

        max_request_bytes = d.pop("maxRequestBytes")

        def _parse_monthly_jobs(data: object) -> MeLimitsMonthlyJobsType0 | None:
            if data is None:
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                monthly_jobs_type_0 = MeLimitsMonthlyJobsType0.from_dict(data)

                return monthly_jobs_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(MeLimitsMonthlyJobsType0 | None, data)

        monthly_jobs = _parse_monthly_jobs(d.pop("monthlyJobs"))

        def _parse_per_job_weighted_hours(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        per_job_weighted_hours = _parse_per_job_weighted_hours(d.pop("perJobWeightedHours"))

        def _parse_requests_per_minute(data: object) -> int | None:
            if data is None:
                return data
            return cast(int | None, data)

        requests_per_minute = _parse_requests_per_minute(d.pop("requestsPerMinute"))

        me_limits = cls(
            max_batch_jobs=max_batch_jobs,
            max_queued_jobs=max_queued_jobs,
            max_request_bytes=max_request_bytes,
            monthly_jobs=monthly_jobs,
            per_job_weighted_hours=per_job_weighted_hours,
            requests_per_minute=requests_per_minute,
        )

        me_limits.additional_properties = d
        return me_limits

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
