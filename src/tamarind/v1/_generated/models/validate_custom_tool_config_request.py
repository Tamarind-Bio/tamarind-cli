from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

T = TypeVar("T", bound="ValidateCustomToolConfigRequest")


@_attrs_define
class ValidateCustomToolConfigRequest:
    """
    Attributes:
        config (str): The full text of the tool's `config.json`.
    """

    config: str

    def to_dict(self) -> dict[str, Any]:
        config = self.config

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "config": config,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        config = d.pop("config")

        validate_custom_tool_config_request = cls(
            config=config,
        )

        return validate_custom_tool_config_request
