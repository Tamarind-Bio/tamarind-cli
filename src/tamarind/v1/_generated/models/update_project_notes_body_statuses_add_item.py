from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..models.update_project_notes_body_statuses_add_item_tone import (
    UpdateProjectNotesBodyStatusesAddItemTone,
)
from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateProjectNotesBodyStatusesAddItem")


@_attrs_define
class UpdateProjectNotesBodyStatusesAddItem:
    """
    Attributes:
        label (str): What the status is called, e.g. `On hold`.
        is_terminal (bool | Unset): True for a status that means the work is finished. The project's completion is
            counted from it.
        tone (UpdateProjectNotesBodyStatusesAddItemTone | Unset): The colour shown beside the label. Defaults to
            `custom`.
    """

    label: str
    is_terminal: bool | Unset = UNSET
    tone: UpdateProjectNotesBodyStatusesAddItemTone | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        label = self.label

        is_terminal = self.is_terminal

        tone: str | Unset = UNSET
        if not isinstance(self.tone, Unset):
            tone = self.tone.value

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "label": label,
            }
        )
        if is_terminal is not UNSET:
            field_dict["isTerminal"] = is_terminal
        if tone is not UNSET:
            field_dict["tone"] = tone

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        label = d.pop("label")

        is_terminal = d.pop("isTerminal", UNSET)

        _tone = d.pop("tone", UNSET)
        tone: UpdateProjectNotesBodyStatusesAddItemTone | Unset
        if isinstance(_tone, Unset):
            tone = UNSET
        else:
            tone = UpdateProjectNotesBodyStatusesAddItemTone(_tone)

        update_project_notes_body_statuses_add_item = cls(
            label=label,
            is_terminal=is_terminal,
            tone=tone,
        )

        return update_project_notes_body_statuses_add_item
