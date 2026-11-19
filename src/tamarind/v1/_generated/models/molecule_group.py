from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

if TYPE_CHECKING:
    from ..models.molecule_group_metadata import MoleculeGroupMetadata
    from ..models.molecule_group_source import MoleculeGroupSource


T = TypeVar("T", bound="MoleculeGroup")


@_attrs_define
class MoleculeGroup:
    """The spec's `Group` — a named collection of molecules.

    Molecule-only vocabulary: `moleculeCount`, never the internal `complexCount`.

        Attributes:
            created_at (datetime.datetime):
            display_name (None | str):
            id (str):
            matched_on (None | str):
            metadata (MoleculeGroupMetadata):
            molecule_count (int):
            name (str):
            schema_id (None | str):
            source (MoleculeGroupSource | None):
            status (str):
            tags (list[str]):
            type_ (None | str):
            updated_at (datetime.datetime):
    """

    created_at: datetime.datetime
    display_name: None | str
    id: str
    matched_on: None | str
    metadata: MoleculeGroupMetadata
    molecule_count: int
    name: str
    schema_id: None | str
    source: MoleculeGroupSource | None
    status: str
    tags: list[str]
    type_: None | str
    updated_at: datetime.datetime
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.molecule_group_source import MoleculeGroupSource

        created_at = self.created_at.isoformat()

        display_name: None | str
        display_name = self.display_name

        id = self.id

        matched_on: None | str
        matched_on = self.matched_on

        metadata = self.metadata.to_dict()

        molecule_count = self.molecule_count

        name = self.name

        schema_id: None | str
        schema_id = self.schema_id

        source: dict[str, Any] | None
        if isinstance(self.source, MoleculeGroupSource):
            source = self.source.to_dict()
        else:
            source = self.source

        status = self.status

        tags = self.tags

        type_: None | str
        type_ = self.type_

        updated_at = self.updated_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "createdAt": created_at,
                "displayName": display_name,
                "id": id,
                "matchedOn": matched_on,
                "metadata": metadata,
                "moleculeCount": molecule_count,
                "name": name,
                "schemaId": schema_id,
                "source": source,
                "status": status,
                "tags": tags,
                "type": type_,
                "updatedAt": updated_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.molecule_group_metadata import MoleculeGroupMetadata
        from ..models.molecule_group_source import MoleculeGroupSource

        d = dict(src_dict)
        created_at = isoparse(d.pop("createdAt"))

        def _parse_display_name(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        display_name = _parse_display_name(d.pop("displayName"))

        id = d.pop("id")

        def _parse_matched_on(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        matched_on = _parse_matched_on(d.pop("matchedOn"))

        metadata = MoleculeGroupMetadata.from_dict(d.pop("metadata"))

        molecule_count = d.pop("moleculeCount")

        name = d.pop("name")

        def _parse_schema_id(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        schema_id = _parse_schema_id(d.pop("schemaId"))

        def _parse_source(data: object) -> MoleculeGroupSource | None:
            if data is None:
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                source_type_0 = MoleculeGroupSource.from_dict(data)

                return source_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(MoleculeGroupSource | None, data)

        source = _parse_source(d.pop("source"))

        status = d.pop("status")

        tags = cast(list[str], d.pop("tags"))

        def _parse_type_(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        type_ = _parse_type_(d.pop("type"))

        updated_at = isoparse(d.pop("updatedAt"))

        molecule_group = cls(
            created_at=created_at,
            display_name=display_name,
            id=id,
            matched_on=matched_on,
            metadata=metadata,
            molecule_count=molecule_count,
            name=name,
            schema_id=schema_id,
            source=source,
            status=status,
            tags=tags,
            type_=type_,
            updated_at=updated_at,
        )

        molecule_group.additional_properties = d
        return molecule_group

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
