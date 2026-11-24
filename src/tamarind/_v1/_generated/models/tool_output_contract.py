from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.tool_output_contract_produces_item import ToolOutputContractProducesItem

if TYPE_CHECKING:
    from ..models.tool_output_column import ToolOutputColumn
    from ..models.tool_output_contract_by_task_type_0 import ToolOutputContractByTaskType0


T = TypeVar("T", bound="ToolOutputContract")


@_attrs_define
class ToolOutputContract:
    """
    Attributes:
        by_task (None | ToolOutputContractByTaskType0): For a tool whose output depends on its task setting, one entry
            per task value, and authoritative for the task you set. Each entry is complete; a task that doesn't redeclare
            `mainCSV` or `taskType` inherits the top-level value. Null for a tool whose output doesn't depend on its task.
        columns (list[ToolOutputColumn]): The main results table's columns, the metrics to filter or rank on. For a tool
            whose output depends on its task, the union over every task's main table; a column with `tasks` appears only in
            those tasks.
        main_csv (None | str): The main results table's file name, as the tool declares it at the top level.
        produces (list[ToolOutputContractProducesItem]): The molecular representations the output carries, as a column
            of the results table or as a file written beside it, including any echoed from the input, so a scoring tool can
            list one. For a tool whose output depends on its task, the union over every task.
        task_type (None | str): The tool's top-level declaration, e.g. `generate` (creates a molecule), `score`
            (annotates one), `structure-prediction`. For a tool with `byTask`, read the task's own entry instead.
    """

    by_task: None | ToolOutputContractByTaskType0
    columns: list[ToolOutputColumn]
    main_csv: None | str
    produces: list[ToolOutputContractProducesItem]
    task_type: None | str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.tool_output_contract_by_task_type_0 import ToolOutputContractByTaskType0

        by_task: dict[str, Any] | None
        if isinstance(self.by_task, ToolOutputContractByTaskType0):
            by_task = self.by_task.to_dict()
        else:
            by_task = self.by_task

        columns = []
        for columns_item_data in self.columns:
            columns_item = columns_item_data.to_dict()
            columns.append(columns_item)

        main_csv: None | str
        main_csv = self.main_csv

        produces = []
        for produces_item_data in self.produces:
            produces_item = produces_item_data.value
            produces.append(produces_item)

        task_type: None | str
        task_type = self.task_type

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "byTask": by_task,
                "columns": columns,
                "mainCSV": main_csv,
                "produces": produces,
                "taskType": task_type,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.tool_output_column import ToolOutputColumn
        from ..models.tool_output_contract_by_task_type_0 import ToolOutputContractByTaskType0

        d = dict(src_dict)

        def _parse_by_task(data: object) -> None | ToolOutputContractByTaskType0:
            if data is None:
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                by_task_type_0 = ToolOutputContractByTaskType0.from_dict(data)

                return by_task_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | ToolOutputContractByTaskType0, data)

        by_task = _parse_by_task(d.pop("byTask"))

        columns = []
        _columns = d.pop("columns")
        for columns_item_data in _columns:
            columns_item = ToolOutputColumn.from_dict(columns_item_data)

            columns.append(columns_item)

        def _parse_main_csv(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        main_csv = _parse_main_csv(d.pop("mainCSV"))

        produces = []
        _produces = d.pop("produces")
        for produces_item_data in _produces:
            produces_item = ToolOutputContractProducesItem(produces_item_data)

            produces.append(produces_item)

        def _parse_task_type(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        task_type = _parse_task_type(d.pop("taskType"))

        tool_output_contract = cls(
            by_task=by_task,
            columns=columns,
            main_csv=main_csv,
            produces=produces,
            task_type=task_type,
        )

        tool_output_contract.additional_properties = d
        return tool_output_contract

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
