from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.board_entry import BoardEntry
    from ..models.board_meta import BoardMeta
    from ..models.board_resource_tagging import BoardResourceTagging


T = TypeVar("T", bound="UpdateEntryResponse")


@_attrs_define
class UpdateEntryResponse:
    """`resourceTagging` comes back only when the request carried `links`. An update that did
    not touch them reports no tagging rather than an empty one.

        Attributes:
            entry (BoardEntry | None):
            meta (BoardMeta | None):
            resource_tagging (BoardResourceTagging | None | Unset):
    """

    entry: BoardEntry | None
    meta: BoardMeta | None
    resource_tagging: BoardResourceTagging | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.board_entry import BoardEntry
        from ..models.board_meta import BoardMeta
        from ..models.board_resource_tagging import BoardResourceTagging

        entry: dict[str, Any] | None
        if isinstance(self.entry, BoardEntry):
            entry = self.entry.to_dict()
        else:
            entry = self.entry

        meta: dict[str, Any] | None
        if isinstance(self.meta, BoardMeta):
            meta = self.meta.to_dict()
        else:
            meta = self.meta

        resource_tagging: dict[str, Any] | None | Unset
        if isinstance(self.resource_tagging, Unset):
            resource_tagging = UNSET
        elif isinstance(self.resource_tagging, BoardResourceTagging):
            resource_tagging = self.resource_tagging.to_dict()
        else:
            resource_tagging = self.resource_tagging

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "entry": entry,
                "meta": meta,
            }
        )
        if resource_tagging is not UNSET:
            field_dict["resourceTagging"] = resource_tagging

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.board_entry import BoardEntry
        from ..models.board_meta import BoardMeta
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

        def _parse_meta(data: object) -> BoardMeta | None:
            if data is None:
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                meta_type_0 = BoardMeta.from_dict(data)

                return meta_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(BoardMeta | None, data)

        meta = _parse_meta(d.pop("meta"))

        def _parse_resource_tagging(data: object) -> BoardResourceTagging | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                resource_tagging_type_0 = BoardResourceTagging.from_dict(data)

                return resource_tagging_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(BoardResourceTagging | None | Unset, data)

        resource_tagging = _parse_resource_tagging(d.pop("resourceTagging", UNSET))

        update_entry_response = cls(
            entry=entry,
            meta=meta,
            resource_tagging=resource_tagging,
        )

        update_entry_response.additional_properties = d
        return update_entry_response

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
