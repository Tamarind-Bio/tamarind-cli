from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="RecommendationSequenceInput")


@_attrs_define
class RecommendationSequenceInput:
    """
    Attributes:
        sequence (str): One protein, DNA or RNA chain, as residue letters (`ACDEFGHIKLMNPQRSTVWYXBZUO`, in either case).
            `*`, `-` and `.` are allowed and whitespace is ignored. Any other character, or only those marks, is 422.
        ccd (None | Unset):
        id (None | str | Unset): Optional label, used to point at this input in error messages.
        role (None | str | Unset): Its part in the complex, in a word — e.g. `heavy`, `light`, `antigen`, `nanobody`,
            `target`, `enzyme` or `ligand`. Free text rather than a fixed list. Optional, and worth setting: it is what
            makes a request antibody-antigen rather than a guess, and it sharpens the benchmark match.
        smiles (None | Unset):
    """

    sequence: str
    ccd: None | Unset = UNSET
    id: None | str | Unset = UNSET
    role: None | str | Unset = UNSET
    smiles: None | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        sequence = self.sequence

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

        smiles = self.smiles

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "sequence": sequence,
            }
        )
        if ccd is not UNSET:
            field_dict["ccd"] = ccd
        if id is not UNSET:
            field_dict["id"] = id
        if role is not UNSET:
            field_dict["role"] = role
        if smiles is not UNSET:
            field_dict["smiles"] = smiles

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        sequence = d.pop("sequence")

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

        smiles = d.pop("smiles", UNSET)

        recommendation_sequence_input = cls(
            sequence=sequence,
            ccd=ccd,
            id=id,
            role=role,
            smiles=smiles,
        )

        return recommendation_sequence_input
