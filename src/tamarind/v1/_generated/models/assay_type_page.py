from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.assay_type import AssayType


T = TypeVar("T", bound="AssayTypePage")


@_attrs_define
class AssayTypePage:
    """
    Attributes:
        items (list[AssayType]):
        next_cursor (None | str):
        request_access_url (str):
        wet_lab_access (bool):
    """

    items: list[AssayType]
    next_cursor: None | str
    request_access_url: str
    wet_lab_access: bool
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        items = []
        for items_item_data in self.items:
            items_item = items_item_data.to_dict()
            items.append(items_item)

        next_cursor: None | str
        next_cursor = self.next_cursor

        request_access_url = self.request_access_url

        wet_lab_access = self.wet_lab_access

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "items": items,
                "nextCursor": next_cursor,
                "requestAccessUrl": request_access_url,
                "wetLabAccess": wet_lab_access,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.assay_type import AssayType

        d = dict(src_dict)
        items = []
        _items = d.pop("items")
        for items_item_data in _items:
            items_item = AssayType.from_dict(items_item_data)

            items.append(items_item)

        def _parse_next_cursor(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        next_cursor = _parse_next_cursor(d.pop("nextCursor"))

        request_access_url = d.pop("requestAccessUrl")

        wet_lab_access = d.pop("wetLabAccess")

        assay_type_page = cls(
            items=items,
            next_cursor=next_cursor,
            request_access_url=request_access_url,
            wet_lab_access=wet_lab_access,
        )

        assay_type_page.additional_properties = d
        return assay_type_page

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
