from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.budget_scope import BudgetScope
from ..models.budget_unit import BudgetUnit

T = TypeVar("T", bound="Budget")


@_attrs_define
class Budget:
    """
    Attributes:
        limit (float | None):
        name (None | str): The team or model name. On a `member` budget, the team whose per-member cap applies to you,
            or null when your own cap or the organization's default applies. Null for the organization's budget.
        period_ends_at (datetime.datetime | None): Always null for now.
        remaining (float | None): `limit` less `used`, and never below zero.
        scope (BudgetScope): `organization`, `team`, `member` or `model` for now. Keys have no budgets yet and the
            contract isn't listed here (see `getOrganizationContract`), so `apiKey` and `contract` don't occur.
        unit (BudgetUnit):
        used (float):
    """

    limit: float | None
    name: None | str
    period_ends_at: datetime.datetime | None
    remaining: float | None
    scope: BudgetScope
    unit: BudgetUnit
    used: float
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        limit: float | None
        limit = self.limit

        name: None | str
        name = self.name

        period_ends_at: None | str
        if isinstance(self.period_ends_at, datetime.datetime):
            period_ends_at = self.period_ends_at.isoformat()
        else:
            period_ends_at = self.period_ends_at

        remaining: float | None
        remaining = self.remaining

        scope = self.scope.value

        unit = self.unit.value

        used = self.used

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "limit": limit,
                "name": name,
                "periodEndsAt": period_ends_at,
                "remaining": remaining,
                "scope": scope,
                "unit": unit,
                "used": used,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_limit(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        limit = _parse_limit(d.pop("limit"))

        def _parse_name(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        name = _parse_name(d.pop("name"))

        def _parse_period_ends_at(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                period_ends_at_type_0 = isoparse(data)

                return period_ends_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        period_ends_at = _parse_period_ends_at(d.pop("periodEndsAt"))

        def _parse_remaining(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        remaining = _parse_remaining(d.pop("remaining"))

        scope = BudgetScope(d.pop("scope"))

        unit = BudgetUnit(d.pop("unit"))

        used = d.pop("used")

        budget = cls(
            limit=limit,
            name=name,
            period_ends_at=period_ends_at,
            remaining=remaining,
            scope=scope,
            unit=unit,
            used=used,
        )

        budget.additional_properties = d
        return budget

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
