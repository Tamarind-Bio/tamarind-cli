from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="ArchiveRequest")


@_attrs_define
class ArchiveRequest:
    """
    Attributes:
        glob (str | Unset): For example `*.pdb`.
        paths (list[str] | Unset):
    """

    glob: str | Unset = UNSET
    paths: list[str] | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        glob = self.glob

        paths: list[str] | Unset = UNSET
        if not isinstance(self.paths, Unset):
            paths = self.paths

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if glob is not UNSET:
            field_dict["glob"] = glob
        if paths is not UNSET:
            field_dict["paths"] = paths

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        glob = d.pop("glob", UNSET)

        paths = cast(list[str], d.pop("paths", UNSET))

        archive_request = cls(
            glob=glob,
            paths=paths,
        )

        return archive_request
