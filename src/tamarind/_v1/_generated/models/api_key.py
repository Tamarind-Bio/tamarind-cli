from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.api_key_status import ApiKeyStatus

if TYPE_CHECKING:
    from ..models.api_key_budget import ApiKeyBudget


T = TypeVar("T", bound="ApiKey")


@_attrs_define
class ApiKey:
    """
    Attributes:
        budget (ApiKeyBudget | None): Always null for now. Nothing enforces a key budget yet.
        created_at (datetime.datetime):
        created_by (None | str): The email of whoever made it, for a key made with `createApiKey`. Null for every other
            key, including the original key and keys made on the website's keys page.
        expires_at (datetime.datetime | None): Always null for now. Nothing enforces a key expiry yet.
        id (str):
        last4 (str): The secret's last four characters.
        last_used_at (datetime.datetime | None): Always null for now. Nothing records a key's last use yet.
        name (str): The name the keys page shows. A key saved without one is `Original key` (the original key) or
            `Untitled key`.
        owner (str): The owning user's or service account's email.
        prefix (None | str): Always null for now. A key's secret is a UUID, as the keys page makes them, so it has no
            display prefix. (The key's `id` is `key_` and 32 hex characters.)
        rotated_from_id (None | str): Always null for now. Keys aren't rotated through this API.
        service_account_id (None | str): The owning service account's id. Null for a person's key.
        status (ApiKeyStatus):
    """

    budget: ApiKeyBudget | None
    created_at: datetime.datetime
    created_by: None | str
    expires_at: datetime.datetime | None
    id: str
    last4: str
    last_used_at: datetime.datetime | None
    name: str
    owner: str
    prefix: None | str
    rotated_from_id: None | str
    service_account_id: None | str
    status: ApiKeyStatus
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.api_key_budget import ApiKeyBudget

        budget: dict[str, Any] | None
        if isinstance(self.budget, ApiKeyBudget):
            budget = self.budget.to_dict()
        else:
            budget = self.budget

        created_at = self.created_at.isoformat()

        created_by: None | str
        created_by = self.created_by

        expires_at: None | str
        if isinstance(self.expires_at, datetime.datetime):
            expires_at = self.expires_at.isoformat()
        else:
            expires_at = self.expires_at

        id = self.id

        last4 = self.last4

        last_used_at: None | str
        if isinstance(self.last_used_at, datetime.datetime):
            last_used_at = self.last_used_at.isoformat()
        else:
            last_used_at = self.last_used_at

        name = self.name

        owner = self.owner

        prefix: None | str
        prefix = self.prefix

        rotated_from_id: None | str
        rotated_from_id = self.rotated_from_id

        service_account_id: None | str
        service_account_id = self.service_account_id

        status = self.status.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "budget": budget,
                "createdAt": created_at,
                "createdBy": created_by,
                "expiresAt": expires_at,
                "id": id,
                "last4": last4,
                "lastUsedAt": last_used_at,
                "name": name,
                "owner": owner,
                "prefix": prefix,
                "rotatedFromId": rotated_from_id,
                "serviceAccountId": service_account_id,
                "status": status,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.api_key_budget import ApiKeyBudget

        d = dict(src_dict)

        def _parse_budget(data: object) -> ApiKeyBudget | None:
            if data is None:
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                budget_type_0 = ApiKeyBudget.from_dict(data)

                return budget_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(ApiKeyBudget | None, data)

        budget = _parse_budget(d.pop("budget"))

        created_at = isoparse(d.pop("createdAt"))

        def _parse_created_by(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        created_by = _parse_created_by(d.pop("createdBy"))

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

        id = d.pop("id")

        last4 = d.pop("last4")

        def _parse_last_used_at(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                last_used_at_type_0 = isoparse(data)

                return last_used_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        last_used_at = _parse_last_used_at(d.pop("lastUsedAt"))

        name = d.pop("name")

        owner = d.pop("owner")

        def _parse_prefix(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        prefix = _parse_prefix(d.pop("prefix"))

        def _parse_rotated_from_id(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        rotated_from_id = _parse_rotated_from_id(d.pop("rotatedFromId"))

        def _parse_service_account_id(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        service_account_id = _parse_service_account_id(d.pop("serviceAccountId"))

        status = ApiKeyStatus(d.pop("status"))

        api_key = cls(
            budget=budget,
            created_at=created_at,
            created_by=created_by,
            expires_at=expires_at,
            id=id,
            last4=last4,
            last_used_at=last_used_at,
            name=name,
            owner=owner,
            prefix=prefix,
            rotated_from_id=rotated_from_id,
            service_account_id=service_account_id,
            status=status,
        )

        api_key.additional_properties = d
        return api_key

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
