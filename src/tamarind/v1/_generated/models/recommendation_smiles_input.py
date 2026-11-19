from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="RecommendationSmilesInput")


@_attrs_define
class RecommendationSmilesInput:
    """
    Attributes:
        smiles (str): A ligand, as SMILES.
        ccd (None | Unset):
        id (None | str | Unset): Optional label, used to point at this input in error messages.
        role (None | str | Unset): Its part in the complex, in a word — e.g. `heavy`, `light`, `antigen`, `nanobody`,
            `target`, `enzyme` or `ligand`. Free text rather than a fixed list. Optional, and worth setting: it is what
            makes a request antibody-antigen rather than a guess, and it sharpens the benchmark match.
        sequence (None | Unset):
    """

    smiles: str
    ccd: None | Unset = UNSET
    id: None | str | Unset = UNSET
    role: None | str | Unset = UNSET
    sequence: None | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        smiles = self.smiles

        ccd = self.ccd

        id: None | str | Unset
        if isinstance(self.id, Unset):
            id = UNSET
        else:
            id = self.id

        role: None | str | Unset
        if isinstance(self.role, Unset):
            role = UNSET
        else:
            role = self.role

        sequence = self.sequence

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "smiles": smiles,
            }
        )
        if ccd is not UNSET:
            field_dict["ccd"] = ccd
        if id is not UNSET:
            field_dict["id"] = id
        if role is not UNSET:
            field_dict["role"] = role
        if sequence is not UNSET:
            field_dict["sequence"] = sequence

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        smiles = d.pop("smiles")

        ccd = d.pop("ccd", UNSET)

        def _parse_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        id = _parse_id(d.pop("id", UNSET))

        def _parse_role(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        role = _parse_role(d.pop("role", UNSET))

        sequence = d.pop("sequence", UNSET)

        recommendation_smiles_input = cls(
            smiles=smiles,
            ccd=ccd,
            id=id,
            role=role,
            sequence=sequence,
        )

        return recommendation_smiles_input
