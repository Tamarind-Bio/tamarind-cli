from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.project_scope import ProjectScope
from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdatedProject")


@_attrs_define
class UpdatedProject:
    """
    Attributes:
        color (None | str): `#RRGGBB`, upper case.
        created_at (datetime.datetime):
        created_by (str):
        description (None | str): Null when empty.
        id (str):
        is_archived (bool): An archived project is left out of `listProjects`.
        name (str):
        read_only (bool): True on `shared` projects you cannot file jobs under.
        scope (ProjectScope): Only `org` satisfies a required-project policy.
        updated_at (datetime.datetime | None):
        failed_adds (list[str]): Members who could not be added. The rest of the update still applied. Send them again
            to retry.
        job_count (int | Unset): Jobs filed under it that you can open. Not sent yet, because `includeCounts=true` is
            400 for now.
    """

    color: None | str
    created_at: datetime.datetime
    created_by: str
    description: None | str
    id: str
    is_archived: bool
    name: str
    read_only: bool
    scope: ProjectScope
    updated_at: datetime.datetime | None
    failed_adds: list[str]
    job_count: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        color: None | str
        color = self.color

        created_at = self.created_at.isoformat()

        created_by = self.created_by

        description: None | str
        description = self.description

        id = self.id

        is_archived = self.is_archived

        name = self.name

        read_only = self.read_only

        scope = self.scope.value

        updated_at: None | str
        if isinstance(self.updated_at, datetime.datetime):
            updated_at = self.updated_at.isoformat()
        else:
            updated_at = self.updated_at

        failed_adds = self.failed_adds

        job_count = self.job_count

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "color": color,
                "createdAt": created_at,
                "createdBy": created_by,
                "description": description,
                "id": id,
                "isArchived": is_archived,
                "name": name,
                "readOnly": read_only,
                "scope": scope,
                "updatedAt": updated_at,
                "failedAdds": failed_adds,
            }
        )
        if job_count is not UNSET:
            field_dict["jobCount"] = job_count

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_color(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        color = _parse_color(d.pop("color"))

        created_at = isoparse(d.pop("createdAt"))

        created_by = d.pop("createdBy")

        def _parse_description(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        description = _parse_description(d.pop("description"))

        id = d.pop("id")

        is_archived = d.pop("isArchived")

        name = d.pop("name")

        read_only = d.pop("readOnly")

        scope = ProjectScope(d.pop("scope"))

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

        failed_adds = cast(list[str], d.pop("failedAdds"))

        job_count = d.pop("jobCount", UNSET)

        updated_project = cls(
            color=color,
            created_at=created_at,
            created_by=created_by,
            description=description,
            id=id,
            is_archived=is_archived,
            name=name,
            read_only=read_only,
            scope=scope,
            updated_at=updated_at,
            failed_adds=failed_adds,
            job_count=job_count,
        )

        updated_project.additional_properties = d
        return updated_project

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
