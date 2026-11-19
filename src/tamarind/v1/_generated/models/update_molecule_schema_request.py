from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.molecule_schema_field import MoleculeSchemaField


T = TypeVar("T", bound="UpdateMoleculeSchemaRequest")


@_attrs_define
class UpdateMoleculeSchemaRequest:
    """The spec's `UpdateSchemaRequest` — partial. `fields` REPLACES the whole
    list; omitted keys are left unchanged.

        Attributes:
            fields (list[MoleculeSchemaField] | None | Unset):
            name (None | str | Unset):
    """

    fields: list[MoleculeSchemaField] | None | Unset = UNSET
    name: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        fields: list[dict[str, Any]] | None | Unset
        if isinstance(self.fields, Unset):
            fields = UNSET
        elif isinstance(self.fields, list):
            fields = []
            for fields_type_0_item_data in self.fields:
                fields_type_0_item = fields_type_0_item_data.to_dict()
                fields.append(fields_type_0_item)

        else:
            fields = self.fields

        name: None | str | Unset
        if isinstance(self.name, Unset):
            name = UNSET
        else:
            name = self.name

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if fields is not UNSET:
            field_dict["fields"] = fields
        if name is not UNSET:
            field_dict["name"] = name

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.molecule_schema_field import MoleculeSchemaField

        d = dict(src_dict)

        def _parse_fields(data: object) -> list[MoleculeSchemaField] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                fields_type_0 = []
                _fields_type_0 = data
                for fields_type_0_item_data in _fields_type_0:
                    fields_type_0_item = MoleculeSchemaField.from_dict(fields_type_0_item_data)

                    fields_type_0.append(fields_type_0_item)

                return fields_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[MoleculeSchemaField] | None | Unset, data)

        fields = _parse_fields(d.pop("fields", UNSET))

        def _parse_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        name = _parse_name(d.pop("name", UNSET))

        update_molecule_schema_request = cls(
            fields=fields,
            name=name,
        )

        return update_molecule_schema_request
