from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="ItemCounts")


@_attrs_define
class ItemCounts:
    """How many parts are in each status.

    Attributes:
        complete (int):
        failed (int):
        in_queue (int):
        running (int):
        stopped (int):
        total (int):
    """

    complete: int
    failed: int
    in_queue: int
    running: int
    stopped: int
    total: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        complete = self.complete

        failed = self.failed

        in_queue = self.in_queue

        running = self.running

        stopped = self.stopped

        total = self.total

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "complete": complete,
                "failed": failed,
                "inQueue": in_queue,
                "running": running,
                "stopped": stopped,
                "total": total,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        complete = d.pop("complete")

        failed = d.pop("failed")

        in_queue = d.pop("inQueue")

        running = d.pop("running")

        stopped = d.pop("stopped")

        total = d.pop("total")

        item_counts = cls(
            complete=complete,
            failed=failed,
            in_queue=in_queue,
            running=running,
            stopped=stopped,
            total=total,
        )

        item_counts.additional_properties = d
        return item_counts

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
