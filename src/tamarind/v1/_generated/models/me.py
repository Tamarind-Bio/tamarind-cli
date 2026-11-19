from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.me_tier import MeTier

if TYPE_CHECKING:
    from ..models.budget import Budget
    from ..models.me_credential import MeCredential
    from ..models.me_limits import MeLimits
    from ..models.me_organization_type_0 import MeOrganizationType0
    from ..models.me_user import MeUser


T = TypeVar("T", bound="Me")


@_attrs_define
class Me:
    """
    Attributes:
        as_of (datetime.datetime): When this answer was made. Organization and team totals can trail it by up to about
            30 minutes.
        budgets (list[Budget]): Every budget the submit checks hold you to that this credential may see. Your own member
            budget whenever one applies; the organization's, teams' and models' only for a service account, or when your
            organization lets members see budgets. Only budgets with a limit are listed, so `limit` and `remaining` are
            numbers. The lowest `remaining` binds.
        credential (MeCredential):
        limits (MeLimits):
        organization (MeOrganizationType0 | None): Null for a personal account.
        tier (MeTier):
        user (MeUser):
    """

    as_of: datetime.datetime
    budgets: list[Budget]
    credential: MeCredential
    limits: MeLimits
    organization: MeOrganizationType0 | None
    tier: MeTier
    user: MeUser
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.me_organization_type_0 import MeOrganizationType0

        as_of = self.as_of.isoformat()

        budgets = []
        for budgets_item_data in self.budgets:
            budgets_item = budgets_item_data.to_dict()
            budgets.append(budgets_item)

        credential = self.credential.to_dict()

        limits = self.limits.to_dict()

        organization: dict[str, Any] | None
        if isinstance(self.organization, MeOrganizationType0):
            organization = self.organization.to_dict()
        else:
            organization = self.organization

        tier = self.tier.value

        user = self.user.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "asOf": as_of,
                "budgets": budgets,
                "credential": credential,
                "limits": limits,
                "organization": organization,
                "tier": tier,
                "user": user,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.budget import Budget
        from ..models.me_credential import MeCredential
        from ..models.me_limits import MeLimits
        from ..models.me_organization_type_0 import MeOrganizationType0
        from ..models.me_user import MeUser

        d = dict(src_dict)
        as_of = isoparse(d.pop("asOf"))

        budgets = []
        _budgets = d.pop("budgets")
        for budgets_item_data in _budgets:
            budgets_item = Budget.from_dict(budgets_item_data)

            budgets.append(budgets_item)

        credential = MeCredential.from_dict(d.pop("credential"))

        limits = MeLimits.from_dict(d.pop("limits"))

        def _parse_organization(data: object) -> MeOrganizationType0 | None:
            if data is None:
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                organization_type_0 = MeOrganizationType0.from_dict(data)

                return organization_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(MeOrganizationType0 | None, data)

        organization = _parse_organization(d.pop("organization"))

        tier = MeTier(d.pop("tier"))

        user = MeUser.from_dict(d.pop("user"))

        me = cls(
            as_of=as_of,
            budgets=budgets,
            credential=credential,
            limits=limits,
            organization=organization,
            tier=tier,
            user=user,
        )

        me.additional_properties = d
        return me

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
