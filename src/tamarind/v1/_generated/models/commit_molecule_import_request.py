from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.commit_molecule_import_request_column_mapping_type_0 import (
        CommitMoleculeImportRequestColumnMappingType0,
    )


T = TypeVar("T", bound="CommitMoleculeImportRequest")


@_attrs_define
class CommitMoleculeImportRequest:
    """The spec's `CommitRequest` — optional overrides applied at commit time.

    Attributes:
        column_mapping (CommitMoleculeImportRequestColumnMappingType0 | None | Unset):
    """

    column_mapping: CommitMoleculeImportRequestColumnMappingType0 | None | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.commit_molecule_import_request_column_mapping_type_0 import (
            CommitMoleculeImportRequestColumnMappingType0,
        )

        column_mapping: dict[str, Any] | None | Unset
        if isinstance(self.column_mapping, Unset):
            column_mapping = UNSET
        elif isinstance(self.column_mapping, CommitMoleculeImportRequestColumnMappingType0):
            column_mapping = self.column_mapping.to_dict()
        else:
            column_mapping = self.column_mapping

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if column_mapping is not UNSET:
            field_dict["columnMapping"] = column_mapping

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.commit_molecule_import_request_column_mapping_type_0 import (
            CommitMoleculeImportRequestColumnMappingType0,
        )

        d = dict(src_dict)

        def _parse_column_mapping(
            data: object,
        ) -> CommitMoleculeImportRequestColumnMappingType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                column_mapping_type_0 = CommitMoleculeImportRequestColumnMappingType0.from_dict(
                    data
                )

                return column_mapping_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(CommitMoleculeImportRequestColumnMappingType0 | None | Unset, data)

        column_mapping = _parse_column_mapping(d.pop("columnMapping", UNSET))

        commit_molecule_import_request = cls(
            column_mapping=column_mapping,
        )

        return commit_molecule_import_request
