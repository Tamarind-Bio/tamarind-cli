from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..models.molecule_type import MoleculeType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.create_molecule_group_request_metadata import CreateMoleculeGroupRequestMetadata


T = TypeVar("T", bound="CreateMoleculeGroupRequest")


@_attrs_define
class CreateMoleculeGroupRequest:
    """The spec's `CreateGroupRequest`.

    Inline group creation was dropped from upload/import, so this is now the ONLY
    way a group comes into existence on the public surface.

        Attributes:
            name (str):
            metadata (CreateMoleculeGroupRequestMetadata | Unset):
            org_id (None | str | Unset):
            schema_id (None | str | Unset):
            tags (list[str] | Unset):
            type_ (MoleculeType | None | Unset):
    """

    name: str
    metadata: CreateMoleculeGroupRequestMetadata | Unset = UNSET
    org_id: None | str | Unset = UNSET
    schema_id: None | str | Unset = UNSET
    tags: list[str] | Unset = UNSET
    type_: MoleculeType | None | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        metadata: dict[str, Any] | Unset = UNSET
        if not isinstance(self.metadata, Unset):
            metadata = self.metadata.to_dict()

        org_id: None | str | Unset
        if isinstance(self.org_id, Unset):
            org_id = UNSET
        else:
            org_id = self.org_id

        schema_id: None | str | Unset
        if isinstance(self.schema_id, Unset):
            schema_id = UNSET
        else:
            schema_id = self.schema_id

        tags: list[str] | Unset = UNSET
        if not isinstance(self.tags, Unset):
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
                "name": name,
            }
        )
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if org_id is not UNSET:
            field_dict["orgId"] = org_id
        if schema_id is not UNSET:
            field_dict["schemaId"] = schema_id
        if tags is not UNSET:
            field_dict["tags"] = tags
        if type_ is not UNSET:
            field_dict["type"] = type_

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.create_molecule_group_request_metadata import (
            CreateMoleculeGroupRequestMetadata,
        )

        d = dict(src_dict)
        name = d.pop("name")

        _metadata = d.pop("metadata", UNSET)
        metadata: CreateMoleculeGroupRequestMetadata | Unset
        if isinstance(_metadata, Unset):
            metadata = UNSET
        else:
            metadata = CreateMoleculeGroupRequestMetadata.from_dict(_metadata)

        def _parse_org_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        org_id = _parse_org_id(d.pop("orgId", UNSET))

        def _parse_schema_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        schema_id = _parse_schema_id(d.pop("schemaId", UNSET))

        tags = cast(list[str], d.pop("tags", UNSET))

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

        create_molecule_group_request = cls(
            name=name,
            metadata=metadata,
            org_id=org_id,
            schema_id=schema_id,
            tags=tags,
            type_=type_,
        )

        return create_molecule_group_request
