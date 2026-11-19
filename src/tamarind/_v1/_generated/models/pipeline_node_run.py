from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.pipeline_node_run_status import PipelineNodeRunStatus

T = TypeVar("T", bound="PipelineNodeRun")


@_attrs_define
class PipelineNodeRun:
    """
    Attributes:
        completed_at (datetime.datetime | None):
        failure_reason (None | str): Why this ended as it did, as a short machine token such as `tool_error`,
            `no_output` or `filter_empty`. More tokens may be added, so handle one you don't know. It can be set when
            nothing failed: `no_output` marks a node that ran correctly and passed nothing on. Null means unclassified, not
            fine.
        id (str):
        jobs_complete (int):
        jobs_total (int):
        label (str):
        node_id (str): The stable pipeline node id.
        node_type (str):
        output_count (int | None):
        output_group (None | str): The molecules group id this node run produced.
        started_at (datetime.datetime | None):
        status (PipelineNodeRunStatus): Today's node statuses. `skipped`, and `cancelled` on older runs, mean the node
            never ran because an earlier step failed. `stopped` means a person halted it.
    """

    completed_at: datetime.datetime | None
    failure_reason: None | str
    id: str
    jobs_complete: int
    jobs_total: int
    label: str
    node_id: str
    node_type: str
    output_count: int | None
    output_group: None | str
    started_at: datetime.datetime | None
    status: PipelineNodeRunStatus
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        completed_at: None | str
        if isinstance(self.completed_at, datetime.datetime):
            completed_at = self.completed_at.isoformat()
        else:
            completed_at = self.completed_at

        failure_reason: None | str
        failure_reason = self.failure_reason

        id = self.id

        jobs_complete = self.jobs_complete

        jobs_total = self.jobs_total

        label = self.label

        node_id = self.node_id

        node_type = self.node_type

        output_count: int | None
        output_count = self.output_count

        output_group: None | str
        output_group = self.output_group

        started_at: None | str
        if isinstance(self.started_at, datetime.datetime):
            started_at = self.started_at.isoformat()
        else:
            started_at = self.started_at

        status = self.status.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "completedAt": completed_at,
                "failureReason": failure_reason,
                "id": id,
                "jobsComplete": jobs_complete,
                "jobsTotal": jobs_total,
                "label": label,
                "nodeId": node_id,
                "nodeType": node_type,
                "outputCount": output_count,
                "outputGroup": output_group,
                "startedAt": started_at,
                "status": status,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

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

        def _parse_failure_reason(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        failure_reason = _parse_failure_reason(d.pop("failureReason"))

        id = d.pop("id")

        jobs_complete = d.pop("jobsComplete")

        jobs_total = d.pop("jobsTotal")

        label = d.pop("label")

        node_id = d.pop("nodeId")

        node_type = d.pop("nodeType")

        def _parse_output_count(data: object) -> int | None:
            if data is None:
                return data
            return cast(int | None, data)

        output_count = _parse_output_count(d.pop("outputCount"))

        def _parse_output_group(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        output_group = _parse_output_group(d.pop("outputGroup"))

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

        status = PipelineNodeRunStatus(d.pop("status"))

        pipeline_node_run = cls(
            completed_at=completed_at,
            failure_reason=failure_reason,
            id=id,
            jobs_complete=jobs_complete,
            jobs_total=jobs_total,
            label=label,
            node_id=node_id,
            node_type=node_type,
            output_count=output_count,
            output_group=output_group,
            started_at=started_at,
            status=status,
        )

        pipeline_node_run.additional_properties = d
        return pipeline_node_run

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
