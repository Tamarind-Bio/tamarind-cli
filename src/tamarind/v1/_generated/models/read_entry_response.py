from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.board_entry import BoardEntry
    from ..models.board_note import BoardNote


T = TypeVar("T", bound="ReadEntryResponse")


@_attrs_define
class ReadEntryResponse:
    """
    Attributes:
        entry (BoardEntry | None):
        notes (list[BoardNote]):
    """

    entry: BoardEntry | None
    notes: list[BoardNote]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.board_entry import BoardEntry

        entry: dict[str, Any] | None
        if isinstance(self.entry, BoardEntry):
            entry = self.entry.to_dict()
        else:
            entry = self.entry

        notes = []
        for notes_item_data in self.notes:
            notes_item = notes_item_data.to_dict()
            notes.append(notes_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "entry": entry,
                "notes": notes,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.board_entry import BoardEntry
        from ..models.board_note import BoardNote

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

        notes = []
        _notes = d.pop("notes")
        for notes_item_data in _notes:
            notes_item = BoardNote.from_dict(notes_item_data)

            notes.append(notes_item)

        read_entry_response = cls(
            entry=entry,
            notes=notes,
        )

        read_entry_response.additional_properties = d
        return read_entry_response

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
