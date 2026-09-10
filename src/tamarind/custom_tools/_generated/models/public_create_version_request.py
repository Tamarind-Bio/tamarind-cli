from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="PublicCreateVersionRequest")


@_attrs_define
class PublicCreateVersionRequest:
    """
    Attributes:
        upload_id (str): The `uploadId` returned when the source upload was created.
        expected_source_digest (None | str | Unset): Optional SHA-256 assertion, formatted as `sha256:<hex>`. The server
            always computes the digest. If supplied, a mismatch rejects the build. Without it, the server builds the
            uploaded bytes it reads.
    """

    upload_id: str
    expected_source_digest: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        upload_id = self.upload_id

        expected_source_digest: None | str | Unset
        if isinstance(self.expected_source_digest, Unset):
            expected_source_digest = UNSET
        else:
            expected_source_digest = self.expected_source_digest

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "uploadId": upload_id,
            }
        )
        if expected_source_digest is not UNSET:
            field_dict["expectedSourceDigest"] = expected_source_digest

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        upload_id = d.pop("uploadId")

        def _parse_expected_source_digest(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        expected_source_digest = _parse_expected_source_digest(d.pop("expectedSourceDigest", UNSET))

        public_create_version_request = cls(
            upload_id=upload_id,
            expected_source_digest=expected_source_digest,
        )

        return public_create_version_request
