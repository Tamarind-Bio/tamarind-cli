from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.custom_tool_version_status import CustomToolVersionStatus

if TYPE_CHECKING:
    from ..models.custom_tool_build_error import CustomToolBuildError


T = TypeVar("T", bound="CustomToolVersion")


@_attrs_define
class CustomToolVersion:
    """
    Attributes:
        completed_at (datetime.datetime | None):
        created_at (datetime.datetime):
        error (CustomToolBuildError | None):
        etag (str): Opaque SDK-managed validator for this exact Version snapshot.
        lifetime_etag (str): Opaque SDK-managed validator for the Tool lifetime that owns this Version.
        origin (str):
        source_digest (None | str): SHA-256 digest of this version's source archive. Null when source is hidden.
        source_revision (None | str): Immutable source revision used by this version. Null when source is hidden.
        started_at (datetime.datetime):
        status (CustomToolVersionStatus): Today's build statuses. `Stopped` means the build was canceled or failed, and
            `error` says why when that was recorded. `Complete` and `Stopped` are terminal.
        terminal (bool): Whether the build has reached a final status and will not run again.
        version (str): The version number, such as `v3`.
    """

    completed_at: datetime.datetime | None
    created_at: datetime.datetime
    error: CustomToolBuildError | None
    etag: str
    lifetime_etag: str
    origin: str
    source_digest: None | str
    source_revision: None | str
    started_at: datetime.datetime
    status: CustomToolVersionStatus
    terminal: bool
    version: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.custom_tool_build_error import CustomToolBuildError

        completed_at: None | str
        if isinstance(self.completed_at, datetime.datetime):
            completed_at = self.completed_at.isoformat()
        else:
            completed_at = self.completed_at

        created_at = self.created_at.isoformat()

        error: dict[str, Any] | None
        if isinstance(self.error, CustomToolBuildError):
            error = self.error.to_dict()
        else:
            error = self.error

        etag = self.etag

        lifetime_etag = self.lifetime_etag

        origin = self.origin

        source_digest: None | str
        source_digest = self.source_digest

        source_revision: None | str
        source_revision = self.source_revision

        started_at = self.started_at.isoformat()

        status = self.status.value

        terminal = self.terminal

        version = self.version

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "completedAt": completed_at,
                "createdAt": created_at,
                "error": error,
                "etag": etag,
                "lifetimeEtag": lifetime_etag,
                "origin": origin,
                "sourceDigest": source_digest,
                "sourceRevision": source_revision,
                "startedAt": started_at,
                "status": status,
                "terminal": terminal,
                "version": version,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.custom_tool_build_error import CustomToolBuildError

        d = dict(src_dict)

        def _parse_completed_at(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                completed_at_type_0 = isoparse(data)

                return completed_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        completed_at = _parse_completed_at(d.pop("completedAt"))

        created_at = isoparse(d.pop("createdAt"))

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

        lifetime_etag = d.pop("lifetimeEtag")

        origin = d.pop("origin")

        def _parse_source_digest(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        source_digest = _parse_source_digest(d.pop("sourceDigest"))

        def _parse_source_revision(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        source_revision = _parse_source_revision(d.pop("sourceRevision"))

        started_at = isoparse(d.pop("startedAt"))

        status = CustomToolVersionStatus(d.pop("status"))

        terminal = d.pop("terminal")

        version = d.pop("version")

        custom_tool_version = cls(
            completed_at=completed_at,
            created_at=created_at,
            error=error,
            etag=etag,
            lifetime_etag=lifetime_etag,
            origin=origin,
            source_digest=source_digest,
            source_revision=source_revision,
            started_at=started_at,
            status=status,
            terminal=terminal,
            version=version,
        )

        custom_tool_version.additional_properties = d
        return custom_tool_version

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
