from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Literal, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

if TYPE_CHECKING:
    from ..models.custom_tool_upload_session_uploadheaders import (
        CustomToolUploadSessionUploadheaders,
    )


T = TypeVar("T", bound="CustomToolUploadSession")


@_attrs_define
class CustomToolUploadSession:
    """
    Attributes:
        expires_at (datetime.datetime): When the upload URL expires, as an ISO 8601 timestamp.
        id (str): Pass this as `uploadId` to `buildCustomTool` after uploading.
        max_bytes (int): Maximum source-archive size, in bytes.
        upload_headers (CustomToolUploadSessionUploadheaders): Headers to include exactly as provided when uploading to
            `uploadUrl`.
        upload_method (Literal['PUT']): HTTP method to use with `uploadUrl`.
        upload_url (str): Short-lived URL for uploading the source archive.
    """

    expires_at: datetime.datetime
    id: str
    max_bytes: int
    upload_headers: CustomToolUploadSessionUploadheaders
    upload_method: Literal["PUT"]
    upload_url: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        expires_at = self.expires_at.isoformat()

        id = self.id

        max_bytes = self.max_bytes

        upload_headers = self.upload_headers.to_dict()

        upload_method = self.upload_method

        upload_url = self.upload_url

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "expiresAt": expires_at,
                "id": id,
                "maxBytes": max_bytes,
                "uploadHeaders": upload_headers,
                "uploadMethod": upload_method,
                "uploadUrl": upload_url,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.custom_tool_upload_session_uploadheaders import (
            CustomToolUploadSessionUploadheaders,
        )

        d = dict(src_dict)
        expires_at = isoparse(d.pop("expiresAt"))

        id = d.pop("id")

        max_bytes = d.pop("maxBytes")

        upload_headers = CustomToolUploadSessionUploadheaders.from_dict(d.pop("uploadHeaders"))

        upload_method = cast(Literal["PUT"], d.pop("uploadMethod"))
        if upload_method != "PUT":
            raise ValueError(f"uploadMethod must match const 'PUT', got '{upload_method}'")

        upload_url = d.pop("uploadUrl")

        custom_tool_upload_session = cls(
            expires_at=expires_at,
            id=id,
            max_bytes=max_bytes,
            upload_headers=upload_headers,
            upload_method=upload_method,
            upload_url=upload_url,
        )

        custom_tool_upload_session.additional_properties = d
        return custom_tool_upload_session

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
