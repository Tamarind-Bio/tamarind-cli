from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="MoleculeChainInfo")


@_attrs_define
class MoleculeChainInfo:
    """Type + role tags of one chain in a molecule's `entity`, keyed by the same
    chain id — so a reader tells a protein sequence from a SMILES, and sees
    heavy/light/lead roles, without loading the group's schema.

        Attributes:
            tags (list[str]):
            type_ (str):
    """

    tags: list[str]
    type_: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        tags = self.tags

        type_ = self.type_

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "tags": tags,
                "type": type_,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        tags = cast(list[str], d.pop("tags"))

        type_ = d.pop("type")

        molecule_chain_info = cls(
            tags=tags,
            type_=type_,
        )

        molecule_chain_info.additional_properties = d
        return molecule_chain_info

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
