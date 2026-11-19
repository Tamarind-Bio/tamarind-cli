from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.update_project_notes_body_statuses_add_item import (
        UpdateProjectNotesBodyStatusesAddItem,
    )
    from ..models.update_project_notes_body_statuses_remove_item import (
        UpdateProjectNotesBodyStatusesRemoveItem,
    )
    from ..models.update_project_notes_body_statuses_rename_item import (
        UpdateProjectNotesBodyStatusesRenameItem,
    )


T = TypeVar("T", bound="UpdateProjectNotesBodyStatuses")


@_attrs_define
class UpdateProjectNotesBodyStatuses:
    """Status operations. Add, rename or remove the project's statuses.

    Example:
        {'add': [{'isTerminal': False, 'label': 'On hold', 'tone': 'yellow'}], 'remove': [{'id': 'on-hold',
            'reassignTo': 'not-started'}], 'rename': [{'id': 'blocked', 'label': 'Waiting on data'}]}

    Attributes:
        add (list[UpdateProjectNotesBodyStatusesAddItem] | Unset): New statuses. The id is made from the label, so an
            `id` sent here is 422 `unknown_field`.
        remove (list[UpdateProjectNotesBodyStatusesRemoveItem] | Unset): Remove a status. The four a project starts with
            cannot be removed.
        rename (list[UpdateProjectNotesBodyStatusesRenameItem] | Unset): Rename a status. Its id does not change, so no
            entry moves.
    """

    add: list[UpdateProjectNotesBodyStatusesAddItem] | Unset = UNSET
    remove: list[UpdateProjectNotesBodyStatusesRemoveItem] | Unset = UNSET
    rename: list[UpdateProjectNotesBodyStatusesRenameItem] | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        add: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.add, Unset):
            add = []
            for add_item_data in self.add:
                add_item = add_item_data.to_dict()
                add.append(add_item)

        remove: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.remove, Unset):
            remove = []
            for remove_item_data in self.remove:
                remove_item = remove_item_data.to_dict()
                remove.append(remove_item)

        rename: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.rename, Unset):
            rename = []
            for rename_item_data in self.rename:
                rename_item = rename_item_data.to_dict()
                rename.append(rename_item)

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if add is not UNSET:
            field_dict["add"] = add
        if remove is not UNSET:
            field_dict["remove"] = remove
        if rename is not UNSET:
            field_dict["rename"] = rename

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.update_project_notes_body_statuses_add_item import (
            UpdateProjectNotesBodyStatusesAddItem,
        )
        from ..models.update_project_notes_body_statuses_remove_item import (
            UpdateProjectNotesBodyStatusesRemoveItem,
        )
        from ..models.update_project_notes_body_statuses_rename_item import (
            UpdateProjectNotesBodyStatusesRenameItem,
        )

        d = dict(src_dict)
        _add = d.pop("add", UNSET)
        add: list[UpdateProjectNotesBodyStatusesAddItem] | Unset = UNSET
        if _add is not UNSET:
            add = []
            for add_item_data in _add:
                add_item = UpdateProjectNotesBodyStatusesAddItem.from_dict(add_item_data)

                add.append(add_item)

        _remove = d.pop("remove", UNSET)
        remove: list[UpdateProjectNotesBodyStatusesRemoveItem] | Unset = UNSET
        if _remove is not UNSET:
            remove = []
            for remove_item_data in _remove:
                remove_item = UpdateProjectNotesBodyStatusesRemoveItem.from_dict(remove_item_data)

                remove.append(remove_item)

        _rename = d.pop("rename", UNSET)
        rename: list[UpdateProjectNotesBodyStatusesRenameItem] | Unset = UNSET
        if _rename is not UNSET:
            rename = []
            for rename_item_data in _rename:
                rename_item = UpdateProjectNotesBodyStatusesRenameItem.from_dict(rename_item_data)

                rename.append(rename_item)

        update_project_notes_body_statuses = cls(
            add=add,
            remove=remove,
            rename=rename,
        )

        return update_project_notes_body_statuses
