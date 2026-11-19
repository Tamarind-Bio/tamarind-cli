from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.update_project_notes_body_lanes import UpdateProjectNotesBodyLanes
    from ..models.update_project_notes_body_statuses import UpdateProjectNotesBodyStatuses


T = TypeVar("T", bound="UpdateProjectNotesBody")


@_attrs_define
class UpdateProjectNotesBody:
    """
    Attributes:
        version (int): The `meta.version` you read.
        due_date (datetime.date | None | Unset): `YYYY-MM-DD` format.
        lane_order (list[str] | Unset): An array of lane ids, ordered in the way you want them to appear. The ids are in
            `lanes` on `GET /projects/{projectId}/notes`.
        lanes (UpdateProjectNotesBodyLanes | Unset): A create appends to `laneOrder`; a delete removes the lane from it.
            The response carries the whole ordered lane set back. Example: {'create': [{'name': 'Assays'}], 'delete':
            [{'laneId': 'lane-3', 'version': 1}], 'update': [{'laneId': 'lane-2', 'name': 'Running', 'statusId': 'in-
            progress', 'version': 1}]}.
        owner (None | str | Unset): Email address of an individual within the organization.
        start_date (datetime.date | None | Unset): `YYYY-MM-DD` format.
        statuses (UpdateProjectNotesBodyStatuses | Unset): Status operations. Add, rename or remove the project's
            statuses. Example: {'add': [{'isTerminal': False, 'label': 'On hold', 'tone': 'yellow'}], 'remove': [{'id': 'on-
            hold', 'reassignTo': 'not-started'}], 'rename': [{'id': 'blocked', 'label': 'Waiting on data'}]}.
        tags (list[str] | Unset): Free-text labels on the project. The whole set, replacing the ones already there.
    """

    version: int
    due_date: datetime.date | None | Unset = UNSET
    lane_order: list[str] | Unset = UNSET
    lanes: UpdateProjectNotesBodyLanes | Unset = UNSET
    owner: None | str | Unset = UNSET
    start_date: datetime.date | None | Unset = UNSET
    statuses: UpdateProjectNotesBodyStatuses | Unset = UNSET
    tags: list[str] | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        version = self.version

        due_date: None | str | Unset
        if isinstance(self.due_date, Unset):
            due_date = UNSET
        elif isinstance(self.due_date, datetime.date):
            due_date = self.due_date.isoformat()
        else:
            due_date = self.due_date

        lane_order: list[str] | Unset = UNSET
        if not isinstance(self.lane_order, Unset):
            lane_order = self.lane_order

        lanes: dict[str, Any] | Unset = UNSET
        if not isinstance(self.lanes, Unset):
            lanes = self.lanes.to_dict()

        owner: None | str | Unset
        if isinstance(self.owner, Unset):
            owner = UNSET
        else:
            owner = self.owner

        start_date: None | str | Unset
        if isinstance(self.start_date, Unset):
            start_date = UNSET
        elif isinstance(self.start_date, datetime.date):
            start_date = self.start_date.isoformat()
        else:
            start_date = self.start_date

        statuses: dict[str, Any] | Unset = UNSET
        if not isinstance(self.statuses, Unset):
            statuses = self.statuses.to_dict()

        tags: list[str] | Unset = UNSET
        if not isinstance(self.tags, Unset):
            tags = self.tags

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "version": version,
            }
        )
        if due_date is not UNSET:
            field_dict["dueDate"] = due_date
        if lane_order is not UNSET:
            field_dict["laneOrder"] = lane_order
        if lanes is not UNSET:
            field_dict["lanes"] = lanes
        if owner is not UNSET:
            field_dict["owner"] = owner
        if start_date is not UNSET:
            field_dict["startDate"] = start_date
        if statuses is not UNSET:
            field_dict["statuses"] = statuses
        if tags is not UNSET:
            field_dict["tags"] = tags

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.update_project_notes_body_lanes import UpdateProjectNotesBodyLanes
        from ..models.update_project_notes_body_statuses import UpdateProjectNotesBodyStatuses

        d = dict(src_dict)
        version = d.pop("version")

        def _parse_due_date(data: object) -> datetime.date | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                due_date_type_0 = isoparse(data).date()

                return due_date_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.date | None | Unset, data)

        due_date = _parse_due_date(d.pop("dueDate", UNSET))

        lane_order = cast(list[str], d.pop("laneOrder", UNSET))

        _lanes = d.pop("lanes", UNSET)
        lanes: UpdateProjectNotesBodyLanes | Unset
        if isinstance(_lanes, Unset):
            lanes = UNSET
        else:
            lanes = UpdateProjectNotesBodyLanes.from_dict(_lanes)

        def _parse_owner(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        owner = _parse_owner(d.pop("owner", UNSET))

        def _parse_start_date(data: object) -> datetime.date | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                start_date_type_0 = isoparse(data).date()

                return start_date_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.date | None | Unset, data)

        start_date = _parse_start_date(d.pop("startDate", UNSET))

        _statuses = d.pop("statuses", UNSET)
        statuses: UpdateProjectNotesBodyStatuses | Unset
        if isinstance(_statuses, Unset):
            statuses = UNSET
        else:
            statuses = UpdateProjectNotesBodyStatuses.from_dict(_statuses)

        tags = cast(list[str], d.pop("tags", UNSET))

        update_project_notes_body = cls(
            version=version,
            due_date=due_date,
            lane_order=lane_order,
            lanes=lanes,
            owner=owner,
            start_date=start_date,
            statuses=statuses,
            tags=tags,
        )

        return update_project_notes_body
