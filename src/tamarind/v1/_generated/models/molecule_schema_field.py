from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..models.chain_tag import ChainTag
from ..models.chain_type import ChainType
from ..models.molecule_field_type import MoleculeFieldType
from ..types import UNSET, Unset

T = TypeVar("T", bound="MoleculeSchemaField")


@_attrs_define
class MoleculeSchemaField:
    """The spec's `SchemaField` — one field in a schema.

    A RequestModel (extra='forbid') even though it also appears on responses: the
    field names are already the wire spelling, so no alias generator is needed, and
    forbidding extras means a typo'd `chaintype` 422s at create instead of being
    silently stored in the JSONB and never enforced.

    `type` defaults to `string` per the spec. `chain` is one of its values — a
    chain field's `name` IS the chain id (`H`, `L`, `A`), matching the keys of a
    molecule's `entity` map.

        Attributes:
            name (str):
            chain_tag (ChainTag | None | Unset):
            chain_type (ChainType | None | Unset):
            description (None | str | Unset):
            formula (None | str | Unset): Spreadsheet expression computing this field's value per molecule. A field with a
                `formula` is COMPUTED: it is evaluated on read and never stored, so a caller may not supply a value for it.
            options (list[str] | None | Unset): Allowed values for a `category` field. REQUIRED (non-empty) when `type` is
                `category`, and must be omitted for every other type.
            required (bool | Unset):  Default: False.
            type_ (MoleculeFieldType | Unset): The spec's `FieldType`.

                NOTE `chain` is a MEMBER of this enum, not a separate axis: a schema's `fields`
                list interleaves scalar fields and chain fields, and `type == "chain"` is what
                distinguishes them.
            units (None | str | Unset):
    """

    name: str
    chain_tag: ChainTag | None | Unset = UNSET
    chain_type: ChainType | None | Unset = UNSET
    description: None | str | Unset = UNSET
    formula: None | str | Unset = UNSET
    options: list[str] | None | Unset = UNSET
    required: bool | Unset = False
    type_: MoleculeFieldType | Unset = UNSET
    units: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        chain_tag: None | str | Unset
        if isinstance(self.chain_tag, Unset):
            chain_tag = UNSET
        elif isinstance(self.chain_tag, ChainTag):
            chain_tag = self.chain_tag.value
        else:
            chain_tag = self.chain_tag

        chain_type: None | str | Unset
        if isinstance(self.chain_type, Unset):
            chain_type = UNSET
        elif isinstance(self.chain_type, ChainType):
            chain_type = self.chain_type.value
        else:
            chain_type = self.chain_type

        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        formula: None | str | Unset
        if isinstance(self.formula, Unset):
            formula = UNSET
        else:
            formula = self.formula

        options: list[str] | None | Unset
        if isinstance(self.options, Unset):
            options = UNSET
        elif isinstance(self.options, list):
            options = self.options

        else:
            options = self.options

        required = self.required

        type_: str | Unset = UNSET
        if not isinstance(self.type_, Unset):
            type_ = self.type_.value

        units: None | str | Unset
        if isinstance(self.units, Unset):
            units = UNSET
        else:
            units = self.units

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "name": name,
            }
        )
        if chain_tag is not UNSET:
            field_dict["chainTag"] = chain_tag
        if chain_type is not UNSET:
            field_dict["chainType"] = chain_type
        if description is not UNSET:
            field_dict["description"] = description
        if formula is not UNSET:
            field_dict["formula"] = formula
        if options is not UNSET:
            field_dict["options"] = options
        if required is not UNSET:
            field_dict["required"] = required
        if type_ is not UNSET:
            field_dict["type"] = type_
        if units is not UNSET:
            field_dict["units"] = units

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        def _parse_chain_tag(data: object) -> ChainTag | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                chain_tag_type_0 = ChainTag(data)

                return chain_tag_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(ChainTag | None | Unset, data)

        chain_tag = _parse_chain_tag(d.pop("chainTag", UNSET))

        def _parse_chain_type(data: object) -> ChainType | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                chain_type_type_0 = ChainType(data)

                return chain_type_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(ChainType | None | Unset, data)

        chain_type = _parse_chain_type(d.pop("chainType", UNSET))

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_formula(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        formula = _parse_formula(d.pop("formula", UNSET))

        def _parse_options(data: object) -> list[str] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                options_type_0 = cast(list[str], data)

                return options_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[str] | None | Unset, data)

        options = _parse_options(d.pop("options", UNSET))

        required = d.pop("required", UNSET)

        _type_ = d.pop("type", UNSET)
        type_: MoleculeFieldType | Unset
        if isinstance(_type_, Unset):
            type_ = UNSET
        else:
            type_ = MoleculeFieldType(_type_)

        def _parse_units(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        units = _parse_units(d.pop("units", UNSET))

        molecule_schema_field = cls(
            name=name,
            chain_tag=chain_tag,
            chain_type=chain_type,
            description=description,
            formula=formula,
            options=options,
            required=required,
            type_=type_,
            units=units,
        )

        return molecule_schema_field
