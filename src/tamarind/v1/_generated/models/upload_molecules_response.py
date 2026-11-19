from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Literal, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="UploadMoleculesResponse")


@_attrs_define
class UploadMoleculesResponse:
    """
    Attributes:
        group_id (str):
        group_name (None | str):
        import_id (str):
        molecule_count (int):
        molecule_ids (list[str]):
        status (Literal['pending']):  Default: 'pending'.
    """

    group_id: str
    group_name: None | str
    import_id: str
    molecule_count: int
    molecule_ids: list[str]
    status: Literal["pending"] = "pending"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        group_id = self.group_id

        group_name: None | str
        group_name = self.group_name

        import_id = self.import_id

        molecule_count = self.molecule_count

        molecule_ids = self.molecule_ids

        status = self.status

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "groupId": group_id,
                "groupName": group_name,
                "importId": import_id,
                "moleculeCount": molecule_count,
                "moleculeIds": molecule_ids,
                "status": status,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        group_id = d.pop("groupId")

        def _parse_group_name(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        group_name = _parse_group_name(d.pop("groupName"))

        import_id = d.pop("importId")

        molecule_count = d.pop("moleculeCount")

        molecule_ids = cast(list[str], d.pop("moleculeIds"))

        status = cast(Literal["pending"], d.pop("status"))
        if status != "pending":
            raise ValueError(f"status must match const 'pending', got '{status}'")

        upload_molecules_response = cls(
            group_id=group_id,
            group_name=group_name,
            import_id=import_id,
            molecule_count=molecule_count,
            molecule_ids=molecule_ids,
            status=status,
        )

        upload_molecules_response.additional_properties = d
        return upload_molecules_response

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
