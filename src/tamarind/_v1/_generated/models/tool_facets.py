from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.tool_facets_functions_item import ToolFacetsFunctionsItem
    from ..models.tool_facets_modalities_item import ToolFacetsModalitiesItem


T = TypeVar("T", bound="ToolFacets")


@_attrs_define
class ToolFacets:
    """
    Attributes:
        functions (list[ToolFacetsFunctionsItem]):
        modalities (list[ToolFacetsModalitiesItem]):
    """

    functions: list[ToolFacetsFunctionsItem]
    modalities: list[ToolFacetsModalitiesItem]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        functions = []
        for functions_item_data in self.functions:
            functions_item = functions_item_data.to_dict()
            functions.append(functions_item)

        modalities = []
        for modalities_item_data in self.modalities:
            modalities_item = modalities_item_data.to_dict()
            modalities.append(modalities_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "functions": functions,
                "modalities": modalities,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.tool_facets_functions_item import ToolFacetsFunctionsItem
        from ..models.tool_facets_modalities_item import ToolFacetsModalitiesItem

        d = dict(src_dict)
        functions = []
        _functions = d.pop("functions")
        for functions_item_data in _functions:
            functions_item = ToolFacetsFunctionsItem.from_dict(functions_item_data)

            functions.append(functions_item)

        modalities = []
        _modalities = d.pop("modalities")
        for modalities_item_data in _modalities:
            modalities_item = ToolFacetsModalitiesItem.from_dict(modalities_item_data)

            modalities.append(modalities_item)

        tool_facets = cls(
            functions=functions,
            modalities=modalities,
        )

        tool_facets.additional_properties = d
        return tool_facets

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
