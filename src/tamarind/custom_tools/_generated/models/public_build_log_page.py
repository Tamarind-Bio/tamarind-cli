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
        etag (str): Opaque SDK-managed validator for the current Version snapshot.
        items (list[PublicBuildEvent]):
        lifetime_etag (str): Opaque SDK-managed validator for the Tool lifetime that owns this Version.
        next_cursor (None | str): Pass as `cursor` for the next page. Null when there are no more events.
        status (PublicVersionStatus):
        version (str): The version these log events belong to, such as `v3`.
    """

    error: None | PublicBuildError
    etag: str
    items: list[PublicBuildEvent]
    lifetime_etag: str
    next_cursor: None | str
    status: PublicVersionStatus
    version: str

    def to_dict(self) -> dict[str, Any]:
        from ..models.public_build_error import PublicBuildError

        error: dict[str, Any] | None
        if isinstance(self.error, PublicBuildError):
            error = self.error.to_dict()
        else:
            error = self.error

        etag = self.etag

        items = []
        for items_item_data in self.items:
            items_item = items_item_data.to_dict()
            items.append(items_item)

        lifetime_etag = self.lifetime_etag

        next_cursor: None | str
        next_cursor = self.next_cursor

        status = self.status.value

        version = self.version

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "error": error,
                "etag": etag,
                "items": items,
                "lifetimeEtag": lifetime_etag,
                "nextCursor": next_cursor,
                "status": status,
                "version": version,
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

        etag = d.pop("etag")

        items = []
        _items = d.pop("items")
        for items_item_data in _items:
            items_item = PublicBuildEvent.from_dict(items_item_data)

            items.append(items_item)

        lifetime_etag = d.pop("lifetimeEtag")

        def _parse_next_cursor(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        next_cursor = _parse_next_cursor(d.pop("nextCursor"))

        status = PublicVersionStatus(d.pop("status"))

        version = d.pop("version")

        public_build_log_page = cls(
            error=error,
            etag=etag,
            items=items,
            lifetime_etag=lifetime_etag,
            next_cursor=next_cursor,
            status=status,
            version=version,
        )

        return public_build_log_page
