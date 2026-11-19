from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.molecule_import_status_error_type_0 import MoleculeImportStatusErrorType0


T = TypeVar("T", bound="MoleculeImportStatus")


@_attrs_define
class MoleculeImportStatus:
    """
    Attributes:
        error (MoleculeImportStatusErrorType0 | None): Why a failed import failed, in the ingestion worker's own terms.
            Null otherwise.
        file_format (None | str):
        file_name (None | str):
        group_id (None | str):
        group_name (None | str):
        id (str):
        molecule_count (int | None):
        molecule_ids (list[str] | None):
        status (str):
    """

    error: MoleculeImportStatusErrorType0 | None
    file_format: None | str
    file_name: None | str
    group_id: None | str
    group_name: None | str
    id: str
    molecule_count: int | None
    molecule_ids: list[str] | None
    status: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.molecule_import_status_error_type_0 import MoleculeImportStatusErrorType0

        error: dict[str, Any] | None
        if isinstance(self.error, MoleculeImportStatusErrorType0):
            error = self.error.to_dict()
        else:
            error = self.error

        file_format: None | str
        file_format = self.file_format

        file_name: None | str
        file_name = self.file_name

        group_id: None | str
        group_id = self.group_id

        group_name: None | str
        group_name = self.group_name

        id = self.id

        molecule_count: int | None
        molecule_count = self.molecule_count

        molecule_ids: list[str] | None
        if isinstance(self.molecule_ids, list):
            molecule_ids = self.molecule_ids

        else:
            molecule_ids = self.molecule_ids

        status = self.status

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "error": error,
                "fileFormat": file_format,
                "fileName": file_name,
                "groupId": group_id,
                "groupName": group_name,
                "id": id,
                "moleculeCount": molecule_count,
                "moleculeIds": molecule_ids,
                "status": status,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.molecule_import_status_error_type_0 import MoleculeImportStatusErrorType0

        d = dict(src_dict)

        def _parse_error(data: object) -> MoleculeImportStatusErrorType0 | None:
            if data is None:
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                error_type_0 = MoleculeImportStatusErrorType0.from_dict(data)

                return error_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(MoleculeImportStatusErrorType0 | None, data)

        error = _parse_error(d.pop("error"))

        def _parse_file_format(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        file_format = _parse_file_format(d.pop("fileFormat"))

        def _parse_file_name(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        file_name = _parse_file_name(d.pop("fileName"))

        def _parse_group_id(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        group_id = _parse_group_id(d.pop("groupId"))

        def _parse_group_name(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        group_name = _parse_group_name(d.pop("groupName"))

        id = d.pop("id")

        def _parse_molecule_count(data: object) -> int | None:
            if data is None:
                return data
            return cast(int | None, data)

        molecule_count = _parse_molecule_count(d.pop("moleculeCount"))

        def _parse_molecule_ids(data: object) -> list[str] | None:
            if data is None:
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                molecule_ids_type_0 = cast(list[str], data)

                return molecule_ids_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[str] | None, data)

        molecule_ids = _parse_molecule_ids(d.pop("moleculeIds"))

        status = d.pop("status")

        molecule_import_status = cls(
            error=error,
            file_format=file_format,
            file_name=file_name,
            group_id=group_id,
            group_name=group_name,
            id=id,
            molecule_count=molecule_count,
            molecule_ids=molecule_ids,
            status=status,
        )

        molecule_import_status.additional_properties = d
        return molecule_import_status

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
