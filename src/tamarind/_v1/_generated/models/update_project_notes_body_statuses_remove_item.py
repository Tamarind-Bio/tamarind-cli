from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateProjectNotesBodyStatusesRemoveItem")


@_attrs_define
class UpdateProjectNotesBodyStatusesRemoveItem:
    """
    Attributes:
        id (str): One of the ids in `meta.statuses`.
        reassign_to (str | Unset): Where the entries holding this status move to. One of the other ids in
            `meta.statuses`, and required when any entry holds the one being removed.
    """

    id: str
    reassign_to: str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        reassign_to = self.reassign_to

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "id": id,
            }
        )
        if reassign_to is not UNSET:
            field_dict["reassignTo"] = reassign_to

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        reassign_to = d.pop("reassignTo", UNSET)

        update_project_notes_body_statuses_remove_item = cls(
            id=id,
            reassign_to=reassign_to,
        )

        return update_project_notes_body_statuses_remove_item
