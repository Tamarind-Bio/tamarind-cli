from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="ScoreObservationQuery")


@_attrs_define
class ScoreObservationQuery:
    """One bounded, explicit concrete-job observation read.

    Attributes:
        job_ids (list[str]): Takes the `job_` or `batch_` ids from `/jobs`, or bare stored ids. Observations report the
            bare stored id.
        cursor (None | str | Unset):
        limit (int | Unset):  Default: 50.
        tool (None | str | Unset):
    """

    job_ids: list[str]
    cursor: None | str | Unset = UNSET
    limit: int | Unset = 50
    tool: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        job_ids = self.job_ids

        cursor: None | str | Unset
        if isinstance(self.cursor, Unset):
            cursor = UNSET
        else:
            cursor = self.cursor

        limit = self.limit

        tool: None | str | Unset
        if isinstance(self.tool, Unset):
            tool = UNSET
        else:
            tool = self.tool

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "jobIds": job_ids,
            }
        )
        if cursor is not UNSET:
            field_dict["cursor"] = cursor
        if limit is not UNSET:
            field_dict["limit"] = limit
        if tool is not UNSET:
            field_dict["tool"] = tool

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        job_ids = cast(list[str], d.pop("jobIds"))

        def _parse_cursor(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        cursor = _parse_cursor(d.pop("cursor", UNSET))

        limit = d.pop("limit", UNSET)

        def _parse_tool(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        tool = _parse_tool(d.pop("tool", UNSET))

        score_observation_query = cls(
            job_ids=job_ids,
            cursor=cursor,
            limit=limit,
            tool=tool,
        )

        return score_observation_query
