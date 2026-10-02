from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..models.public_version_status import PublicVersionStatus

if TYPE_CHECKING:
    from ..models.public_build_error import PublicBuildError


T = TypeVar("T", bound="PublicVersion")


@_attrs_define
class PublicVersion:
    """
    Attributes:
        completed_at (None | str):
        created_at (str):
        error (None | PublicBuildError):
        etag (str): Opaque SDK-managed validator for this exact Version snapshot.
        lifetime_etag (str): Opaque SDK-managed validator for the Tool lifetime that owns this Version.
        origin (str):
        source_digest (None | str): SHA-256 digest of this version's source archive. Null when source is hidden.
        source_revision (None | str): Immutable source revision used by this version. Null when source is hidden.
        started_at (str):
        status (PublicVersionStatus):
        terminal (bool): Whether the build has reached a final status and will not run again.
        version (str): The version number, such as `v3`.
    """

    completed_at: None | str
    created_at: str
    error: None | PublicBuildError
    etag: str
    lifetime_etag: str
    origin: str
    source_digest: None | str
    source_revision: None | str
    started_at: str
    status: PublicVersionStatus
    terminal: bool
    version: str

    def to_dict(self) -> dict[str, Any]:
        from ..models.public_build_error import PublicBuildError

        completed_at: None | str
        completed_at = self.completed_at

        created_at = self.created_at

        error: dict[str, Any] | None
        if isinstance(self.error, PublicBuildError):
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

        started_at = self.started_at

        status = self.status.value

        terminal = self.terminal

        version = self.version

        field_dict: dict[str, Any] = {}

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
        from ..models.public_build_error import PublicBuildError

        d = dict(src_dict)

        def _parse_completed_at(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        completed_at = _parse_completed_at(d.pop("completedAt"))

        created_at = d.pop("createdAt")

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

        started_at = d.pop("startedAt")

        status = PublicVersionStatus(d.pop("status"))

        terminal = d.pop("terminal")

        version = d.pop("version")

        public_version = cls(
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

        return public_version
