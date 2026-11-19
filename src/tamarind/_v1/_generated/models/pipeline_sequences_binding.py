from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.pipeline_sequences_binding_chain_mapping_type_0 import (
        PipelineSequencesBindingChainMappingType0,
    )
    from ..models.pipeline_sequences_binding_residues_by_chain_type_0 import (
        PipelineSequencesBindingResiduesByChainType0,
    )


T = TypeVar("T", bound="PipelineSequencesBinding")


@_attrs_define
class PipelineSequencesBinding:
    """
    Attributes:
        sequences (list[str]): Raw protein or nucleic-acid sequences to make a group from.
        chain_mapping (None | PipelineSequencesBindingChainMappingType0 | Unset): Optional; defaults to identity.
            referenceChain -> yourChain — only needed for an existing template whose reference chain IDs differ from your
            molecule's (for an inline pipeline your molecule IS the reference, so omit it).
        name (None | str | Unset): Name for the group created from raw values (auto if omitted).
        residues_by_chain (None | PipelineSequencesBindingResiduesByChainType0 | Unset): Residue selection for this
            input, in ONE of two shapes (auto-detected by the value: a reference chain maps to a range STRING => SIMPLE; a
            tool node id maps to a per-field OBJECT => ADVANCED):
            - SIMPLE fan-out: `{ referenceChain -> ranges }` (e.g. `{"A": "1-76"}`). ONE selection applied to every residue
            field this input feeds. Used when the template maker turned on 'Simplified residue selection'.
            - ADVANCED per-field: `{ toolNodeId -> { field -> { referenceChain -> ranges } } }` — pick residues
            independently per (tool node, field) that this input feeds; two settings on the same chain can differ. Advanced
            is the DEFAULT for newly created templates. Picks under each binding are merged across bindings into one map.
            Each range value is a string of space/comma-separated residue numbers and inclusive ranges, e.g. `"1-76"` or
            `"42 43 44 58 59"` or `"10-20,45,60-64"`.
    """

    sequences: list[str]
    chain_mapping: None | PipelineSequencesBindingChainMappingType0 | Unset = UNSET
    name: None | str | Unset = UNSET
    residues_by_chain: None | PipelineSequencesBindingResiduesByChainType0 | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.pipeline_sequences_binding_chain_mapping_type_0 import (
            PipelineSequencesBindingChainMappingType0,
        )
        from ..models.pipeline_sequences_binding_residues_by_chain_type_0 import (
            PipelineSequencesBindingResiduesByChainType0,
        )

        sequences = self.sequences

        chain_mapping: dict[str, Any] | None | Unset
        if isinstance(self.chain_mapping, Unset):
            chain_mapping = UNSET
        elif isinstance(self.chain_mapping, PipelineSequencesBindingChainMappingType0):
            chain_mapping = self.chain_mapping.to_dict()
        else:
            chain_mapping = self.chain_mapping

        name: None | str | Unset
        if isinstance(self.name, Unset):
            name = UNSET
        else:
            name = self.name

        residues_by_chain: dict[str, Any] | None | Unset
        if isinstance(self.residues_by_chain, Unset):
            residues_by_chain = UNSET
        elif isinstance(self.residues_by_chain, PipelineSequencesBindingResiduesByChainType0):
            residues_by_chain = self.residues_by_chain.to_dict()
        else:
            residues_by_chain = self.residues_by_chain

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "sequences": sequences,
            }
        )
        if chain_mapping is not UNSET:
            field_dict["chainMapping"] = chain_mapping
        if name is not UNSET:
            field_dict["name"] = name
        if residues_by_chain is not UNSET:
            field_dict["residuesByChain"] = residues_by_chain

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.pipeline_sequences_binding_chain_mapping_type_0 import (
            PipelineSequencesBindingChainMappingType0,
        )
        from ..models.pipeline_sequences_binding_residues_by_chain_type_0 import (
            PipelineSequencesBindingResiduesByChainType0,
        )

        d = dict(src_dict)
        sequences = cast(list[str], d.pop("sequences"))

        def _parse_chain_mapping(
            data: object,
        ) -> None | PipelineSequencesBindingChainMappingType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                chain_mapping_type_0 = PipelineSequencesBindingChainMappingType0.from_dict(data)

                return chain_mapping_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | PipelineSequencesBindingChainMappingType0 | Unset, data)

        chain_mapping = _parse_chain_mapping(d.pop("chainMapping", UNSET))

        def _parse_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        name = _parse_name(d.pop("name", UNSET))

        def _parse_residues_by_chain(
            data: object,
        ) -> None | PipelineSequencesBindingResiduesByChainType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                residues_by_chain_type_0 = PipelineSequencesBindingResiduesByChainType0.from_dict(
                    data
                )

                return residues_by_chain_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | PipelineSequencesBindingResiduesByChainType0 | Unset, data)

        residues_by_chain = _parse_residues_by_chain(d.pop("residuesByChain", UNSET))

        pipeline_sequences_binding = cls(
            sequences=sequences,
            chain_mapping=chain_mapping,
            name=name,
            residues_by_chain=residues_by_chain,
        )

        return pipeline_sequences_binding
