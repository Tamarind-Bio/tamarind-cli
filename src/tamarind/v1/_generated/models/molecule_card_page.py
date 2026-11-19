from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.molecule_card_page_wait_reason_type_0 import MoleculeCardPageWaitReasonType0
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.molecule_card import MoleculeCard


T = TypeVar("T", bound="MoleculeCardPage")


@_attrs_define
class MoleculeCardPage:
    """
    Attributes:
        items (list[MoleculeCard]):
        mode (None | str):
        next_cursor (None | str):
        retry_after_ms (int | None):
        scan_progress (float | None):
        slice_delivered (int | None):
        slice_matched (int | None):
        waiting (bool | None):
        wait_reason (MoleculeCardPageWaitReasonType0 | None | Unset): On a waiting page when a cursor from a
            `searchCaps=persist` request is followed without `searchCaps`. `busy` means transient load; `stuck` means a unit
            needs repeated retries.
    """

    items: list[MoleculeCard]
    mode: None | str
    next_cursor: None | str
    retry_after_ms: int | None
    scan_progress: float | None
    slice_delivered: int | None
    slice_matched: int | None
    waiting: bool | None
    wait_reason: MoleculeCardPageWaitReasonType0 | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        items = []
        for items_item_data in self.items:
            items_item = items_item_data.to_dict()
            items.append(items_item)

        mode: None | str
        mode = self.mode

        next_cursor: None | str
        next_cursor = self.next_cursor

        retry_after_ms: int | None
        retry_after_ms = self.retry_after_ms

        scan_progress: float | None
        scan_progress = self.scan_progress

        slice_delivered: int | None
        slice_delivered = self.slice_delivered

        slice_matched: int | None
        slice_matched = self.slice_matched

        waiting: bool | None
        waiting = self.waiting

        wait_reason: None | str | Unset
        if isinstance(self.wait_reason, Unset):
            wait_reason = UNSET
        elif isinstance(self.wait_reason, MoleculeCardPageWaitReasonType0):
            wait_reason = self.wait_reason.value
        else:
            wait_reason = self.wait_reason

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "items": items,
                "mode": mode,
                "nextCursor": next_cursor,
                "retryAfterMs": retry_after_ms,
                "scanProgress": scan_progress,
                "sliceDelivered": slice_delivered,
                "sliceMatched": slice_matched,
                "waiting": waiting,
            }
        )
        if wait_reason is not UNSET:
            field_dict["waitReason"] = wait_reason

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.molecule_card import MoleculeCard

        d = dict(src_dict)
        items = []
        _items = d.pop("items")
        for items_item_data in _items:
            items_item = MoleculeCard.from_dict(items_item_data)

            items.append(items_item)

        def _parse_mode(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        mode = _parse_mode(d.pop("mode"))

        def _parse_next_cursor(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        next_cursor = _parse_next_cursor(d.pop("nextCursor"))

        def _parse_retry_after_ms(data: object) -> int | None:
            if data is None:
                return data
            return cast(int | None, data)

        retry_after_ms = _parse_retry_after_ms(d.pop("retryAfterMs"))

        def _parse_scan_progress(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        scan_progress = _parse_scan_progress(d.pop("scanProgress"))

        def _parse_slice_delivered(data: object) -> int | None:
            if data is None:
                return data
            return cast(int | None, data)

        slice_delivered = _parse_slice_delivered(d.pop("sliceDelivered"))

        def _parse_slice_matched(data: object) -> int | None:
            if data is None:
                return data
            return cast(int | None, data)

        slice_matched = _parse_slice_matched(d.pop("sliceMatched"))

        def _parse_waiting(data: object) -> bool | None:
            if data is None:
                return data
            return cast(bool | None, data)

        waiting = _parse_waiting(d.pop("waiting"))

        def _parse_wait_reason(data: object) -> MoleculeCardPageWaitReasonType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                wait_reason_type_0 = MoleculeCardPageWaitReasonType0(data)

                return wait_reason_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(MoleculeCardPageWaitReasonType0 | None | Unset, data)

        wait_reason = _parse_wait_reason(d.pop("waitReason", UNSET))

        molecule_card_page = cls(
            items=items,
            mode=mode,
            next_cursor=next_cursor,
            retry_after_ms=retry_after_ms,
            scan_progress=scan_progress,
            slice_delivered=slice_delivered,
            slice_matched=slice_matched,
            waiting=waiting,
            wait_reason=wait_reason,
        )

        molecule_card_page.additional_properties = d
        return molecule_card_page

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
