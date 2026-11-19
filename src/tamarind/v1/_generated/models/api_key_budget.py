from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..models.api_key_budget_period import ApiKeyBudgetPeriod

T = TypeVar("T", bound="ApiKeyBudget")


@_attrs_define
class ApiKeyBudget:
    """A hard spending limit on a key. Not supported yet; the shape is kept for when key budgets are enforced.

    Attributes:
        period (ApiKeyBudgetPeriod):
        weighted_hours (float):
    """

    period: ApiKeyBudgetPeriod
    weighted_hours: float

    def to_dict(self) -> dict[str, Any]:
        period = self.period.value

        weighted_hours = self.weighted_hours

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "period": period,
                "weightedHours": weighted_hours,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        period = ApiKeyBudgetPeriod(d.pop("period"))

        weighted_hours = d.pop("weightedHours")

        api_key_budget = cls(
            period=period,
            weighted_hours=weighted_hours,
        )

        return api_key_budget
