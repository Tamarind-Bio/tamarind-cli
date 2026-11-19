from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.usage_page_items_item_dimensions import UsagePageItemsItemDimensions


T = TypeVar("T", bound="UsagePageItemsItem")


@_attrs_define
class UsagePageItemsItem:
    """
    Attributes:
        dimensions (UsagePageItemsItemDimensions): One entry per `groupBy` value, e.g. `{"tool": "alphafold", "month":
            "2026-10"}`.
        value (float):
    """

    dimensions: UsagePageItemsItemDimensions
    value: float
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        dimensions = self.dimensions.to_dict()

        value = self.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "dimensions": dimensions,
                "value": value,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.usage_page_items_item_dimensions import UsagePageItemsItemDimensions

        d = dict(src_dict)
        dimensions = UsagePageItemsItemDimensions.from_dict(d.pop("dimensions"))

        value = d.pop("value")

        usage_page_items_item = cls(
            dimensions=dimensions,
            value=value,
        )

        usage_page_items_item.additional_properties = d
        return usage_page_items_item

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
