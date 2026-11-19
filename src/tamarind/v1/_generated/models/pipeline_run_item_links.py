from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="PipelineRunItemLinks")


@_attrs_define
class PipelineRunItemLinks:
    """
    Attributes:
        jobs (str): `/jobs?pipelineRunId=run_...`, the jobs its steps launched.
        pipeline (str): `/pipelines/runs/run_...`, the run's own detail, with the same `run_` id.
        self_ (str): `/jobs/run_...`
    """

    jobs: str
    pipeline: str
    self_: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        jobs = self.jobs

        pipeline = self.pipeline

        self_ = self.self_

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "jobs": jobs,
                "pipeline": pipeline,
                "self": self_,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        jobs = d.pop("jobs")

        pipeline = d.pop("pipeline")

        self_ = d.pop("self")

        pipeline_run_item_links = cls(
            jobs=jobs,
            pipeline=pipeline,
            self_=self_,
        )

        pipeline_run_item_links.additional_properties = d
        return pipeline_run_item_links

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
