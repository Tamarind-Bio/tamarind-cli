from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="UploadFileInlineRequest")


@_attrs_define
class UploadFileInlineRequest:
    """
    Attributes:
        content_base_64 (str): The file itself, up to 3 MiB before encoding, which is 4,194,304 characters of base64.
        path (str): Where to store it, e.g. `targets/1abc.pdb`.
        content_type (str | Unset): The file's media type, e.g. `chemical/x-pdb`, in printable ASCII. Stored with the
            file. For a signed URL, `upload.headers` then carries it as `Content-Type`.
    """

    content_base_64: str
    path: str
    content_type: str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        content_base_64 = self.content_base_64

        path = self.path

        content_type = self.content_type

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "contentBase64": content_base_64,
                "path": path,
            }
        )
        if content_type is not UNSET:
            field_dict["contentType"] = content_type

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        content_base_64 = d.pop("contentBase64")

        path = d.pop("path")

        content_type = d.pop("contentType", UNSET)

        upload_file_inline_request = cls(
            content_base_64=content_base_64,
            path=path,
            content_type=content_type,
        )

        return upload_file_inline_request
