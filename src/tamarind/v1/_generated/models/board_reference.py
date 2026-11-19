from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

T = TypeVar("T", bound="BoardReference")


@_attrs_define
class BoardReference:
    """A link is an object of `{type, id}`.

    Attributes:
        id (None | str): The resource's own id: a job or batch name, a pipeline run id, a molecule group id, a custom
            tool name, an agent chat id, or a file key.
        type_ (None | str): One of `job`, `batch`, `pipeline-run`, `molecule-group`, `custom-tool`, `tool`, `agent-
            chat`, `file`.
    """

    id: None | str
    type_: None | str

    def to_dict(self) -> dict[str, Any]:
        id: None | str
        id = self.id

        type_: None | str
        type_ = self.type_

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "id": id,
                "type": type_,
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

        def _parse_type_(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        type_ = _parse_type_(d.pop("type"))

        board_reference = cls(
            id=id,
            type_=type_,
        )

        return board_reference
