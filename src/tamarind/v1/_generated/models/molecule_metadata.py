from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="MoleculeMetadata")


@_attrs_define
class MoleculeMetadata:
    """TWO namespaces in one map, and knowing which is which is what makes `filter` work.

    A key naming a TOOL holds a LIST of that tool's score runs — `{"protenix": [{"jobId": "...", "runId": "...",
    "ipSAE_AB": 0.62}]}`. Any other key is a SCALAR annotation you set yourself — `{"affinity_nM": 12.4}`.

    One carve-out: a key naming a COMPUTED schema field holds that formula's value, evaluated on read and never stored.
    It is READ-ONLY — you cannot set it here — and `filter`/`sortBy` do not address it, because they resolve against
    stored values and a computed field has none.

    Filter and sort address the two writable namespaces differently: a tool score is the DOTTED path `protenix.ipSAE_AB`
    (`?filter=protenix.ipSAE_AB:gte:0.5`), and a scalar is the BARE key (`?filter=affinity_nM:lte:50`). Metric names are
    case-sensitive and must match what you see here. `exists` applies to scalar keys only; to ask whether a tool
    reported a metric, filter on its value instead.

    Each run entry carries `jobId` AND `runId`, which answer different questions. `jobId` is the DISPATCH that produced
    the entry, and the engine dispatches one job per molecule — so the same run has a different `jobId` on every
    molecule and grouping a page by it yields one group per molecule. `runId` is the run — the pipeline NODE RUN, where
    there is one — and is the field to group by. Pass it straight back as `nodeRunId` to list everything that node run
    produced; the `nr-` prefix a pipeline run carries is accepted as-is, and `nodeRuns[].id` (the bare uuid) names the
    same run.

    """

    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        molecule_metadata = cls()

        molecule_metadata.additional_properties = d
        return molecule_metadata

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
