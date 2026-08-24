from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..models.public_version_status import PublicVersionStatus

if TYPE_CHECKING:
    from ..models.public_build_error import PublicBuildError
    from ..models.public_build_event import PublicBuildEvent


T = TypeVar("T", bound="PublicBuildLogPage")


@_attrs_define
class PublicBuildLogPage:
    """
    Attributes:
        error (None | PublicBuildError):
        items (list[PublicBuildEvent]):
        next_cursor (None | str): Pass as `cursor` for the next page. Null when there are no more events.
        status (PublicVersionStatus):
    """

    error: None | PublicBuildError
    items: list[PublicBuildEvent]
    next_cursor: None | str
    status: PublicVersionStatus

    def to_dict(self) -> dict[str, Any]:
        from ..models.public_build_error import PublicBuildError

        error: dict[str, Any] | None
        if isinstance(self.error, PublicBuildError):
            error = self.error.to_dict()
        else:
            error = self.error

        items = []
        for items_item_data in self.items:
            items_item = items_item_data.to_dict()
            items.append(items_item)

        next_cursor: None | str
        next_cursor = self.next_cursor

        status = self.status.value

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "error": error,
                "items": items,
                "nextCursor": next_cursor,
                "status": status,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.public_build_error import PublicBuildError
        from ..models.public_build_event import PublicBuildEvent

        d = dict(src_dict)

        def _parse_error(data: object) -> None | PublicBuildError:
            if data is None:
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                error_type_0 = PublicBuildError.from_dict(data)

                return error_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | PublicBuildError, data)

        error = _parse_error(d.pop("error"))

        items = []
        _items = d.pop("items")
        for items_item_data in _items:
            items_item = PublicBuildEvent.from_dict(items_item_data)

            items.append(items_item)

        def _parse_next_cursor(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        next_cursor = _parse_next_cursor(d.pop("nextCursor"))

        status = PublicVersionStatus(d.pop("status"))

        public_build_log_page = cls(
            error=error,
            items=items,
            next_cursor=next_cursor,
            status=status,
        )

        return public_build_log_page
