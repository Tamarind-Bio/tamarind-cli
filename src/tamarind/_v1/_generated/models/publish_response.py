from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="PublishResponse")


@_attrs_define
class PublishResponse:
    """
    Attributes:
        is_published (bool):
        published_version (None | str): The published version handle e.g. 'v1'.
        template_id (str):
    """

    is_published: bool
    published_version: None | str
    template_id: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        is_published = self.is_published

        published_version: None | str
        published_version = self.published_version

        template_id = self.template_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "isPublished": is_published,
                "publishedVersion": published_version,
                "templateId": template_id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        is_published = d.pop("isPublished")

        def _parse_published_version(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        published_version = _parse_published_version(d.pop("publishedVersion"))

        template_id = d.pop("templateId")

        publish_response = cls(
            is_published=is_published,
            published_version=published_version,
            template_id=template_id,
        )

        publish_response.additional_properties = d
        return publish_response

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
