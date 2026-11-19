from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, Literal, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

T = TypeVar("T", bound="ArchiveReady")


@_attrs_define
class ArchiveReady:
    """
    Attributes:
        download_url (str): A short-lived signed link. Fetch it without your API key.
        expires_at (datetime.datetime): When `downloadUrl` stops working. Never later than the link's own expiry.
        file_count (int | None): How many files the zip holds, from its own directory. A job's or a batch's archive
            always has it. Null when nothing records it, as for a pipeline run's archive.
        size_bytes (int): The zip's size.
        status (Literal['ready']):
        truncated (bool | None): True when the archive hit a size or file-count limit and is missing files. A job's or a
            batch's archive is the stored one and never cut short, so it is false. Null when nothing records it, as for a
            pipeline run's archive.
    """

    download_url: str
    expires_at: datetime.datetime
    file_count: int | None
    size_bytes: int
    status: Literal["ready"]
    truncated: bool | None
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        download_url = self.download_url

        expires_at = self.expires_at.isoformat()

        file_count: int | None
        file_count = self.file_count

        size_bytes = self.size_bytes

        status = self.status

        truncated: bool | None
        truncated = self.truncated

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "downloadUrl": download_url,
                "expiresAt": expires_at,
                "fileCount": file_count,
                "sizeBytes": size_bytes,
                "status": status,
                "truncated": truncated,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        download_url = d.pop("downloadUrl")

        expires_at = isoparse(d.pop("expiresAt"))

        def _parse_file_count(data: object) -> int | None:
            if data is None:
                return data
            return cast(int | None, data)

        file_count = _parse_file_count(d.pop("fileCount"))

        size_bytes = d.pop("sizeBytes")

        status = cast(Literal["ready"], d.pop("status"))
        if status != "ready":
            raise ValueError(f"status must match const 'ready', got '{status}'")

        def _parse_truncated(data: object) -> bool | None:
            if data is None:
                return data
            return cast(bool | None, data)

        truncated = _parse_truncated(d.pop("truncated"))

        archive_ready = cls(
            download_url=download_url,
            expires_at=expires_at,
            file_count=file_count,
            size_bytes=size_bytes,
            status=status,
            truncated=truncated,
        )

        archive_ready.additional_properties = d
        return archive_ready

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
