from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.batch_validation_report_results_item import BatchValidationReportResultsItem
    from ..models.diagnostic import Diagnostic


T = TypeVar("T", bound="BatchValidationReport")


@_attrs_define
class BatchValidationReport:
    """`validateJob`'s verdict on an inline batch.

    Attributes:
        count (int): The rows sent.
        errors (list[Diagnostic]): Problems with the batch as a whole, such as an unknown tool, a taken `name`, the
            `weightedHoursBudget` option, or the rows' total over a budget, the monthly limit or the queue limit.
        results (list[BatchValidationReportResultsItem]): The rows with an error or a warning, in row order, at most
            1,000. Their pointers lead into the row, such as `/settings/17/numRecycles` or `/names/17`.
        results_truncated (bool): True when more rows had an error or a warning than `results` lists.
        valid (bool):
        valid_count (int): The rows with no error. 0 when the batch as a whole has a problem.
    """

    count: int
    errors: list[Diagnostic]
    results: list[BatchValidationReportResultsItem]
    results_truncated: bool
    valid: bool
    valid_count: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        count = self.count

        errors = []
        for errors_item_data in self.errors:
            errors_item = errors_item_data.to_dict()
            errors.append(errors_item)

        results = []
        for results_item_data in self.results:
            results_item = results_item_data.to_dict()
            results.append(results_item)

        results_truncated = self.results_truncated

        valid = self.valid

        valid_count = self.valid_count

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "count": count,
                "errors": errors,
                "results": results,
                "resultsTruncated": results_truncated,
                "valid": valid,
                "validCount": valid_count,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.batch_validation_report_results_item import BatchValidationReportResultsItem
        from ..models.diagnostic import Diagnostic

        d = dict(src_dict)
        count = d.pop("count")

        errors = []
        _errors = d.pop("errors")
        for errors_item_data in _errors:
            errors_item = Diagnostic.from_dict(errors_item_data)

            errors.append(errors_item)

        results = []
        _results = d.pop("results")
        for results_item_data in _results:
            results_item = BatchValidationReportResultsItem.from_dict(results_item_data)

            results.append(results_item)

        results_truncated = d.pop("resultsTruncated")

        valid = d.pop("valid")

        valid_count = d.pop("validCount")

        batch_validation_report = cls(
            count=count,
            errors=errors,
            results=results,
            results_truncated=results_truncated,
            valid=valid,
            valid_count=valid_count,
        )

        batch_validation_report.additional_properties = d
        return batch_validation_report

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
