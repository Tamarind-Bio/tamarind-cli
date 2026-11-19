from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="AssayTarget")


@_attrs_define
class AssayTarget:
    """A target to name in an order's `settings`. Labs publish different details, so only `id` and `name` are always
    present.

        Attributes:
            id (str):
            name (str):
            aliases (list[str] | Unset):
            catalog_no (str | Unset): GenScript only.
            organism (str | Unset):
            size (str | Unset): GenScript only.
            uniprot_id (str | Unset):
    """

    id: str
    name: str
    aliases: list[str] | Unset = UNSET
    catalog_no: str | Unset = UNSET
    organism: str | Unset = UNSET
    size: str | Unset = UNSET
    uniprot_id: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        name = self.name

        aliases: list[str] | Unset = UNSET
        if not isinstance(self.aliases, Unset):
            aliases = self.aliases

        catalog_no = self.catalog_no

        organism = self.organism

        size = self.size

        uniprot_id = self.uniprot_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
            }
        )
        if aliases is not UNSET:
            field_dict["aliases"] = aliases
        if catalog_no is not UNSET:
            field_dict["catalogNo"] = catalog_no
        if organism is not UNSET:
            field_dict["organism"] = organism
        if size is not UNSET:
            field_dict["size"] = size
        if uniprot_id is not UNSET:
            field_dict["uniprotId"] = uniprot_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        name = d.pop("name")

        aliases = cast(list[str], d.pop("aliases", UNSET))

        catalog_no = d.pop("catalogNo", UNSET)

        organism = d.pop("organism", UNSET)

        size = d.pop("size", UNSET)

        uniprot_id = d.pop("uniprotId", UNSET)

        assay_target = cls(
            id=id,
            name=name,
            aliases=aliases,
            catalog_no=catalog_no,
            organism=organism,
            size=size,
            uniprot_id=uniprot_id,
        )

        assay_target.additional_properties = d
        return assay_target

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
