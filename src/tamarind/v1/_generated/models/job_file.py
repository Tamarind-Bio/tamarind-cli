from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

T = TypeVar("T", bound="JobFile")


@_attrs_define
class JobFile:
    """
    Attributes:
        download_url (None | str): Null without `includeDownloadUrls=true`.
        download_url_expires_at (datetime.datetime | None): Null without `includeDownloadUrls=true`.
        modified_at (datetime.datetime):
        path (str): Relative to the job's output folder.
        ref (None | str): Pass this as any file setting of another job to reuse this file without downloading it. It is
            `{folder}/{path}`, the job's folder in your workspace and the file's `path`. A job stored under its own id has a
            folder named by that id, without `job_`; older jobs' folders are their names. Null for another account's job,
            such as an organization peer's or one you claimed from an agent trial, whose files no file setting of yours can
            name.
        size_bytes (int):
    """

    download_url: None | str
    download_url_expires_at: datetime.datetime | None
    modified_at: datetime.datetime
    path: str
    ref: None | str
    size_bytes: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        download_url: None | str
        download_url = self.download_url

        download_url_expires_at: None | str
        if isinstance(self.download_url_expires_at, datetime.datetime):
            download_url_expires_at = self.download_url_expires_at.isoformat()
        else:
            download_url_expires_at = self.download_url_expires_at

        modified_at = self.modified_at.isoformat()

        path = self.path

        ref: None | str
        ref = self.ref

        size_bytes = self.size_bytes

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "downloadUrl": download_url,
                "downloadUrlExpiresAt": download_url_expires_at,
                "modifiedAt": modified_at,
                "path": path,
                "ref": ref,
                "sizeBytes": size_bytes,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_download_url(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        download_url = _parse_download_url(d.pop("downloadUrl"))

        def _parse_download_url_expires_at(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                download_url_expires_at_type_0 = isoparse(data)

                return download_url_expires_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        download_url_expires_at = _parse_download_url_expires_at(d.pop("downloadUrlExpiresAt"))

        modified_at = isoparse(d.pop("modifiedAt"))

        path = d.pop("path")

        def _parse_ref(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        ref = _parse_ref(d.pop("ref"))

        size_bytes = d.pop("sizeBytes")

        job_file = cls(
            download_url=download_url,
            download_url_expires_at=download_url_expires_at,
            modified_at=modified_at,
            path=path,
            ref=ref,
            size_bytes=size_bytes,
        )

        job_file.additional_properties = d
        return job_file

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
