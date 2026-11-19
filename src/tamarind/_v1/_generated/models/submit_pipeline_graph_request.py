from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..models.run_source import RunSource
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.pipeline_ir import PipelineIR
    from ..models.submit_pipeline_graph_request_bindings import SubmitPipelineGraphRequestBindings
    from ..models.submit_pipeline_graph_request_settings_type_0 import (
        SubmitPipelineGraphRequestSettingsType0,
    )


T = TypeVar("T", bound="SubmitPipelineGraphRequest")


@_attrs_define
class SubmitPipelineGraphRequest:
    """
    Attributes:
        bindings (SubmitPipelineGraphRequestBindings): One binding per input slot, keyed by the slot's input-node id.
            Bindings may be defined as an array of sequences, smiles, or sdf/pdb files (uploaded using `POST /files`), or an
            existing molecule group id (created using /molecules/groups below).
        name (str): Name for this pipeline. When `runName` is omitted, the run's JobName is derived from this (spaces
            removed, a random suffix appended for uniqueness).
        pipeline (PipelineIR): A pipeline IR document. Full schema (typed, versioned):
            https://tamarind.bio/schemas/pipeline-v1.json
        project_id (None | str | Unset): Organization project id to stamp on jobs this run creates.
        run_name (None | str | Unset): Optional explicit JobName for THIS run. Spaces are replaced with underscores;
            used verbatim otherwise (no random suffix). Omit to auto-generate a unique JobName from `name`.
        settings (None | SubmitPipelineGraphRequestSettingsType0 | Unset): Per-node settings `{nodeId: {settingKey:
            value}}`. Chain and residue selections may be supplied here alongside ordinary settings. For existing templates,
            ordinary settings must be editable. Chain labels use reference space and follow chainMapping; inline residue
            selections must agree with overlapping binding selections.
        source (None | RunSource | Unset): Run source; defaults to production. Default: RunSource.PRODUCTION.
    """

    bindings: SubmitPipelineGraphRequestBindings
    name: str
    pipeline: PipelineIR
    project_id: None | str | Unset = UNSET
    run_name: None | str | Unset = UNSET
    settings: None | SubmitPipelineGraphRequestSettingsType0 | Unset = UNSET
    source: None | RunSource | Unset = RunSource.PRODUCTION

    def to_dict(self) -> dict[str, Any]:
        from ..models.submit_pipeline_graph_request_settings_type_0 import (
            SubmitPipelineGraphRequestSettingsType0,
        )

        bindings = self.bindings.to_dict()

        name = self.name

        pipeline = self.pipeline.to_dict()

        project_id: None | str | Unset
        if isinstance(self.project_id, Unset):
            project_id = UNSET
        else:
            project_id = self.project_id

        run_name: None | str | Unset
        if isinstance(self.run_name, Unset):
            run_name = UNSET
        else:
            run_name = self.run_name

        settings: dict[str, Any] | None | Unset
        if isinstance(self.settings, Unset):
            settings = UNSET
        elif isinstance(self.settings, SubmitPipelineGraphRequestSettingsType0):
            settings = self.settings.to_dict()
        else:
            settings = self.settings

        source: None | str | Unset
        if isinstance(self.source, Unset):
            source = UNSET
        elif isinstance(self.source, RunSource):
            source = self.source.value
        else:
            source = self.source

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "bindings": bindings,
                "name": name,
                "pipeline": pipeline,
            }
        )
        if project_id is not UNSET:
            field_dict["projectId"] = project_id
        if run_name is not UNSET:
            field_dict["runName"] = run_name
        if settings is not UNSET:
            field_dict["settings"] = settings
        if source is not UNSET:
            field_dict["source"] = source

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.pipeline_ir import PipelineIR
        from ..models.submit_pipeline_graph_request_bindings import (
            SubmitPipelineGraphRequestBindings,
        )
        from ..models.submit_pipeline_graph_request_settings_type_0 import (
            SubmitPipelineGraphRequestSettingsType0,
        )

        d = dict(src_dict)
        bindings = SubmitPipelineGraphRequestBindings.from_dict(d.pop("bindings"))

        name = d.pop("name")

        pipeline = PipelineIR.from_dict(d.pop("pipeline"))

        def _parse_project_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        project_id = _parse_project_id(d.pop("projectId", UNSET))

        def _parse_run_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        run_name = _parse_run_name(d.pop("runName", UNSET))

        def _parse_settings(data: object) -> None | SubmitPipelineGraphRequestSettingsType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                settings_type_0 = SubmitPipelineGraphRequestSettingsType0.from_dict(data)

                return settings_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | SubmitPipelineGraphRequestSettingsType0 | Unset, data)

        settings = _parse_settings(d.pop("settings", UNSET))

        def _parse_source(data: object) -> None | RunSource | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                source_type_0 = RunSource(data)

                return source_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | RunSource | Unset, data)

        source = _parse_source(d.pop("source", UNSET))

        submit_pipeline_graph_request = cls(
            bindings=bindings,
            name=name,
            pipeline=pipeline,
            project_id=project_id,
            run_name=run_name,
            settings=settings,
            source=source,
        )

        return submit_pipeline_graph_request
