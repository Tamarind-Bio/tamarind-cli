from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.board_reference import BoardReference


T = TypeVar("T", bound="BoardEntry")


@_attrs_define
class BoardEntry:
    """One step of a campaign: what it is, who owns it, where it stands, and what it tracks.

    Attributes:
        created_at (datetime.datetime | None):
        created_by (None | str):
        created_by_actor_type (str):
        deadline (None | str):
        depends_on (list[str]):
        estimated_effort_days (float | int | None):
        id (str):
        lane_id (None | str):
        links (list[BoardReference]):
        note_count (float | int):
        overview (None | str):
        owners (list[str]):
        position (float | int):
        status_id (None | str):
        title (None | str):
        updated_at (datetime.datetime | None):
        version (float | int):
        template_id (None | str | Unset):
        template_version (float | int | None | Unset):
    """

    created_at: datetime.datetime | None
    created_by: None | str
    created_by_actor_type: str
    deadline: None | str
    depends_on: list[str]
    estimated_effort_days: float | int | None
    id: str
    lane_id: None | str
    links: list[BoardReference]
    note_count: float | int
    overview: None | str
    owners: list[str]
    position: float | int
    status_id: None | str
    title: None | str
    updated_at: datetime.datetime | None
    version: float | int
    template_id: None | str | Unset = UNSET
    template_version: float | int | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        created_at: None | str
        if isinstance(self.created_at, datetime.datetime):
            created_at = self.created_at.isoformat()
        else:
            created_at = self.created_at

        created_by: None | str
        created_by = self.created_by

        created_by_actor_type = self.created_by_actor_type

        deadline: None | str
        deadline = self.deadline

        depends_on = self.depends_on

        estimated_effort_days: float | int | None
        estimated_effort_days = self.estimated_effort_days

        id = self.id

        lane_id: None | str
        lane_id = self.lane_id

        links = []
        for links_item_data in self.links:
            links_item = links_item_data.to_dict()
            links.append(links_item)

        note_count: float | int
        note_count = self.note_count

        overview: None | str
        overview = self.overview

        owners = self.owners

        position: float | int
        position = self.position

        status_id: None | str
        status_id = self.status_id

        title: None | str
        title = self.title

        updated_at: None | str
        if isinstance(self.updated_at, datetime.datetime):
            updated_at = self.updated_at.isoformat()
        else:
            updated_at = self.updated_at

        version: float | int
        version = self.version

        template_id: None | str | Unset
        if isinstance(self.template_id, Unset):
            template_id = UNSET
        else:
            template_id = self.template_id

        template_version: float | int | None | Unset
        if isinstance(self.template_version, Unset):
            template_version = UNSET
        else:
            template_version = self.template_version

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "createdAt": created_at,
                "createdBy": created_by,
                "createdByActorType": created_by_actor_type,
                "deadline": deadline,
                "dependsOn": depends_on,
                "estimatedEffortDays": estimated_effort_days,
                "id": id,
                "laneId": lane_id,
                "links": links,
                "noteCount": note_count,
                "overview": overview,
                "owners": owners,
                "position": position,
                "statusId": status_id,
                "title": title,
                "updatedAt": updated_at,
                "version": version,
            }
        )
        if template_id is not UNSET:
            field_dict["templateId"] = template_id
        if template_version is not UNSET:
            field_dict["templateVersion"] = template_version

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.board_reference import BoardReference

        d = dict(src_dict)

        def _parse_created_at(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                created_at_type_0 = isoparse(data)

                return created_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        created_at = _parse_created_at(d.pop("createdAt"))

        def _parse_created_by(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        created_by = _parse_created_by(d.pop("createdBy"))

        created_by_actor_type = d.pop("createdByActorType")

        def _parse_deadline(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        deadline = _parse_deadline(d.pop("deadline"))

        depends_on = cast(list[str], d.pop("dependsOn"))

        def _parse_estimated_effort_days(data: object) -> float | int | None:
            if data is None:
                return data
            return cast(float | int | None, data)

        estimated_effort_days = _parse_estimated_effort_days(d.pop("estimatedEffortDays"))

        id = d.pop("id")

        def _parse_lane_id(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        lane_id = _parse_lane_id(d.pop("laneId"))

        links = []
        _links = d.pop("links")
        for links_item_data in _links:
            links_item = BoardReference.from_dict(links_item_data)

            links.append(links_item)

        def _parse_note_count(data: object) -> float | int:
            return cast(float | int, data)

        note_count = _parse_note_count(d.pop("noteCount"))

        def _parse_overview(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        overview = _parse_overview(d.pop("overview"))

        owners = cast(list[str], d.pop("owners"))

        def _parse_position(data: object) -> float | int:
            return cast(float | int, data)

        position = _parse_position(d.pop("position"))

        def _parse_status_id(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        status_id = _parse_status_id(d.pop("statusId"))

        def _parse_title(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        title = _parse_title(d.pop("title"))

        def _parse_updated_at(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                updated_at_type_0 = isoparse(data)

                return updated_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        updated_at = _parse_updated_at(d.pop("updatedAt"))

        def _parse_version(data: object) -> float | int:
            return cast(float | int, data)

        version = _parse_version(d.pop("version"))

        def _parse_template_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        template_id = _parse_template_id(d.pop("templateId", UNSET))

        def _parse_template_version(data: object) -> float | int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | int | None | Unset, data)

        template_version = _parse_template_version(d.pop("templateVersion", UNSET))

        board_entry = cls(
            created_at=created_at,
            created_by=created_by,
            created_by_actor_type=created_by_actor_type,
            deadline=deadline,
            depends_on=depends_on,
            estimated_effort_days=estimated_effort_days,
            id=id,
            lane_id=lane_id,
            links=links,
            note_count=note_count,
            overview=overview,
            owners=owners,
            position=position,
            status_id=status_id,
            title=title,
            updated_at=updated_at,
            version=version,
            template_id=template_id,
            template_version=template_version,
        )

        board_entry.additional_properties = d
        return board_entry

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
