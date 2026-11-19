from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define

from ..models.submit_file_batch_request_kind import SubmitFileBatchRequestKind
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.batch_source import BatchSource
    from ..models.pipeline_tool_input_type_0 import PipelineToolInputType0
    from ..models.pipeline_tool_input_type_1 import PipelineToolInputType1
    from ..models.pipeline_tool_input_type_2 import PipelineToolInputType2
    from ..models.pipeline_tool_input_type_3 import PipelineToolInputType3
    from ..models.submit_file_batch_request_shared_settings import (
        SubmitFileBatchRequestSharedSettings,
    )


T = TypeVar("T", bound="SubmitFileBatchRequest")


@_attrs_define
class SubmitFileBatchRequest:
    """
    Attributes:
        kind (SubmitFileBatchRequestKind): Always `batch` for a batch. Required, so a batch is never inferred from the
            shape of `settings`.
        source (BatchSource): Read the batch's rows from one of your files, at submit. Replaces the MCP-only `fromFile`
            handling. A problem with the file itself is 422 at the member at fault, such as `/source/file` or
            `/source/sequenceColumn`; the rows' settings are checked after the 202, like an inline batch's.
        tool (str):
        atom_count (float | Unset): Atoms of an uploaded input, when `settings` hold only its path. The estimate uses a
            default without it, and it is not checked against the file.
        binder_seq_row_count (float | Unset): Binder sequence rows of an uploaded input, when `settings` hold only its
            path. The estimate uses a default without it, and it is not checked against the file.
        csv_row_count (float | Unset): CSV rows of an uploaded input, when `settings` hold only its path. The estimate
            uses a default without it, and it is not checked against the file.
        gpu (str | Unset): Request a specific GPU type for every job. Premium only. Not built yet, so any value is 422
            at `/gpu`.
        inputs (list[list[PipelineToolInputType0 | PipelineToolInputType1 | PipelineToolInputType2 |
            PipelineToolInputType3]] | Unset): One molecule-input list per row, for tools that take them. Not built yet on a
            batch, so any value is 422 `not_supported` at `/inputs`; put the values in the rows' settings.
        low_priority (bool | Unset): Run every job at the low-priority tier, as for `submitJob`. Whether you may ask is
            checked at submit (422 `validation_failed`, with the reason at `/lowPriority`); a row whose job can't run at the
            tier is a row problem, which fails the batch after the 202. Optional. Default: False.
        max_runtime_seconds (int | Unset): Stop each job after this long. No business maximum; a number a job can't
            store is 422 `out_of_range`.
        model_id (str | Unset):
        name (str | Unset): Unique per owner, and never changes. Invalid characters are refused, not silently removed.
        project_id (str | Unset): A project you can use. One that doesn't resolve for you is never silently dropped,
            whether or not your organization requires projects. Submit and estimate answer 422 `validation_failed` with an
            `invalid_option` error at `/projectId`; validate reports a failed `project` check with that error.
        shared_settings (SubmitFileBatchRequestSharedSettings | Unset): Merged into every row. A row's own value wins.
            With them, the rows are at most 64 MiB of JSON (422 `out_of_range` at `/sharedSettings`).
        smiles_row_count (float | Unset): SMILES rows of an uploaded input, when `settings` hold only its path. The
            estimate uses a default without it, and it is not checked against the file.
        tool_lifetime_etag (str | Unset): A custom tool version's `lifetimeEtag`. If the tool was deleted and its name
            reused since, submit is 409 `tool_lifetime_changed`, and validate reports a failed `access` check with an error
            at `/toolLifetimeEtag` with the same code.
        tool_version (str | Unset):
        weighted_hours_budget (float | Unset): A budget for the whole batch. Only Premium members of an organization can
            set one, and not above the organization's hard limit when it has one (`not_supported` or `out_of_range` at this
            field). No business maximum; a number a job can't store is 422 `out_of_range`.
    """

    kind: SubmitFileBatchRequestKind
    source: BatchSource
    tool: str
    atom_count: float | Unset = UNSET
    binder_seq_row_count: float | Unset = UNSET
    csv_row_count: float | Unset = UNSET
    gpu: str | Unset = UNSET
    inputs: (
        list[
            list[
                PipelineToolInputType0
                | PipelineToolInputType1
                | PipelineToolInputType2
                | PipelineToolInputType3
            ]
        ]
        | Unset
    ) = UNSET
    low_priority: bool | Unset = False
    max_runtime_seconds: int | Unset = UNSET
    model_id: str | Unset = UNSET
    name: str | Unset = UNSET
    project_id: str | Unset = UNSET
    shared_settings: SubmitFileBatchRequestSharedSettings | Unset = UNSET
    smiles_row_count: float | Unset = UNSET
    tool_lifetime_etag: str | Unset = UNSET
    tool_version: str | Unset = UNSET
    weighted_hours_budget: float | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.pipeline_tool_input_type_0 import PipelineToolInputType0
        from ..models.pipeline_tool_input_type_1 import PipelineToolInputType1
        from ..models.pipeline_tool_input_type_2 import PipelineToolInputType2

        kind = self.kind.value

        source = self.source.to_dict()

        tool = self.tool

        atom_count = self.atom_count

        binder_seq_row_count = self.binder_seq_row_count

        csv_row_count = self.csv_row_count

        gpu = self.gpu

        inputs: list[list[dict[str, Any]]] | Unset = UNSET
        if not isinstance(self.inputs, Unset):
            inputs = []
            for inputs_item_data in self.inputs:
                inputs_item = []
                for inputs_item_item_data in inputs_item_data:
                    inputs_item_item: dict[str, Any]
                    if isinstance(inputs_item_item_data, PipelineToolInputType0):
                        inputs_item_item = inputs_item_item_data.to_dict()
                    elif isinstance(inputs_item_item_data, PipelineToolInputType1):
                        inputs_item_item = inputs_item_item_data.to_dict()
                    elif isinstance(inputs_item_item_data, PipelineToolInputType2):
                        inputs_item_item = inputs_item_item_data.to_dict()
                    else:
                        inputs_item_item = inputs_item_item_data.to_dict()

                    inputs_item.append(inputs_item_item)

                inputs.append(inputs_item)

        low_priority = self.low_priority

        max_runtime_seconds = self.max_runtime_seconds

        model_id = self.model_id

        name = self.name

        project_id = self.project_id

        shared_settings: dict[str, Any] | Unset = UNSET
        if not isinstance(self.shared_settings, Unset):
            shared_settings = self.shared_settings.to_dict()

        smiles_row_count = self.smiles_row_count

        tool_lifetime_etag = self.tool_lifetime_etag

        tool_version = self.tool_version

        weighted_hours_budget = self.weighted_hours_budget

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "kind": kind,
                "source": source,
                "tool": tool,
            }
        )
        if atom_count is not UNSET:
            field_dict["atomCount"] = atom_count
        if binder_seq_row_count is not UNSET:
            field_dict["binderSeqRowCount"] = binder_seq_row_count
        if csv_row_count is not UNSET:
            field_dict["csvRowCount"] = csv_row_count
        if gpu is not UNSET:
            field_dict["gpu"] = gpu
        if inputs is not UNSET:
            field_dict["inputs"] = inputs
        if low_priority is not UNSET:
            field_dict["lowPriority"] = low_priority
        if max_runtime_seconds is not UNSET:
            field_dict["maxRuntimeSeconds"] = max_runtime_seconds
        if model_id is not UNSET:
            field_dict["modelId"] = model_id
        if name is not UNSET:
            field_dict["name"] = name
        if project_id is not UNSET:
            field_dict["projectId"] = project_id
        if shared_settings is not UNSET:
            field_dict["sharedSettings"] = shared_settings
        if smiles_row_count is not UNSET:
            field_dict["smilesRowCount"] = smiles_row_count
        if tool_lifetime_etag is not UNSET:
            field_dict["toolLifetimeEtag"] = tool_lifetime_etag
        if tool_version is not UNSET:
            field_dict["toolVersion"] = tool_version
        if weighted_hours_budget is not UNSET:
            field_dict["weightedHoursBudget"] = weighted_hours_budget

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.batch_source import BatchSource
        from ..models.pipeline_tool_input_type_0 import PipelineToolInputType0
        from ..models.pipeline_tool_input_type_1 import PipelineToolInputType1
        from ..models.pipeline_tool_input_type_2 import PipelineToolInputType2
        from ..models.pipeline_tool_input_type_3 import PipelineToolInputType3
        from ..models.submit_file_batch_request_shared_settings import (
            SubmitFileBatchRequestSharedSettings,
        )

        d = dict(src_dict)
        kind = SubmitFileBatchRequestKind(d.pop("kind"))

        source = BatchSource.from_dict(d.pop("source"))

        tool = d.pop("tool")

        atom_count = d.pop("atomCount", UNSET)

        binder_seq_row_count = d.pop("binderSeqRowCount", UNSET)

        csv_row_count = d.pop("csvRowCount", UNSET)

        gpu = d.pop("gpu", UNSET)

        _inputs = d.pop("inputs", UNSET)
        inputs: (
            list[
                list[
                    PipelineToolInputType0
                    | PipelineToolInputType1
                    | PipelineToolInputType2
                    | PipelineToolInputType3
                ]
            ]
            | Unset
        ) = UNSET
        if _inputs is not UNSET:
            inputs = []
            for inputs_item_data in _inputs:
                inputs_item = []
                _inputs_item = inputs_item_data
                for inputs_item_item_data in _inputs_item:

                    def _parse_inputs_item_item(
                        data: object,
                    ) -> (
                        PipelineToolInputType0
                        | PipelineToolInputType1
                        | PipelineToolInputType2
                        | PipelineToolInputType3
                    ):
                        try:
                            if not isinstance(data, dict):
                                raise TypeError()
                            componentsschemas_pipeline_tool_input_type_0 = (
                                PipelineToolInputType0.from_dict(data)
                            )

                            return componentsschemas_pipeline_tool_input_type_0
                        except (TypeError, ValueError, AttributeError, KeyError):
                            pass
                        try:
                            if not isinstance(data, dict):
                                raise TypeError()
                            componentsschemas_pipeline_tool_input_type_1 = (
                                PipelineToolInputType1.from_dict(data)
                            )

                            return componentsschemas_pipeline_tool_input_type_1
                        except (TypeError, ValueError, AttributeError, KeyError):
                            pass
                        try:
                            if not isinstance(data, dict):
                                raise TypeError()
                            componentsschemas_pipeline_tool_input_type_2 = (
                                PipelineToolInputType2.from_dict(data)
                            )

                            return componentsschemas_pipeline_tool_input_type_2
                        except (TypeError, ValueError, AttributeError, KeyError):
                            pass
                        if not isinstance(data, dict):
                            raise TypeError()
                        componentsschemas_pipeline_tool_input_type_3 = (
                            PipelineToolInputType3.from_dict(data)
                        )

                        return componentsschemas_pipeline_tool_input_type_3

                    inputs_item_item = _parse_inputs_item_item(inputs_item_item_data)

                    inputs_item.append(inputs_item_item)

                inputs.append(inputs_item)

        low_priority = d.pop("lowPriority", UNSET)

        max_runtime_seconds = d.pop("maxRuntimeSeconds", UNSET)

        model_id = d.pop("modelId", UNSET)

        name = d.pop("name", UNSET)

        project_id = d.pop("projectId", UNSET)

        _shared_settings = d.pop("sharedSettings", UNSET)
        shared_settings: SubmitFileBatchRequestSharedSettings | Unset
        if isinstance(_shared_settings, Unset):
            shared_settings = UNSET
        else:
            shared_settings = SubmitFileBatchRequestSharedSettings.from_dict(_shared_settings)

        smiles_row_count = d.pop("smilesRowCount", UNSET)

        tool_lifetime_etag = d.pop("toolLifetimeEtag", UNSET)

        tool_version = d.pop("toolVersion", UNSET)

        weighted_hours_budget = d.pop("weightedHoursBudget", UNSET)

        submit_file_batch_request = cls(
            kind=kind,
            source=source,
            tool=tool,
            atom_count=atom_count,
            binder_seq_row_count=binder_seq_row_count,
            csv_row_count=csv_row_count,
            gpu=gpu,
            inputs=inputs,
            low_priority=low_priority,
            max_runtime_seconds=max_runtime_seconds,
            model_id=model_id,
            name=name,
            project_id=project_id,
            shared_settings=shared_settings,
            smiles_row_count=smiles_row_count,
            tool_lifetime_etag=tool_lifetime_etag,
            tool_version=tool_version,
            weighted_hours_budget=weighted_hours_budget,
        )

        return submit_file_batch_request
