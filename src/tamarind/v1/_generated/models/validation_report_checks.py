from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.validation_check import ValidationCheck

T = TypeVar("T", bound="ValidationReportChecks")


@_attrs_define
class ValidationReportChecks:
    """Which families of check ran. Each one maps to a way `submitJob` can refuse.

    Attributes:
        access (ValidationCheck): `skipped` means this family of check didn't run: it doesn't apply to the operation, or
            validation stopped at an earlier refusal (on `validateAssay`, `settings` and `name` are skipped when `access`
            failed).
        budget (ValidationCheck): `skipped` means this family of check didn't run: it doesn't apply to the operation, or
            validation stopped at an earlier refusal (on `validateAssay`, `settings` and `name` are skipped when `access`
            failed).
        name (ValidationCheck): `skipped` means this family of check didn't run: it doesn't apply to the operation, or
            validation stopped at an earlier refusal (on `validateAssay`, `settings` and `name` are skipped when `access`
            failed).
        project (ValidationCheck): `skipped` means this family of check didn't run: it doesn't apply to the operation,
            or validation stopped at an earlier refusal (on `validateAssay`, `settings` and `name` are skipped when `access`
            failed).
        settings (ValidationCheck): `skipped` means this family of check didn't run: it doesn't apply to the operation,
            or validation stopped at an earlier refusal (on `validateAssay`, `settings` and `name` are skipped when `access`
            failed).
    """

    access: ValidationCheck
    budget: ValidationCheck
    name: ValidationCheck
    project: ValidationCheck
    settings: ValidationCheck
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        access = self.access.value

        budget = self.budget.value

        name = self.name.value

        project = self.project.value

        settings = self.settings.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "access": access,
                "budget": budget,
                "name": name,
                "project": project,
                "settings": settings,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        access = ValidationCheck(d.pop("access"))

        budget = ValidationCheck(d.pop("budget"))

        name = ValidationCheck(d.pop("name"))

        project = ValidationCheck(d.pop("project"))

        settings = ValidationCheck(d.pop("settings"))

        validation_report_checks = cls(
            access=access,
            budget=budget,
            name=name,
            project=project,
            settings=settings,
        )

        validation_report_checks.additional_properties = d
        return validation_report_checks

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
