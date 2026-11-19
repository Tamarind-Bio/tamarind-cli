from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.contract_terms_item import ContractTermsItem


T = TypeVar("T", bound="Contract")


@_attrs_define
class Contract:
    """
    Attributes:
        dollars_per_weighted_hour (float | None): Always null for now. The app shows the rate only behind a flag.
        terms (list[ContractTermsItem]): Every stored term, newest start first; a term with no readable start is last.
    """

    dollars_per_weighted_hour: float | None
    terms: list[ContractTermsItem]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        dollars_per_weighted_hour: float | None
        dollars_per_weighted_hour = self.dollars_per_weighted_hour

        terms = []
        for terms_item_data in self.terms:
            terms_item = terms_item_data.to_dict()
            terms.append(terms_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "dollarsPerWeightedHour": dollars_per_weighted_hour,
                "terms": terms,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.contract_terms_item import ContractTermsItem

        d = dict(src_dict)

        def _parse_dollars_per_weighted_hour(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        dollars_per_weighted_hour = _parse_dollars_per_weighted_hour(
            d.pop("dollarsPerWeightedHour")
        )

        terms = []
        _terms = d.pop("terms")
        for terms_item_data in _terms:
            terms_item = ContractTermsItem.from_dict(terms_item_data)

            terms.append(terms_item)

        contract = cls(
            dollars_per_weighted_hour=dollars_per_weighted_hour,
            terms=terms,
        )

        contract.additional_properties = d
        return contract

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
