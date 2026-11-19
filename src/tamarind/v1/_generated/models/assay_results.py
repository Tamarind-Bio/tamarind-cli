from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.assay_results_status import AssayResultsStatus

if TYPE_CHECKING:
    from ..models.assay_results_files_item import AssayResultsFilesItem


T = TypeVar("T", bound="AssayResults")


@_attrs_define
class AssayResults:
    """
    Attributes:
        assay_id (str):
        available (bool): Whether there is anything to download now. It stays false on an order that ended without
            results, so poll only while `status` is not `failed`, `cancelled` or `rejected`.
        complete (bool): Whether this is the full result set. It can be false while `available` is true: a file could
            not be linked yet (`missingFiles`), the lab's own links (Adaptyv's data package) could not be fetched in time,
            files fetched from the lab are not yet recorded on the order (the next read records them), the lab's delivery
            failed, or a GenScript report was collected before the order completed and may still grow.
        expires_at (datetime.datetime | None): The latest that `files` links stop working. A lab's own link can stop
            sooner. Null when there are no files.
        files (list[AssayResultsFilesItem]):
        missing_files (list[str]): Names of files the lab sent that cannot be linked yet.
        status (AssayResultsStatus):
    """

    assay_id: str
    available: bool
    complete: bool
    expires_at: datetime.datetime | None
    files: list[AssayResultsFilesItem]
    missing_files: list[str]
    status: AssayResultsStatus
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        assay_id = self.assay_id

        available = self.available

        complete = self.complete

        expires_at: None | str
        if isinstance(self.expires_at, datetime.datetime):
            expires_at = self.expires_at.isoformat()
        else:
            expires_at = self.expires_at

        files = []
        for files_item_data in self.files:
            files_item = files_item_data.to_dict()
            files.append(files_item)

        missing_files = self.missing_files

        status = self.status.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "assayId": assay_id,
                "available": available,
                "complete": complete,
                "expiresAt": expires_at,
                "files": files,
                "missingFiles": missing_files,
                "status": status,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.assay_results_files_item import AssayResultsFilesItem

        d = dict(src_dict)
        assay_id = d.pop("assayId")

        available = d.pop("available")

        complete = d.pop("complete")

        def _parse_expires_at(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                expires_at_type_0 = isoparse(data)

                return expires_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        expires_at = _parse_expires_at(d.pop("expiresAt"))

        files = []
        _files = d.pop("files")
        for files_item_data in _files:
            files_item = AssayResultsFilesItem.from_dict(files_item_data)

            files.append(files_item)

        missing_files = cast(list[str], d.pop("missingFiles"))

        status = AssayResultsStatus(d.pop("status"))

        assay_results = cls(
            assay_id=assay_id,
            available=available,
            complete=complete,
            expires_at=expires_at,
            files=files,
            missing_files=missing_files,
            status=status,
        )

        assay_results.additional_properties = d
        return assay_results

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
