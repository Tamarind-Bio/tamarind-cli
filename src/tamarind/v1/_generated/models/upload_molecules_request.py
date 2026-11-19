from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.molecule_input import MoleculeInput
    from ..models.upload_molecules_request_chainmapping import UploadMoleculesRequestChainmapping


T = TypeVar("T", bound="UploadMoleculesRequest")


@_attrs_define
class UploadMoleculesRequest:
    """The spec's `UploadRequest`.

    Attributes:
        group_id (str):
        molecules (list[MoleculeInput]):
        chain_mapping (UploadMoleculesRequestChainmapping | Unset):
    """

    group_id: str
    molecules: list[MoleculeInput]
    chain_mapping: UploadMoleculesRequestChainmapping | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        group_id = self.group_id

        molecules = []
        for molecules_item_data in self.molecules:
            molecules_item = molecules_item_data.to_dict()
            molecules.append(molecules_item)

        chain_mapping: dict[str, Any] | Unset = UNSET
        if not isinstance(self.chain_mapping, Unset):
            chain_mapping = self.chain_mapping.to_dict()

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "groupId": group_id,
                "molecules": molecules,
            }
        )
        if chain_mapping is not UNSET:
            field_dict["chainMapping"] = chain_mapping

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.molecule_input import MoleculeInput
        from ..models.upload_molecules_request_chainmapping import (
            UploadMoleculesRequestChainmapping,
        )

        d = dict(src_dict)
        group_id = d.pop("groupId")

        molecules = []
        _molecules = d.pop("molecules")
        for molecules_item_data in _molecules:
            molecules_item = MoleculeInput.from_dict(molecules_item_data)

            molecules.append(molecules_item)

        _chain_mapping = d.pop("chainMapping", UNSET)
        chain_mapping: UploadMoleculesRequestChainmapping | Unset
        if isinstance(_chain_mapping, Unset):
            chain_mapping = UNSET
        else:
            chain_mapping = UploadMoleculesRequestChainmapping.from_dict(_chain_mapping)

        upload_molecules_request = cls(
            group_id=group_id,
            molecules=molecules,
            chain_mapping=chain_mapping,
        )

        return upload_molecules_request
