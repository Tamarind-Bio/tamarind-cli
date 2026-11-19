from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

T = TypeVar("T", bound="RemoveMoleculesRequest")


@_attrs_define
class RemoveMoleculesRequest:
    """Body for `POST /molecules/groups/{groupId}/molecules/remove`: the molecules to detach from the group in the path.
    Same `moleculeIds` cap (maxItems, a real statement bound — every id is a bound `uuid[]` parameter, never inlined).

        Attributes:
            molecule_ids (list[str]):
    """

    molecule_ids: list[str]

    def to_dict(self) -> dict[str, Any]:
        molecule_ids = self.molecule_ids

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "moleculeIds": molecule_ids,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        molecule_ids = cast(list[str], d.pop("moleculeIds"))

        remove_molecules_request = cls(
            molecule_ids=molecule_ids,
        )

        return remove_molecules_request
