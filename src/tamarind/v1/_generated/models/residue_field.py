from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="ResidueField")


@_attrs_define
class ResidueField:
    """
    Attributes:
        field (str):
        multichain (bool):
        node (str):
        targets_chains (list[str]):
    """

    field: str
    multichain: bool
    node: str
    targets_chains: list[str]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        field = self.field

        multichain = self.multichain

        node = self.node

        targets_chains = self.targets_chains

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "field": field,
                "multichain": multichain,
                "node": node,
                "targetsChains": targets_chains,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        field = d.pop("field")

        multichain = d.pop("multichain")

        node = d.pop("node")

        targets_chains = cast(list[str], d.pop("targetsChains"))

        residue_field = cls(
            field=field,
            multichain=multichain,
            node=node,
            targets_chains=targets_chains,
        )

        residue_field.additional_properties = d
        return residue_field

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
