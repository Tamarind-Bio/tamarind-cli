from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.molecule_file_entry import MoleculeFileEntry


T = TypeVar("T", bound="MoleculeFiles")


@_attrs_define
class MoleculeFiles:
    """Structures and other artifacts, keyed by the PRODUCER that made them — a tool name (`alphafold`, `protenix`) or
    `user` for your own uploads. Each entry carries a short-lived signed `downloadUrl`. This is where `hasStructure:
    true` resolves to an actual file. It can be EMPTY on the org-wide listing even for a molecule that has a structure:
    with no group to relabel a chain-bearing file's chains against, those files are served without a link and dropped —
    pass `group`, or read the molecule by id.

    """

    additional_properties: dict[str, list[MoleculeFileEntry]] = _attrs_field(
        init=False, factory=dict
    )

    def to_dict(self) -> dict[str, Any]:

        field_dict: dict[str, Any] = {}
        for prop_name, prop in self.additional_properties.items():
            field_dict[prop_name] = []
            for additional_property_item_data in prop:
                additional_property_item = additional_property_item_data.to_dict()
                field_dict[prop_name].append(additional_property_item)

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.molecule_file_entry import MoleculeFileEntry

        d = dict(src_dict)
        molecule_files = cls()

        additional_properties = {}
        for prop_name, prop_dict in d.items():
            additional_property = []
            _additional_property = prop_dict
            for additional_property_item_data in _additional_property:
                additional_property_item = MoleculeFileEntry.from_dict(
                    additional_property_item_data
                )

                additional_property.append(additional_property_item)

            additional_properties[prop_name] = additional_property

        molecule_files.additional_properties = additional_properties
        return molecule_files

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> list[MoleculeFileEntry]:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: list[MoleculeFileEntry]) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
