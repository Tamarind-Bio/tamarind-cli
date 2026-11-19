from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="DuplicatePipelineTemplateRequest")


@_attrs_define
class DuplicatePipelineTemplateRequest:
    """Body for `POST /pipelines/templates/{templateId}/duplicate`.

    Both fields are optional; `{}` is a valid body.

    VERSIONS ONLY — never the working draft. A draft is mutable and unversioned, so there is no
    stable thing for an API client to reference ("the draft as of now" isn't expressible) and it
    may be a teammate's mid-edit graph. So `version` omitted resolves to the published version if
    one is pinned, else the latest SAVED version. This is the one place the API deliberately
    differs from the in-app menu, which forks the draft because the user can see it.

        Example:
            {'name': 'binder-design v2 experiment', 'version': 'v2'}

        Attributes:
            name (None | str | Unset):
            version (None | str | Unset): A version handle e.g. 'v3'; absent -> default.
    """

    name: None | str | Unset = UNSET
    version: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        name: None | str | Unset
        if isinstance(self.name, Unset):
            name = UNSET
        else:
            name = self.name

        version: None | str | Unset
        if isinstance(self.version, Unset):
            version = UNSET
        else:
            version = self.version

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if name is not UNSET:
            field_dict["name"] = name
        if version is not UNSET:
            field_dict["version"] = version

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        name = _parse_name(d.pop("name", UNSET))

        def _parse_version(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        version = _parse_version(d.pop("version", UNSET))

        duplicate_pipeline_template_request = cls(
            name=name,
            version=version,
        )

        return duplicate_pipeline_template_request
