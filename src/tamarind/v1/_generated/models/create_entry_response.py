from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.board_entry import BoardEntry
    from ..models.board_resource_tagging import BoardResourceTagging


T = TypeVar("T", bound="CreateEntryResponse")


@_attrs_define
class CreateEntryResponse:
    """Every link on a new entry is a new link, so `resourceTagging` always comes back here —
    unlike an update, where it comes back only when the request carried `links`.

        Attributes:
            entry (BoardEntry | None):
            resource_tagging (BoardResourceTagging | None):
    """

    entry: BoardEntry | None
    resource_tagging: BoardResourceTagging | None
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.board_entry import BoardEntry
        from ..models.board_resource_tagging import BoardResourceTagging

        entry: dict[str, Any] | None
        if isinstance(self.entry, BoardEntry):
            entry = self.entry.to_dict()
        else:
            entry = self.entry

        resource_tagging: dict[str, Any] | None
        if isinstance(self.resource_tagging, BoardResourceTagging):
            resource_tagging = self.resource_tagging.to_dict()
        else:
            resource_tagging = self.resource_tagging

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "entry": entry,
                "resourceTagging": resource_tagging,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.board_entry import BoardEntry
        from ..models.board_resource_tagging import BoardResourceTagging

        d = dict(src_dict)

        def _parse_entry(data: object) -> BoardEntry | None:
            if data is None:
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                entry_type_0 = BoardEntry.from_dict(data)

                return entry_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(BoardEntry | None, data)

        entry = _parse_entry(d.pop("entry"))

        def _parse_resource_tagging(data: object) -> BoardResourceTagging | None:
            if data is None:
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                resource_tagging_type_0 = BoardResourceTagging.from_dict(data)

                return resource_tagging_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(BoardResourceTagging | None, data)

        resource_tagging = _parse_resource_tagging(d.pop("resourceTagging"))

        create_entry_response = cls(
            entry=entry,
            resource_tagging=resource_tagging,
        )

        create_entry_response.additional_properties = d
        return create_entry_response

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
