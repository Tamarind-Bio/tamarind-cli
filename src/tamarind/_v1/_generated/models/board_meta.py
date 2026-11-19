from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

if TYPE_CHECKING:
    from ..models.board_meta_countsbystatus import BoardMetaCountsbystatus
    from ..models.board_status import BoardStatus


T = TypeVar("T", bound="BoardMeta")


@_attrs_define
class BoardMeta:
    """The project's own details: its statuses, its lane order, its dates and its counts.

    `countsByStatus` is keyed by status id, so it gains and loses keys as the statuses do.

        Attributes:
            counts_by_status (BoardMetaCountsbystatus):
            created_at (datetime.datetime | None):
            due_date (None | str):
            entry_count (float | int):
            lane_order (list[str]):
            owner (None | str):
            project_id (None | str):
            projected_end_date (None | str):
            start_date (None | str):
            statuses (list[BoardStatus]):
            tags (list[str]):
            untracked_count (float | int):
            updated_at (datetime.datetime | None):
            version (float | int):
    """

    counts_by_status: BoardMetaCountsbystatus
    created_at: datetime.datetime | None
    due_date: None | str
    entry_count: float | int
    lane_order: list[str]
    owner: None | str
    project_id: None | str
    projected_end_date: None | str
    start_date: None | str
    statuses: list[BoardStatus]
    tags: list[str]
    untracked_count: float | int
    updated_at: datetime.datetime | None
    version: float | int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        counts_by_status = self.counts_by_status.to_dict()

        created_at: None | str
        if isinstance(self.created_at, datetime.datetime):
            created_at = self.created_at.isoformat()
        else:
            created_at = self.created_at

        due_date: None | str
        due_date = self.due_date

        entry_count: float | int
        entry_count = self.entry_count

        lane_order = self.lane_order

        owner: None | str
        owner = self.owner

        project_id: None | str
        project_id = self.project_id

        projected_end_date: None | str
        projected_end_date = self.projected_end_date

        start_date: None | str
        start_date = self.start_date

        statuses = []
        for statuses_item_data in self.statuses:
            statuses_item = statuses_item_data.to_dict()
            statuses.append(statuses_item)

        tags = self.tags

        untracked_count: float | int
        untracked_count = self.untracked_count

        updated_at: None | str
        if isinstance(self.updated_at, datetime.datetime):
            updated_at = self.updated_at.isoformat()
        else:
            updated_at = self.updated_at

        version: float | int
        version = self.version

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "countsByStatus": counts_by_status,
                "createdAt": created_at,
                "dueDate": due_date,
                "entryCount": entry_count,
                "laneOrder": lane_order,
                "owner": owner,
                "projectId": project_id,
                "projectedEndDate": projected_end_date,
                "startDate": start_date,
                "statuses": statuses,
                "tags": tags,
                "untrackedCount": untracked_count,
                "updatedAt": updated_at,
                "version": version,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.board_meta_countsbystatus import BoardMetaCountsbystatus
        from ..models.board_status import BoardStatus

        d = dict(src_dict)
        counts_by_status = BoardMetaCountsbystatus.from_dict(d.pop("countsByStatus"))

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

        def _parse_due_date(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        due_date = _parse_due_date(d.pop("dueDate"))

        def _parse_entry_count(data: object) -> float | int:
            return cast(float | int, data)

        entry_count = _parse_entry_count(d.pop("entryCount"))

        lane_order = cast(list[str], d.pop("laneOrder"))

        def _parse_owner(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        owner = _parse_owner(d.pop("owner"))

        def _parse_project_id(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        project_id = _parse_project_id(d.pop("projectId"))

        def _parse_projected_end_date(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        projected_end_date = _parse_projected_end_date(d.pop("projectedEndDate"))

        def _parse_start_date(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        start_date = _parse_start_date(d.pop("startDate"))

        statuses = []
        _statuses = d.pop("statuses")
        for statuses_item_data in _statuses:
            statuses_item = BoardStatus.from_dict(statuses_item_data)

            statuses.append(statuses_item)

        tags = cast(list[str], d.pop("tags"))

        def _parse_untracked_count(data: object) -> float | int:
            return cast(float | int, data)

        untracked_count = _parse_untracked_count(d.pop("untrackedCount"))

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

        board_meta = cls(
            counts_by_status=counts_by_status,
            created_at=created_at,
            due_date=due_date,
            entry_count=entry_count,
            lane_order=lane_order,
            owner=owner,
            project_id=project_id,
            projected_end_date=projected_end_date,
            start_date=start_date,
            statuses=statuses,
            tags=tags,
            untracked_count=untracked_count,
            updated_at=updated_at,
            version=version,
        )

        board_meta.additional_properties = d
        return board_meta

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
