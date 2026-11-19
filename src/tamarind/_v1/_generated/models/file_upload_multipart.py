from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Literal, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

if TYPE_CHECKING:
    from ..models.file_upload_multipart_parts_item import FileUploadMultipartPartsItem


T = TypeVar("T", bound="FileUploadMultipart")


@_attrs_define
class FileUploadMultipart:
    """Send each part to its `url`, then call `completeFileUpload`.

    Attributes:
        expires_at (datetime.datetime):
        id (str): Pass this as `uploadId` to `completeFileUpload`.
        method (Literal['PUT']):
        part_size_bytes (int):
        parts (list[FileUploadMultipartPartsItem]):
    """

    expires_at: datetime.datetime
    id: str
    method: Literal["PUT"]
    part_size_bytes: int
    parts: list[FileUploadMultipartPartsItem]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        expires_at = self.expires_at.isoformat()

        id = self.id

        method = self.method

        part_size_bytes = self.part_size_bytes

        parts = []
        for parts_item_data in self.parts:
            parts_item = parts_item_data.to_dict()
            parts.append(parts_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "expiresAt": expires_at,
                "id": id,
                "method": method,
                "partSizeBytes": part_size_bytes,
                "parts": parts,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.file_upload_multipart_parts_item import FileUploadMultipartPartsItem

        d = dict(src_dict)
        expires_at = isoparse(d.pop("expiresAt"))

        id = d.pop("id")

        method = cast(Literal["PUT"], d.pop("method"))
        if method != "PUT":
            raise ValueError(f"method must match const 'PUT', got '{method}'")

        part_size_bytes = d.pop("partSizeBytes")

        parts = []
        _parts = d.pop("parts")
        for parts_item_data in _parts:
            parts_item = FileUploadMultipartPartsItem.from_dict(parts_item_data)

            parts.append(parts_item)

        file_upload_multipart = cls(
            expires_at=expires_at,
            id=id,
            method=method,
            part_size_bytes=part_size_bytes,
            parts=parts,
        )

        file_upload_multipart.additional_properties = d
        return file_upload_multipart

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
