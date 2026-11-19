from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

T = TypeVar("T", bound="UpdateProjectNotesBodyLanesDeleteItem")


@_attrs_define
class UpdateProjectNotesBodyLanesDeleteItem:
    """
    Attributes:
        lane_id (str): The lane's `id`, from `lanes` on `GET /projects/{projectId}/notes`.
        version (int): The lane's own `version`, from `lanes` on a read — not the project's.
    """

    lane_id: str
    version: int

    def to_dict(self) -> dict[str, Any]:
        lane_id = self.lane_id

        version = self.version

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "laneId": lane_id,
                "version": version,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        lane_id = d.pop("laneId")

        version = d.pop("version")

        update_project_notes_body_lanes_delete_item = cls(
            lane_id=lane_id,
            version=version,
        )

        return update_project_notes_body_lanes_delete_item
