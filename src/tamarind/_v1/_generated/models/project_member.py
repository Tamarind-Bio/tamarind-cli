from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

T = TypeVar("T", bound="ProjectMember")


@_attrs_define
class ProjectMember:
    """
    Attributes:
        email (str):
        invited_at (datetime.datetime | None): Null on older memberships.
        invited_by (None | str): Who shared the project with this person. Null on older memberships.
    """

    email: str
    invited_at: datetime.datetime | None
    invited_by: None | str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        email = self.email

        invited_at: None | str
        if isinstance(self.invited_at, datetime.datetime):
            invited_at = self.invited_at.isoformat()
        else:
            invited_at = self.invited_at

        invited_by: None | str
        invited_by = self.invited_by

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "email": email,
                "invitedAt": invited_at,
                "invitedBy": invited_by,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        email = d.pop("email")

        def _parse_invited_at(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                invited_at_type_0 = isoparse(data)

                return invited_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        invited_at = _parse_invited_at(d.pop("invitedAt"))

        def _parse_invited_by(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        invited_by = _parse_invited_by(d.pop("invitedBy"))

        project_member = cls(
            email=email,
            invited_at=invited_at,
            invited_by=invited_by,
        )

        project_member.additional_properties = d
        return project_member

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
