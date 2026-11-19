from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define

from ..models.submit_job_request_kind import SubmitJobRequestKind
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.pipeline_tool_input_type_0 import PipelineToolInputType0
    from ..models.pipeline_tool_input_type_1 import PipelineToolInputType1
    from ..models.pipeline_tool_input_type_2 import PipelineToolInputType2
    from ..models.pipeline_tool_input_type_3 import PipelineToolInputType3
    from ..models.submit_job_request_settings import SubmitJobRequestSettings


T = TypeVar("T", bound="SubmitJobRequest")


@_attrs_define
class SubmitJobRequest:
    """One job. The same body is accepted by `submitJob`, `validateJob` and `estimateJob`.

    Attributes:
        settings (SubmitJobRequestSettings): The tool's settings. See `getToolSchema`. For a file setting, send a
            workspace `path`, a job file's `ref`, or a job's file under the job's name (see File settings in the
            introduction).
        tool (str): A `name` from `listTools`.
        atom_count (float | Unset): Atoms of an uploaded input, when `settings` hold only its path. The estimate uses a
            default without it, and it is not checked against the file.
        binder_seq_row_count (float | Unset): Binder sequence rows of an uploaded input, when `settings` hold only its
            path. The estimate uses a default without it, and it is not checked against the file.
        csv_row_count (float | Unset): CSV rows of an uploaded input, when `settings` hold only its path. The estimate
            uses a default without it, and it is not checked against the file.
        gpu (str | Unset): Request a specific GPU type. Premium only. Not built yet, so any value is 422 at `/gpu`.
        inputs (list[PipelineToolInputType0 | PipelineToolInputType1 | PipelineToolInputType2 | PipelineToolInputType3]
            | Unset): Named molecule inputs, for tools that take them. Not priced by `estimateJob` (422 there).
        kind (SubmitJobRequestKind | Unset): `job` (the default) for one job. Send `batch` to run the tool across many
            inputs. Default: SubmitJobRequestKind.JOB.
        low_priority (bool | Unset): Run at the low-priority tier: 20% off the weighted hours, no completion guarantee
            (they target finishing within a week), and a job not started within 7 days stops with no charge. For T2 GPU
            tools in Premium organizations that have it enabled. When it isn't available for this caller or this job, the
            request is refused with 422 `validation_failed` and an error at `/lowPriority` whose `code` is the reason, never
            run at full price. Optional. Default: False.
        max_runtime_seconds (int | Unset): Stop the job after this long. No business maximum; a number a job can't store
            is 422 `out_of_range`.
        model_id (str | Unset): Run this finetuned model. `tool` must be its `inferenceTool`.
        name (str | Unset): Unique per owner, and never changes. Invalid characters are refused, not silently removed.
        project_id (str | Unset): A project you can use. One that doesn't resolve for you is never silently dropped,
            whether or not your organization requires projects. Submit and estimate answer 422 `validation_failed` with an
            `invalid_option` error at `/projectId`; validate reports a failed `project` check with that error.
        smiles_row_count (float | Unset): SMILES rows of an uploaded input, when `settings` hold only its path. The
            estimate uses a default without it, and it is not checked against the file.
        tool_lifetime_etag (str | Unset): A custom tool version's `lifetimeEtag`. If the tool was deleted and its name
            reused since, submit is 409 `tool_lifetime_changed`, and validate reports a failed `access` check with an error
            at `/toolLifetimeEtag` with the same code.
        tool_version (str | Unset): A custom tool version. Defaults to the published one.
        weighted_hours_budget (float | Unset): Stop the job if it would use more than this. Only Premium members of an
            organization can set one, and not above the organization's hard limit when it has one (`not_supported` or
            `out_of_range` at this field). No business maximum; a number a job can't store is 422 `out_of_range`.
    """

    settings: SubmitJobRequestSettings
    tool: str
    atom_count: float | Unset = UNSET
    binder_seq_row_count: float | Unset = UNSET
    csv_row_count: float | Unset = UNSET
    gpu: str | Unset = UNSET
    inputs: (
        list[
            PipelineToolInputType0
            | PipelineToolInputType1
            | PipelineToolInputType2
            | PipelineToolInputType3
        ]
        | Unset
    ) = UNSET
    kind: SubmitJobRequestKind | Unset = SubmitJobRequestKind.JOB
    low_priority: bool | Unset = False
    max_runtime_seconds: int | Unset = UNSET
    model_id: str | Unset = UNSET
    name: str | Unset = UNSET
    project_id: str | Unset = UNSET
    smiles_row_count: float | Unset = UNSET
    tool_lifetime_etag: str | Unset = UNSET
    tool_version: str | Unset = UNSET
    weighted_hours_budget: float | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.pipeline_tool_input_type_0 import PipelineToolInputType0
        from ..models.pipeline_tool_input_type_1 import PipelineToolInputType1
        from ..models.pipeline_tool_input_type_2 import PipelineToolInputType2

        settings = self.settings.to_dict()

        tool = self.tool

        atom_count = self.atom_count

        binder_seq_row_count = self.binder_seq_row_count

        csv_row_count = self.csv_row_count

        gpu = self.gpu

        inputs: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.inputs, Unset):
            inputs = []
            for inputs_item_data in self.inputs:
                inputs_item: dict[str, Any]
                if isinstance(inputs_item_data, PipelineToolInputType0):
                    inputs_item = inputs_item_data.to_dict()
                elif isinstance(inputs_item_data, PipelineToolInputType1):
                    inputs_item = inputs_item_data.to_dict()
                elif isinstance(inputs_item_data, PipelineToolInputType2):
                    inputs_item = inputs_item_data.to_dict()
                else:
                    inputs_item = inputs_item_data.to_dict()

                inputs.append(inputs_item)

        kind: str | Unset = UNSET
        if not isinstance(self.kind, Unset):
            kind = self.kind.value

        low_priority = self.low_priority

        max_runtime_seconds = self.max_runtime_seconds

        model_id = self.model_id

        name = self.name

        project_id = self.project_id

        smiles_row_count = self.smiles_row_count

        tool_lifetime_etag = self.tool_lifetime_etag

        tool_version = self.tool_version

        weighted_hours_budget = self.weighted_hours_budget

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "settings": settings,
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
        if kind is not UNSET:
            field_dict["kind"] = kind
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
        from ..models.pipeline_tool_input_type_0 import PipelineToolInputType0
        from ..models.pipeline_tool_input_type_1 import PipelineToolInputType1
        from ..models.pipeline_tool_input_type_2 import PipelineToolInputType2
        from ..models.pipeline_tool_input_type_3 import PipelineToolInputType3
        from ..models.submit_job_request_settings import SubmitJobRequestSettings

        d = dict(src_dict)
        settings = SubmitJobRequestSettings.from_dict(d.pop("settings"))

        tool = d.pop("tool")

        atom_count = d.pop("atomCount", UNSET)

        binder_seq_row_count = d.pop("binderSeqRowCount", UNSET)

        csv_row_count = d.pop("csvRowCount", UNSET)

        gpu = d.pop("gpu", UNSET)

        _inputs = d.pop("inputs", UNSET)
        inputs: (
            list[
                PipelineToolInputType0
                | PipelineToolInputType1
                | PipelineToolInputType2
                | PipelineToolInputType3
            ]
            | Unset
        ) = UNSET
        if _inputs is not UNSET:
            inputs = []
            for inputs_item_data in _inputs:

                def _parse_inputs_item(
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
                    componentsschemas_pipeline_tool_input_type_3 = PipelineToolInputType3.from_dict(
                        data
                    )

                    return componentsschemas_pipeline_tool_input_type_3

                inputs_item = _parse_inputs_item(inputs_item_data)

                inputs.append(inputs_item)

        _kind = d.pop("kind", UNSET)
        kind: SubmitJobRequestKind | Unset
        if isinstance(_kind, Unset):
            kind = UNSET
        else:
            kind = SubmitJobRequestKind(_kind)

        low_priority = d.pop("lowPriority", UNSET)

        max_runtime_seconds = d.pop("maxRuntimeSeconds", UNSET)

        model_id = d.pop("modelId", UNSET)

        name = d.pop("name", UNSET)

        project_id = d.pop("projectId", UNSET)

        smiles_row_count = d.pop("smilesRowCount", UNSET)

        tool_lifetime_etag = d.pop("toolLifetimeEtag", UNSET)

        tool_version = d.pop("toolVersion", UNSET)

        weighted_hours_budget = d.pop("weightedHoursBudget", UNSET)

        submit_job_request = cls(
            settings=settings,
            tool=tool,
            atom_count=atom_count,
            binder_seq_row_count=binder_seq_row_count,
            csv_row_count=csv_row_count,
            gpu=gpu,
            inputs=inputs,
            kind=kind,
            low_priority=low_priority,
            max_runtime_seconds=max_runtime_seconds,
            model_id=model_id,
            name=name,
            project_id=project_id,
            smiles_row_count=smiles_row_count,
            tool_lifetime_etag=tool_lifetime_etag,
            tool_version=tool_version,
            weighted_hours_budget=weighted_hours_budget,
        )

        return submit_job_request
