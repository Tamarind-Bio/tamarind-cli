from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.assay_order_status import AssayOrderStatus

if TYPE_CHECKING:
    from ..models.assay_order_assays_item import AssayOrderAssaysItem
    from ..models.assay_order_cost_type_0 import AssayOrderCostType0


T = TypeVar("T", bound="AssayOrder")


@_attrs_define
class AssayOrder:
    """An assay order. You get one back when you submit, list or cancel orders.

    Attributes:
        assay_type (None | str): Which assay the order is for. Null for some older orders placed in the web app.
        assays (list[AssayOrderAssaysItem]):
        cancellable (bool): Whether `cancelAssay` would cancel the order now, by its lab's rule for the order's status.
            False when that lab isn't set up on this deployment (or its settings can't be read), since the cancel would be
            refused then.
        cost (AssayOrderCostType0 | None): The price on file for the order, once there is one. Null before that.
        created_at (datetime.datetime):
        id (str):
        name (None | str):
        notes (None | str):
        provider (None | str): The lab running the order, for example adaptyv, ginkgo, aalpha or genscript. More labs
            may be added, so don't assume these are the only values.
        provider_name (None | str):
        results_available (bool): True once the lab has delivered results and `GET /assays/{assayId}/results` has files
            for you. It stays true from then on, even if the order's `status` changes later, so check this field instead of
            waiting for `status` to be `completed`.
        sequence_count (int | None):
        status (AssayOrderStatus): `unknown` when the order is in a state this API has no name for yet.
        updated_at (datetime.datetime | None):
    """

    assay_type: None | str
    assays: list[AssayOrderAssaysItem]
    cancellable: bool
    cost: AssayOrderCostType0 | None
    created_at: datetime.datetime
    id: str
    name: None | str
    notes: None | str
    provider: None | str
    provider_name: None | str
    results_available: bool
    sequence_count: int | None
    status: AssayOrderStatus
    updated_at: datetime.datetime | None
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.assay_order_cost_type_0 import AssayOrderCostType0

        assay_type: None | str
        assay_type = self.assay_type

        assays = []
        for assays_item_data in self.assays:
            assays_item = assays_item_data.to_dict()
            assays.append(assays_item)

        cancellable = self.cancellable

        cost: dict[str, Any] | None
        if isinstance(self.cost, AssayOrderCostType0):
            cost = self.cost.to_dict()
        else:
            cost = self.cost

        created_at = self.created_at.isoformat()

        id = self.id

        name: None | str
        name = self.name

        notes: None | str
        notes = self.notes

        provider: None | str
        provider = self.provider

        provider_name: None | str
        provider_name = self.provider_name

        results_available = self.results_available

        sequence_count: int | None
        sequence_count = self.sequence_count

        status = self.status.value

        updated_at: None | str
        if isinstance(self.updated_at, datetime.datetime):
            updated_at = self.updated_at.isoformat()
        else:
            updated_at = self.updated_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "assayType": assay_type,
                "assays": assays,
                "cancellable": cancellable,
                "cost": cost,
                "createdAt": created_at,
                "id": id,
                "name": name,
                "notes": notes,
                "provider": provider,
                "providerName": provider_name,
                "resultsAvailable": results_available,
                "sequenceCount": sequence_count,
                "status": status,
                "updatedAt": updated_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.assay_order_assays_item import AssayOrderAssaysItem
        from ..models.assay_order_cost_type_0 import AssayOrderCostType0

        d = dict(src_dict)

        def _parse_assay_type(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        assay_type = _parse_assay_type(d.pop("assayType"))

        assays = []
        _assays = d.pop("assays")
        for assays_item_data in _assays:
            assays_item = AssayOrderAssaysItem.from_dict(assays_item_data)

            assays.append(assays_item)

        cancellable = d.pop("cancellable")

        def _parse_cost(data: object) -> AssayOrderCostType0 | None:
            if data is None:
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                cost_type_0 = AssayOrderCostType0.from_dict(data)

                return cost_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(AssayOrderCostType0 | None, data)

        cost = _parse_cost(d.pop("cost"))

        created_at = isoparse(d.pop("createdAt"))

        id = d.pop("id")

        def _parse_name(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        name = _parse_name(d.pop("name"))

        def _parse_notes(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        notes = _parse_notes(d.pop("notes"))

        def _parse_provider(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        provider = _parse_provider(d.pop("provider"))

        def _parse_provider_name(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        provider_name = _parse_provider_name(d.pop("providerName"))

        results_available = d.pop("resultsAvailable")

        def _parse_sequence_count(data: object) -> int | None:
            if data is None:
                return data
            return cast(int | None, data)

        sequence_count = _parse_sequence_count(d.pop("sequenceCount"))

        status = AssayOrderStatus(d.pop("status"))

        def _parse_updated_at(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                updated_at_type_0 = isoparse(data)

                return updated_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        updated_at = _parse_updated_at(d.pop("updatedAt"))

        assay_order = cls(
            assay_type=assay_type,
            assays=assays,
            cancellable=cancellable,
            cost=cost,
            created_at=created_at,
            id=id,
            name=name,
            notes=notes,
            provider=provider,
            provider_name=provider_name,
            results_available=results_available,
            sequence_count=sequence_count,
            status=status,
            updated_at=updated_at,
        )

        assay_order.additional_properties = d
        return assay_order

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
