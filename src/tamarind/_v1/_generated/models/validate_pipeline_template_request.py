from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="ValidatePipelineTemplateRequest")


@_attrs_define
class ValidatePipelineTemplateRequest:
    """Body for `POST /pipelines/templates/{templateId}/validate` — validate the TEMPLATE ITSELF (no run bindings),
    against its own `metadata.defaultGroup` reference groups. `{}` is valid (validate the default
    version).

        Attributes:
            version (None | str | Unset): A version handle e.g. 'v1' to validate; absent -> default.
    """

    version: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        version: None | str | Unset
        if isinstance(self.version, Unset):
            version = UNSET
        else:
            version = self.version

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if version is not UNSET:
            field_dict["version"] = version

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_version(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        version = _parse_version(d.pop("version", UNSET))

        validate_pipeline_template_request = cls(
            version=version,
        )

        return validate_pipeline_template_request
