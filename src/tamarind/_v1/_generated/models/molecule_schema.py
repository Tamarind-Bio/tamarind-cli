from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

if TYPE_CHECKING:
    from ..models.molecule_schema_field import MoleculeSchemaField


T = TypeVar("T", bound="MoleculeSchema")


@_attrs_define
class MoleculeSchema:
    """The spec's `Schema`.

    Attributes:
        created_at (datetime.datetime):
        fields (list[MoleculeSchemaField]):
        id (str):
        name (str):
    """

    created_at: datetime.datetime
    fields: list[MoleculeSchemaField]
    id: str
    name: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        created_at = self.created_at.isoformat()

        fields = []
        for fields_item_data in self.fields:
            fields_item = fields_item_data.to_dict()
            fields.append(fields_item)

        id = self.id

        name = self.name

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "createdAt": created_at,
                "fields": fields,
                "id": id,
                "name": name,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.molecule_schema_field import MoleculeSchemaField

        d = dict(src_dict)
        created_at = isoparse(d.pop("createdAt"))

        fields = []
        _fields = d.pop("fields")
        for fields_item_data in _fields:
            fields_item = MoleculeSchemaField.from_dict(fields_item_data)

            fields.append(fields_item)

        id = d.pop("id")

        name = d.pop("name")

        molecule_schema = cls(
            created_at=created_at,
            fields=fields,
            id=id,
            name=name,
        )

        molecule_schema.additional_properties = d
        return molecule_schema

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
