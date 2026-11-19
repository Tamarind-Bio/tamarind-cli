from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

T = TypeVar("T", bound="RefreshUsageBody")


@_attrs_define
class RefreshUsageBody:
    """
    Attributes:
        users (list[str]): Whose figures to refresh. Duplicates are refreshed once. Anyone you can't refresh is 403.
    """

    users: list[str]

    def to_dict(self) -> dict[str, Any]:
        users = self.users

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "users": users,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        users = cast(list[str], d.pop("users"))

        refresh_usage_body = cls(
            users=users,
        )

        return refresh_usage_body
