from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.tool_timing_predictability_type_1 import ToolTimingPredictabilityType1
from ..models.tool_timing_predictability_type_2_type_1 import ToolTimingPredictabilityType2Type1
from ..models.tool_timing_predictability_type_3_type_1 import ToolTimingPredictabilityType3Type1

T = TypeVar("T", bound="Tool")


@_attrs_define
class Tool:
    """
    Attributes:
        custom (bool): True on your organization's custom tools, which `listTools` lists with `custom=true`; false on
            built-in ones.
        description (str):
        display_name (str): The catalog's display name, or `name` when it has none.
        docs_url (None | str): Always null for now. Nothing records it yet.
        finetune (bool): True when submitting this tool trains a model.
        functions (list[str]): The catalog's tags for this tool, as stored. `getToolFacets` lists them lower-cased, and
            the `function` filter matches them in any case.
        modalities (list[str]): The catalog's categories for this tool, as stored. `getToolFacets` lists them lower-
            cased, and the `modality` filter matches them in any case.
        name (str): The exact value to send as `tool`.
        output_types (list[str]): What the tool declares it produces, in the catalog's own vocabulary, molecular (pdb,
            sequence, sdf, smiles) and otherwise (csv, score, cif, ...). A few are compound, like `pdb-list`, so match by
            containment. Empty means the tool declares nothing (unknown), not that it produces nothing.
        required_settings (list[str]): The settings every submit must send, by name. A setting needed only for some
            tasks or under a condition, one the platform fills a default for, and one behind a flag that's off for you
            aren't here. Use `getToolSchema` for everything else.
        timing_predictability (None | ToolTimingPredictabilityType1 | ToolTimingPredictabilityType2Type1 |
            ToolTimingPredictabilityType3Type1): Always null for now. Nothing records it yet.
    """

    custom: bool
    description: str
    display_name: str
    docs_url: None | str
    finetune: bool
    functions: list[str]
    modalities: list[str]
    name: str
    output_types: list[str]
    required_settings: list[str]
    timing_predictability: (
        None
        | ToolTimingPredictabilityType1
        | ToolTimingPredictabilityType2Type1
        | ToolTimingPredictabilityType3Type1
    )
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        custom = self.custom

        description = self.description

        display_name = self.display_name

        docs_url: None | str
        docs_url = self.docs_url

        finetune = self.finetune

        functions = self.functions

        modalities = self.modalities

        name = self.name

        output_types = self.output_types

        required_settings = self.required_settings

        timing_predictability: None | str
        if isinstance(self.timing_predictability, ToolTimingPredictabilityType1):
            timing_predictability = self.timing_predictability.value
        elif isinstance(self.timing_predictability, ToolTimingPredictabilityType2Type1):
            timing_predictability = self.timing_predictability.value
        elif isinstance(self.timing_predictability, ToolTimingPredictabilityType3Type1):
            timing_predictability = self.timing_predictability.value
        else:
            timing_predictability = self.timing_predictability

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "custom": custom,
                "description": description,
                "displayName": display_name,
                "docsUrl": docs_url,
                "finetune": finetune,
                "functions": functions,
                "modalities": modalities,
                "name": name,
                "outputTypes": output_types,
                "requiredSettings": required_settings,
                "timingPredictability": timing_predictability,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        custom = d.pop("custom")

        description = d.pop("description")

        display_name = d.pop("displayName")

        def _parse_docs_url(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        docs_url = _parse_docs_url(d.pop("docsUrl"))

        finetune = d.pop("finetune")

        functions = cast(list[str], d.pop("functions"))

        modalities = cast(list[str], d.pop("modalities"))

        name = d.pop("name")

        output_types = cast(list[str], d.pop("outputTypes"))

        required_settings = cast(list[str], d.pop("requiredSettings"))

        def _parse_timing_predictability(
            data: object,
        ) -> (
            None
            | ToolTimingPredictabilityType1
            | ToolTimingPredictabilityType2Type1
            | ToolTimingPredictabilityType3Type1
        ):
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                timing_predictability_type_1 = ToolTimingPredictabilityType1(data)

                return timing_predictability_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            try:
                if not isinstance(data, str):
                    raise TypeError()
                timing_predictability_type_2_type_1 = ToolTimingPredictabilityType2Type1(data)

                return timing_predictability_type_2_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            try:
                if not isinstance(data, str):
                    raise TypeError()
                timing_predictability_type_3_type_1 = ToolTimingPredictabilityType3Type1(data)

                return timing_predictability_type_3_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(
                None
                | ToolTimingPredictabilityType1
                | ToolTimingPredictabilityType2Type1
                | ToolTimingPredictabilityType3Type1,
                data,
            )

        timing_predictability = _parse_timing_predictability(d.pop("timingPredictability"))

        tool = cls(
            custom=custom,
            description=description,
            display_name=display_name,
            docs_url=docs_url,
            finetune=finetune,
            functions=functions,
            modalities=modalities,
            name=name,
            output_types=output_types,
            required_settings=required_settings,
            timing_predictability=timing_predictability,
        )

        tool.additional_properties = d
        return tool

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
