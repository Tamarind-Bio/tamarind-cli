from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.run_status import RunStatus
from ..models.source import Source

if TYPE_CHECKING:
    from ..models.public_node_run import PublicNodeRun
    from ..models.public_run_inputs import PublicRunInputs


T = TypeVar("T", bound="PublicRun")


@_attrs_define
class PublicRun:
    """
    Attributes:
        completed_at (None | str):
        id (str):
        inputs (PublicRunInputs): The recorded inputs (input-node id -> {group} or {file}).
        name (None | str):
        node_runs (list[PublicNodeRun]):
        source (Source):
        started_at (str):
        status (RunStatus):
        template_id (str):
        template_version (None | str): The executed version handle e.g. 'v1'.
    """

    completed_at: None | str
    id: str
    inputs: PublicRunInputs
    name: None | str
    node_runs: list[PublicNodeRun]
    source: Source
    started_at: str
    status: RunStatus
    template_id: str
    template_version: None | str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        completed_at: None | str
        completed_at = self.completed_at

        id = self.id

        inputs = self.inputs.to_dict()

        name: None | str
        name = self.name

        node_runs = []
        for node_runs_item_data in self.node_runs:
            node_runs_item = node_runs_item_data.to_dict()
            node_runs.append(node_runs_item)

        source = self.source.value

        started_at = self.started_at

        status = self.status.value

        template_id = self.template_id

        template_version: None | str
        template_version = self.template_version

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "completedAt": completed_at,
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
        from ..models.public_node_run import PublicNodeRun
        from ..models.public_run_inputs import PublicRunInputs

        d = dict(src_dict)

        def _parse_completed_at(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        completed_at = _parse_completed_at(d.pop("completedAt"))

        id = d.pop("id")

        inputs = PublicRunInputs.from_dict(d.pop("inputs"))

        def _parse_name(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        name = _parse_name(d.pop("name"))

        node_runs = []
        _node_runs = d.pop("nodeRuns")
        for node_runs_item_data in _node_runs:
            node_runs_item = PublicNodeRun.from_dict(node_runs_item_data)

            node_runs.append(node_runs_item)

        source = Source(d.pop("source"))

        started_at = d.pop("startedAt")

        status = RunStatus(d.pop("status"))

        template_id = d.pop("templateId")

        def _parse_template_version(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        template_version = _parse_template_version(d.pop("templateVersion"))

        public_run = cls(
            completed_at=completed_at,
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

        public_run.additional_properties = d
        return public_run

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
