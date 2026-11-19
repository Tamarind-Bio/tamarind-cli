from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.board_entry import BoardEntry
    from ..models.board_lane import BoardLane
    from ..models.board_meta import BoardMeta


T = TypeVar("T", bound="ReadNotesResponse")


@_attrs_define
class ReadNotesResponse:
    """
    Attributes:
        entries (list[BoardEntry]):
        lanes (list[BoardLane]):
        meta (BoardMeta | None):
    """

    entries: list[BoardEntry]
    lanes: list[BoardLane]
    meta: BoardMeta | None
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.board_meta import BoardMeta

        entries = []
        for entries_item_data in self.entries:
            entries_item = entries_item_data.to_dict()
            entries.append(entries_item)

        lanes = []
        for lanes_item_data in self.lanes:
            lanes_item = lanes_item_data.to_dict()
            lanes.append(lanes_item)

        meta: dict[str, Any] | None
        if isinstance(self.meta, BoardMeta):
            meta = self.meta.to_dict()
        else:
            meta = self.meta

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "entries": entries,
                "lanes": lanes,
                "meta": meta,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.board_entry import BoardEntry
        from ..models.board_lane import BoardLane
        from ..models.board_meta import BoardMeta

        d = dict(src_dict)
        entries = []
        _entries = d.pop("entries")
        for entries_item_data in _entries:
            entries_item = BoardEntry.from_dict(entries_item_data)

            entries.append(entries_item)

        lanes = []
        _lanes = d.pop("lanes")
        for lanes_item_data in _lanes:
            lanes_item = BoardLane.from_dict(lanes_item_data)

            lanes.append(lanes_item)

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

        read_notes_response = cls(
            entries=entries,
            lanes=lanes,
            meta=meta,
        )

        read_notes_response.additional_properties = d
        return read_notes_response

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
