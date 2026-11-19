from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.molecule_schema_field import MoleculeSchemaField


T = TypeVar("T", bound="CreateMoleculeSchemaRequest")


@_attrs_define
class CreateMoleculeSchemaRequest:
    """
    Attributes:
        fields (list[MoleculeSchemaField]):
        name (str):
        org_id (None | str | Unset):
    """

    fields: list[MoleculeSchemaField]
    name: str
    org_id: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        fields = []
        for fields_item_data in self.fields:
            fields_item = fields_item_data.to_dict()
            fields.append(fields_item)

        name = self.name

        org_id: None | str | Unset
        if isinstance(self.org_id, Unset):
            org_id = UNSET
        else:
            org_id = self.org_id

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "fields": fields,
                "name": name,
            }
        )
        if org_id is not UNSET:
            field_dict["orgId"] = org_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.molecule_schema_field import MoleculeSchemaField

        d = dict(src_dict)
        fields = []
        _fields = d.pop("fields")
        for fields_item_data in _fields:
            fields_item = MoleculeSchemaField.from_dict(fields_item_data)

            fields.append(fields_item)

        name = d.pop("name")

        def _parse_org_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        org_id = _parse_org_id(d.pop("orgId", UNSET))

        create_molecule_schema_request = cls(
            fields=fields,
            name=name,
            org_id=org_id,
        )

        return create_molecule_schema_request
