from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

T = TypeVar("T", bound="ContractTermsItem")


@_attrs_define
class ContractTermsItem:
    """
    Attributes:
        contracted_hours (float):
        effective_hours (float):
        end_at (datetime.datetime | None): Pacific midnight after the term's last day (exclusive). Null when the stored
            date is unreadable.
        is_active (bool):
        promo_hours (float):
        remaining_hours (float | None): Null whenever `usedHours` is.
        rollover_hours (float):
        start_at (datetime.datetime | None): Pacific midnight on the term's first day. Null when the stored date is
            unreadable.
        used_hours (float | None): Null when nothing records the usage, such as an active term whose stored figure is
            unreadable or an ended term with no final usage.
    """

    contracted_hours: float
    effective_hours: float
    end_at: datetime.datetime | None
    is_active: bool
    promo_hours: float
    remaining_hours: float | None
    rollover_hours: float
    start_at: datetime.datetime | None
    used_hours: float | None
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        contracted_hours = self.contracted_hours

        effective_hours = self.effective_hours

        end_at: None | str
        if isinstance(self.end_at, datetime.datetime):
            end_at = self.end_at.isoformat()
        else:
            end_at = self.end_at

        is_active = self.is_active

        promo_hours = self.promo_hours

        remaining_hours: float | None
        remaining_hours = self.remaining_hours

        rollover_hours = self.rollover_hours

        start_at: None | str
        if isinstance(self.start_at, datetime.datetime):
            start_at = self.start_at.isoformat()
        else:
            start_at = self.start_at

        used_hours: float | None
        used_hours = self.used_hours

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "contractedHours": contracted_hours,
                "effectiveHours": effective_hours,
                "endAt": end_at,
                "isActive": is_active,
                "promoHours": promo_hours,
                "remainingHours": remaining_hours,
                "rolloverHours": rollover_hours,
                "startAt": start_at,
                "usedHours": used_hours,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        contracted_hours = d.pop("contractedHours")

        effective_hours = d.pop("effectiveHours")

        def _parse_end_at(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                end_at_type_0 = isoparse(data)

                return end_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        end_at = _parse_end_at(d.pop("endAt"))

        is_active = d.pop("isActive")

        promo_hours = d.pop("promoHours")

        def _parse_remaining_hours(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        remaining_hours = _parse_remaining_hours(d.pop("remainingHours"))

        rollover_hours = d.pop("rolloverHours")

        def _parse_start_at(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                start_at_type_0 = isoparse(data)

                return start_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        start_at = _parse_start_at(d.pop("startAt"))

        def _parse_used_hours(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        used_hours = _parse_used_hours(d.pop("usedHours"))

        contract_terms_item = cls(
            contracted_hours=contracted_hours,
            effective_hours=effective_hours,
            end_at=end_at,
            is_active=is_active,
            promo_hours=promo_hours,
            remaining_hours=remaining_hours,
            rollover_hours=rollover_hours,
            start_at=start_at,
            used_hours=used_hours,
        )

        contract_terms_item.additional_properties = d
        return contract_terms_item

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
