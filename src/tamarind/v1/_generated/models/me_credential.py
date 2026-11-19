from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.me_credential_type import MeCredentialType

T = TypeVar("T", bound="MeCredential")


@_attrs_define
class MeCredential:
    """
    Attributes:
        expires_at (datetime.datetime | None): When a short-lived key a Tamarind service made, or an agent trial,
            expires. Null for every other key.
        key_id (None | str): The key's `id`, as `listApiKeys` shows it. Null when it can't be read.
        name (None | str): The key's stored name. Null when it has none, such as the original key.
        type_ (MeCredentialType): `agentTrial` for an unclaimed agent trial's key, else `apiKey`. v1 takes API keys
            only, so `oauth` and `session` don't occur yet.
    """

    expires_at: datetime.datetime | None
    key_id: None | str
    name: None | str
    type_: MeCredentialType
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        expires_at: None | str
        if isinstance(self.expires_at, datetime.datetime):
            expires_at = self.expires_at.isoformat()
        else:
            expires_at = self.expires_at

        key_id: None | str
        key_id = self.key_id

        name: None | str
        name = self.name

        type_ = self.type_.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "expiresAt": expires_at,
                "keyId": key_id,
                "name": name,
                "type": type_,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
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

        def _parse_key_id(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        key_id = _parse_key_id(d.pop("keyId"))

        def _parse_name(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        name = _parse_name(d.pop("name"))

        type_ = MeCredentialType(d.pop("type"))

        me_credential = cls(
            expires_at=expires_at,
            key_id=key_id,
            name=name,
            type_=type_,
        )

        me_credential.additional_properties = d
        return me_credential

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
