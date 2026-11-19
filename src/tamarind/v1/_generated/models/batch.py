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
    from ..models.batch_links import BatchLinks
    from ..models.batch_stop_reason_type_0 import BatchStopReasonType0
    from ..models.item_counts import ItemCounts


T = TypeVar("T", bound="Batch")


@_attrs_define
class Batch:
    """A `/jobs` item of `kind` `batch`. `Complete` once every job has finished, whatever the mix, and `Failed` only when
    the batch itself broke. Until it finishes it is `In Queue` while it has no jobs yet and `Running` once it has any.

        Attributes:
            api_key_id (None | str): Null for now.
            completed_at (datetime.datetime | None):
            counts (ItemCounts): How many parts are in each status.
            created_at (datetime.datetime):
            created_by (str):
            display_name (None | str):
            id (str):
            jobs_created (bool): False while the batch's jobs are still being created from a `kind` `batch` submit. Any
                other batch reads false until it has a job. True once the batch has finished.
            kind (Literal['batch']):
            links (BatchLinks):
            name (str): Unique per owner, and never changes.
            poll_after_seconds (int | None): How long to wait before checking again, 30 while `In Queue` and 15 while
                `Running`. Null once the batch is finished.
            project_id (None | str):
            rerun_of (None | str): The `job_` id of the job whose rerun the tool split into this batch, on batches an
                earlier v1 rerun created. `rerunJob` now reruns in place and never sets it, so it's null otherwise.
            source (SubmissionChannel): The channel a job, batch or pipeline run was submitted through. Tamarind's SDK, CLI,
                MCP and agents declare theirs with `X-Tamarind-Client-Channel` (see Attribution in the introduction); any other
                API-key submit is `api`, and the app's is `web`.
            started_at (datetime.datetime | None):
            status (JobStatus): Shared by jobs, batches and pipeline runs. `Complete`, `Stopped` and `Failed` are final.
                `Failed` means it ended in an error (`stopReason.kind` `error`). `Stopped` means it was canceled, hit a limit,
                or stopped with no recorded reason (`kind` `canceled`, `limit` or `unknown`). Both always carry `stopReason`. A
                new value here would need a new `Tamarind-Version` date.
            stop_reason (BatchStopReasonType0 | None): Set when `status` is `Stopped` or `Failed`. How each job ended is in
                `counts`; the batch's own `stopReason` is about the batch. It is `Failed` only when the batch itself broke, with
                `platform_error` when its jobs couldn't be created or their results couldn't be combined, and `invalid_input`
                when a `kind` `batch` submit couldn't go ahead as sent (rows that can't run, or a project no longer available).
                A `kind` `batch` submit that a budget, the monthly quota or the queue limit refused before any job was created
                is `Stopped` with `kind` `limit`. On those two, `errors` holds the problems, a row's pointing into the request
                the batch was submitted with; at most 100, and when there were more, the last one has code `truncated` and says
                how many aren't listed. `errors` is absent otherwise.
            tool (str):
            tool_version (None | str):
            weighted_hours (float | None):
    """

    api_key_id: None | str
    completed_at: datetime.datetime | None
    counts: ItemCounts
    created_at: datetime.datetime
    created_by: str
    display_name: None | str
    id: str
    jobs_created: bool
    kind: Literal["batch"]
    links: BatchLinks
    name: str
    poll_after_seconds: int | None
    project_id: None | str
    rerun_of: None | str
    source: SubmissionChannel
    started_at: datetime.datetime | None
    status: JobStatus
    stop_reason: BatchStopReasonType0 | None
    tool: str
    tool_version: None | str
    weighted_hours: float | None
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.batch_stop_reason_type_0 import BatchStopReasonType0

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

        jobs_created = self.jobs_created

        kind = self.kind

        links = self.links.to_dict()

        name = self.name

        poll_after_seconds: int | None
        poll_after_seconds = self.poll_after_seconds

        project_id: None | str
        project_id = self.project_id

        rerun_of: None | str
        rerun_of = self.rerun_of

        source = self.source.value

        started_at: None | str
        if isinstance(self.started_at, datetime.datetime):
            started_at = self.started_at.isoformat()
        else:
            started_at = self.started_at

        status = self.status.value

        stop_reason: dict[str, Any] | None
        if isinstance(self.stop_reason, BatchStopReasonType0):
            stop_reason = self.stop_reason.to_dict()
        else:
            stop_reason = self.stop_reason

        tool = self.tool

        tool_version: None | str
        tool_version = self.tool_version

        weighted_hours: float | None
        weighted_hours = self.weighted_hours

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
                "jobsCreated": jobs_created,
                "kind": kind,
                "links": links,
                "name": name,
                "pollAfterSeconds": poll_after_seconds,
                "projectId": project_id,
                "rerunOf": rerun_of,
                "source": source,
                "startedAt": started_at,
                "status": status,
                "stopReason": stop_reason,
                "tool": tool,
                "toolVersion": tool_version,
                "weightedHours": weighted_hours,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.batch_links import BatchLinks
        from ..models.batch_stop_reason_type_0 import BatchStopReasonType0
        from ..models.item_counts import ItemCounts

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

        jobs_created = d.pop("jobsCreated")

        kind = cast(Literal["batch"], d.pop("kind"))
        if kind != "batch":
            raise ValueError(f"kind must match const 'batch', got '{kind}'")

        links = BatchLinks.from_dict(d.pop("links"))

        name = d.pop("name")

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

        def _parse_rerun_of(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        rerun_of = _parse_rerun_of(d.pop("rerunOf"))

        source = SubmissionChannel(d.pop("source"))

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

        def _parse_stop_reason(data: object) -> BatchStopReasonType0 | None:
            if data is None:
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                stop_reason_type_0 = BatchStopReasonType0.from_dict(data)

                return stop_reason_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(BatchStopReasonType0 | None, data)

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

        batch = cls(
            api_key_id=api_key_id,
            completed_at=completed_at,
            counts=counts,
            created_at=created_at,
            created_by=created_by,
            display_name=display_name,
            id=id,
            jobs_created=jobs_created,
            kind=kind,
            links=links,
            name=name,
            poll_after_seconds=poll_after_seconds,
            project_id=project_id,
            rerun_of=rerun_of,
            source=source,
            started_at=started_at,
            status=status,
            stop_reason=stop_reason,
            tool=tool,
            tool_version=tool_version,
            weighted_hours=weighted_hours,
        )

        batch.additional_properties = d
        return batch

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
