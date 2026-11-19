from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.pipeline_ir import PipelineIR


T = TypeVar("T", bound="CreatePipelineTemplateRequest")


@_attrs_define
class CreatePipelineTemplateRequest:
    """
    Example:
        {'description': 'AF2 + ProteinMPNN', 'name': 'binder-design', 'pipeline': {'nodes': {'af2': {'inputs':
            {'sequence': [{'node': 'target'}]}, 'kind': 'tool', 'tool': 'tamarind://alphafold'}, 'target': {'flow':
            'molecule', 'kind': 'user_input', 'metadata': {'defaultGroup': '3f8a1c2e-5b7d-4e9f-a1b2-c3d4e5f6a7b8'},
            'molecule_type': 'protein'}}, 'schema_version': '1.0'}}

    Attributes:
        name (str):
        pipeline (PipelineIR): A pipeline IR document. Full schema (typed, versioned):
            https://tamarind.bio/schemas/pipeline-v1.json
        description (None | str | Unset):
    """

    name: str
    pipeline: PipelineIR
    description: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        pipeline = self.pipeline.to_dict()

        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "name": name,
                "pipeline": pipeline,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.pipeline_ir import PipelineIR

        d = dict(src_dict)
        name = d.pop("name")

        pipeline = PipelineIR.from_dict(d.pop("pipeline"))

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        create_pipeline_template_request = cls(
            name=name,
            pipeline=pipeline,
            description=description,
        )

        return create_pipeline_template_request
