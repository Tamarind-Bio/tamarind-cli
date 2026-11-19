from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Literal, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.job_status import JobStatus
from ..models.submission_channel import SubmissionChannel

if TYPE_CHECKING:
    from ..models.diagnostic import Diagnostic
    from ..models.item_counts import ItemCounts
    from ..models.job_stop_reason import JobStopReason
    from ..models.pipeline_run_item_links import PipelineRunItemLinks


T = TypeVar("T", bound="SubmittedPipelineRun")


@_attrs_define
class SubmittedPipelineRun:
    """What `submitJob` returns for a tool that runs as a pipeline behind the scenes (such as BinderScout), the pipeline
    run it started, as `getJob` shows it, plus the validator's non-blocking findings.

        Attributes:
            api_key_id (None | str): Null for now.
            completed_at (datetime.datetime | None):
            counts (ItemCounts): How many parts are in each status.
            created_at (datetime.datetime): When the run started, which is when it was submitted.
            created_by (str):
            display_name (None | str): The name the run was given; null when it has none.
            id (str): `run_` and the run's id, the same run `/pipelines/runs/{runId}` takes.
            job_counts (ItemCounts | None): The jobs the run's steps launched, each once at its newest attempt, by the same
                status `GET /jobs` shows for that job. In a list, only what's already cached, and null when nothing is; on `GET
                /jobs/run_...`, read at most 60 seconds ago.
            kind (Literal['pipeline']):
            links (PipelineRunItemLinks):
            name (str): The run's name, or a generated `run-` and the first 8 characters of its id when it has none.
            pipeline (None | str): The name of the pipeline it ran.
            poll_after_seconds (int | None): How long to wait before checking again, 30 while `In Queue` and 15 while
                `Running`. Null once the run is finished.
            project_id (None | str): Null for now.
            source (None | SubmissionChannel): The channel the run was submitted through. Null for a run that recorded none,
                which is every run started before runs recorded it.
            started_at (datetime.datetime | None): The same time as `createdAt`.
            status (JobStatus): Shared by jobs, batches and pipeline runs. `Complete`, `Stopped` and `Failed` are final.
                `Failed` means it ended in an error (`stopReason.kind` `error`). `Stopped` means it was canceled, hit a limit,
                or stopped with no recorded reason (`kind` `canceled`, `limit` or `unknown`). Both always carry `stopReason`. A
                new value here would need a new `Tamarind-Version` date.
            stop_reason (JobStopReason | None): Set when `status` is `Stopped` or `Failed`.
            warnings (list[Diagnostic]): The validator's non-blocking findings. Empty when there are none. A replay returns
                the original request's. Not returned by `getJob`.
    """

    api_key_id: None | str
    completed_at: datetime.datetime | None
    counts: ItemCounts
    created_at: datetime.datetime
    created_by: str
    display_name: None | str
    id: str
    job_counts: ItemCounts | None
    kind: Literal["pipeline"]
    links: PipelineRunItemLinks
    name: str
    pipeline: None | str
    poll_after_seconds: int | None
    project_id: None | str
    source: None | SubmissionChannel
    started_at: datetime.datetime | None
    status: JobStatus
    stop_reason: JobStopReason | None
    warnings: list[Diagnostic]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.item_counts import ItemCounts
        from ..models.job_stop_reason import JobStopReason

        api_key_id: None | str
        api_key_id = self.api_key_id

        completed_at: None | str
        if isinstance(self.completed_at, datetime.datetime):
            completed_at = self.completed_at.isoformat()
        else:
            completed_at = self.completed_at

        counts = self.counts.to_dict()

        created_at = self.created_at.isoformat()

        created_by = self.created_by

        display_name: None | str
        display_name = self.display_name

        id = self.id

        job_counts: dict[str, Any] | None
        if isinstance(self.job_counts, ItemCounts):
            job_counts = self.job_counts.to_dict()
        else:
            job_counts = self.job_counts

        kind = self.kind

        links = self.links.to_dict()

        name = self.name

        pipeline: None | str
        pipeline = self.pipeline

        poll_after_seconds: int | None
        poll_after_seconds = self.poll_after_seconds

        project_id: None | str
        project_id = self.project_id

        source: None | str
        if isinstance(self.source, SubmissionChannel):
            source = self.source.value
        else:
            source = self.source

        started_at: None | str
        if isinstance(self.started_at, datetime.datetime):
            started_at = self.started_at.isoformat()
        else:
            started_at = self.started_at

        status = self.status.value

        stop_reason: dict[str, Any] | None
        if isinstance(self.stop_reason, JobStopReason):
            stop_reason = self.stop_reason.to_dict()
        else:
            stop_reason = self.stop_reason

        warnings = []
        for warnings_item_data in self.warnings:
            warnings_item = warnings_item_data.to_dict()
            warnings.append(warnings_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "apiKeyId": api_key_id,
                "completedAt": completed_at,
                "counts": counts,
                "createdAt": created_at,
                "createdBy": created_by,
                "displayName": display_name,
                "id": id,
                "jobCounts": job_counts,
                "kind": kind,
                "links": links,
                "name": name,
                "pipeline": pipeline,
                "pollAfterSeconds": poll_after_seconds,
                "projectId": project_id,
                "source": source,
                "startedAt": started_at,
                "status": status,
                "stopReason": stop_reason,
                "warnings": warnings,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.diagnostic import Diagnostic
        from ..models.item_counts import ItemCounts
        from ..models.job_stop_reason import JobStopReason
        from ..models.pipeline_run_item_links import PipelineRunItemLinks

        d = dict(src_dict)

        def _parse_api_key_id(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        api_key_id = _parse_api_key_id(d.pop("apiKeyId"))

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

        counts = ItemCounts.from_dict(d.pop("counts"))

        created_at = isoparse(d.pop("createdAt"))

        created_by = d.pop("createdBy")

        def _parse_display_name(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        display_name = _parse_display_name(d.pop("displayName"))

        id = d.pop("id")

        def _parse_job_counts(data: object) -> ItemCounts | None:
            if data is None:
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                job_counts_type_0 = ItemCounts.from_dict(data)

                return job_counts_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(ItemCounts | None, data)

        job_counts = _parse_job_counts(d.pop("jobCounts"))

        kind = cast(Literal["pipeline"], d.pop("kind"))
        if kind != "pipeline":
            raise ValueError(f"kind must match const 'pipeline', got '{kind}'")

        links = PipelineRunItemLinks.from_dict(d.pop("links"))

        name = d.pop("name")

        def _parse_pipeline(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        pipeline = _parse_pipeline(d.pop("pipeline"))

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

        def _parse_source(data: object) -> None | SubmissionChannel:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                source_type_0 = SubmissionChannel(data)

                return source_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | SubmissionChannel, data)

        source = _parse_source(d.pop("source"))

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

        warnings = []
        _warnings = d.pop("warnings")
        for warnings_item_data in _warnings:
            warnings_item = Diagnostic.from_dict(warnings_item_data)

            warnings.append(warnings_item)

        submitted_pipeline_run = cls(
            api_key_id=api_key_id,
            completed_at=completed_at,
            counts=counts,
            created_at=created_at,
            created_by=created_by,
            display_name=display_name,
            id=id,
            job_counts=job_counts,
            kind=kind,
            links=links,
            name=name,
            pipeline=pipeline,
            poll_after_seconds=poll_after_seconds,
            project_id=project_id,
            source=source,
            started_at=started_at,
            status=status,
            stop_reason=stop_reason,
            warnings=warnings,
        )

        submitted_pipeline_run.additional_properties = d
        return submitted_pipeline_run

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
