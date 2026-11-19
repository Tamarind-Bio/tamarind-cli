from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

if TYPE_CHECKING:
    from ..models.pipeline_input_slot import PipelineInputSlot
    from ..models.pipeline_ir import PipelineIR
    from ..models.pipeline_template_version_summary import PipelineTemplateVersionSummary


T = TypeVar("T", bound="PipelineTemplate")


@_attrs_define
class PipelineTemplate:
    """
    Attributes:
        created_at (datetime.datetime):
        description (None | str):
        id (str):
        inputs (list[PipelineInputSlot]):
        is_published (bool):
        name (str):
        pipeline (PipelineIR): A pipeline IR document. Full schema (typed, versioned):
            https://tamarind.bio/schemas/pipeline-v1.json
        published_version (None | str): The published version handle e.g. 'v1' (null if none).
        simplified_residues (bool): Which residue-selection shape to send in each binding's `residuesByChain`. True: one
            selection per binding, `{chain: ranges}`, fanned to every residue field it feeds. False (the default for new
            templates): per tool node and field, `{toolNodeId: {field: {chain: ranges}}}`. There is no top-level
            `residuesByChain`.
        updated_at (datetime.datetime):
        version (None | str): The version handle e.g. 'v1' (null if never saved).
        versions (list[PipelineTemplateVersionSummary]): All saved versions, oldest first.
    """

    created_at: datetime.datetime
    description: None | str
    id: str
    inputs: list[PipelineInputSlot]
    is_published: bool
    name: str
    pipeline: PipelineIR
    published_version: None | str
    simplified_residues: bool
    updated_at: datetime.datetime
    version: None | str
    versions: list[PipelineTemplateVersionSummary]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        created_at = self.created_at.isoformat()

        description: None | str
        description = self.description

        id = self.id

        inputs = []
        for inputs_item_data in self.inputs:
            inputs_item = inputs_item_data.to_dict()
            inputs.append(inputs_item)

        is_published = self.is_published

        name = self.name

        pipeline = self.pipeline.to_dict()

        published_version: None | str
        published_version = self.published_version

        simplified_residues = self.simplified_residues

        updated_at = self.updated_at.isoformat()

        version: None | str
        version = self.version

        versions = []
        for versions_item_data in self.versions:
            versions_item = versions_item_data.to_dict()
            versions.append(versions_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "createdAt": created_at,
                "description": description,
                "id": id,
                "inputs": inputs,
                "isPublished": is_published,
                "name": name,
                "pipeline": pipeline,
                "publishedVersion": published_version,
                "simplifiedResidues": simplified_residues,
                "updatedAt": updated_at,
                "version": version,
                "versions": versions,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.pipeline_input_slot import PipelineInputSlot
        from ..models.pipeline_ir import PipelineIR
        from ..models.pipeline_template_version_summary import PipelineTemplateVersionSummary

        d = dict(src_dict)
        created_at = isoparse(d.pop("createdAt"))

        def _parse_description(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        description = _parse_description(d.pop("description"))

        id = d.pop("id")

        inputs = []
        _inputs = d.pop("inputs")
        for inputs_item_data in _inputs:
            inputs_item = PipelineInputSlot.from_dict(inputs_item_data)

            inputs.append(inputs_item)

        is_published = d.pop("isPublished")

        name = d.pop("name")

        pipeline = PipelineIR.from_dict(d.pop("pipeline"))

        def _parse_published_version(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        published_version = _parse_published_version(d.pop("publishedVersion"))

        simplified_residues = d.pop("simplifiedResidues")

        updated_at = isoparse(d.pop("updatedAt"))

        def _parse_version(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        version = _parse_version(d.pop("version"))

        versions = []
        _versions = d.pop("versions")
        for versions_item_data in _versions:
            versions_item = PipelineTemplateVersionSummary.from_dict(versions_item_data)

            versions.append(versions_item)

        pipeline_template = cls(
            created_at=created_at,
            description=description,
            id=id,
            inputs=inputs,
            is_published=is_published,
            name=name,
            pipeline=pipeline,
            published_version=published_version,
            simplified_residues=simplified_residues,
            updated_at=updated_at,
            version=version,
            versions=versions,
        )

        pipeline_template.additional_properties = d
        return pipeline_template

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
