from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Literal, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="ArchivePreparing")


@_attrs_define
class ArchivePreparing:
    """
    Attributes:
        retry_after_seconds (int): How long to wait, in seconds, before repeating the request. The `Retry-After` header
            says the same.
        status (Literal['preparing']):
    """

    retry_after_seconds: int
    status: Literal["preparing"]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        retry_after_seconds = self.retry_after_seconds

        status = self.status

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "retryAfterSeconds": retry_after_seconds,
                "status": status,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        retry_after_seconds = d.pop("retryAfterSeconds")

        status = cast(Literal["preparing"], d.pop("status"))
        if status != "preparing":
            raise ValueError(f"status must match const 'preparing', got '{status}'")

        archive_preparing = cls(
            retry_after_seconds=retry_after_seconds,
            status=status,
        )

        archive_preparing.additional_properties = d
        return archive_preparing

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
