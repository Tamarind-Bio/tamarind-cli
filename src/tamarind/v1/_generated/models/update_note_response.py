from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.board_note import BoardNote


T = TypeVar("T", bound="UpdateNoteResponse")


@_attrs_define
class UpdateNoteResponse:
    """
    Attributes:
        note (BoardNote | None):
    """

    note: BoardNote | None
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.board_note import BoardNote

        note: dict[str, Any] | None
        if isinstance(self.note, BoardNote):
            note = self.note.to_dict()
        else:
            note = self.note

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "note": note,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.board_note import BoardNote

        d = dict(src_dict)

        def _parse_note(data: object) -> BoardNote | None:
            if data is None:
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                note_type_0 = BoardNote.from_dict(data)

                return note_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(BoardNote | None, data)

        note = _parse_note(d.pop("note"))

        update_note_response = cls(
            note=note,
        )

        update_note_response.additional_properties = d
        return update_note_response

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
