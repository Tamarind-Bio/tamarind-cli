from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.pipeline_node_run_molecule import PipelineNodeRunMolecule


T = TypeVar("T", bound="PipelineNodeRunMoleculePage")


@_attrs_define
class PipelineNodeRunMoleculePage:
    """
    Attributes:
        input_group_exact (bool | None): Whether inputGroupId contains exactly the molecules this node processed. False
            means it is a superset; null means there is no single molecular upstream group.
        input_group_id (None | str): The derived molecular upstream group id; it may be a superset of this node's
            inputs.
        items (list[PipelineNodeRunMolecule]):
        next_cursor (None | str): Pass as `cursor` for the next page.
    """

    input_group_exact: bool | None
    input_group_id: None | str
    items: list[PipelineNodeRunMolecule]
    next_cursor: None | str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        input_group_exact: bool | None
        input_group_exact = self.input_group_exact

        input_group_id: None | str
        input_group_id = self.input_group_id

        items = []
        for items_item_data in self.items:
            items_item = items_item_data.to_dict()
            items.append(items_item)

        next_cursor: None | str
        next_cursor = self.next_cursor

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "inputGroupExact": input_group_exact,
                "inputGroupId": input_group_id,
                "items": items,
                "nextCursor": next_cursor,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.pipeline_node_run_molecule import PipelineNodeRunMolecule

        d = dict(src_dict)

        def _parse_input_group_exact(data: object) -> bool | None:
            if data is None:
                return data
            return cast(bool | None, data)

        input_group_exact = _parse_input_group_exact(d.pop("inputGroupExact"))

        def _parse_input_group_id(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        input_group_id = _parse_input_group_id(d.pop("inputGroupId"))

        items = []
        _items = d.pop("items")
        for items_item_data in _items:
            items_item = PipelineNodeRunMolecule.from_dict(items_item_data)

            items.append(items_item)

        def _parse_next_cursor(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        next_cursor = _parse_next_cursor(d.pop("nextCursor"))

        pipeline_node_run_molecule_page = cls(
            input_group_exact=input_group_exact,
            input_group_id=input_group_id,
            items=items,
            next_cursor=next_cursor,
        )

        pipeline_node_run_molecule_page.additional_properties = d
        return pipeline_node_run_molecule_page

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
