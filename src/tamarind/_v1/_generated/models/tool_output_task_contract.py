from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.tool_output_task_contract_generates_type_0_item import (
    ToolOutputTaskContractGeneratesType0Item,
)

T = TypeVar("T", bound="ToolOutputTaskContract")


@_attrs_define
class ToolOutputTaskContract:
    """
    Attributes:
        generates (list[ToolOutputTaskContractGeneratesType0Item] | None): What this task creates fresh. Empty for a
            scoring task whose table still echoes its input; null when the tool declares nothing for this task.
        main_csv (None | str):
        task_type (None | str):
    """

    generates: list[ToolOutputTaskContractGeneratesType0Item] | None
    main_csv: None | str
    task_type: None | str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        generates: list[str] | None
        if isinstance(self.generates, list):
            generates = []
            for generates_type_0_item_data in self.generates:
                generates_type_0_item = generates_type_0_item_data.value
                generates.append(generates_type_0_item)

        else:
            generates = self.generates

        main_csv: None | str
        main_csv = self.main_csv

        task_type: None | str
        task_type = self.task_type

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "generates": generates,
                "mainCSV": main_csv,
                "taskType": task_type,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_generates(data: object) -> list[ToolOutputTaskContractGeneratesType0Item] | None:
            if data is None:
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                generates_type_0 = []
                _generates_type_0 = data
                for generates_type_0_item_data in _generates_type_0:
                    generates_type_0_item = ToolOutputTaskContractGeneratesType0Item(
                        generates_type_0_item_data
                    )

                    generates_type_0.append(generates_type_0_item)

                return generates_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[ToolOutputTaskContractGeneratesType0Item] | None, data)

        generates = _parse_generates(d.pop("generates"))

        def _parse_main_csv(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        main_csv = _parse_main_csv(d.pop("mainCSV"))

        def _parse_task_type(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        task_type = _parse_task_type(d.pop("taskType"))

        tool_output_task_contract = cls(
            generates=generates,
            main_csv=main_csv,
            task_type=task_type,
        )

        tool_output_task_contract.additional_properties = d
        return tool_output_task_contract

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
