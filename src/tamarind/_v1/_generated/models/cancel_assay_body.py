from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="CancelAssayBody")


@_attrs_define
class CancelAssayBody:
    """
    Attributes:
        reason (str | Unset): Recorded on the order, and sent to the lab when it holds the order. Left out or empty, it
            is `Cancelled via API`.
    """

    reason: str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        reason = self.reason

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if reason is not UNSET:
            field_dict["reason"] = reason

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        reason = d.pop("reason", UNSET)

        cancel_assay_body = cls(
            reason=reason,
        )

        return cancel_assay_body
