from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.me_organization_type_0_role import MeOrganizationType0Role

T = TypeVar("T", bound="MeOrganizationType0")


@_attrs_define
class MeOrganizationType0:
    """Null for a personal account.

    Attributes:
        name (str): The organization's slug for now.
        role (MeOrganizationType0Role): EFFECTIVE role for THIS credential, which may be lower than the person's role in
            the app. A service account's key is `admin`; any other API key is `member`, an organization admin's own key
            included. That key acts as admin on `/service-accounts` and `GET /api-keys?scope=org`, and in reading and
            canceling members' jobs as far as today's API lets an admin's key (decision 74), and, once built, in refiling
            them.
        slug (str):
    """

    name: str
    role: MeOrganizationType0Role
    slug: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        role = self.role.value

        slug = self.slug

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "role": role,
                "slug": slug,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        role = MeOrganizationType0Role(d.pop("role"))

        slug = d.pop("slug")

        me_organization_type_0 = cls(
            name=name,
            role=role,
            slug=slug,
        )

        me_organization_type_0.additional_properties = d
        return me_organization_type_0

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
