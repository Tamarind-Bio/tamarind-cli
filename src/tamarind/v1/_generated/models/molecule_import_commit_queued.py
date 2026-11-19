from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Literal, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="MoleculeImportCommitQueued")


@_attrs_define
class MoleculeImportCommitQueued:
    """Returned after the import is queued.

    Attributes:
        group_name (None | str):
        id (str):
        status (Literal['queued']):  Default: 'queued'.
    """

    group_name: None | str
    id: str
    status: Literal["queued"] = "queued"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        group_name: None | str
        group_name = self.group_name

        id = self.id

        status = self.status

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "groupName": group_name,
                "id": id,
                "status": status,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_group_name(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        group_name = _parse_group_name(d.pop("groupName"))

        id = d.pop("id")

        status = cast(Literal["queued"], d.pop("status"))
        if status != "queued":
            raise ValueError(f"status must match const 'queued', got '{status}'")

        molecule_import_commit_queued = cls(
            group_name=group_name,
            id=id,
            status=status,
        )

        molecule_import_commit_queued.additional_properties = d
        return molecule_import_commit_queued

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
