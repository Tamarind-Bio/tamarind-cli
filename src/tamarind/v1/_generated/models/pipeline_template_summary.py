from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

T = TypeVar("T", bound="PipelineTemplateSummary")


@_attrs_define
class PipelineTemplateSummary:
    """
    Attributes:
        created_at (datetime.datetime):
        created_by (None | str):
        description (None | str):
        id (str):
        is_published (bool):
        name (str):
        run_count (int | None):
        updated_at (datetime.datetime):
        version_count (int):
    """

    created_at: datetime.datetime
    created_by: None | str
    description: None | str
    id: str
    is_published: bool
    name: str
    run_count: int | None
    updated_at: datetime.datetime
    version_count: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        created_at = self.created_at.isoformat()

        created_by: None | str
        created_by = self.created_by

        description: None | str
        description = self.description

        id = self.id

        is_published = self.is_published

        name = self.name

        run_count: int | None
        run_count = self.run_count

        updated_at = self.updated_at.isoformat()

        version_count = self.version_count

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "createdAt": created_at,
                "createdBy": created_by,
                "description": description,
                "id": id,
                "isPublished": is_published,
                "name": name,
                "runCount": run_count,
                "updatedAt": updated_at,
                "versionCount": version_count,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        created_at = isoparse(d.pop("createdAt"))

        def _parse_created_by(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        created_by = _parse_created_by(d.pop("createdBy"))

        def _parse_description(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        description = _parse_description(d.pop("description"))

        id = d.pop("id")

        is_published = d.pop("isPublished")

        name = d.pop("name")

        def _parse_run_count(data: object) -> int | None:
            if data is None:
                return data
            return cast(int | None, data)

        run_count = _parse_run_count(d.pop("runCount"))

        updated_at = isoparse(d.pop("updatedAt"))

        version_count = d.pop("versionCount")

        pipeline_template_summary = cls(
            created_at=created_at,
            created_by=created_by,
            description=description,
            id=id,
            is_published=is_published,
            name=name,
            run_count=run_count,
            updated_at=updated_at,
            version_count=version_count,
        )

        pipeline_template_summary.additional_properties = d
        return pipeline_template_summary

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
