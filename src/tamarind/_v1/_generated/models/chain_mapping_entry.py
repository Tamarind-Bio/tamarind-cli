from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..models.chain_tag import ChainTag
from ..models.chain_type import ChainType
from ..types import UNSET, Unset

T = TypeVar("T", bound="ChainMappingEntry")


@_attrs_define
class ChainMappingEntry:
    """The spec's `ChainMappingEntry` — how ONE chain is defined for ingestion,
    keyed by chain id.

    This is what REPLACED the old fixed CSV role vocabulary
    (`heavy_chain`/`light_chain`/`sequence`/...), which could only describe
    antibody-shaped data and could not name a chain id at all (design notes §1).

        Attributes:
            csv_column (None | str | Unset):
            tags (list[ChainTag] | None | Unset): Roles for this chain. A chain is `heavy` OR `light`, never both (storage
                keeps one subtype); `lead` is compatible with either. Omit to inherit the schema's tag.
            type_ (ChainType | None | Unset):
    """

    csv_column: None | str | Unset = UNSET
    tags: list[ChainTag] | None | Unset = UNSET
    type_: ChainType | None | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        csv_column: None | str | Unset
        if isinstance(self.csv_column, Unset):
            csv_column = UNSET
        else:
            csv_column = self.csv_column

        tags: list[str] | None | Unset
        if isinstance(self.tags, Unset):
            tags = UNSET
        elif isinstance(self.tags, list):
            tags = []
            for tags_type_0_item_data in self.tags:
                tags_type_0_item = tags_type_0_item_data.value
                tags.append(tags_type_0_item)

        else:
            tags = self.tags

        type_: None | str | Unset
        if isinstance(self.type_, Unset):
            type_ = UNSET
        elif isinstance(self.type_, ChainType):
            type_ = self.type_.value
        else:
            type_ = self.type_

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if csv_column is not UNSET:
            field_dict["csvColumn"] = csv_column
        if tags is not UNSET:
            field_dict["tags"] = tags
        if type_ is not UNSET:
            field_dict["type"] = type_

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_csv_column(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        csv_column = _parse_csv_column(d.pop("csvColumn", UNSET))

        def _parse_tags(data: object) -> list[ChainTag] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                tags_type_0 = []
                _tags_type_0 = data
                for tags_type_0_item_data in _tags_type_0:
                    tags_type_0_item = ChainTag(tags_type_0_item_data)

                    tags_type_0.append(tags_type_0_item)

                return tags_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[ChainTag] | None | Unset, data)

        tags = _parse_tags(d.pop("tags", UNSET))

        def _parse_type_(data: object) -> ChainType | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                type_type_0 = ChainType(data)

                return type_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(ChainType | None | Unset, data)

        type_ = _parse_type_(d.pop("type", UNSET))

        chain_mapping_entry = cls(
            csv_column=csv_column,
            tags=tags,
            type_=type_,
        )

        return chain_mapping_entry
