from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="MeLimitsMonthlyJobsType0")


@_attrs_define
class MeLimitsMonthlyJobsType0:
    """Null unless your tier is Free, the only tier with a monthly job cap.

    Attributes:
        limit (int):
        remaining (int):
        used (int):
    """

    limit: int
    remaining: int
    used: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        limit = self.limit

        remaining = self.remaining

        used = self.used

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "limit": limit,
                "remaining": remaining,
                "used": used,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        limit = d.pop("limit")

        remaining = d.pop("remaining")

        used = d.pop("used")

        me_limits_monthly_jobs_type_0 = cls(
            limit=limit,
            remaining=remaining,
            used=used,
        )

        me_limits_monthly_jobs_type_0.additional_properties = d
        return me_limits_monthly_jobs_type_0

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
