from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.board_reference import BoardReference
    from ..models.board_tag_skip import BoardTagSkip


T = TypeVar("T", bound="BoardResourceTagging")


@_attrs_define
class BoardResourceTagging:
    """What happened to each job or batch this write linked.

    Comes back only when the request carried `links`, and reports only what that write added.
    A resource that could not be added to the project is listed here and the link to it still
    stands.

        Attributes:
            skipped (list[BoardTagSkip]):
            tagged (list[BoardReference]):
    """

    skipped: list[BoardTagSkip]
    tagged: list[BoardReference]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        skipped = []
        for skipped_item_data in self.skipped:
            skipped_item = skipped_item_data.to_dict()
            skipped.append(skipped_item)

        tagged = []
        for tagged_item_data in self.tagged:
            tagged_item = tagged_item_data.to_dict()
            tagged.append(tagged_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "skipped": skipped,
                "tagged": tagged,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.board_reference import BoardReference
        from ..models.board_tag_skip import BoardTagSkip

        d = dict(src_dict)
        skipped = []
        _skipped = d.pop("skipped")
        for skipped_item_data in _skipped:
            skipped_item = BoardTagSkip.from_dict(skipped_item_data)

            skipped.append(skipped_item)

        tagged = []
        _tagged = d.pop("tagged")
        for tagged_item_data in _tagged:
            tagged_item = BoardReference.from_dict(tagged_item_data)

            tagged.append(tagged_item)

        board_resource_tagging = cls(
            skipped=skipped,
            tagged=tagged,
        )

        board_resource_tagging.additional_properties = d
        return board_resource_tagging

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
