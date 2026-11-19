from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

if TYPE_CHECKING:
    from ..models.score_observation_dimensions import ScoreObservationDimensions
    from ..models.score_observation_metrics import ScoreObservationMetrics


T = TypeVar("T", bound="ScoreObservation")


@_attrs_define
class ScoreObservation:
    """One retained prediction beneath a molecule's score run.

    Attributes:
        created_at (datetime.datetime):
        dimensions (ScoreObservationDimensions):
        id (str):
        job_id (str): The job's bare stored id, without the `job_` or `batch_` prefix `/jobs` uses.
        job_name (str):
        metrics (ScoreObservationMetrics):
        molecule_id (str):
        score_run_id (str):
        selected (bool):
        structure_file_id (str):
        tool (str):
    """

    created_at: datetime.datetime
    dimensions: ScoreObservationDimensions
    id: str
    job_id: str
    job_name: str
    metrics: ScoreObservationMetrics
    molecule_id: str
    score_run_id: str
    selected: bool
    structure_file_id: str
    tool: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        created_at = self.created_at.isoformat()

        dimensions = self.dimensions.to_dict()

        id = self.id

        job_id = self.job_id

        job_name = self.job_name

        metrics = self.metrics.to_dict()

        molecule_id = self.molecule_id

        score_run_id = self.score_run_id

        selected = self.selected

        structure_file_id = self.structure_file_id

        tool = self.tool

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "createdAt": created_at,
                "dimensions": dimensions,
                "id": id,
                "jobId": job_id,
                "jobName": job_name,
                "metrics": metrics,
                "moleculeId": molecule_id,
                "scoreRunId": score_run_id,
                "selected": selected,
                "structureFileId": structure_file_id,
                "tool": tool,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.score_observation_dimensions import ScoreObservationDimensions
        from ..models.score_observation_metrics import ScoreObservationMetrics

        d = dict(src_dict)
        created_at = isoparse(d.pop("createdAt"))

        dimensions = ScoreObservationDimensions.from_dict(d.pop("dimensions"))

        id = d.pop("id")

        job_id = d.pop("jobId")

        job_name = d.pop("jobName")

        metrics = ScoreObservationMetrics.from_dict(d.pop("metrics"))

        molecule_id = d.pop("moleculeId")

        score_run_id = d.pop("scoreRunId")

        selected = d.pop("selected")

        structure_file_id = d.pop("structureFileId")

        tool = d.pop("tool")

        score_observation = cls(
            created_at=created_at,
            dimensions=dimensions,
            id=id,
            job_id=job_id,
            job_name=job_name,
            metrics=metrics,
            molecule_id=molecule_id,
            score_run_id=score_run_id,
            selected=selected,
            structure_file_id=structure_file_id,
            tool=tool,
        )

        score_observation.additional_properties = d
        return score_observation

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
