from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="AssayOrderCostType0")


@_attrs_define
class AssayOrderCostType0:
    """The price on file for the order, once there is one. Null before that.

    Attributes:
        amount_usd (float):
        invoice_url (None | str): The order's invoice, once one is issued.
        is_estimate (bool): True when the figure is an estimate, not the lab's quote.
    """

    amount_usd: float
    invoice_url: None | str
    is_estimate: bool
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        amount_usd = self.amount_usd

        invoice_url: None | str
        invoice_url = self.invoice_url

        is_estimate = self.is_estimate

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "amountUsd": amount_usd,
                "invoiceUrl": invoice_url,
                "isEstimate": is_estimate,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        amount_usd = d.pop("amountUsd")

        def _parse_invoice_url(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        invoice_url = _parse_invoice_url(d.pop("invoiceUrl"))

        is_estimate = d.pop("isEstimate")

        assay_order_cost_type_0 = cls(
            amount_usd=amount_usd,
            invoice_url=invoice_url,
            is_estimate=is_estimate,
        )

        assay_order_cost_type_0.additional_properties = d
        return assay_order_cost_type_0

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
