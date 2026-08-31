from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.public_node_run_molecule_scores import PublicNodeRunMoleculeScores


T = TypeVar("T", bound="PublicNodeRunMolecule")


@_attrs_define
class PublicNodeRunMolecule:
    """One molecule a node run produced.

    Read from the node run's passing outputs directly, NOT from `PublicNodeRun.outputGroup` — which
    is why this exists. A node run's `outputGroup` is the group the node minted, and a node that enriches its
    inputs in place (scoring, structure prediction) mints none: its molecules never moved, so they
    stay in the group they came from and `outputGroup` is correctly null. A filter node has no group
    either — its survivors exist only as outputs. Reading results by group therefore reports
    "produced nothing" for exactly the node runs that produced the most interesting thing.

        Attributes:
            has_structure (bool):
            id (str):
            name (str):
            scores (PublicNodeRunMoleculeScores): Per-tool scores keyed by tool.
            sequence (None | str): The ':'-joined chain sequences.
            type_ (None | str):
    """

    has_structure: bool
    id: str
    name: str
    scores: PublicNodeRunMoleculeScores
    sequence: None | str
    type_: None | str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        has_structure = self.has_structure

        id = self.id

        name = self.name

        scores = self.scores.to_dict()

        sequence: None | str
        sequence = self.sequence

        type_: None | str
        type_ = self.type_

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "hasStructure": has_structure,
                "id": id,
                "name": name,
                "scores": scores,
                "sequence": sequence,
                "type": type_,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.public_node_run_molecule_scores import PublicNodeRunMoleculeScores

        d = dict(src_dict)
        has_structure = d.pop("hasStructure")

        id = d.pop("id")

        name = d.pop("name")

        scores = PublicNodeRunMoleculeScores.from_dict(d.pop("scores"))

        def _parse_sequence(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        sequence = _parse_sequence(d.pop("sequence"))

        def _parse_type_(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        type_ = _parse_type_(d.pop("type"))

        public_node_run_molecule = cls(
            has_structure=has_structure,
            id=id,
            name=name,
            scores=scores,
            sequence=sequence,
            type_=type_,
        )

        public_node_run_molecule.additional_properties = d
        return public_node_run_molecule

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
