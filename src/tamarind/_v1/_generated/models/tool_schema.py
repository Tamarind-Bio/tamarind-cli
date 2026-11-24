from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.tool_output_contract import ToolOutputContract
    from ..models.tool_schema_example import ToolSchemaExample
    from ..models.tool_schema_outputs_item import ToolSchemaOutputsItem
    from ..models.tool_schema_schema import ToolSchemaSchema


T = TypeVar("T", bound="ToolSchema")


@_attrs_define
class ToolSchema:
    """
    Attributes:
        example (ToolSchemaExample): A `settings` object built from each setting's example or default, for one task
            branch. File settings carry placeholder names until you upload your own.
        output_contract (None | ToolOutputContract): What the results look like. Null when the tool declares no output
            contract.
        output_types (list[str]): What the tool declares it produces, as on `Tool`. Empty means the tool declares
            nothing (unknown), not that it produces nothing.
        outputs (list[ToolSchemaOutputsItem]): The result tables this tool declares, the main one first. A `{JobName}`
            in a path is `*`, so each `glob` matches the file a job writes. Empty when the tool declares none.
        schema (ToolSchemaSchema): JSON Schema 2020-12 for `settings`. Conditional fields are expressed with
            `if`/`then`.
        tool (str): The tool's name; a custom tool's as you sent it, which is what a submit sends.
        version (None | str): The tool's settings schema version, as jobs record it. For a custom tool, the version this
            schema is. Null when the tool has none.
    """

    example: ToolSchemaExample
    output_contract: None | ToolOutputContract
    output_types: list[str]
    outputs: list[ToolSchemaOutputsItem]
    schema: ToolSchemaSchema
    tool: str
    version: None | str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.tool_output_contract import ToolOutputContract

        example = self.example.to_dict()

        output_contract: dict[str, Any] | None
        if isinstance(self.output_contract, ToolOutputContract):
            output_contract = self.output_contract.to_dict()
        else:
            output_contract = self.output_contract

        output_types = self.output_types

        outputs = []
        for outputs_item_data in self.outputs:
            outputs_item = outputs_item_data.to_dict()
            outputs.append(outputs_item)

        schema = self.schema.to_dict()

        tool = self.tool

        version: None | str
        version = self.version

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "example": example,
                "outputContract": output_contract,
                "outputTypes": output_types,
                "outputs": outputs,
                "schema": schema,
                "tool": tool,
                "version": version,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.tool_output_contract import ToolOutputContract
        from ..models.tool_schema_example import ToolSchemaExample
        from ..models.tool_schema_outputs_item import ToolSchemaOutputsItem
        from ..models.tool_schema_schema import ToolSchemaSchema

        d = dict(src_dict)
        example = ToolSchemaExample.from_dict(d.pop("example"))

        def _parse_output_contract(data: object) -> None | ToolOutputContract:
            if data is None:
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                output_contract_type_0 = ToolOutputContract.from_dict(data)

                return output_contract_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | ToolOutputContract, data)

        output_contract = _parse_output_contract(d.pop("outputContract"))

        output_types = cast(list[str], d.pop("outputTypes"))

        outputs = []
        _outputs = d.pop("outputs")
        for outputs_item_data in _outputs:
            outputs_item = ToolSchemaOutputsItem.from_dict(outputs_item_data)

            outputs.append(outputs_item)

        schema = ToolSchemaSchema.from_dict(d.pop("schema"))

        tool = d.pop("tool")

        def _parse_version(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        version = _parse_version(d.pop("version"))

        tool_schema = cls(
            example=example,
            output_contract=output_contract,
            output_types=output_types,
            outputs=outputs,
            schema=schema,
            tool=tool,
            version=version,
        )

        tool_schema.additional_properties = d
        return tool_schema

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
