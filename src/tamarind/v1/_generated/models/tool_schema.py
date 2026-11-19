from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
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
        outputs (list[ToolSchemaOutputsItem]): The result tables this tool declares, the main one first. A `{JobName}`
            in a path is `*`, so each `glob` matches the file a job writes. Empty when the tool declares none.
        schema (ToolSchemaSchema): JSON Schema 2020-12 for `settings`. Conditional fields are expressed with
            `if`/`then`.
        tool (str):
        version (None | str): The tool's settings schema version, as jobs record it. Null when the tool has none.
    """

    example: ToolSchemaExample
    outputs: list[ToolSchemaOutputsItem]
    schema: ToolSchemaSchema
    tool: str
    version: None | str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        example = self.example.to_dict()

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
                "outputs": outputs,
                "schema": schema,
                "tool": tool,
                "version": version,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.tool_schema_example import ToolSchemaExample
        from ..models.tool_schema_outputs_item import ToolSchemaOutputsItem
        from ..models.tool_schema_schema import ToolSchemaSchema

        d = dict(src_dict)
        example = ToolSchemaExample.from_dict(d.pop("example"))

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
