from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.board_lane import BoardLane
    from ..models.board_meta import BoardMeta


T = TypeVar("T", bound="UpdateNotesResponse")


@_attrs_define
class UpdateNotesResponse:
    """`lanes` comes back only when the request carried a `lanes` operation, and then it is
    the whole ordered set — a new lane gets an id you could not have predicted, and a removed
    one leaves `laneOrder` rewritten.

        Attributes:
            meta (BoardMeta | None):
            lanes (list[BoardLane] | None | Unset):
    """

    meta: BoardMeta | None
    lanes: list[BoardLane] | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.board_meta import BoardMeta

        meta: dict[str, Any] | None
        if isinstance(self.meta, BoardMeta):
            meta = self.meta.to_dict()
        else:
            meta = self.meta

        lanes: list[dict[str, Any]] | None | Unset
        if isinstance(self.lanes, Unset):
            lanes = UNSET
        elif isinstance(self.lanes, list):
            lanes = []
            for lanes_type_0_item_data in self.lanes:
                lanes_type_0_item = lanes_type_0_item_data.to_dict()
                lanes.append(lanes_type_0_item)

        else:
            lanes = self.lanes

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "meta": meta,
            }
        )
        if lanes is not UNSET:
            field_dict["lanes"] = lanes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.board_lane import BoardLane
        from ..models.board_meta import BoardMeta

        d = dict(src_dict)

        def _parse_meta(data: object) -> BoardMeta | None:
            if data is None:
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                meta_type_0 = BoardMeta.from_dict(data)

                return meta_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(BoardMeta | None, data)

        meta = _parse_meta(d.pop("meta"))

        def _parse_lanes(data: object) -> list[BoardLane] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                lanes_type_0 = []
                _lanes_type_0 = data
                for lanes_type_0_item_data in _lanes_type_0:
                    lanes_type_0_item = BoardLane.from_dict(lanes_type_0_item_data)

                    lanes_type_0.append(lanes_type_0_item)

                return lanes_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[BoardLane] | None | Unset, data)

        lanes = _parse_lanes(d.pop("lanes", UNSET))

        update_notes_response = cls(
            meta=meta,
            lanes=lanes,
        )

        update_notes_response.additional_properties = d
        return update_notes_response

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
