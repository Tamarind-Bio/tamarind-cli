from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

T = TypeVar("T", bound="UpdateProjectNotesBodyStatusesRenameItem")


@_attrs_define
class UpdateProjectNotesBodyStatusesRenameItem:
    """
    Attributes:
        id (str): One of the ids in `meta.statuses`.
        label (str): The new name.
    """

    id: str
    label: str

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        label = self.label

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "id": id,
                "label": label,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        label = d.pop("label")

        update_project_notes_body_statuses_rename_item = cls(
            id=id,
            label=label,
        )

        return update_project_notes_body_statuses_rename_item
