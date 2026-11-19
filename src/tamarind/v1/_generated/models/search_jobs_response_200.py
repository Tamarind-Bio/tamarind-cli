from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.batch import Batch
    from ..models.job import Job
    from ..models.job_summary import JobSummary
    from ..models.pipeline_run_item import PipelineRunItem


T = TypeVar("T", bound="SearchJobsResponse200")


@_attrs_define
class SearchJobsResponse200:
    """
    Attributes:
        items (list[Batch | Job | JobSummary | PipelineRunItem]):
        not_found (list[str]):
    """

    items: list[Batch | Job | JobSummary | PipelineRunItem]
    not_found: list[str]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.batch import Batch
        from ..models.job import Job
        from ..models.job_summary import JobSummary

        items = []
        for items_item_data in self.items:
            items_item: dict[str, Any]
            if isinstance(items_item_data, Job):
                items_item = items_item_data.to_dict()
            elif isinstance(items_item_data, JobSummary):
                items_item = items_item_data.to_dict()
            elif isinstance(items_item_data, Batch):
                items_item = items_item_data.to_dict()
            else:
                items_item = items_item_data.to_dict()

            items.append(items_item)

        not_found = self.not_found

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "items": items,
                "notFound": not_found,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.batch import Batch
        from ..models.job import Job
        from ..models.job_summary import JobSummary
        from ..models.pipeline_run_item import PipelineRunItem

        d = dict(src_dict)
        items = []
        _items = d.pop("items")
        for items_item_data in _items:

            def _parse_items_item(data: object) -> Batch | Job | JobSummary | PipelineRunItem:
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    items_item_type_0 = Job.from_dict(data)

                    return items_item_type_0
                except (TypeError, ValueError, AttributeError, KeyError):
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    items_item_type_1 = JobSummary.from_dict(data)

                    return items_item_type_1
                except (TypeError, ValueError, AttributeError, KeyError):
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    items_item_type_2 = Batch.from_dict(data)

                    return items_item_type_2
                except (TypeError, ValueError, AttributeError, KeyError):
                    pass
                if not isinstance(data, dict):
                    raise TypeError()
                items_item_type_3 = PipelineRunItem.from_dict(data)

                return items_item_type_3

            items_item = _parse_items_item(items_item_data)

            items.append(items_item)

        not_found = cast(list[str], d.pop("notFound"))

        search_jobs_response_200 = cls(
            items=items,
            not_found=not_found,
        )

        search_jobs_response_200.additional_properties = d
        return search_jobs_response_200

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
