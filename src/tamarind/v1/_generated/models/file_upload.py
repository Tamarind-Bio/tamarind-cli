from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.file_entry import FileEntry
    from ..models.file_upload_multipart import FileUploadMultipart
    from ..models.file_upload_signed import FileUploadSigned


T = TypeVar("T", bound="FileUpload")


@_attrs_define
class FileUpload:
    """
    Attributes:
        file (FileEntry):
        upload (FileUploadMultipart | FileUploadSigned | None): Null when the content was sent inline.
    """

    file: FileEntry
    upload: FileUploadMultipart | FileUploadSigned | None
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.file_upload_multipart import FileUploadMultipart
        from ..models.file_upload_signed import FileUploadSigned

        file = self.file.to_dict()

        upload: dict[str, Any] | None
        if isinstance(self.upload, FileUploadSigned):
            upload = self.upload.to_dict()
        elif isinstance(self.upload, FileUploadMultipart):
            upload = self.upload.to_dict()
        else:
            upload = self.upload

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "file": file,
                "upload": upload,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.file_entry import FileEntry
        from ..models.file_upload_multipart import FileUploadMultipart
        from ..models.file_upload_signed import FileUploadSigned

        d = dict(src_dict)
        file = FileEntry.from_dict(d.pop("file"))

        def _parse_upload(data: object) -> FileUploadMultipart | FileUploadSigned | None:
            if data is None:
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                upload_type_0 = FileUploadSigned.from_dict(data)

                return upload_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                upload_type_1 = FileUploadMultipart.from_dict(data)

                return upload_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(FileUploadMultipart | FileUploadSigned | None, data)

        upload = _parse_upload(d.pop("upload"))

        file_upload = cls(
            file=file,
            upload=upload,
        )

        file_upload.additional_properties = d
        return file_upload

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
