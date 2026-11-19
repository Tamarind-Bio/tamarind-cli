from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..models.pipeline_tool_input_type_2_kind import PipelineToolInputType2Kind
from ..types import UNSET, Unset

T = TypeVar("T", bound="PipelineToolInputType2")


@_attrs_define
class PipelineToolInputType2:
    """
    Attributes:
        complex_id (str):
        kind (PipelineToolInputType2Kind):
        file_id (None | str | Unset):
        group_id (None | str | Unset):
        input_chain_id (None | str | Unset):
        settings_key (None | str | Unset):
    """

    complex_id: str
    kind: PipelineToolInputType2Kind
    file_id: None | str | Unset = UNSET
    group_id: None | str | Unset = UNSET
    input_chain_id: None | str | Unset = UNSET
    settings_key: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        complex_id = self.complex_id

        kind = self.kind.value

        file_id: None | str | Unset
        if isinstance(self.file_id, Unset):
            file_id = UNSET
        else:
            file_id = self.file_id

        group_id: None | str | Unset
        if isinstance(self.group_id, Unset):
            group_id = UNSET
        else:
            group_id = self.group_id

        input_chain_id: None | str | Unset
        if isinstance(self.input_chain_id, Unset):
            input_chain_id = UNSET
        else:
            input_chain_id = self.input_chain_id

        settings_key: None | str | Unset
        if isinstance(self.settings_key, Unset):
            settings_key = UNSET
        else:
            settings_key = self.settings_key

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "complexId": complex_id,
                "kind": kind,
            }
        )
        if file_id is not UNSET:
            field_dict["fileId"] = file_id
        if group_id is not UNSET:
            field_dict["groupId"] = group_id
        if input_chain_id is not UNSET:
            field_dict["inputChainId"] = input_chain_id
        if settings_key is not UNSET:
            field_dict["settingsKey"] = settings_key

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        complex_id = d.pop("complexId")

        kind = PipelineToolInputType2Kind(d.pop("kind"))

        def _parse_file_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        file_id = _parse_file_id(d.pop("fileId", UNSET))

        def _parse_group_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        group_id = _parse_group_id(d.pop("groupId", UNSET))

        def _parse_input_chain_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        input_chain_id = _parse_input_chain_id(d.pop("inputChainId", UNSET))

        def _parse_settings_key(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        settings_key = _parse_settings_key(d.pop("settingsKey", UNSET))

        pipeline_tool_input_type_2 = cls(
            complex_id=complex_id,
            kind=kind,
            file_id=file_id,
            group_id=group_id,
            input_chain_id=input_chain_id,
            settings_key=settings_key,
        )

        return pipeline_tool_input_type_2
