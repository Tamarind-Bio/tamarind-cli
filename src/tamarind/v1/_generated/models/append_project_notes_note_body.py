from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

T = TypeVar("T", bound="AppendProjectNotesNoteBody")


@_attrs_define
class AppendProjectNotesNoteBody:
    """
    Attributes:
        body (str): The text contained within the entry.
    """

    body: str

    def to_dict(self) -> dict[str, Any]:
        body = self.body

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "body": body,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        body = d.pop("body")

        append_project_notes_note_body = cls(
            body=body,
        )

        return append_project_notes_note_body
