from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

if TYPE_CHECKING:
    from ..models.molecule_card_entity import MoleculeCardEntity
    from ..models.molecule_group import MoleculeGroup
    from ..models.molecule_match_detail import MoleculeMatchDetail
    from ..models.molecule_origin import MoleculeOrigin
    from ..models.molecule_sort_group import MoleculeSortGroup


T = TypeVar("T", bound="MoleculeCard")


@_attrs_define
class MoleculeCard:
    """
    Attributes:
        added_at (datetime.datetime | None):
        created_at (datetime.datetime | None):
        created_by (None | str):
        entity (MoleculeCardEntity):
        groups (list[MoleculeGroup]):
        has_structure (bool | None): Whether the molecule has a structure. Blank if unknown.
        id (str):
        match_detail (MoleculeMatchDetail | None):
        matched_on (list[str] | None):
        name (None | str):
        notes (None | str):
        origin (MoleculeOrigin | None):
        sort_group (MoleculeSortGroup | None):
        source (None | str):
        tags (list[str]):
        truncated (list[str]):
        type_ (None | str):
    """

    added_at: datetime.datetime | None
    created_at: datetime.datetime | None
    created_by: None | str
    entity: MoleculeCardEntity
    groups: list[MoleculeGroup]
    has_structure: bool | None
    id: str
    match_detail: MoleculeMatchDetail | None
    matched_on: list[str] | None
    name: None | str
    notes: None | str
    origin: MoleculeOrigin | None
    sort_group: MoleculeSortGroup | None
    source: None | str
    tags: list[str]
    truncated: list[str]
    type_: None | str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.molecule_match_detail import MoleculeMatchDetail
        from ..models.molecule_origin import MoleculeOrigin
        from ..models.molecule_sort_group import MoleculeSortGroup

        added_at: None | str
        if isinstance(self.added_at, datetime.datetime):
            added_at = self.added_at.isoformat()
        else:
            added_at = self.added_at

        created_at: None | str
        if isinstance(self.created_at, datetime.datetime):
            created_at = self.created_at.isoformat()
        else:
            created_at = self.created_at

        created_by: None | str
        created_by = self.created_by

        entity = self.entity.to_dict()

        groups = []
        for groups_item_data in self.groups:
            groups_item = groups_item_data.to_dict()
            groups.append(groups_item)

        has_structure: bool | None
        has_structure = self.has_structure

        id = self.id

        match_detail: dict[str, Any] | None
        if isinstance(self.match_detail, MoleculeMatchDetail):
            match_detail = self.match_detail.to_dict()
        else:
            match_detail = self.match_detail

        matched_on: list[str] | None
        if isinstance(self.matched_on, list):
            matched_on = self.matched_on

        else:
            matched_on = self.matched_on

        name: None | str
        name = self.name

        notes: None | str
        notes = self.notes

        origin: dict[str, Any] | None
        if isinstance(self.origin, MoleculeOrigin):
            origin = self.origin.to_dict()
        else:
            origin = self.origin

        sort_group: dict[str, Any] | None
        if isinstance(self.sort_group, MoleculeSortGroup):
            sort_group = self.sort_group.to_dict()
        else:
            sort_group = self.sort_group

        source: None | str
        source = self.source

        tags = self.tags

        truncated = self.truncated

        type_: None | str
        type_ = self.type_

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "addedAt": added_at,
                "createdAt": created_at,
                "createdBy": created_by,
                "entity": entity,
                "groups": groups,
                "hasStructure": has_structure,
                "id": id,
                "matchDetail": match_detail,
                "matchedOn": matched_on,
                "name": name,
                "notes": notes,
                "origin": origin,
                "sortGroup": sort_group,
                "source": source,
                "tags": tags,
                "truncated": truncated,
                "type": type_,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.molecule_card_entity import MoleculeCardEntity
        from ..models.molecule_group import MoleculeGroup
        from ..models.molecule_match_detail import MoleculeMatchDetail
        from ..models.molecule_origin import MoleculeOrigin
        from ..models.molecule_sort_group import MoleculeSortGroup

        d = dict(src_dict)

        def _parse_added_at(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                added_at_type_0 = isoparse(data)

                return added_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        added_at = _parse_added_at(d.pop("addedAt"))

        def _parse_created_at(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                created_at_type_0 = isoparse(data)

                return created_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        created_at = _parse_created_at(d.pop("createdAt"))

        def _parse_created_by(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        created_by = _parse_created_by(d.pop("createdBy"))

        entity = MoleculeCardEntity.from_dict(d.pop("entity"))

        groups = []
        _groups = d.pop("groups")
        for groups_item_data in _groups:
            groups_item = MoleculeGroup.from_dict(groups_item_data)

            groups.append(groups_item)

        def _parse_has_structure(data: object) -> bool | None:
            if data is None:
                return data
            return cast(bool | None, data)

        has_structure = _parse_has_structure(d.pop("hasStructure"))

        id = d.pop("id")

        def _parse_match_detail(data: object) -> MoleculeMatchDetail | None:
            if data is None:
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                match_detail_type_0 = MoleculeMatchDetail.from_dict(data)

                return match_detail_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(MoleculeMatchDetail | None, data)

        match_detail = _parse_match_detail(d.pop("matchDetail"))

        def _parse_matched_on(data: object) -> list[str] | None:
            if data is None:
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                matched_on_type_0 = cast(list[str], data)

                return matched_on_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[str] | None, data)

        matched_on = _parse_matched_on(d.pop("matchedOn"))

        def _parse_name(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        name = _parse_name(d.pop("name"))

        def _parse_notes(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        notes = _parse_notes(d.pop("notes"))

        def _parse_origin(data: object) -> MoleculeOrigin | None:
            if data is None:
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                origin_type_0 = MoleculeOrigin.from_dict(data)

                return origin_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(MoleculeOrigin | None, data)

        origin = _parse_origin(d.pop("origin"))

        def _parse_sort_group(data: object) -> MoleculeSortGroup | None:
            if data is None:
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                sort_group_type_0 = MoleculeSortGroup.from_dict(data)

                return sort_group_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(MoleculeSortGroup | None, data)

        sort_group = _parse_sort_group(d.pop("sortGroup"))

        def _parse_source(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        source = _parse_source(d.pop("source"))

        tags = cast(list[str], d.pop("tags"))

        truncated = cast(list[str], d.pop("truncated"))

        def _parse_type_(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        type_ = _parse_type_(d.pop("type"))

        molecule_card = cls(
            added_at=added_at,
            created_at=created_at,
            created_by=created_by,
            entity=entity,
            groups=groups,
            has_structure=has_structure,
            id=id,
            match_detail=match_detail,
            matched_on=matched_on,
            name=name,
            notes=notes,
            origin=origin,
            sort_group=sort_group,
            source=source,
            tags=tags,
            truncated=truncated,
            type_=type_,
        )

        molecule_card.additional_properties = d
        return molecule_card

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
