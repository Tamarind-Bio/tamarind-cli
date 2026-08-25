from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.public_node_run_molecule import PublicNodeRunMolecule


T = TypeVar("T", bound="PublicNodeRunMoleculePage")


@_attrs_define
class PublicNodeRunMoleculePage:
    """
    Attributes:
        molecules (list[PublicNodeRunMolecule]):
        next_cursor (None | str): Pass as `cursor` for the next page.
    """

    molecules: list[PublicNodeRunMolecule]
    next_cursor: None | str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        molecules = []
        for molecules_item_data in self.molecules:
            molecules_item = molecules_item_data.to_dict()
            molecules.append(molecules_item)

        next_cursor: None | str
        next_cursor = self.next_cursor

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "molecules": molecules,
                "nextCursor": next_cursor,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.public_node_run_molecule import PublicNodeRunMolecule

        d = dict(src_dict)
        molecules = []
        _molecules = d.pop("molecules")
        for molecules_item_data in _molecules:
            molecules_item = PublicNodeRunMolecule.from_dict(molecules_item_data)

            molecules.append(molecules_item)

        def _parse_next_cursor(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        next_cursor = _parse_next_cursor(d.pop("nextCursor"))

        public_node_run_molecule_page = cls(
            molecules=molecules,
            next_cursor=next_cursor,
        )

        public_node_run_molecule_page.additional_properties = d
        return public_node_run_molecule_page

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
