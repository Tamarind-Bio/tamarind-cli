from __future__ import annotations

from collections.abc import Mapping
from typing import (
    TYPE_CHECKING,
    Any,
    Literal,
    TypeVar,
    cast,
)

from attrs import define as _attrs_define

if TYPE_CHECKING:
    from ..models.public_upload_session_uploadheaders import (
        PublicUploadSessionUploadheaders,
    )


T = TypeVar("T", bound="PublicUploadSession")


@_attrs_define
class PublicUploadSession:
    """
    Attributes:
        expires_at (str): When the upload URL expires, as an ISO 8601 timestamp.
        max_bytes (int): Maximum source-archive size, in bytes.
        upload_headers (PublicUploadSessionUploadheaders): Headers to include exactly as provided when uploading to
            `uploadUrl`.
        upload_id (str): Pass this value to the version-build request after uploading.
        upload_method (Literal['PUT']): HTTP method to use with `uploadUrl`.
        upload_url (str): Short-lived URL for uploading the source archive.
    """

    expires_at: str
    max_bytes: int
    upload_headers: PublicUploadSessionUploadheaders
    upload_id: str
    upload_method: Literal["PUT"]
    upload_url: str

    def to_dict(self) -> dict[str, Any]:
        expires_at = self.expires_at

        max_bytes = self.max_bytes

        upload_headers = self.upload_headers.to_dict()

        upload_id = self.upload_id

        upload_method = self.upload_method

        upload_url = self.upload_url

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "expiresAt": expires_at,
                "maxBytes": max_bytes,
                "uploadHeaders": upload_headers,
                "uploadId": upload_id,
                "uploadMethod": upload_method,
                "uploadUrl": upload_url,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.public_upload_session_uploadheaders import (
            PublicUploadSessionUploadheaders,
        )

        d = dict(src_dict)
        expires_at = d.pop("expiresAt")

        max_bytes = d.pop("maxBytes")

        upload_headers = PublicUploadSessionUploadheaders.from_dict(
            d.pop("uploadHeaders")
        )

        upload_id = d.pop("uploadId")

        upload_method = cast(Literal["PUT"], d.pop("uploadMethod"))
        if upload_method != "PUT":
            raise ValueError(
                f"uploadMethod must match const 'PUT', got '{upload_method}'"
            )

        upload_url = d.pop("uploadUrl")

        public_upload_session = cls(
            expires_at=expires_at,
            max_bytes=max_bytes,
            upload_headers=upload_headers,
            upload_id=upload_id,
            upload_method=upload_method,
            upload_url=upload_url,
        )

        return public_upload_session
