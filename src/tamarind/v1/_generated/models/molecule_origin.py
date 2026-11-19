from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="MoleculeOrigin")


@_attrs_define
class MoleculeOrigin:
    """`Molecule.origin` — how this molecule came to exist.

    `type` is the `complexes.origin_type` provenance class and is ALWAYS present (an
    uploaded molecule is `user_import`). `jobId`/`jobType` name the job behind a tool-produced
    molecule, `jobType` being the tool; for a plain batch submission `jobId` is the batch's own
    id rather than the run inside it, and it is that id `GET /molecules?jobId=` takes. A split
    design batch carries one of its runs' ids instead, as do molecules ingested before batches
    began naming the parent.
    BOTH are null for an upload — an upload has no job, and
    we do not fabricate one. Read-only, projected from columns that already exist (no
    migration).

        Attributes:
            job_id (None | str): The job's bare stored id, without the `job_` or `batch_` prefix `/jobs` uses.
            job_type (None | str):
            type_ (str):
    """

    job_id: None | str
    job_type: None | str
    type_: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        job_id: None | str
        job_id = self.job_id

        job_type: None | str
        job_type = self.job_type

        type_ = self.type_

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "jobId": job_id,
                "jobType": job_type,
                "type": type_,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_job_id(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        job_id = _parse_job_id(d.pop("jobId"))

        def _parse_job_type(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        job_type = _parse_job_type(d.pop("jobType"))

        type_ = d.pop("type")

        molecule_origin = cls(
            job_id=job_id,
            job_type=job_type,
            type_=type_,
        )

        molecule_origin.additional_properties = d
        return molecule_origin

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
