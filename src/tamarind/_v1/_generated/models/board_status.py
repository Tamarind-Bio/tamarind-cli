from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="BoardStatus")


@_attrs_define
class BoardStatus:
    """One status a project can put on an entry. The `id` is made from the `label`.

    Attributes:
        id (None | str):
        is_terminal (bool):
        label (None | str):
        tone (None | str):
    """

    id: None | str
    is_terminal: bool
    label: None | str
    tone: None | str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id: None | str
        id = self.id

        is_terminal = self.is_terminal

        label: None | str
        label = self.label

        tone: None | str
        tone = self.tone

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "isTerminal": is_terminal,
                "label": label,
                "tone": tone,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_id(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        id = _parse_id(d.pop("id"))

        is_terminal = d.pop("isTerminal")

        def _parse_label(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        label = _parse_label(d.pop("label"))

        def _parse_tone(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        tone = _parse_tone(d.pop("tone"))

        board_status = cls(
            id=id,
            is_terminal=is_terminal,
            label=label,
            tone=tone,
        )

        board_status.additional_properties = d
        return board_status

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
