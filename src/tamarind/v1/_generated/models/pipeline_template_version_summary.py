from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

T = TypeVar("T", bound="PipelineTemplateVersionSummary")


@_attrs_define
class PipelineTemplateVersionSummary:
    """One saved version of a pipeline template.

    Attributes:
        created_at (datetime.datetime):
        is_published (bool):
        is_valid (bool):
        version (None | str): The version handle e.g. 'v1'. Null only for a version saved before handles existed, which
            can't be addressed by name.
    """

    created_at: datetime.datetime
    is_published: bool
    is_valid: bool
    version: None | str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        created_at = self.created_at.isoformat()

        is_published = self.is_published

        is_valid = self.is_valid

        version: None | str
        version = self.version

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "createdAt": created_at,
                "isPublished": is_published,
                "isValid": is_valid,
                "version": version,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        created_at = isoparse(d.pop("createdAt"))

        is_published = d.pop("isPublished")

        is_valid = d.pop("isValid")

        def _parse_version(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        version = _parse_version(d.pop("version"))

        pipeline_template_version_summary = cls(
            created_at=created_at,
            is_published=is_published,
            is_valid=is_valid,
            version=version,
        )

        pipeline_template_version_summary.additional_properties = d
        return pipeline_template_version_summary

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
