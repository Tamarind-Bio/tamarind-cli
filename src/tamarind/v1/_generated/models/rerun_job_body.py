from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..models.rerun_job_body_only import RerunJobBodyOnly
from ..types import UNSET, Unset

T = TypeVar("T", bound="RerunJobBody")


@_attrs_define
class RerunJobBody:
    """
    Attributes:
        only (RerunJobBodyOnly | Unset): For a batch, which of its jobs to rerun. `incomplete` skips the `Complete`
            ones. Default: RerunJobBodyOnly.ALL.
    """

    only: RerunJobBodyOnly | Unset = RerunJobBodyOnly.ALL

    def to_dict(self) -> dict[str, Any]:
        only: str | Unset = UNSET
        if not isinstance(self.only, Unset):
            only = self.only.value

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if only is not UNSET:
            field_dict["only"] = only

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _only = d.pop("only", UNSET)
        only: RerunJobBodyOnly | Unset
        if isinstance(_only, Unset):
            only = UNSET
        else:
            only = RerunJobBodyOnly(_only)

        rerun_job_body = cls(
            only=only,
        )

        return rerun_job_body
