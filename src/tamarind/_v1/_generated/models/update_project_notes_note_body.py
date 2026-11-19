from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

T = TypeVar("T", bound="UpdateProjectNotesNoteBody")


@_attrs_define
class UpdateProjectNotesNoteBody:
    """
    Attributes:
        body (str): Updated text for the entry.
        version (int): The `note.version` you read.
    """

    body: str
    version: int

    def to_dict(self) -> dict[str, Any]:
        body = self.body

        version = self.version

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "body": body,
                "version": version,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        body = d.pop("body")

        version = d.pop("version")

        update_project_notes_note_body = cls(
            body=body,
            version=version,
        )

        return update_project_notes_note_body
