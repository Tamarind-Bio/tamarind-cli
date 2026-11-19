from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

T = TypeVar("T", bound="MoleculeFileEntry")


@_attrs_define
class MoleculeFileEntry:
    """One structure file on a molecule. Appears in the `files` map, whose KEY is
    the producer (a job/tool name, or `user` for uploads).

        Attributes:
            created_at (datetime.datetime | None):
            download_url (str):
            file_name (str):
            file_type (None | str):
    """

    created_at: datetime.datetime | None
    download_url: str
    file_name: str
    file_type: None | str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        created_at: None | str
        if isinstance(self.created_at, datetime.datetime):
            created_at = self.created_at.isoformat()
        else:
            created_at = self.created_at

        download_url = self.download_url

        file_name = self.file_name

        file_type: None | str
        file_type = self.file_type

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "createdAt": created_at,
                "downloadUrl": download_url,
                "fileName": file_name,
                "fileType": file_type,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_created_at(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                created_at_type_0 = isoparse(data)

                return created_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        created_at = _parse_created_at(d.pop("createdAt"))

        download_url = d.pop("downloadUrl")

        file_name = d.pop("fileName")

        def _parse_file_type(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        file_type = _parse_file_type(d.pop("fileType"))

        molecule_file_entry = cls(
            created_at=created_at,
            download_url=download_url,
            file_name=file_name,
            file_type=file_type,
        )

        molecule_file_entry.additional_properties = d
        return molecule_file_entry

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
