from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateProjectNotesBodyLanesUpdateItem")


@_attrs_define
class UpdateProjectNotesBodyLanesUpdateItem:
    """
    Attributes:
        lane_id (str): The lane's `id`, from `lanes` on `GET /projects/{projectId}/notes`.
        version (int): The lane's own `version`, from `lanes` on a read — not the project's.
        is_hidden (bool | Unset): Hide the lane from the board without deleting it or its entries.
        name (str | Unset): A new name for the lane.
        status_id (None | str | Unset): Tie the lane to a status, so moving an entry into it changes that entry's
            status. One of the ids in `meta.statuses`.
    """

    lane_id: str
    version: int
    is_hidden: bool | Unset = UNSET
    name: str | Unset = UNSET
    status_id: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        lane_id = self.lane_id

        version = self.version

        is_hidden = self.is_hidden

        name = self.name

        status_id: None | str | Unset
        if isinstance(self.status_id, Unset):
            status_id = UNSET
        else:
            status_id = self.status_id

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "laneId": lane_id,
                "version": version,
            }
        )
        if is_hidden is not UNSET:
            field_dict["isHidden"] = is_hidden
        if name is not UNSET:
            field_dict["name"] = name
        if status_id is not UNSET:
            field_dict["statusId"] = status_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        lane_id = d.pop("laneId")

        version = d.pop("version")

        is_hidden = d.pop("isHidden", UNSET)

        name = d.pop("name", UNSET)

        def _parse_status_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        status_id = _parse_status_id(d.pop("statusId", UNSET))

        update_project_notes_body_lanes_update_item = cls(
            lane_id=lane_id,
            version=version,
            is_hidden=is_hidden,
            name=name,
            status_id=status_id,
        )

        return update_project_notes_body_lanes_update_item
