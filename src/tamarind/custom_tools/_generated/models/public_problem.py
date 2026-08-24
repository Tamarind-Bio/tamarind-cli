from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.public_problem_errors_type_0_item import PublicProblemErrorsType0Item


T = TypeVar("T", bound="PublicProblem")


@_attrs_define
class PublicProblem:
    """RFC 9457 problem detail. Serialized as `application/problem+json` on every public error.

    Attributes:
        code (str): A stable machine-readable slug; switch on THIS, not prose.
        status (int): The HTTP status code, duplicated in the body per RFC 9457.
        title (str): A short, human-readable summary of the error kind.
        type_ (str): A URI identifying the error kind (dereferenceable docs).
        detail (None | str | Unset): Instance-specific human explanation.
        errors (list[PublicProblemErrorsType0Item] | None | Unset): Structured per-item detail (request-validation
            fields OR pipeline diagnostics).
    """

    code: str
    status: int
    title: str
    type_: str
    detail: None | str | Unset = UNSET
    errors: list[PublicProblemErrorsType0Item] | None | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        code = self.code

        status = self.status

        title = self.title

        type_ = self.type_

        detail: None | str | Unset
        if isinstance(self.detail, Unset):
            detail = UNSET
        else:
            detail = self.detail

        errors: list[dict[str, Any]] | None | Unset
        if isinstance(self.errors, Unset):
            errors = UNSET
        elif isinstance(self.errors, list):
            errors = []
            for errors_type_0_item_data in self.errors:
                errors_type_0_item = errors_type_0_item_data.to_dict()
                errors.append(errors_type_0_item)

        else:
            errors = self.errors

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "code": code,
                "status": status,
                "title": title,
                "type": type_,
            }
        )
        if detail is not UNSET:
            field_dict["detail"] = detail
        if errors is not UNSET:
            field_dict["errors"] = errors

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.public_problem_errors_type_0_item import PublicProblemErrorsType0Item

        d = dict(src_dict)
        code = d.pop("code")

        status = d.pop("status")

        title = d.pop("title")

        type_ = d.pop("type")

        def _parse_detail(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        detail = _parse_detail(d.pop("detail", UNSET))

        def _parse_errors(data: object) -> list[PublicProblemErrorsType0Item] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                errors_type_0 = []
                _errors_type_0 = data
                for errors_type_0_item_data in _errors_type_0:
                    errors_type_0_item = PublicProblemErrorsType0Item.from_dict(
                        errors_type_0_item_data
                    )

                    errors_type_0.append(errors_type_0_item)

                return errors_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[PublicProblemErrorsType0Item] | None | Unset, data)

        errors = _parse_errors(d.pop("errors", UNSET))

        public_problem = cls(
            code=code,
            status=status,
            title=title,
            type_=type_,
            detail=detail,
            errors=errors,
        )

        return public_problem
