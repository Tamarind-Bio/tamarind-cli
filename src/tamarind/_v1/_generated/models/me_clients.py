from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="MeClients")


@_attrs_define
class MeClients:
    """
    Attributes:
        use_v1 (bool): For Tamarind's own CLI and SDK, which choose by it between v1 and today's API for this caller;
            true sends their calls to v1. It's the `cli-sdk-v1-api` flag for the key's owner, and false when the flag is off
            or can't be read. Other clients can ignore it.
    """

    use_v1: bool
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        use_v1 = self.use_v1

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "useV1": use_v1,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        use_v1 = d.pop("useV1")

        me_clients = cls(
            use_v1=use_v1,
        )

        me_clients.additional_properties = d
        return me_clients

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
