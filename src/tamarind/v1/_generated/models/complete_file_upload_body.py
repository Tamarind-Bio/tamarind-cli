from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define

if TYPE_CHECKING:
    from ..models.complete_file_upload_body_parts_item import CompleteFileUploadBodyPartsItem


T = TypeVar("T", bound="CompleteFileUploadBody")


@_attrs_define
class CompleteFileUploadBody:
    """
    Attributes:
        parts (list[CompleteFileUploadBodyPartsItem]):
        upload_id (str):
    """

    parts: list[CompleteFileUploadBodyPartsItem]
    upload_id: str

    def to_dict(self) -> dict[str, Any]:
        parts = []
        for parts_item_data in self.parts:
            parts_item = parts_item_data.to_dict()
            parts.append(parts_item)

        upload_id = self.upload_id

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "parts": parts,
                "uploadId": upload_id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.complete_file_upload_body_parts_item import CompleteFileUploadBodyPartsItem

        d = dict(src_dict)
        parts = []
        _parts = d.pop("parts")
        for parts_item_data in _parts:
            parts_item = CompleteFileUploadBodyPartsItem.from_dict(parts_item_data)

            parts.append(parts_item)

        upload_id = d.pop("uploadId")

        complete_file_upload_body = cls(
            parts=parts,
            upload_id=upload_id,
        )

        return complete_file_upload_body
