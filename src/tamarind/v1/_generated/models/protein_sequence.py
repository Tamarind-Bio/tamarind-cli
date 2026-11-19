from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="ProteinSequence")


@_attrs_define
class ProteinSequence:
    """A protein, for `modality: protein`.

    Attributes:
        sequence (str):
        name (str | Unset): At most 100 characters once trimmed.
    """

    sequence: str
    name: str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        sequence = self.sequence

        name = self.name

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "sequence": sequence,
            }
        )
        if name is not UNSET:
            field_dict["name"] = name

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        sequence = d.pop("sequence")

        name = d.pop("name", UNSET)

        protein_sequence = cls(
            sequence=sequence,
            name=name,
        )

        return protein_sequence
