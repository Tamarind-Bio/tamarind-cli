from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

T = TypeVar("T", bound="PublicCreateVersionRequest")


@_attrs_define
class PublicCreateVersionRequest:
    """
    Attributes:
        expected_source_digest (str): SHA-256 digest of the uploaded archive, formatted as `sha256:<hex>`.
        upload_id (str): The `uploadId` returned when the source upload was created.
    """

    expected_source_digest: str
    upload_id: str

    def to_dict(self) -> dict[str, Any]:
        expected_source_digest = self.expected_source_digest

        upload_id = self.upload_id

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "expectedSourceDigest": expected_source_digest,
                "uploadId": upload_id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        expected_source_digest = d.pop("expectedSourceDigest")

        upload_id = d.pop("uploadId")

        public_create_version_request = cls(
            expected_source_digest=expected_source_digest,
            upload_id=upload_id,
        )

        return public_create_version_request
