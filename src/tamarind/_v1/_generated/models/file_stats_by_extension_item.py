from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="FileStatsByExtensionItem")


@_attrs_define
class FileStatsByExtensionItem:
    """
    Attributes:
        extension (str):
        file_count (int):
        total_bytes (int):
    """

    extension: str
    file_count: int
    total_bytes: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        extension = self.extension

        file_count = self.file_count

        total_bytes = self.total_bytes

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "extension": extension,
                "fileCount": file_count,
                "totalBytes": total_bytes,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        extension = d.pop("extension")

        file_count = d.pop("fileCount")

        total_bytes = d.pop("totalBytes")

        file_stats_by_extension_item = cls(
            extension=extension,
            file_count=file_count,
            total_bytes=total_bytes,
        )

        file_stats_by_extension_item.additional_properties = d
        return file_stats_by_extension_item

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
