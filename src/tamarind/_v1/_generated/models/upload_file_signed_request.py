from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="UploadFileSignedRequest")


@_attrs_define
class UploadFileSignedRequest:
    """
    Attributes:
        path (str): Where to store it, e.g. `targets/1abc.pdb`.
        size_bytes (int): At most 5 GB, the limit for one PUT. Above that, set `multipart: true`.
        content_type (str | Unset): The file's media type, e.g. `chemical/x-pdb`, in printable ASCII. Stored with the
            file. For a signed URL, `upload.headers` then carries it as `Content-Type`.
    """

    path: str
    size_bytes: int
    content_type: str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        path = self.path

        size_bytes = self.size_bytes

        content_type = self.content_type

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "path": path,
                "sizeBytes": size_bytes,
            }
        )
        if content_type is not UNSET:
            field_dict["contentType"] = content_type

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        path = d.pop("path")

        size_bytes = d.pop("sizeBytes")

        content_type = d.pop("contentType", UNSET)

        upload_file_signed_request = cls(
            path=path,
            size_bytes=size_bytes,
            content_type=content_type,
        )

        return upload_file_signed_request
