from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.molecule_chain_info import MoleculeChainInfo


T = TypeVar("T", bound="MoleculeChainmapping")


@_attrs_define
class MoleculeChainmapping:
    """Per-chain detail, keyed by the same chain ids as `entity`: its `type` and any `tags`."""

    additional_properties: dict[str, MoleculeChainInfo] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:

        field_dict: dict[str, Any] = {}
        for prop_name, prop in self.additional_properties.items():
            field_dict[prop_name] = prop.to_dict()

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.molecule_chain_info import MoleculeChainInfo

        d = dict(src_dict)
        molecule_chainmapping = cls()

        additional_properties = {}
        for prop_name, prop_dict in d.items():
            additional_property = MoleculeChainInfo.from_dict(prop_dict)

            additional_properties[prop_name] = additional_property

        molecule_chainmapping.additional_properties = additional_properties
        return molecule_chainmapping

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> MoleculeChainInfo:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: MoleculeChainInfo) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
