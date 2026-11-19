from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

T = TypeVar("T", bound="BoardLane")


@_attrs_define
class BoardLane:
    """
    Attributes:
        created_at (datetime.datetime | None):
        id (str):
        is_hidden (bool):
        name (None | str):
        status_id (None | str):
        updated_at (datetime.datetime | None):
        version (float | int):
    """

    created_at: datetime.datetime | None
    id: str
    is_hidden: bool
    name: None | str
    status_id: None | str
    updated_at: datetime.datetime | None
    version: float | int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        created_at: None | str
        if isinstance(self.created_at, datetime.datetime):
            created_at = self.created_at.isoformat()
        else:
            created_at = self.created_at

        id = self.id

        is_hidden = self.is_hidden

        name: None | str
        name = self.name

        status_id: None | str
        status_id = self.status_id

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
                "createdAt": created_at,
                "id": id,
                "isHidden": is_hidden,
                "name": name,
                "statusId": status_id,
                "updatedAt": updated_at,
                "version": version,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
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

        id = d.pop("id")

        is_hidden = d.pop("isHidden")

        def _parse_name(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        name = _parse_name(d.pop("name"))

        def _parse_status_id(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        status_id = _parse_status_id(d.pop("statusId"))

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

        board_lane = cls(
            created_at=created_at,
            id=id,
            is_hidden=is_hidden,
            name=name,
            status_id=status_id,
            updated_at=updated_at,
            version=version,
        )

        board_lane.additional_properties = d
        return board_lane

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
