from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.molecule_chainmapping import MoleculeChainmapping
    from ..models.molecule_entity import MoleculeEntity
    from ..models.molecule_files import MoleculeFiles
    from ..models.molecule_group import MoleculeGroup
    from ..models.molecule_metadata import MoleculeMetadata
    from ..models.molecule_origin import MoleculeOrigin
    from ..models.molecule_sort_group import MoleculeSortGroup


T = TypeVar("T", bound="Molecule")


@_attrs_define
class Molecule:
    """One molecule, everything inline — no follow-up call to read scores.

    Attributes:
        added_at (datetime.datetime | None):
        chain_mapping (MoleculeChainmapping): Per-chain detail, keyed by the same chain ids as `entity`: its `type` and
            any `tags`.
        created_at (datetime.datetime | None):
        created_by (None | str):
        entity (MoleculeEntity): The molecule's chains: chain id -> the chain's sequence — amino acids for a protein,
            nucleotides for a nucleic acid, or a SMILES string for a small molecule. `chainMapping[<chain id>].type` says
            which.
        files (MoleculeFiles): Structures and other artifacts, keyed by the PRODUCER that made them — a tool name
            (`alphafold`, `protenix`) or `user` for your own uploads. Each entry carries a short-lived signed `downloadUrl`.
            This is where `hasStructure: true` resolves to an actual file. It can be EMPTY on the org-wide listing even for
            a molecule that has a structure: with no group to relabel a chain-bearing file's chains against, those files are
            served without a link and dropped — pass `group`, or read the molecule by id.
        groups (list[MoleculeGroup]):
        has_structure (bool): Whether this molecule has a structure at all (a pdb/cif, or an sdf). The files themselves
            are in `files`, keyed by the tool that produced them — but see that field: on the org-wide listing `files` can
            be empty even when this is true, because chain-bearing files need a group to relabel against. Pass `group`, or
            read the molecule by id, to get the download.
        id (str):
        matched_on (list[str] | None):
        metadata (MoleculeMetadata): TWO namespaces in one map, and knowing which is which is what makes `filter` work.

            A key naming a TOOL holds a LIST of that tool's score runs — `{"protenix": [{"jobId": "...", "runId": "...",
            "ipSAE_AB": 0.62}]}`. Any other key is a SCALAR annotation you set yourself — `{"affinity_nM": 12.4}`.

            One carve-out: a key naming a COMPUTED schema field holds that formula's value, evaluated on read and never
            stored. It is READ-ONLY — you cannot set it here — and `filter`/`sortBy` do not address it, because they resolve
            against stored values and a computed field has none.

            Filter and sort address the two writable namespaces differently: a tool score is the DOTTED path
            `protenix.ipSAE_AB` (`?filter=protenix.ipSAE_AB:gte:0.5`), and a scalar is the BARE key
            (`?filter=affinity_nM:lte:50`). Metric names are case-sensitive and must match what you see here. `exists`
            applies to scalar keys only; to ask whether a tool reported a metric, filter on its value instead.

            Each run entry carries `jobId` AND `runId`, which answer different questions. `jobId` is the DISPATCH that
            produced the entry, and the engine dispatches one job per molecule — so the same run has a different `jobId` on
            every molecule and grouping a page by it yields one group per molecule. `runId` is the run — the pipeline NODE
            RUN, where there is one — and is the field to group by. Pass it straight back as `nodeRunId` to list everything
            that node run produced; the `nr-` prefix a pipeline run carries is accepted as-is, and `nodeRuns[].id` (the bare
            uuid) names the same run.
        name (None | str):
        notes (None | str):
        origin (MoleculeOrigin | None):
        source (None | str):
        tags (list[str]):
        truncated (list[str]): Which inline collections were CAPPED for this molecule, so you know you are not looking
            at all of it: `"scores"` (more score runs than returned), `"files"`, or `"groups"` (page the rest via `GET
            /molecules/{moleculeId}/groups`). Empty means the maps above are the molecule's full accumulated history.
        type_ (None | str):
        sort_group (MoleculeSortGroup | None | Unset):
    """

    added_at: datetime.datetime | None
    chain_mapping: MoleculeChainmapping
    created_at: datetime.datetime | None
    created_by: None | str
    entity: MoleculeEntity
    files: MoleculeFiles
    groups: list[MoleculeGroup]
    has_structure: bool
    id: str
    matched_on: list[str] | None
    metadata: MoleculeMetadata
    name: None | str
    notes: None | str
    origin: MoleculeOrigin | None
    source: None | str
    tags: list[str]
    truncated: list[str]
    type_: None | str
    sort_group: MoleculeSortGroup | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.molecule_origin import MoleculeOrigin
        from ..models.molecule_sort_group import MoleculeSortGroup

        added_at: None | str
        if isinstance(self.added_at, datetime.datetime):
            added_at = self.added_at.isoformat()
        else:
            added_at = self.added_at

        chain_mapping = self.chain_mapping.to_dict()

        created_at: None | str
        if isinstance(self.created_at, datetime.datetime):
            created_at = self.created_at.isoformat()
        else:
            created_at = self.created_at

        created_by: None | str
        created_by = self.created_by

        entity = self.entity.to_dict()

        files = self.files.to_dict()

        groups = []
        for groups_item_data in self.groups:
            groups_item = groups_item_data.to_dict()
            groups.append(groups_item)

        has_structure = self.has_structure

        id = self.id

        matched_on: list[str] | None
        if isinstance(self.matched_on, list):
            matched_on = self.matched_on

        else:
            matched_on = self.matched_on

        metadata = self.metadata.to_dict()

        name: None | str
        name = self.name

        notes: None | str
        notes = self.notes

        origin: dict[str, Any] | None
        if isinstance(self.origin, MoleculeOrigin):
            origin = self.origin.to_dict()
        else:
            origin = self.origin

        source: None | str
        source = self.source

        tags = self.tags

        truncated = self.truncated

        type_: None | str
        type_ = self.type_

        sort_group: dict[str, Any] | None | Unset
        if isinstance(self.sort_group, Unset):
            sort_group = UNSET
        elif isinstance(self.sort_group, MoleculeSortGroup):
            sort_group = self.sort_group.to_dict()
        else:
            sort_group = self.sort_group

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "addedAt": added_at,
                "chainMapping": chain_mapping,
                "createdAt": created_at,
                "createdBy": created_by,
                "entity": entity,
                "files": files,
                "groups": groups,
                "hasStructure": has_structure,
                "id": id,
                "matchedOn": matched_on,
                "metadata": metadata,
                "name": name,
                "notes": notes,
                "origin": origin,
                "source": source,
                "tags": tags,
                "truncated": truncated,
                "type": type_,
            }
        )
        if sort_group is not UNSET:
            field_dict["sortGroup"] = sort_group

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.molecule_chainmapping import MoleculeChainmapping
        from ..models.molecule_entity import MoleculeEntity
        from ..models.molecule_files import MoleculeFiles
        from ..models.molecule_group import MoleculeGroup
        from ..models.molecule_metadata import MoleculeMetadata
        from ..models.molecule_origin import MoleculeOrigin
        from ..models.molecule_sort_group import MoleculeSortGroup

        d = dict(src_dict)

        def _parse_added_at(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                added_at_type_0 = isoparse(data)

                return added_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        added_at = _parse_added_at(d.pop("addedAt"))

        chain_mapping = MoleculeChainmapping.from_dict(d.pop("chainMapping"))

        def _parse_created_at(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                created_at_type_0 = isoparse(data)

                return created_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        created_at = _parse_created_at(d.pop("createdAt"))

        def _parse_created_by(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        created_by = _parse_created_by(d.pop("createdBy"))

        entity = MoleculeEntity.from_dict(d.pop("entity"))

        files = MoleculeFiles.from_dict(d.pop("files"))

        groups = []
        _groups = d.pop("groups")
        for groups_item_data in _groups:
            groups_item = MoleculeGroup.from_dict(groups_item_data)

            groups.append(groups_item)

        has_structure = d.pop("hasStructure")

        id = d.pop("id")

        def _parse_matched_on(data: object) -> list[str] | None:
            if data is None:
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                matched_on_type_0 = cast(list[str], data)

                return matched_on_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[str] | None, data)

        matched_on = _parse_matched_on(d.pop("matchedOn"))

        metadata = MoleculeMetadata.from_dict(d.pop("metadata"))

        def _parse_name(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        name = _parse_name(d.pop("name"))

        def _parse_notes(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        notes = _parse_notes(d.pop("notes"))

        def _parse_origin(data: object) -> MoleculeOrigin | None:
            if data is None:
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                origin_type_0 = MoleculeOrigin.from_dict(data)

                return origin_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(MoleculeOrigin | None, data)

        origin = _parse_origin(d.pop("origin"))

        def _parse_source(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        source = _parse_source(d.pop("source"))

        tags = cast(list[str], d.pop("tags"))

        truncated = cast(list[str], d.pop("truncated"))

        def _parse_type_(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        type_ = _parse_type_(d.pop("type"))

        def _parse_sort_group(data: object) -> MoleculeSortGroup | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                sort_group_type_0 = MoleculeSortGroup.from_dict(data)

                return sort_group_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(MoleculeSortGroup | None | Unset, data)

        sort_group = _parse_sort_group(d.pop("sortGroup", UNSET))

        molecule = cls(
            added_at=added_at,
            chain_mapping=chain_mapping,
            created_at=created_at,
            created_by=created_by,
            entity=entity,
            files=files,
            groups=groups,
            has_structure=has_structure,
            id=id,
            matched_on=matched_on,
            metadata=metadata,
            name=name,
            notes=notes,
            origin=origin,
            source=source,
            tags=tags,
            truncated=truncated,
            type_=type_,
            sort_group=sort_group,
        )

        molecule.additional_properties = d
        return molecule

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
