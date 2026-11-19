from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.diagnostic import Diagnostic


T = TypeVar("T", bound="PipelineValidationReport")


@_attrs_define
class PipelineValidationReport:
    """
    Attributes:
        errors (list[Diagnostic]):
        valid (bool):
    """

    errors: list[Diagnostic]
    valid: bool
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        errors = []
        for errors_item_data in self.errors:
            errors_item = errors_item_data.to_dict()
            errors.append(errors_item)

        valid = self.valid

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "errors": errors,
                "valid": valid,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.diagnostic import Diagnostic

        d = dict(src_dict)
        errors = []
        _errors = d.pop("errors")
        for errors_item_data in _errors:
            errors_item = Diagnostic.from_dict(errors_item_data)

            errors.append(errors_item)

        valid = d.pop("valid")

        pipeline_validation_report = cls(
            errors=errors,
            valid=valid,
        )

        pipeline_validation_report.additional_properties = d
        return pipeline_validation_report

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
