from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

T = TypeVar("T", bound="PublicBuildEvent")


@_attrs_define
class PublicBuildEvent:
    """
    Attributes:
        message (str):
        timestamp (int): Event time as Unix milliseconds.
    """

    message: str
    timestamp: int

    def to_dict(self) -> dict[str, Any]:
        message = self.message

        timestamp = self.timestamp

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "message": message,
                "timestamp": timestamp,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        message = d.pop("message")

        timestamp = d.pop("timestamp")

        public_build_event = cls(
            message=message,
            timestamp=timestamp,
        )

        return public_build_event
