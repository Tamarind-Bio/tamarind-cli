from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.pipeline_file_binding import PipelineFileBinding
    from ..models.pipeline_group_binding import PipelineGroupBinding
    from ..models.pipeline_pdbs_binding import PipelinePdbsBinding
    from ..models.pipeline_sdfs_binding import PipelineSdfsBinding
    from ..models.pipeline_sequences_binding import PipelineSequencesBinding
    from ..models.pipeline_smiles_binding import PipelineSmilesBinding


T = TypeVar("T", bound="SubmitPipelineGraphRequestBindings")


@_attrs_define
class SubmitPipelineGraphRequestBindings:
    """One binding per input slot, keyed by the slot's input-node id. Bindings may be defined as an array of sequences,
    smiles, or sdf/pdb files (uploaded using `POST /files`), or an existing molecule group id (created using
    /molecules/groups below).

    """

    additional_properties: dict[
        str,
        PipelineFileBinding
        | PipelineGroupBinding
        | PipelinePdbsBinding
        | PipelineSdfsBinding
        | PipelineSequencesBinding
        | PipelineSmilesBinding,
    ] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.pipeline_group_binding import PipelineGroupBinding
        from ..models.pipeline_pdbs_binding import PipelinePdbsBinding
        from ..models.pipeline_sdfs_binding import PipelineSdfsBinding
        from ..models.pipeline_sequences_binding import PipelineSequencesBinding
        from ..models.pipeline_smiles_binding import PipelineSmilesBinding

        field_dict: dict[str, Any] = {}
        for prop_name, prop in self.additional_properties.items():
            if isinstance(prop, PipelineGroupBinding):
                field_dict[prop_name] = prop.to_dict()
            elif isinstance(prop, PipelineSequencesBinding):
                field_dict[prop_name] = prop.to_dict()
            elif isinstance(prop, PipelineSmilesBinding):
                field_dict[prop_name] = prop.to_dict()
            elif isinstance(prop, PipelinePdbsBinding):
                field_dict[prop_name] = prop.to_dict()
            elif isinstance(prop, PipelineSdfsBinding):
                field_dict[prop_name] = prop.to_dict()
            else:
                field_dict[prop_name] = prop.to_dict()

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.pipeline_file_binding import PipelineFileBinding
        from ..models.pipeline_group_binding import PipelineGroupBinding
        from ..models.pipeline_pdbs_binding import PipelinePdbsBinding
        from ..models.pipeline_sdfs_binding import PipelineSdfsBinding
        from ..models.pipeline_sequences_binding import PipelineSequencesBinding
        from ..models.pipeline_smiles_binding import PipelineSmilesBinding

        d = dict(src_dict)
        submit_pipeline_graph_request_bindings = cls()

        additional_properties = {}
        for prop_name, prop_dict in d.items():

            def _parse_additional_property(
                data: object,
            ) -> (
                PipelineFileBinding
                | PipelineGroupBinding
                | PipelinePdbsBinding
                | PipelineSdfsBinding
                | PipelineSequencesBinding
                | PipelineSmilesBinding
            ):
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_pipeline_molecule_binding_type_0 = (
                        PipelineGroupBinding.from_dict(data)
                    )

                    return componentsschemas_pipeline_molecule_binding_type_0
                except (TypeError, ValueError, AttributeError, KeyError):
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_pipeline_molecule_binding_type_1 = (
                        PipelineSequencesBinding.from_dict(data)
                    )

                    return componentsschemas_pipeline_molecule_binding_type_1
                except (TypeError, ValueError, AttributeError, KeyError):
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_pipeline_molecule_binding_type_2 = (
                        PipelineSmilesBinding.from_dict(data)
                    )

                    return componentsschemas_pipeline_molecule_binding_type_2
                except (TypeError, ValueError, AttributeError, KeyError):
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_pipeline_molecule_binding_type_3 = (
                        PipelinePdbsBinding.from_dict(data)
                    )

                    return componentsschemas_pipeline_molecule_binding_type_3
                except (TypeError, ValueError, AttributeError, KeyError):
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_pipeline_molecule_binding_type_4 = (
                        PipelineSdfsBinding.from_dict(data)
                    )

                    return componentsschemas_pipeline_molecule_binding_type_4
                except (TypeError, ValueError, AttributeError, KeyError):
                    pass
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_pipeline_binding_type_1 = PipelineFileBinding.from_dict(data)

                return componentsschemas_pipeline_binding_type_1

            additional_property = _parse_additional_property(prop_dict)

            additional_properties[prop_name] = additional_property

        submit_pipeline_graph_request_bindings.additional_properties = additional_properties
        return submit_pipeline_graph_request_bindings

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(
        self, key: str
    ) -> (
        PipelineFileBinding
        | PipelineGroupBinding
        | PipelinePdbsBinding
        | PipelineSdfsBinding
        | PipelineSequencesBinding
        | PipelineSmilesBinding
    ):
        return self.additional_properties[key]

    def __setitem__(
        self,
        key: str,
        value: PipelineFileBinding
        | PipelineGroupBinding
        | PipelinePdbsBinding
        | PipelineSdfsBinding
        | PipelineSequencesBinding
        | PipelineSmilesBinding,
    ) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
