from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="ToolOutputColumn")


@_attrs_define
class ToolOutputColumn:
    """
    Attributes:
        description (None | str):
        display_name (None | str):
        name (str):
        tasks (list[str] | None): The tasks that write this column. Null when the declaration doesn't gate it by task,
            which doesn't promise every task fills it; read `byTask.*.generates` for what a task produces.
        type_ (str): The column's declared type (pdb, sequence, sdf, smiles, number, string, ...); `string` when it
            declares none.
        units (None | str):
    """

    description: None | str
    display_name: None | str
    name: str
    tasks: list[str] | None
    type_: str
    units: None | str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        description: None | str
        description = self.description

        display_name: None | str
        display_name = self.display_name

        name = self.name

        tasks: list[str] | None
        if isinstance(self.tasks, list):
            tasks = self.tasks

        else:
            tasks = self.tasks

        type_ = self.type_

        units: None | str
        units = self.units

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "description": description,
                "displayName": display_name,
                "name": name,
                "tasks": tasks,
                "type": type_,
                "units": units,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_description(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        description = _parse_description(d.pop("description"))

        def _parse_display_name(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        display_name = _parse_display_name(d.pop("displayName"))

        name = d.pop("name")

        def _parse_tasks(data: object) -> list[str] | None:
            if data is None:
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                tasks_type_0 = cast(list[str], data)

                return tasks_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[str] | None, data)

        tasks = _parse_tasks(d.pop("tasks"))

        type_ = d.pop("type")

        def _parse_units(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        units = _parse_units(d.pop("units"))

        tool_output_column = cls(
            description=description,
            display_name=display_name,
            name=name,
            tasks=tasks,
            type_=type_,
            units=units,
        )

        tool_output_column.additional_properties = d
        return tool_output_column

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
