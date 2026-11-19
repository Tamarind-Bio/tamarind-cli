from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateProjectRequest")


@_attrs_define
class UpdateProjectRequest:
    """
    Attributes:
        add_members (list[str] | Unset): People to share a `personal` project with. Ignored on an `org` project, which
            is open to the whole organization. An entry that isn't an email address is skipped.
        color (str | Unset):
        description (None | str | Unset): At most 2,000 characters once trimmed (an emoji counts as two). Null or empty
            clears it.
        is_archived (bool | Unset): Archive or restore it. `listProjects` leaves out archived projects, so keep the `id`
            to restore one.
        name (str | Unset): Letters, digits, spaces and `- _ . , ( ) &`, at most 100 characters once trimmed. Stored
            trimmed.
        remove_members (list[str] | Unset): People to stop sharing a `personal` project with. Ignored on an `org`
            project.
    """

    add_members: list[str] | Unset = UNSET
    color: str | Unset = UNSET
    description: None | str | Unset = UNSET
    is_archived: bool | Unset = UNSET
    name: str | Unset = UNSET
    remove_members: list[str] | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        add_members: list[str] | Unset = UNSET
        if not isinstance(self.add_members, Unset):
            add_members = self.add_members

        color = self.color

        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        is_archived = self.is_archived

        name = self.name

        remove_members: list[str] | Unset = UNSET
        if not isinstance(self.remove_members, Unset):
            remove_members = self.remove_members

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if add_members is not UNSET:
            field_dict["addMembers"] = add_members
        if color is not UNSET:
            field_dict["color"] = color
        if description is not UNSET:
            field_dict["description"] = description
        if is_archived is not UNSET:
            field_dict["isArchived"] = is_archived
        if name is not UNSET:
            field_dict["name"] = name
        if remove_members is not UNSET:
            field_dict["removeMembers"] = remove_members

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        add_members = cast(list[str], d.pop("addMembers", UNSET))

        color = d.pop("color", UNSET)

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        is_archived = d.pop("isArchived", UNSET)

        name = d.pop("name", UNSET)

        remove_members = cast(list[str], d.pop("removeMembers", UNSET))

        update_project_request = cls(
            add_members=add_members,
            color=color,
            description=description,
            is_archived=is_archived,
            name=name,
            remove_members=remove_members,
        )

        return update_project_request
