from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="ArchiveRequest")


@_attrs_define
class ArchiveRequest:
    """Send at most one of `paths`, `glob` and `bestStructures`; send none for the whole archive.

    Attributes:
        best_structures (bool | Unset): One best structure per job, as the app's "PDBs only" download gives. A job's or
            a batch's stored structures zip when it has one. Otherwise, for a batch submitted as a batch, a zip of each
            Complete job's best structure, chosen by its tool, named after the job, at most 500 or 2 GiB of structures
            (`truncated` is true past either), which may take a while (202, then poll). That build has an 8-minute deadline
            (past it, 503 `jobs_dependency_unavailable`, retryable), and runs one per account at a time (another is 429
            `rate_limited`) and two per server (past that, 503 `service_unavailable`). A job or a design batch
            (`numDesigns`) without one is 422 `not_supported`. With `paths` or `glob` it is 422 `conditional_not_met` at
            `/bestStructures`.
        glob (str | Unset): Matches the whole path inside the archive, case-sensitive, with `*` also matching `/`. For
            example `*.pdb`.
        paths (list[str] | Unset): Paths inside the archive. A job's are the paths `listJobFiles` shows; a batch's
            archive holds each job's files under the job's name, plus its combined files.
    """

    best_structures: bool | Unset = UNSET
    glob: str | Unset = UNSET
    paths: list[str] | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        best_structures = self.best_structures

        glob = self.glob

        paths: list[str] | Unset = UNSET
        if not isinstance(self.paths, Unset):
            paths = self.paths

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if best_structures is not UNSET:
            field_dict["bestStructures"] = best_structures
        if glob is not UNSET:
            field_dict["glob"] = glob
        if paths is not UNSET:
            field_dict["paths"] = paths

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        best_structures = d.pop("bestStructures", UNSET)

        glob = d.pop("glob", UNSET)

        paths = cast(list[str], d.pop("paths", UNSET))

        archive_request = cls(
            best_structures=best_structures,
            glob=glob,
            paths=paths,
        )

        return archive_request
