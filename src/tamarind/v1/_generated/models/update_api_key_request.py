from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.api_key_budget import ApiKeyBudget


T = TypeVar("T", bound="UpdateApiKeyRequest")


@_attrs_define
class UpdateApiKeyRequest:
    """
    Attributes:
        budget (ApiKeyBudget | None | Unset): Not supported yet. Null or absent; a value is 422 `not_supported`.
        expires_at (datetime.datetime | None | Unset): Not supported yet. Null or absent; a value is 422
            `not_supported`.
        name (None | str | Unset): The new name. Control characters are removed and the ends trimmed; nothing left is
            422 `invalid_format`. Absent or null renames nothing.
    """

    budget: ApiKeyBudget | None | Unset = UNSET
    expires_at: datetime.datetime | None | Unset = UNSET
    name: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.api_key_budget import ApiKeyBudget

        budget: dict[str, Any] | None | Unset
        if isinstance(self.budget, Unset):
            budget = UNSET
        elif isinstance(self.budget, ApiKeyBudget):
            budget = self.budget.to_dict()
        else:
            budget = self.budget

        expires_at: None | str | Unset
        if isinstance(self.expires_at, Unset):
            expires_at = UNSET
        elif isinstance(self.expires_at, datetime.datetime):
            expires_at = self.expires_at.isoformat()
        else:
            expires_at = self.expires_at

        name: None | str | Unset
        if isinstance(self.name, Unset):
            name = UNSET
        else:
            name = self.name

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if budget is not UNSET:
            field_dict["budget"] = budget
        if expires_at is not UNSET:
            field_dict["expiresAt"] = expires_at
        if name is not UNSET:
            field_dict["name"] = name

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.api_key_budget import ApiKeyBudget

        d = dict(src_dict)

        def _parse_budget(data: object) -> ApiKeyBudget | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                budget_type_0 = ApiKeyBudget.from_dict(data)

                return budget_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(ApiKeyBudget | None | Unset, data)

        budget = _parse_budget(d.pop("budget", UNSET))

        def _parse_expires_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                expires_at_type_0 = isoparse(data)

                return expires_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        expires_at = _parse_expires_at(d.pop("expiresAt", UNSET))

        def _parse_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        name = _parse_name(d.pop("name", UNSET))

        update_api_key_request = cls(
            budget=budget,
            expires_at=expires_at,
            name=name,
        )

        return update_api_key_request
