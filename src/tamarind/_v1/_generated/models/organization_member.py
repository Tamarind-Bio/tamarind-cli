from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.organization_member_role import OrganizationMemberRole

T = TypeVar("T", bound="OrganizationMember")


@_attrs_define
class OrganizationMember:
    """
    Attributes:
        email (str):
        name (None | str): The name the sign-in provider holds. Null when it has no membership for this person.
        role (OrganizationMemberRole): The person's role in the app, from the sign-in provider. Not what their API key
            may do (see `GET /me`).
        teams (list[str]): The names of your organization's teams that list this member.
    """

    email: str
    name: None | str
    role: OrganizationMemberRole
    teams: list[str]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        email = self.email

        name: None | str
        name = self.name

        role = self.role.value

        teams = self.teams

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "email": email,
                "name": name,
                "role": role,
                "teams": teams,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        email = d.pop("email")

        def _parse_name(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        name = _parse_name(d.pop("name"))

        role = OrganizationMemberRole(d.pop("role"))

        teams = cast(list[str], d.pop("teams"))

        organization_member = cls(
            email=email,
            name=name,
            role=role,
            teams=teams,
        )

        organization_member.additional_properties = d
        return organization_member

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
