from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.board_reference import BoardReference


T = TypeVar("T", bound="UpdateProjectNotesEntryBody")


@_attrs_define
class UpdateProjectNotesEntryBody:
    """
    Attributes:
        version (int): The `entry.version` you read.
        deadline (datetime.date | None | Unset): `YYYY-MM-DD` format.
        depends_on (list[str] | Unset): Other entries this one waits on, by `id`, from `GET
            /projects/{projectId}/notes`. A chain that loops back on itself is refused.
        estimated_effort_days (float | None | Unset):
        lane_id (str | Unset): The lane the entry belongs to. One of the lane ids from `GET
            /projects/{projectId}/notes`.
        links (list[BoardReference] | Unset): The whole set of resources this entry tracks, replacing the ones already
            on it.
        overview (None | str | Unset): The entry's body text. Markdown.
        owners (list[str] | Unset): An array of emails belonging to the project's organization.
        position (int | Unset): Order within the lane.
        status_id (None | str | Unset): One of the ids in `meta.statuses`. Defaults to `no-status`.
        title (str | Unset):
    """

    version: int
    deadline: datetime.date | None | Unset = UNSET
    depends_on: list[str] | Unset = UNSET
    estimated_effort_days: float | None | Unset = UNSET
    lane_id: str | Unset = UNSET
    links: list[BoardReference] | Unset = UNSET
    overview: None | str | Unset = UNSET
    owners: list[str] | Unset = UNSET
    position: int | Unset = UNSET
    status_id: None | str | Unset = UNSET
    title: str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        version = self.version

        deadline: None | str | Unset
        if isinstance(self.deadline, Unset):
            deadline = UNSET
        elif isinstance(self.deadline, datetime.date):
            deadline = self.deadline.isoformat()
        else:
            deadline = self.deadline

        depends_on: list[str] | Unset = UNSET
        if not isinstance(self.depends_on, Unset):
            depends_on = self.depends_on

        estimated_effort_days: float | None | Unset
        if isinstance(self.estimated_effort_days, Unset):
            estimated_effort_days = UNSET
        else:
            estimated_effort_days = self.estimated_effort_days

        lane_id = self.lane_id

        links: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.links, Unset):
            links = []
            for links_item_data in self.links:
                links_item = links_item_data.to_dict()
                links.append(links_item)

        overview: None | str | Unset
        if isinstance(self.overview, Unset):
            overview = UNSET
        else:
            overview = self.overview

        owners: list[str] | Unset = UNSET
        if not isinstance(self.owners, Unset):
            owners = self.owners

        position = self.position

        status_id: None | str | Unset
        if isinstance(self.status_id, Unset):
            status_id = UNSET
        else:
            status_id = self.status_id

        title = self.title

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "version": version,
            }
        )
        if deadline is not UNSET:
            field_dict["deadline"] = deadline
        if depends_on is not UNSET:
            field_dict["dependsOn"] = depends_on
        if estimated_effort_days is not UNSET:
            field_dict["estimatedEffortDays"] = estimated_effort_days
        if lane_id is not UNSET:
            field_dict["laneId"] = lane_id
        if links is not UNSET:
            field_dict["links"] = links
        if overview is not UNSET:
            field_dict["overview"] = overview
        if owners is not UNSET:
            field_dict["owners"] = owners
        if position is not UNSET:
            field_dict["position"] = position
        if status_id is not UNSET:
            field_dict["statusId"] = status_id
        if title is not UNSET:
            field_dict["title"] = title

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.board_reference import BoardReference

        d = dict(src_dict)
        version = d.pop("version")

        def _parse_deadline(data: object) -> datetime.date | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                deadline_type_0 = isoparse(data).date()

                return deadline_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.date | None | Unset, data)

        deadline = _parse_deadline(d.pop("deadline", UNSET))

        depends_on = cast(list[str], d.pop("dependsOn", UNSET))

        def _parse_estimated_effort_days(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        estimated_effort_days = _parse_estimated_effort_days(d.pop("estimatedEffortDays", UNSET))

        lane_id = d.pop("laneId", UNSET)

        _links = d.pop("links", UNSET)
        links: list[BoardReference] | Unset = UNSET
        if _links is not UNSET:
            links = []
            for links_item_data in _links:
                links_item = BoardReference.from_dict(links_item_data)

                links.append(links_item)

        def _parse_overview(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        overview = _parse_overview(d.pop("overview", UNSET))

        owners = cast(list[str], d.pop("owners", UNSET))

        position = d.pop("position", UNSET)

        def _parse_status_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        status_id = _parse_status_id(d.pop("statusId", UNSET))

        title = d.pop("title", UNSET)

        update_project_notes_entry_body = cls(
            version=version,
            deadline=deadline,
            depends_on=depends_on,
            estimated_effort_days=estimated_effort_days,
            lane_id=lane_id,
            links=links,
            overview=overview,
            owners=owners,
            position=position,
            status_id=status_id,
            title=title,
        )

        return update_project_notes_entry_body
