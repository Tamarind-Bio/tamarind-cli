from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Literal, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

if TYPE_CHECKING:
    from ..models.molecule_import_start_uploadheaders import MoleculeImportStartUploadheaders


T = TypeVar("T", bound="MoleculeImportStart")


@_attrs_define
class MoleculeImportStart:
    """
    Attributes:
        expires_at (datetime.datetime | None): When `uploadUrl` stops working.
        group_name (None | str):
        id (str):
        upload_headers (MoleculeImportStartUploadheaders):
        upload_method (Literal['PUT']):  Default: 'PUT'.
        upload_url (str):
    """

    expires_at: datetime.datetime | None
    group_name: None | str
    id: str
    upload_headers: MoleculeImportStartUploadheaders
    upload_url: str
    upload_method: Literal["PUT"] = "PUT"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        expires_at: None | str
        if isinstance(self.expires_at, datetime.datetime):
            expires_at = self.expires_at.isoformat()
        else:
            expires_at = self.expires_at

        group_name: None | str
        group_name = self.group_name

        id = self.id

        upload_headers = self.upload_headers.to_dict()

        upload_method = self.upload_method

        upload_url = self.upload_url

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "expiresAt": expires_at,
                "groupName": group_name,
                "id": id,
                "uploadHeaders": upload_headers,
                "uploadMethod": upload_method,
                "uploadUrl": upload_url,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.molecule_import_start_uploadheaders import MoleculeImportStartUploadheaders

        d = dict(src_dict)

        def _parse_expires_at(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                expires_at_type_0 = isoparse(data)

                return expires_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        expires_at = _parse_expires_at(d.pop("expiresAt"))

        def _parse_group_name(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        group_name = _parse_group_name(d.pop("groupName"))

        id = d.pop("id")

        upload_headers = MoleculeImportStartUploadheaders.from_dict(d.pop("uploadHeaders"))

        upload_method = cast(Literal["PUT"], d.pop("uploadMethod"))
        if upload_method != "PUT":
            raise ValueError(f"uploadMethod must match const 'PUT', got '{upload_method}'")

        upload_url = d.pop("uploadUrl")

        molecule_import_start = cls(
            expires_at=expires_at,
            group_name=group_name,
            id=id,
            upload_headers=upload_headers,
            upload_method=upload_method,
            upload_url=upload_url,
        )

        molecule_import_start.additional_properties = d
        return molecule_import_start

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
