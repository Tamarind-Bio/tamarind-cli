from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..models.pipeline_tool_input_type_1_kind import PipelineToolInputType1Kind
from ..types import UNSET, Unset

T = TypeVar("T", bound="PipelineToolInputType1")


@_attrs_define
class PipelineToolInputType1:
    """
    Attributes:
        kind (PipelineToolInputType1Kind):
        smiles (str):
        name (None | str | Unset):
        settings_key (None | str | Unset):
    """

    kind: PipelineToolInputType1Kind
    smiles: str
    name: None | str | Unset = UNSET
    settings_key: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        kind = self.kind.value

        smiles = self.smiles

        name: None | str | Unset
        if isinstance(self.name, Unset):
            name = UNSET
        else:
            name = self.name

        settings_key: None | str | Unset
        if isinstance(self.settings_key, Unset):
            settings_key = UNSET
        else:
            settings_key = self.settings_key

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "kind": kind,
                "smiles": smiles,
            }
        )
        if name is not UNSET:
            field_dict["name"] = name
        if settings_key is not UNSET:
            field_dict["settingsKey"] = settings_key

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        kind = PipelineToolInputType1Kind(d.pop("kind"))

        smiles = d.pop("smiles")

        def _parse_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        name = _parse_name(d.pop("name", UNSET))

        def _parse_settings_key(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        settings_key = _parse_settings_key(d.pop("settingsKey", UNSET))

        pipeline_tool_input_type_1 = cls(
            kind=kind,
            smiles=smiles,
            name=name,
            settings_key=settings_key,
        )

        return pipeline_tool_input_type_1
