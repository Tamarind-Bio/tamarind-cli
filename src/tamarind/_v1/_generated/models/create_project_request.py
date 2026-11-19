from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..models.create_project_request_scope import CreateProjectRequestScope
from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateProjectRequest")


@_attrs_define
class CreateProjectRequest:
    """
    Attributes:
        name (str): Letters, digits, spaces and `- _ . , ( ) &`, at most 100 characters once trimmed. Stored trimmed.
        color (str | Unset):
        description (None | str | Unset): At most 2,000 characters once trimmed (an emoji counts as two). Null or empty
            leaves it out.
        scope (CreateProjectRequestScope | Unset): `org` files it in your organization. `personal` keeps it private to
            you until you add members. With no organization, every project is personal. Default:
            CreateProjectRequestScope.ORG.
    """

    name: str
    color: str | Unset = UNSET
    description: None | str | Unset = UNSET
    scope: CreateProjectRequestScope | Unset = CreateProjectRequestScope.ORG

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        color = self.color

        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        scope: str | Unset = UNSET
        if not isinstance(self.scope, Unset):
            scope = self.scope.value

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "name": name,
            }
        )
        if color is not UNSET:
            field_dict["color"] = color
        if description is not UNSET:
            field_dict["description"] = description
        if scope is not UNSET:
            field_dict["scope"] = scope

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        color = d.pop("color", UNSET)

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        _scope = d.pop("scope", UNSET)
        scope: CreateProjectRequestScope | Unset
        if isinstance(_scope, Unset):
            scope = UNSET
        else:
            scope = CreateProjectRequestScope(_scope)

        create_project_request = cls(
            name=name,
            color=color,
            description=description,
            scope=scope,
        )

        return create_project_request
