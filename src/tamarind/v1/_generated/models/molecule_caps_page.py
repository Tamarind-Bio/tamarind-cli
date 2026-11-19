from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.molecule_caps_page_wait_reason_type_0 import MoleculeCapsPageWaitReasonType0
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.molecule import Molecule


T = TypeVar("T", bound="MoleculeCapsPage")


@_attrs_define
class MoleculeCapsPage:
    """
    Attributes:
        caps (list[str]):
        items (list[Molecule]):
        mode (None | str):
        next_cursor (None | str):
        scan_progress (float | None):
        retry_after_ms (int | None | Unset):
        slice_delivered (int | None | Unset):
        slice_matched (int | None | Unset):
        wait_reason (MoleculeCapsPageWaitReasonType0 | None | Unset): On a waiting page when you asked for
            `searchCaps=persist`. `busy` means transient load; `stuck` means a unit needs repeated retries.
        waiting (bool | None | Unset):
    """

    caps: list[str]
    items: list[Molecule]
    mode: None | str
    next_cursor: None | str
    scan_progress: float | None
    retry_after_ms: int | None | Unset = UNSET
    slice_delivered: int | None | Unset = UNSET
    slice_matched: int | None | Unset = UNSET
    wait_reason: MoleculeCapsPageWaitReasonType0 | None | Unset = UNSET
    waiting: bool | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        caps = self.caps

        items = []
        for items_item_data in self.items:
            items_item = items_item_data.to_dict()
            items.append(items_item)

        mode: None | str
        mode = self.mode

        next_cursor: None | str
        next_cursor = self.next_cursor

        scan_progress: float | None
        scan_progress = self.scan_progress

        retry_after_ms: int | None | Unset
        if isinstance(self.retry_after_ms, Unset):
            retry_after_ms = UNSET
        else:
            retry_after_ms = self.retry_after_ms

        slice_delivered: int | None | Unset
        if isinstance(self.slice_delivered, Unset):
            slice_delivered = UNSET
        else:
            slice_delivered = self.slice_delivered

        slice_matched: int | None | Unset
        if isinstance(self.slice_matched, Unset):
            slice_matched = UNSET
        else:
            slice_matched = self.slice_matched

        wait_reason: None | str | Unset
        if isinstance(self.wait_reason, Unset):
            wait_reason = UNSET
        elif isinstance(self.wait_reason, MoleculeCapsPageWaitReasonType0):
            wait_reason = self.wait_reason.value
        else:
            wait_reason = self.wait_reason

        waiting: bool | None | Unset
        if isinstance(self.waiting, Unset):
            waiting = UNSET
        else:
            waiting = self.waiting

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "caps": caps,
                "items": items,
                "mode": mode,
                "nextCursor": next_cursor,
                "scanProgress": scan_progress,
            }
        )
        if retry_after_ms is not UNSET:
            field_dict["retryAfterMs"] = retry_after_ms
        if slice_delivered is not UNSET:
            field_dict["sliceDelivered"] = slice_delivered
        if slice_matched is not UNSET:
            field_dict["sliceMatched"] = slice_matched
        if wait_reason is not UNSET:
            field_dict["waitReason"] = wait_reason
        if waiting is not UNSET:
            field_dict["waiting"] = waiting

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.molecule import Molecule

        d = dict(src_dict)
        caps = cast(list[str], d.pop("caps"))

        items = []
        _items = d.pop("items")
        for items_item_data in _items:
            items_item = Molecule.from_dict(items_item_data)

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

        def _parse_scan_progress(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        scan_progress = _parse_scan_progress(d.pop("scanProgress"))

        def _parse_retry_after_ms(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        retry_after_ms = _parse_retry_after_ms(d.pop("retryAfterMs", UNSET))

        def _parse_slice_delivered(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        slice_delivered = _parse_slice_delivered(d.pop("sliceDelivered", UNSET))

        def _parse_slice_matched(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        slice_matched = _parse_slice_matched(d.pop("sliceMatched", UNSET))

        def _parse_wait_reason(data: object) -> MoleculeCapsPageWaitReasonType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                wait_reason_type_0 = MoleculeCapsPageWaitReasonType0(data)

                return wait_reason_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(MoleculeCapsPageWaitReasonType0 | None | Unset, data)

        wait_reason = _parse_wait_reason(d.pop("waitReason", UNSET))

        def _parse_waiting(data: object) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        waiting = _parse_waiting(d.pop("waiting", UNSET))

        molecule_caps_page = cls(
            caps=caps,
            items=items,
            mode=mode,
            next_cursor=next_cursor,
            scan_progress=scan_progress,
            retry_after_ms=retry_after_ms,
            slice_delivered=slice_delivered,
            slice_matched=slice_matched,
            wait_reason=wait_reason,
            waiting=waiting,
        )

        molecule_caps_page.additional_properties = d
        return molecule_caps_page

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
