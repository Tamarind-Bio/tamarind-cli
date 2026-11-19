from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.diagnostic_severity import DiagnosticSeverity
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.diagnostic_allowed_range import DiagnosticAllowedRange


T = TypeVar("T", bound="Diagnostic")


@_attrs_define
class Diagnostic:
    """One problem with a request. The same shape in `Problem.errors` and in validation reports.

    Attributes:
        code (str): Stable. For example `required`, `unknown_field`, `out_of_range`, `invalid_option`,
            `invalid_residue`, `conditional_not_met`, `file_not_accessible`, `file_not_found`.
        detail (str):
        severity (DiagnosticSeverity):
        allowed_range (DiagnosticAllowedRange | Unset):
        allowed_values (list[Any] | Unset):
        field (str | Unset): In pipeline validation, the setting at fault on `node`.
        node (str | Unset): In pipeline validation, the node concerned.
        pointer (str | Unset): JSON Pointer to the field in the request body, e.g. `/settings/17/numRecycles`. Absent
            when the problem concerns the whole request.
        suggestion (str | Unset): A likely intended value, e.g. the closest valid field name.
    """

    code: str
    detail: str
    severity: DiagnosticSeverity
    allowed_range: DiagnosticAllowedRange | Unset = UNSET
    allowed_values: list[Any] | Unset = UNSET
    field: str | Unset = UNSET
    node: str | Unset = UNSET
    pointer: str | Unset = UNSET
    suggestion: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        code = self.code

        detail = self.detail

        severity = self.severity.value

        allowed_range: dict[str, Any] | Unset = UNSET
        if not isinstance(self.allowed_range, Unset):
            allowed_range = self.allowed_range.to_dict()

        allowed_values: list[Any] | Unset = UNSET
        if not isinstance(self.allowed_values, Unset):
            allowed_values = self.allowed_values

        field = self.field

        node = self.node

        pointer = self.pointer

        suggestion = self.suggestion

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "code": code,
                "detail": detail,
                "severity": severity,
            }
        )
        if allowed_range is not UNSET:
            field_dict["allowedRange"] = allowed_range
        if allowed_values is not UNSET:
            field_dict["allowedValues"] = allowed_values
        if field is not UNSET:
            field_dict["field"] = field
        if node is not UNSET:
            field_dict["node"] = node
        if pointer is not UNSET:
            field_dict["pointer"] = pointer
        if suggestion is not UNSET:
            field_dict["suggestion"] = suggestion

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.diagnostic_allowed_range import DiagnosticAllowedRange

        d = dict(src_dict)
        code = d.pop("code")

        detail = d.pop("detail")

        severity = DiagnosticSeverity(d.pop("severity"))

        _allowed_range = d.pop("allowedRange", UNSET)
        allowed_range: DiagnosticAllowedRange | Unset
        if isinstance(_allowed_range, Unset):
            allowed_range = UNSET
        else:
            allowed_range = DiagnosticAllowedRange.from_dict(_allowed_range)

        allowed_values = cast(list[Any], d.pop("allowedValues", UNSET))

        field = d.pop("field", UNSET)

        node = d.pop("node", UNSET)

        pointer = d.pop("pointer", UNSET)

        suggestion = d.pop("suggestion", UNSET)

        diagnostic = cls(
            code=code,
            detail=detail,
            severity=severity,
            allowed_range=allowed_range,
            allowed_values=allowed_values,
            field=field,
            node=node,
            pointer=pointer,
            suggestion=suggestion,
        )

        diagnostic.additional_properties = d
        return diagnostic

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
