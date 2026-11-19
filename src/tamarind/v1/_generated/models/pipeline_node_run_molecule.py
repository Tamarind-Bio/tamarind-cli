from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.pipeline_node_run_molecule_scores import PipelineNodeRunMoleculeScores


T = TypeVar("T", bound="PipelineNodeRunMolecule")


@_attrs_define
class PipelineNodeRunMolecule:
    """One molecule a node run produced.

    Read from the node run's passing outputs directly, NOT from `PipelineNodeRun.outputGroup` — which
    is why this exists. A node run's `outputGroup` is the group the node minted, and a node that enriches its
    inputs in place (scoring, structure prediction) mints none: its molecules never moved, so they
    stay in the group they came from and `outputGroup` is correctly null. A filter node has no group
    either — its survivors exist only as outputs. Reading results by group therefore reports
    "produced nothing" for exactly the node runs that produced the most interesting thing.

        Attributes:
            has_structure (bool): Whether this molecule has a structure. The FILES are not on this shape — read them from
                `GET /molecules?nodeRunId=...&groupId=...` or `GET /molecules/{moleculeId}`, whose `files` map carries a signed
                `downloadUrl` per artifact.
            id (str): The molecule's id, the same one the `/molecules` endpoints use. `GET /molecules/{moleculeId}`
                describes this molecule in a richer shape, and `GET /molecules?nodeRunId=` this whole node run's outputs at
                once.
            molecule_type (None | str): protein, small_molecule, nucleic_acid, …
            name (str):
            scores (PipelineNodeRunMoleculeScores): Per-tool scores keyed by tool, e.g. `{"protenix": {"ipSAE_AB": 0.62,
                "pDockQ_AB": 0.41}}`. Metric names are case-sensitive. To THRESHOLD or RANK on one of these, use `GET
                /molecules?nodeRunId=` with `filter=protenix.ipSAE_AB:gte:0.5` and `sortBy=protenix.ipSAE_AB` — this endpoint
                returns them but does not filter or sort by them.
            sequence (None | str): The ':'-joined chain sequences.
    """

    has_structure: bool
    id: str
    molecule_type: None | str
    name: str
    scores: PipelineNodeRunMoleculeScores
    sequence: None | str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        has_structure = self.has_structure

        id = self.id

        molecule_type: None | str
        molecule_type = self.molecule_type

        name = self.name

        scores = self.scores.to_dict()

        sequence: None | str
        sequence = self.sequence

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "hasStructure": has_structure,
                "id": id,
                "moleculeType": molecule_type,
                "name": name,
                "scores": scores,
                "sequence": sequence,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.pipeline_node_run_molecule_scores import PipelineNodeRunMoleculeScores

        d = dict(src_dict)
        has_structure = d.pop("hasStructure")

        id = d.pop("id")

        def _parse_molecule_type(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        molecule_type = _parse_molecule_type(d.pop("moleculeType"))

        name = d.pop("name")

        scores = PipelineNodeRunMoleculeScores.from_dict(d.pop("scores"))

        def _parse_sequence(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        sequence = _parse_sequence(d.pop("sequence"))

        pipeline_node_run_molecule = cls(
            has_structure=has_structure,
            id=id,
            molecule_type=molecule_type,
            name=name,
            scores=scores,
            sequence=sequence,
        )

        pipeline_node_run_molecule.additional_properties = d
        return pipeline_node_run_molecule

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
