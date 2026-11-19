from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

if TYPE_CHECKING:
    from ..models.usage_page_items_item import UsagePageItemsItem


T = TypeVar("T", bound="UsagePage")


@_attrs_define
class UsagePage:
    """
    Attributes:
        as_of (datetime.datetime): The oldest refresh time of the rows read. The time of the request when no rows were
            read.
        from_ (datetime.datetime): The start of the range, a Pacific month start.
        items (list[UsagePageItemsItem]): One per group with a value above zero, in the order of their dimension values.
        metric (str): The `metric` asked for.
        next_cursor (None | str):
        to (datetime.datetime): The end of the range, exclusive. Without a `to` in the request, when the reads finished
            (rounded up to the second), but never past the end of the month they read.
        total (float): The total for the whole query, not just this page.
    """

    as_of: datetime.datetime
    from_: datetime.datetime
    items: list[UsagePageItemsItem]
    metric: str
    next_cursor: None | str
    to: datetime.datetime
    total: float
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        as_of = self.as_of.isoformat()

        from_ = self.from_.isoformat()

        items = []
        for items_item_data in self.items:
            items_item = items_item_data.to_dict()
            items.append(items_item)

        metric = self.metric

        next_cursor: None | str
        next_cursor = self.next_cursor

        to = self.to.isoformat()

        total = self.total

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "asOf": as_of,
                "from": from_,
                "items": items,
                "metric": metric,
                "nextCursor": next_cursor,
                "to": to,
                "total": total,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.usage_page_items_item import UsagePageItemsItem

        d = dict(src_dict)
        as_of = isoparse(d.pop("asOf"))

        from_ = isoparse(d.pop("from"))

        items = []
        _items = d.pop("items")
        for items_item_data in _items:
            items_item = UsagePageItemsItem.from_dict(items_item_data)

            items.append(items_item)

        metric = d.pop("metric")

        def _parse_next_cursor(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        next_cursor = _parse_next_cursor(d.pop("nextCursor"))

        to = isoparse(d.pop("to"))

        total = d.pop("total")

        usage_page = cls(
            as_of=as_of,
            from_=from_,
            items=items,
            metric=metric,
            next_cursor=next_cursor,
            to=to,
            total=total,
        )

        usage_page.additional_properties = d
        return usage_page

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
