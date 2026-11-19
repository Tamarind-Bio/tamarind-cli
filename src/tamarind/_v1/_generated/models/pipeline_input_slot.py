from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.molecule_class import MoleculeClass
from ..models.pipeline_flow import PipelineFlow

if TYPE_CHECKING:
    from ..models.pipeline_input_slot_chainlabels import PipelineInputSlotChainlabels
    from ..models.residue_field import ResidueField


T = TypeVar("T", bound="PipelineInputSlot")


@_attrs_define
class PipelineInputSlot:
    """
    Attributes:
        chain_labels (PipelineInputSlotChainlabels):
        chains (list[str]):
        flow (PipelineFlow):
        label (None | str):
        molecule_type (MoleculeClass):
        node (str): The stable input-node id you bind to.
        requires_structure (bool):
        residue_fields (list[ResidueField]):
    """

    chain_labels: PipelineInputSlotChainlabels
    chains: list[str]
    flow: PipelineFlow
    label: None | str
    molecule_type: MoleculeClass
    node: str
    requires_structure: bool
    residue_fields: list[ResidueField]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        chain_labels = self.chain_labels.to_dict()

        chains = self.chains

        flow = self.flow.value

        label: None | str
        label = self.label

        molecule_type = self.molecule_type.value

        node = self.node

        requires_structure = self.requires_structure

        residue_fields = []
        for residue_fields_item_data in self.residue_fields:
            residue_fields_item = residue_fields_item_data.to_dict()
            residue_fields.append(residue_fields_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "chainLabels": chain_labels,
                "chains": chains,
                "flow": flow,
                "label": label,
                "moleculeType": molecule_type,
                "node": node,
                "requiresStructure": requires_structure,
                "residueFields": residue_fields,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.pipeline_input_slot_chainlabels import PipelineInputSlotChainlabels
        from ..models.residue_field import ResidueField

        d = dict(src_dict)
        chain_labels = PipelineInputSlotChainlabels.from_dict(d.pop("chainLabels"))

        chains = cast(list[str], d.pop("chains"))

        flow = PipelineFlow(d.pop("flow"))

        def _parse_label(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        label = _parse_label(d.pop("label"))

        molecule_type = MoleculeClass(d.pop("moleculeType"))

        node = d.pop("node")

        requires_structure = d.pop("requiresStructure")

        residue_fields = []
        _residue_fields = d.pop("residueFields")
        for residue_fields_item_data in _residue_fields:
            residue_fields_item = ResidueField.from_dict(residue_fields_item_data)

            residue_fields.append(residue_fields_item)

        pipeline_input_slot = cls(
            chain_labels=chain_labels,
            chains=chains,
            flow=flow,
            label=label,
            molecule_type=molecule_type,
            node=node,
            requires_structure=requires_structure,
            residue_fields=residue_fields,
        )

        pipeline_input_slot.additional_properties = d
        return pipeline_input_slot

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
