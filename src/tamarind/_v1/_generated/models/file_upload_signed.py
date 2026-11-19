from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Literal, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

if TYPE_CHECKING:
    from ..models.file_upload_signed_headers import FileUploadSignedHeaders


T = TypeVar("T", bound="FileUploadSigned")


@_attrs_define
class FileUploadSigned:
    """Send the whole file to `url`, with `method` and every value in `headers`.

    Attributes:
        expires_at (datetime.datetime):
        headers (FileUploadSignedHeaders):
        method (Literal['PUT']):
        url (str):
    """

    expires_at: datetime.datetime
    headers: FileUploadSignedHeaders
    method: Literal["PUT"]
    url: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        expires_at = self.expires_at.isoformat()

        headers = self.headers.to_dict()

        method = self.method

        url = self.url

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "expiresAt": expires_at,
                "headers": headers,
                "method": method,
                "url": url,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.file_upload_signed_headers import FileUploadSignedHeaders

        d = dict(src_dict)
        expires_at = isoparse(d.pop("expiresAt"))

        headers = FileUploadSignedHeaders.from_dict(d.pop("headers"))

        method = cast(Literal["PUT"], d.pop("method"))
        if method != "PUT":
            raise ValueError(f"method must match const 'PUT', got '{method}'")

        url = d.pop("url")

        file_upload_signed = cls(
            expires_at=expires_at,
            headers=headers,
            method=method,
            url=url,
        )

        file_upload_signed.additional_properties = d
        return file_upload_signed

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
