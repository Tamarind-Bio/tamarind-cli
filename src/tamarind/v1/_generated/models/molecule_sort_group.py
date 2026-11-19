from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="MoleculeSortGroup")


@_attrs_define
class MoleculeSortGroup:
    """`Molecule.sortGroup` — the group this row was ORDERED BY, under `sortBy=groupName`.

    A molecule can be in many of your groups, so `sortBy=groupName` has to rank it by ONE
    of them: the alphabetically first EFFECTIVE (displayed) name across all your in-scope
    memberships. That group is what makes a group's rows arrive contiguously, and it is
    the group a grouped presentation should file the row under.

    It is served because the inline `groups` list cannot be trusted to contain it: that
    list is CAPPED and selected by membership recency, so a molecule in more groups than
    the cap can be ranked by a group the response never carries. Re-deriving the section
    by name-sorting `groups` then files the row under the wrong heading — silently, and
    with no way for a client to tell.

    `name` is the EFFECTIVE name (the rename label when one exists, else the canonical
    one) — the exact string the ordering compared, so a section header built from it
    cannot disagree with the position the row was served in. That makes it the
    `displayName`-preferring sibling of `Group.name`, which is always the raw canonical
    column; for a group that was never renamed the two are identical.

        Attributes:
            id (str):
            name (str):
    """

    id: str
    name: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        name = self.name

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        name = d.pop("name")

        molecule_sort_group = cls(
            id=id,
            name=name,
        )

        molecule_sort_group.additional_properties = d
        return molecule_sort_group

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
