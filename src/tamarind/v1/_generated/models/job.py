from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Literal, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.job_status import JobStatus
from ..models.job_summary_source import JobSummarySource

if TYPE_CHECKING:
    from ..models.job_settings import JobSettings
    from ..models.job_stop_reason import JobStopReason
    from ..models.job_summary_links import JobSummaryLinks
    from ..models.job_summary_scores_type_0 import JobSummaryScoresType0


T = TypeVar("T", bound="Job")


@_attrs_define
class Job:
    """
    Attributes:
        api_key_id (None | str): The key that submitted this job. Null for now.
        batch_id (None | str): The `batch_` id of the batch this job is in; null when it isn't in one.
        completed_at (datetime.datetime | None):
        created_at (datetime.datetime):
        created_by (str):
        display_name (None | str): Editable label.
        id (str): The stable address of this job.
        kind (Literal['job']):
        links (JobSummaryLinks):
        low_priority (bool): Whether the job runs at the low-priority tier (`lowPriority` at submit), as the job records
            it. False for every other job.
        name (str): Unique per owner, chosen at submit or generated, and never changes.
        pipeline_run_id (None | str): The `run_` id of the pipeline run whose step launched this job. Null otherwise,
            and for a single-tool run's job, which stands for its run.
        poll_after_seconds (int | None): How long to wait before checking again, 30 while `In Queue` and 15 while
            `Running`. Null once the job is finished.
        project_id (None | str):
        runtime_seconds (float | None):
        scores (JobSummaryScoresType0 | None): The tool's headline metrics, when finished. A single number the tool
            recorded reads as `{"score": <number>}`.
        source (JobSummarySource): The channel the job was submitted through; `web` when none was recorded.
        started_at (datetime.datetime | None):
        status (JobStatus): Shared by jobs, batches and pipeline runs. `Complete`, `Stopped` and `Failed` are final.
            `Failed` means it ended in an error (`stopReason.kind` `error`). `Stopped` means it was canceled, hit a limit,
            or stopped with no recorded reason (`kind` `canceled`, `limit` or `unknown`). Both always carry `stopReason`. A
            new value here would need a new `Tamarind-Version` date.
        status_detail (None | str): What the job is doing now, in words, e.g. `Waiting for MSA`. For display only. Null
            for now.
        stop_reason (JobStopReason | None): Set when `status` is `Stopped` or `Failed`. Says why. A single-tool run's
            job shows its run's status and reason.
        tool (str):
        tool_version (None | str):
        weighted_hours (float | None):
        max_runtime_seconds (int | None):
        model_id (None | str):
        rerun_of (None | str): The `job_` id of the job this one reran, on jobs an earlier v1 rerun created as a new
            job. `rerunJob` now reruns in place and never sets it, so it's null otherwise.
        settings (JobSettings): The settings as submitted, without internal keys. A molecule picked from the Molecules
            Database reads as its sequence, SMILES or structure file name. A file setting reads as its stored key, under the
            owner's email, and a job name's path as the job's folder.
        weighted_hours_budget (float | None):
    """

    api_key_id: None | str
    batch_id: None | str
    completed_at: datetime.datetime | None
    created_at: datetime.datetime
    created_by: str
    display_name: None | str
    id: str
    kind: Literal["job"]
    links: JobSummaryLinks
    low_priority: bool
    name: str
    pipeline_run_id: None | str
    poll_after_seconds: int | None
    project_id: None | str
    runtime_seconds: float | None
    scores: JobSummaryScoresType0 | None
    source: JobSummarySource
    started_at: datetime.datetime | None
    status: JobStatus
    status_detail: None | str
    stop_reason: JobStopReason | None
    tool: str
    tool_version: None | str
    weighted_hours: float | None
    max_runtime_seconds: int | None
    model_id: None | str
    rerun_of: None | str
    settings: JobSettings
    weighted_hours_budget: float | None
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.job_stop_reason import JobStopReason
        from ..models.job_summary_scores_type_0 import JobSummaryScoresType0

        api_key_id: None | str
        api_key_id = self.api_key_id

        batch_id: None | str
        batch_id = self.batch_id

        completed_at: None | str
        if isinstance(self.completed_at, datetime.datetime):
            completed_at = self.completed_at.isoformat()
        else:
            completed_at = self.completed_at

        created_at = self.created_at.isoformat()

        created_by = self.created_by

        display_name: None | str
        display_name = self.display_name

        id = self.id

        kind = self.kind

        links = self.links.to_dict()

        low_priority = self.low_priority

        name = self.name

        pipeline_run_id: None | str
        pipeline_run_id = self.pipeline_run_id

        poll_after_seconds: int | None
        poll_after_seconds = self.poll_after_seconds

        project_id: None | str
        project_id = self.project_id

        runtime_seconds: float | None
        runtime_seconds = self.runtime_seconds

        scores: dict[str, Any] | None
        if isinstance(self.scores, JobSummaryScoresType0):
            scores = self.scores.to_dict()
        else:
            scores = self.scores

        source = self.source.value

        started_at: None | str
        if isinstance(self.started_at, datetime.datetime):
            started_at = self.started_at.isoformat()
        else:
            started_at = self.started_at

        status = self.status.value

        status_detail: None | str
        status_detail = self.status_detail

        stop_reason: dict[str, Any] | None
        if isinstance(self.stop_reason, JobStopReason):
            stop_reason = self.stop_reason.to_dict()
        else:
            stop_reason = self.stop_reason

        tool = self.tool

        tool_version: None | str
        tool_version = self.tool_version

        weighted_hours: float | None
        weighted_hours = self.weighted_hours

        max_runtime_seconds: int | None
        max_runtime_seconds = self.max_runtime_seconds

        model_id: None | str
        model_id = self.model_id

        rerun_of: None | str
        rerun_of = self.rerun_of

        settings = self.settings.to_dict()

        weighted_hours_budget: float | None
        weighted_hours_budget = self.weighted_hours_budget

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "apiKeyId": api_key_id,
                "batchId": batch_id,
                "completedAt": completed_at,
                "createdAt": created_at,
                "createdBy": created_by,
                "displayName": display_name,
                "id": id,
                "kind": kind,
                "links": links,
                "lowPriority": low_priority,
                "name": name,
                "pipelineRunId": pipeline_run_id,
                "pollAfterSeconds": poll_after_seconds,
                "projectId": project_id,
                "runtimeSeconds": runtime_seconds,
                "scores": scores,
                "source": source,
                "startedAt": started_at,
                "status": status,
                "statusDetail": status_detail,
                "stopReason": stop_reason,
                "tool": tool,
                "toolVersion": tool_version,
                "weightedHours": weighted_hours,
                "maxRuntimeSeconds": max_runtime_seconds,
                "modelId": model_id,
                "rerunOf": rerun_of,
                "settings": settings,
                "weightedHoursBudget": weighted_hours_budget,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.job_settings import JobSettings
        from ..models.job_stop_reason import JobStopReason
        from ..models.job_summary_links import JobSummaryLinks
        from ..models.job_summary_scores_type_0 import JobSummaryScoresType0

        d = dict(src_dict)

        def _parse_api_key_id(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        api_key_id = _parse_api_key_id(d.pop("apiKeyId"))

        def _parse_batch_id(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        batch_id = _parse_batch_id(d.pop("batchId"))

        def _parse_completed_at(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                completed_at_type_0 = isoparse(data)

                return completed_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        completed_at = _parse_completed_at(d.pop("completedAt"))

        created_at = isoparse(d.pop("createdAt"))

        created_by = d.pop("createdBy")

        def _parse_display_name(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        display_name = _parse_display_name(d.pop("displayName"))

        id = d.pop("id")

        kind = cast(Literal["job"], d.pop("kind"))
        if kind != "job":
            raise ValueError(f"kind must match const 'job', got '{kind}'")

        links = JobSummaryLinks.from_dict(d.pop("links"))

        low_priority = d.pop("lowPriority")

        name = d.pop("name")

        def _parse_pipeline_run_id(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        pipeline_run_id = _parse_pipeline_run_id(d.pop("pipelineRunId"))

        def _parse_poll_after_seconds(data: object) -> int | None:
            if data is None:
                return data
            return cast(int | None, data)

        poll_after_seconds = _parse_poll_after_seconds(d.pop("pollAfterSeconds"))

        def _parse_project_id(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        project_id = _parse_project_id(d.pop("projectId"))

        def _parse_runtime_seconds(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        runtime_seconds = _parse_runtime_seconds(d.pop("runtimeSeconds"))

        def _parse_scores(data: object) -> JobSummaryScoresType0 | None:
            if data is None:
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                scores_type_0 = JobSummaryScoresType0.from_dict(data)

                return scores_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(JobSummaryScoresType0 | None, data)

        scores = _parse_scores(d.pop("scores"))

        source = JobSummarySource(d.pop("source"))

        def _parse_started_at(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                started_at_type_0 = isoparse(data)

                return started_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        started_at = _parse_started_at(d.pop("startedAt"))

        status = JobStatus(d.pop("status"))

        def _parse_status_detail(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        status_detail = _parse_status_detail(d.pop("statusDetail"))

        def _parse_stop_reason(data: object) -> JobStopReason | None:
            if data is None:
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                stop_reason_type_0 = JobStopReason.from_dict(data)

                return stop_reason_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(JobStopReason | None, data)

        stop_reason = _parse_stop_reason(d.pop("stopReason"))

        tool = d.pop("tool")

        def _parse_tool_version(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        tool_version = _parse_tool_version(d.pop("toolVersion"))

        def _parse_weighted_hours(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        weighted_hours = _parse_weighted_hours(d.pop("weightedHours"))

        def _parse_max_runtime_seconds(data: object) -> int | None:
            if data is None:
                return data
            return cast(int | None, data)

        max_runtime_seconds = _parse_max_runtime_seconds(d.pop("maxRuntimeSeconds"))

        def _parse_model_id(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        model_id = _parse_model_id(d.pop("modelId"))

        def _parse_rerun_of(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        rerun_of = _parse_rerun_of(d.pop("rerunOf"))

        settings = JobSettings.from_dict(d.pop("settings"))

        def _parse_weighted_hours_budget(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        weighted_hours_budget = _parse_weighted_hours_budget(d.pop("weightedHoursBudget"))

        job = cls(
            api_key_id=api_key_id,
            batch_id=batch_id,
            completed_at=completed_at,
            created_at=created_at,
            created_by=created_by,
            display_name=display_name,
            id=id,
            kind=kind,
            links=links,
            low_priority=low_priority,
            name=name,
            pipeline_run_id=pipeline_run_id,
            poll_after_seconds=poll_after_seconds,
            project_id=project_id,
            runtime_seconds=runtime_seconds,
            scores=scores,
            source=source,
            started_at=started_at,
            status=status,
            status_detail=status_detail,
            stop_reason=stop_reason,
            tool=tool,
            tool_version=tool_version,
            weighted_hours=weighted_hours,
            max_runtime_seconds=max_runtime_seconds,
            model_id=model_id,
            rerun_of=rerun_of,
            settings=settings,
            weighted_hours_budget=weighted_hours_budget,
        )

        job.additional_properties = d
        return job

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
