from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..models.molecule_type import MoleculeType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.molecule_input_entity import MoleculeInputEntity
    from ..models.molecule_input_metadata import MoleculeInputMetadata


T = TypeVar("T", bound="MoleculeInput")


@_attrs_define
class MoleculeInput:
    """The spec's `MoleculeInput` — one molecule to create.

    Attributes:
        entity (MoleculeInputEntity):
        metadata (MoleculeInputMetadata | Unset):
        name (None | str | Unset):
        tags (list[str] | None | Unset): Tags to add to the molecule. Existing tags are preserved; omission or an empty
            list leaves them unchanged.
        type_ (MoleculeType | None | Unset):
    """

    entity: MoleculeInputEntity
    metadata: MoleculeInputMetadata | Unset = UNSET
    name: None | str | Unset = UNSET
    tags: list[str] | None | Unset = UNSET
    type_: MoleculeType | None | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        entity = self.entity.to_dict()

        metadata: dict[str, Any] | Unset = UNSET
        if not isinstance(self.metadata, Unset):
            metadata = self.metadata.to_dict()

        name: None | str | Unset
        if isinstance(self.name, Unset):
            name = UNSET
        else:
            name = self.name

        tags: list[str] | None | Unset
        if isinstance(self.tags, Unset):
            tags = UNSET
        elif isinstance(self.tags, list):
            tags = self.tags

        else:
            tags = self.tags

        type_: None | str | Unset
        if isinstance(self.type_, Unset):
            type_ = UNSET
        elif isinstance(self.type_, MoleculeType):
            type_ = self.type_.value
        else:
            type_ = self.type_

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "entity": entity,
            }
        )
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if name is not UNSET:
            field_dict["name"] = name
        if tags is not UNSET:
            field_dict["tags"] = tags
        if type_ is not UNSET:
            field_dict["type"] = type_

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.molecule_input_entity import MoleculeInputEntity
        from ..models.molecule_input_metadata import MoleculeInputMetadata

        d = dict(src_dict)
        entity = MoleculeInputEntity.from_dict(d.pop("entity"))

        _metadata = d.pop("metadata", UNSET)
        metadata: MoleculeInputMetadata | Unset
        if isinstance(_metadata, Unset):
            metadata = UNSET
        else:
            metadata = MoleculeInputMetadata.from_dict(_metadata)

        def _parse_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        name = _parse_name(d.pop("name", UNSET))

        def _parse_tags(data: object) -> list[str] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                tags_type_0 = cast(list[str], data)

                return tags_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[str] | None | Unset, data)

        tags = _parse_tags(d.pop("tags", UNSET))

        def _parse_type_(data: object) -> MoleculeType | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                type_type_0 = MoleculeType(data)

                return type_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(MoleculeType | None | Unset, data)

        type_ = _parse_type_(d.pop("type", UNSET))

        molecule_input = cls(
            entity=entity,
            metadata=metadata,
            name=name,
            tags=tags,
            type_=type_,
        )

        return molecule_input
