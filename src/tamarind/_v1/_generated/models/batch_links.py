from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="BatchLinks")


@_attrs_define
class BatchLinks:
    """
    Attributes:
        files (str): `/jobs/batch_.../files`, the batch's own folder.
        jobs (str): `/jobs?batchId=batch_...`, the batch's jobs.
        self_ (str): `/jobs/batch_...`
    """

    files: str
    jobs: str
    self_: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        files = self.files

        jobs = self.jobs

        self_ = self.self_

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "files": files,
                "jobs": jobs,
                "self": self_,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        files = d.pop("files")

        jobs = d.pop("jobs")

        self_ = d.pop("self")

        batch_links = cls(
            files=files,
            jobs=jobs,
            self_=self_,
        )

        batch_links.additional_properties = d
        return batch_links

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
