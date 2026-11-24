from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="JobLogChunk")


@_attrs_define
class JobLogChunk:
    """
    Attributes:
        complete (bool): Whether the job or batch has finished (`Complete`, `Stopped` or `Failed`, by the status
            `getJob` shows), so nothing more will be written. False while it may still write to its log. A batch is finished
            once every job in it is.
        content (str):
        next_cursor (None | str): Fetches OLDER output. Null when at the start of the log.
    """

    complete: bool
    content: str
    next_cursor: None | str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        complete = self.complete

        content = self.content

        next_cursor: None | str
        next_cursor = self.next_cursor

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "complete": complete,
                "content": content,
                "nextCursor": next_cursor,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        complete = d.pop("complete")

        content = d.pop("content")

        def _parse_next_cursor(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        next_cursor = _parse_next_cursor(d.pop("nextCursor"))

        job_log_chunk = cls(
            complete=complete,
            content=content,
            next_cursor=next_cursor,
        )

        job_log_chunk.additional_properties = d
        return job_log_chunk

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
