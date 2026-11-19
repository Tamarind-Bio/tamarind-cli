from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.custom_tool_version_status import CustomToolVersionStatus

if TYPE_CHECKING:
    from ..models.custom_tool_build_error import CustomToolBuildError
    from ..models.custom_tool_build_event import CustomToolBuildEvent


T = TypeVar("T", bound="CustomToolBuildLogPage")


@_attrs_define
class CustomToolBuildLogPage:
    """
    Attributes:
        error (CustomToolBuildError | None):
        etag (str): Opaque SDK-managed validator for the current Version snapshot.
        items (list[CustomToolBuildEvent]):
        lifetime_etag (str): Opaque SDK-managed validator for the Tool lifetime that owns this Version.
        next_cursor (None | str): Pass as `cursor` for the next page. Null when there are no more events.
        status (CustomToolVersionStatus): Today's build statuses. `Stopped` means the build was canceled or failed, and
            `error` says why when that was recorded. `Complete` and `Stopped` are terminal.
        version (str): The version these log events belong to, such as `v3`.
    """

    error: CustomToolBuildError | None
    etag: str
    items: list[CustomToolBuildEvent]
    lifetime_etag: str
    next_cursor: None | str
    status: CustomToolVersionStatus
    version: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.custom_tool_build_error import CustomToolBuildError

        error: dict[str, Any] | None
        if isinstance(self.error, CustomToolBuildError):
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
        field_dict.update(self.additional_properties)
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
        from ..models.custom_tool_build_error import CustomToolBuildError
        from ..models.custom_tool_build_event import CustomToolBuildEvent

        d = dict(src_dict)

        def _parse_error(data: object) -> CustomToolBuildError | None:
            if data is None:
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                error_type_0 = CustomToolBuildError.from_dict(data)

                return error_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(CustomToolBuildError | None, data)

        error = _parse_error(d.pop("error"))

        etag = d.pop("etag")

        items = []
        _items = d.pop("items")
        for items_item_data in _items:
            items_item = CustomToolBuildEvent.from_dict(items_item_data)

            items.append(items_item)

        lifetime_etag = d.pop("lifetimeEtag")

        def _parse_next_cursor(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        next_cursor = _parse_next_cursor(d.pop("nextCursor"))

        status = CustomToolVersionStatus(d.pop("status"))

        version = d.pop("version")

        custom_tool_build_log_page = cls(
            error=error,
            etag=etag,
            items=items,
            lifetime_etag=lifetime_etag,
            next_cursor=next_cursor,
            status=status,
            version=version,
        )

        custom_tool_build_log_page.additional_properties = d
        return custom_tool_build_log_page

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
