from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.pipeline_run_status import PipelineRunStatus
from ..models.run_source import RunSource

if TYPE_CHECKING:
    from ..models.pipeline_node_run import PipelineNodeRun
    from ..models.pipeline_run_inputs import PipelineRunInputs


T = TypeVar("T", bound="PipelineRun")


@_attrs_define
class PipelineRun:
    """
    Attributes:
        completed_at (datetime.datetime | None):
        failure_reason (None | str): Why this ended as it did, as a short machine token such as `tool_error`,
            `no_output` or `filter_empty`. More tokens may be added, so handle one you don't know. It can be set when
            nothing failed: `no_output` marks a node that ran correctly and passed nothing on. Null means unclassified, not
            fine.
        id (str):
        inputs (PipelineRunInputs): The recorded inputs (input-node id -> {group} or {file}).
        name (None | str):
        node_runs (list[PipelineNodeRun]):
        source (RunSource):
        started_at (datetime.datetime):
        status (PipelineRunStatus): Today's run statuses, kept under `/pipelines/runs`. In `/jobs` a run shows the
            shared statuses instead (`queued` In Queue, `running` Running, `finished` and `partial` Complete, `stopped`
            Stopped, `failed` Failed with `stopReason` `platform_error` or `tool_error`). `partial` means some of the run's
            final steps delivered and some did not.
        template_id (str):
        template_version (None | str): The executed version handle e.g. 'v1'.
    """

    completed_at: datetime.datetime | None
    failure_reason: None | str
    id: str
    inputs: PipelineRunInputs
    name: None | str
    node_runs: list[PipelineNodeRun]
    source: RunSource
    started_at: datetime.datetime
    status: PipelineRunStatus
    template_id: str
    template_version: None | str
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

        inputs = self.inputs.to_dict()

        name: None | str
        name = self.name

        node_runs = []
        for node_runs_item_data in self.node_runs:
            node_runs_item = node_runs_item_data.to_dict()
            node_runs.append(node_runs_item)

        source = self.source.value

        started_at = self.started_at.isoformat()

        status = self.status.value

        template_id = self.template_id

        template_version: None | str
        template_version = self.template_version

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "completedAt": completed_at,
                "failureReason": failure_reason,
                "id": id,
                "inputs": inputs,
                "name": name,
                "nodeRuns": node_runs,
                "source": source,
                "startedAt": started_at,
                "status": status,
                "templateId": template_id,
                "templateVersion": template_version,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.pipeline_node_run import PipelineNodeRun
        from ..models.pipeline_run_inputs import PipelineRunInputs

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

        inputs = PipelineRunInputs.from_dict(d.pop("inputs"))

        def _parse_name(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        name = _parse_name(d.pop("name"))

        node_runs = []
        _node_runs = d.pop("nodeRuns")
        for node_runs_item_data in _node_runs:
            node_runs_item = PipelineNodeRun.from_dict(node_runs_item_data)

            node_runs.append(node_runs_item)

        source = RunSource(d.pop("source"))

        started_at = isoparse(d.pop("startedAt"))

        status = PipelineRunStatus(d.pop("status"))

        template_id = d.pop("templateId")

        def _parse_template_version(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        template_version = _parse_template_version(d.pop("templateVersion"))

        pipeline_run = cls(
            completed_at=completed_at,
            failure_reason=failure_reason,
            id=id,
            inputs=inputs,
            name=name,
            node_runs=node_runs,
            source=source,
            started_at=started_at,
            status=status,
            template_id=template_id,
            template_version=template_version,
        )

        pipeline_run.additional_properties = d
        return pipeline_run

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
