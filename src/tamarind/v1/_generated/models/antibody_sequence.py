from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="AntibodySequence")


@_attrs_define
class AntibodySequence:
    """An antibody, for `modality: antibody`.

    Attributes:
        heavy (str):
        light (str | Unset):
        name (str | Unset): At most 100 characters once trimmed.
    """

    heavy: str
    light: str | Unset = UNSET
    name: str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        heavy = self.heavy

        light = self.light

        name = self.name

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "heavy": heavy,
            }
        )
        if light is not UNSET:
            field_dict["light"] = light
        if name is not UNSET:
            field_dict["name"] = name

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        heavy = d.pop("heavy")

        light = d.pop("light", UNSET)

        name = d.pop("name", UNSET)

        antibody_sequence = cls(
            heavy=heavy,
            light=light,
            name=name,
        )

        return antibody_sequence
