from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.update_project_notes_body_lanes_create_item import (
        UpdateProjectNotesBodyLanesCreateItem,
    )
    from ..models.update_project_notes_body_lanes_delete_item import (
        UpdateProjectNotesBodyLanesDeleteItem,
    )
    from ..models.update_project_notes_body_lanes_update_item import (
        UpdateProjectNotesBodyLanesUpdateItem,
    )


T = TypeVar("T", bound="UpdateProjectNotesBodyLanes")


@_attrs_define
class UpdateProjectNotesBodyLanes:
    """A create appends to `laneOrder`; a delete removes the lane from it. The response carries the whole ordered lane set
    back.

        Example:
            {'create': [{'name': 'Assays'}], 'delete': [{'laneId': 'lane-3', 'version': 1}], 'update': [{'laneId': 'lane-2',
                'name': 'Running', 'statusId': 'in-progress', 'version': 1}]}

        Attributes:
            create (list[UpdateProjectNotesBodyLanesCreateItem] | Unset): New lanes, appended to `laneOrder` in the order
                given.
            delete (list[UpdateProjectNotesBodyLanesDeleteItem] | Unset): Lanes to remove. Only a lane holding no entries
                can go, and a project always keeps at least one lane. To take a lane off the board but keep it and its entries,
                hide it instead.
            update (list[UpdateProjectNotesBodyLanesUpdateItem] | Unset): Edits to existing lanes.
    """

    create: list[UpdateProjectNotesBodyLanesCreateItem] | Unset = UNSET
    delete: list[UpdateProjectNotesBodyLanesDeleteItem] | Unset = UNSET
    update: list[UpdateProjectNotesBodyLanesUpdateItem] | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        create: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.create, Unset):
            create = []
            for create_item_data in self.create:
                create_item = create_item_data.to_dict()
                create.append(create_item)

        delete: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.delete, Unset):
            delete = []
            for delete_item_data in self.delete:
                delete_item = delete_item_data.to_dict()
                delete.append(delete_item)

        update: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.update, Unset):
            update = []
            for update_item_data in self.update:
                update_item = update_item_data.to_dict()
                update.append(update_item)

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if create is not UNSET:
            field_dict["create"] = create
        if delete is not UNSET:
            field_dict["delete"] = delete
        if update is not UNSET:
            field_dict["update"] = update

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.update_project_notes_body_lanes_create_item import (
            UpdateProjectNotesBodyLanesCreateItem,
        )
        from ..models.update_project_notes_body_lanes_delete_item import (
            UpdateProjectNotesBodyLanesDeleteItem,
        )
        from ..models.update_project_notes_body_lanes_update_item import (
            UpdateProjectNotesBodyLanesUpdateItem,
        )

        d = dict(src_dict)
        _create = d.pop("create", UNSET)
        create: list[UpdateProjectNotesBodyLanesCreateItem] | Unset = UNSET
        if _create is not UNSET:
            create = []
            for create_item_data in _create:
                create_item = UpdateProjectNotesBodyLanesCreateItem.from_dict(create_item_data)

                create.append(create_item)

        _delete = d.pop("delete", UNSET)
        delete: list[UpdateProjectNotesBodyLanesDeleteItem] | Unset = UNSET
        if _delete is not UNSET:
            delete = []
            for delete_item_data in _delete:
                delete_item = UpdateProjectNotesBodyLanesDeleteItem.from_dict(delete_item_data)

                delete.append(delete_item)

        _update = d.pop("update", UNSET)
        update: list[UpdateProjectNotesBodyLanesUpdateItem] | Unset = UNSET
        if _update is not UNSET:
            update = []
            for update_item_data in _update:
                update_item = UpdateProjectNotesBodyLanesUpdateItem.from_dict(update_item_data)

                update.append(update_item)

        update_project_notes_body_lanes = cls(
            create=create,
            delete=delete,
            update=update,
        )

        return update_project_notes_body_lanes
