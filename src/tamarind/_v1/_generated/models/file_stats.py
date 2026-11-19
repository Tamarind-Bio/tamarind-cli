from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.file_stats_by_extension_item import FileStatsByExtensionItem


T = TypeVar("T", bound="FileStats")


@_attrs_define
class FileStats:
    """
    Attributes:
        by_extension (list[FileStatsByExtensionItem]): Most files first, then by extension. Extensions are lower-case
            and without the dot.
        file_count (int):
        total_bytes (int):
    """

    by_extension: list[FileStatsByExtensionItem]
    file_count: int
    total_bytes: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        by_extension = []
        for by_extension_item_data in self.by_extension:
            by_extension_item = by_extension_item_data.to_dict()
            by_extension.append(by_extension_item)

        file_count = self.file_count

        total_bytes = self.total_bytes

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "byExtension": by_extension,
                "fileCount": file_count,
                "totalBytes": total_bytes,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.file_stats_by_extension_item import FileStatsByExtensionItem

        d = dict(src_dict)
        by_extension = []
        _by_extension = d.pop("byExtension")
        for by_extension_item_data in _by_extension:
            by_extension_item = FileStatsByExtensionItem.from_dict(by_extension_item_data)

            by_extension.append(by_extension_item)

        file_count = d.pop("fileCount")

        total_bytes = d.pop("totalBytes")

        file_stats = cls(
            by_extension=by_extension,
            file_count=file_count,
            total_bytes=total_bytes,
        )

        file_stats.additional_properties = d
        return file_stats

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
