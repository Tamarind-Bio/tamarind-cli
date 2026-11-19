from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.diagnostic import Diagnostic
    from ..models.validation_report_checks import ValidationReportChecks
    from ..models.validation_report_normalized import ValidationReportNormalized


T = TypeVar("T", bound="ValidationReport")


@_attrs_define
class ValidationReport:
    """
    Attributes:
        checks (ValidationReportChecks): Which families of check ran. Each one maps to a way `submitJob` can refuse.
        errors (list[Diagnostic]):
        valid (bool):
        warnings (list[Diagnostic]):
        name (str | Unset): The name you sent, trimmed and checked. Present only when the request included `name`; a
            name the submit would generate isn't predicted. Absent when the name was blank or is what failed.
        normalized (ValidationReportNormalized | Unset): Present only when valid, for reading. On `validateJob`, the
            settings as a submit would take them, with defaults filled in and molecule references resolved. On
            `validateAssay`, `{assayType, provider, modality, settings, sequenceCount}`. Send your original request, not
            these.
    """

    checks: ValidationReportChecks
    errors: list[Diagnostic]
    valid: bool
    warnings: list[Diagnostic]
    name: str | Unset = UNSET
    normalized: ValidationReportNormalized | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        checks = self.checks.to_dict()

        errors = []
        for errors_item_data in self.errors:
            errors_item = errors_item_data.to_dict()
            errors.append(errors_item)

        valid = self.valid

        warnings = []
        for warnings_item_data in self.warnings:
            warnings_item = warnings_item_data.to_dict()
            warnings.append(warnings_item)

        name = self.name

        normalized: dict[str, Any] | Unset = UNSET
        if not isinstance(self.normalized, Unset):
            normalized = self.normalized.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "checks": checks,
                "errors": errors,
                "valid": valid,
                "warnings": warnings,
            }
        )
        if name is not UNSET:
            field_dict["name"] = name
        if normalized is not UNSET:
            field_dict["normalized"] = normalized

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.diagnostic import Diagnostic
        from ..models.validation_report_checks import ValidationReportChecks
        from ..models.validation_report_normalized import ValidationReportNormalized

        d = dict(src_dict)
        checks = ValidationReportChecks.from_dict(d.pop("checks"))

        errors = []
        _errors = d.pop("errors")
        for errors_item_data in _errors:
            errors_item = Diagnostic.from_dict(errors_item_data)

            errors.append(errors_item)

        valid = d.pop("valid")

        warnings = []
        _warnings = d.pop("warnings")
        for warnings_item_data in _warnings:
            warnings_item = Diagnostic.from_dict(warnings_item_data)

            warnings.append(warnings_item)

        name = d.pop("name", UNSET)

        _normalized = d.pop("normalized", UNSET)
        normalized: ValidationReportNormalized | Unset
        if isinstance(_normalized, Unset):
            normalized = UNSET
        else:
            normalized = ValidationReportNormalized.from_dict(_normalized)

        validation_report = cls(
            checks=checks,
            errors=errors,
            valid=valid,
            warnings=warnings,
            name=name,
            normalized=normalized,
        )

        validation_report.additional_properties = d
        return validation_report

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
