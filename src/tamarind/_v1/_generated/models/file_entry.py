from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.file_entry_type import FileEntryType

T = TypeVar("T", bound="FileEntry")


@_attrs_define
class FileEntry:
    """
    Attributes:
        modified_at (datetime.datetime | None): When the file was last written. Null for a folder, and for a signed or
            multipart upload that isn't finished yet. A root file listed from the catalog shows when it was uploaded.
        path (str):
        size_bytes (int | None): Null for a folder, and for a root file the catalog has no size for. For a signed or
            multipart upload that isn't finished yet, the size it was started for.
        type_ (FileEntryType):
    """

    modified_at: datetime.datetime | None
    path: str
    size_bytes: int | None
    type_: FileEntryType
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        modified_at: None | str
        if isinstance(self.modified_at, datetime.datetime):
            modified_at = self.modified_at.isoformat()
        else:
            modified_at = self.modified_at

        path = self.path

        size_bytes: int | None
        size_bytes = self.size_bytes

        type_ = self.type_.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "modifiedAt": modified_at,
                "path": path,
                "sizeBytes": size_bytes,
                "type": type_,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_modified_at(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                modified_at_type_0 = isoparse(data)

                return modified_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        modified_at = _parse_modified_at(d.pop("modifiedAt"))

        path = d.pop("path")

        def _parse_size_bytes(data: object) -> int | None:
            if data is None:
                return data
            return cast(int | None, data)

        size_bytes = _parse_size_bytes(d.pop("sizeBytes"))

        type_ = FileEntryType(d.pop("type"))

        file_entry = cls(
            modified_at=modified_at,
            path=path,
            size_bytes=size_bytes,
            type_=type_,
        )

        file_entry.additional_properties = d
        return file_entry

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
