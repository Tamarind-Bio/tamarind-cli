from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="DiagnosticAllowedRange")


@_attrs_define
class DiagnosticAllowedRange:
    """
    Attributes:
        maximum (float | Unset):
        minimum (float | Unset):
    """

    maximum: float | Unset = UNSET
    minimum: float | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        maximum = self.maximum

        minimum = self.minimum

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if maximum is not UNSET:
            field_dict["maximum"] = maximum
        if minimum is not UNSET:
            field_dict["minimum"] = minimum

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        maximum = d.pop("maximum", UNSET)

        minimum = d.pop("minimum", UNSET)

        diagnostic_allowed_range = cls(
            maximum=maximum,
            minimum=minimum,
        )

        diagnostic_allowed_range.additional_properties = d
        return diagnostic_allowed_range

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
