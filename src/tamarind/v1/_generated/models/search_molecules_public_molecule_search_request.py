from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..models.search_molecules_public_molecule_search_request_molecule_type import (
    SearchMoleculesPublicMoleculeSearchRequestMoleculeType,
)
from ..models.search_molecules_public_molecule_search_request_view import (
    SearchMoleculesPublicMoleculeSearchRequestView,
)
from ..types import UNSET, Unset

T = TypeVar("T", bound="SearchMoleculesPublicMoleculeSearchRequest")


@_attrs_define
class SearchMoleculesPublicMoleculeSearchRequest:
    """
    Attributes:
        cursor (None | str | Unset): Omit for your first request. To get the next page, copy the `nextCursor` value from
            the response into this parameter and send another request with the same filters. Repeat until `nextCursor` is
            null, even if a page is empty.
        dir_ (str | Unset): `asc`: ascending order. `desc`: descending order. Default: 'desc'.
        filter_ (list[str] | None | Unset): String in format `field:operator:value`. "field" can be user-uploaded
            properties or tool scores (in format `tool-id.score`). Supported operators: `gt`, `gte`, `lt`, `lte`, `eq`,
            `neq`, `iequals`, `includes`, `in` (any of a `|`-separated set of at most 64 members, e.g.
            `stage:in:lead|backup`), `exists` (written `field:exists`, no value). Append `:jobId` to a tool score (not with
            `in` or `exists`) to filter only from tool scores from a particular job. Repeat `filter` to combine conditions;
            a molecule must match all of them. See `/tools` endpoint for list of output scores for each tool.
        group_id (None | str | Unset): Limit results to one group by id (from `GET /molecules/groups`), the same filter
            as `GET /molecules?groupId=`. Today's name `group` is refused with a hint to use `groupId`.
        job_id (None | str | Unset): Limit results to one job's input and output molecules by ID. For batches, use the
            batch's ID to retrieve molecules for all jobs within the batch. Takes the `job_` or `batch_` id from `/jobs`, or
            the bare stored id.
        job_name (None | str | Unset): List input and output molecules by job or batch name.
        limit (int | Unset): Maximum number of items to return in one page. Default: 50.
        mode (str | Unset): Choose what `search` matches: `sequence` searches amino acid chains by exact or subsequence
            match, while `sequenceMatch=exact_smiles` matches a small molecule's stored SMILES exactly. `default`/`name`
            match molecule, property, and score names. Default: 'default'.
        molecules_per_group (int | None | Unset): Maximum molecules per group across the whole result set. Requires
            `sortBy=groupName`; unavailable with `mode=sequence`.
        node_run_id (None | str | Unset): Limit results to one pipeline step's output molecules by node run ID (retrieve
            ID using `/pipelines/runs/{runId}`).
        owner (None | str | Unset): Only groups whose owner equals this value, as the owners list returns it.
        scope (str | Unset): `mine` (the default) shows molecules in groups you created; `org` shows everything across
            your organization. Default: 'mine'.
        search (None | str | Unset): Enter a search term to find molecule names, user-uploaded property names, or tool
            score names. To search chains instead, set `mode=sequence` and enter a sequence or exact SMILES. Use at least 3
            characters for sequence searches or when searching without a group.
        search_caps (None | str | Unset): Comma-separated list of capabilities. The response's `caps` field lists the
            values the API supports from your request.
        sequence (None | str | Unset): Match molecules containing this amino-acid subsequence in any chain (case-
            insensitive, at least 3 characters).
        sequence_match (str | Unset): Only available with `mode=sequence`: `subsequence` matches part of an amino-acid
            chain; `exact` matches a whole amino-acid chain; `exact_smiles` matches a whole small-molecule chain exactly,
            including case. Default: 'subsequence'.
        sort_by (str | Unset): Sort by `id`, `added`, `type`, `groupName`, a property, or a score such as
            `alphafold.ptm`. Scores use the tool's "best run." `groupName` keeps each group together; use
            `moleculesPerGroup` to limit its results. Default: 'added'.
        tags (list[str] | None | Unset): Limit results to molecules carrying this tag. Repeat it to require several
            tags.
        type_ (list[SearchMoleculesPublicMoleculeSearchRequestMoleculeType] | None | Unset): Filter by molecule type,
            such as `protein`, `small_molecule`, or `nucleic_acid`.
        view (SearchMoleculesPublicMoleculeSearchRequestView | Unset): Return full molecules (default) or molecule
            cards. Default: SearchMoleculesPublicMoleculeSearchRequestView.FULL.
    """

    cursor: None | str | Unset = UNSET
    dir_: str | Unset = "desc"
    filter_: list[str] | None | Unset = UNSET
    group_id: None | str | Unset = UNSET
    job_id: None | str | Unset = UNSET
    job_name: None | str | Unset = UNSET
    limit: int | Unset = 50
    mode: str | Unset = "default"
    molecules_per_group: int | None | Unset = UNSET
    node_run_id: None | str | Unset = UNSET
    owner: None | str | Unset = UNSET
    scope: str | Unset = "mine"
    search: None | str | Unset = UNSET
    search_caps: None | str | Unset = UNSET
    sequence: None | str | Unset = UNSET
    sequence_match: str | Unset = "subsequence"
    sort_by: str | Unset = "added"
    tags: list[str] | None | Unset = UNSET
    type_: list[SearchMoleculesPublicMoleculeSearchRequestMoleculeType] | None | Unset = UNSET
    view: SearchMoleculesPublicMoleculeSearchRequestView | Unset = (
        SearchMoleculesPublicMoleculeSearchRequestView.FULL
    )

    def to_dict(self) -> dict[str, Any]:
        cursor: None | str | Unset
        if isinstance(self.cursor, Unset):
            cursor = UNSET
        else:
            cursor = self.cursor

        dir_ = self.dir_

        filter_: list[str] | None | Unset
        if isinstance(self.filter_, Unset):
            filter_ = UNSET
        elif isinstance(self.filter_, list):
            filter_ = self.filter_

        else:
            filter_ = self.filter_

        group_id: None | str | Unset
        if isinstance(self.group_id, Unset):
            group_id = UNSET
        else:
            group_id = self.group_id

        job_id: None | str | Unset
        if isinstance(self.job_id, Unset):
            job_id = UNSET
        else:
            job_id = self.job_id

        job_name: None | str | Unset
        if isinstance(self.job_name, Unset):
            job_name = UNSET
        else:
            job_name = self.job_name

        limit = self.limit

        mode = self.mode

        molecules_per_group: int | None | Unset
        if isinstance(self.molecules_per_group, Unset):
            molecules_per_group = UNSET
        else:
            molecules_per_group = self.molecules_per_group

        node_run_id: None | str | Unset
        if isinstance(self.node_run_id, Unset):
            node_run_id = UNSET
        else:
            node_run_id = self.node_run_id

        owner: None | str | Unset
        if isinstance(self.owner, Unset):
            owner = UNSET
        else:
            owner = self.owner

        scope = self.scope

        search: None | str | Unset
        if isinstance(self.search, Unset):
            search = UNSET
        else:
            search = self.search

        search_caps: None | str | Unset
        if isinstance(self.search_caps, Unset):
            search_caps = UNSET
        else:
            search_caps = self.search_caps

        sequence: None | str | Unset
        if isinstance(self.sequence, Unset):
            sequence = UNSET
        else:
            sequence = self.sequence

        sequence_match = self.sequence_match

        sort_by = self.sort_by

        tags: list[str] | None | Unset
        if isinstance(self.tags, Unset):
            tags = UNSET
        elif isinstance(self.tags, list):
            tags = self.tags

        else:
            tags = self.tags

        type_: list[str] | None | Unset
        if isinstance(self.type_, Unset):
            type_ = UNSET
        elif isinstance(self.type_, list):
            type_ = []
            for type_type_0_item_data in self.type_:
                type_type_0_item = type_type_0_item_data.value
                type_.append(type_type_0_item)

        else:
            type_ = self.type_

        view: str | Unset = UNSET
        if not isinstance(self.view, Unset):
            view = self.view.value

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if cursor is not UNSET:
            field_dict["cursor"] = cursor
        if dir_ is not UNSET:
            field_dict["dir"] = dir_
        if filter_ is not UNSET:
            field_dict["filter"] = filter_
        if group_id is not UNSET:
            field_dict["groupId"] = group_id
        if job_id is not UNSET:
            field_dict["jobId"] = job_id
        if job_name is not UNSET:
            field_dict["jobName"] = job_name
        if limit is not UNSET:
            field_dict["limit"] = limit
        if mode is not UNSET:
            field_dict["mode"] = mode
        if molecules_per_group is not UNSET:
            field_dict["moleculesPerGroup"] = molecules_per_group
        if node_run_id is not UNSET:
            field_dict["nodeRunId"] = node_run_id
        if owner is not UNSET:
            field_dict["owner"] = owner
        if scope is not UNSET:
            field_dict["scope"] = scope
        if search is not UNSET:
            field_dict["search"] = search
        if search_caps is not UNSET:
            field_dict["searchCaps"] = search_caps
        if sequence is not UNSET:
            field_dict["sequence"] = sequence
        if sequence_match is not UNSET:
            field_dict["sequenceMatch"] = sequence_match
        if sort_by is not UNSET:
            field_dict["sortBy"] = sort_by
        if tags is not UNSET:
            field_dict["tags"] = tags
        if type_ is not UNSET:
            field_dict["type"] = type_
        if view is not UNSET:
            field_dict["view"] = view

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_cursor(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        cursor = _parse_cursor(d.pop("cursor", UNSET))

        dir_ = d.pop("dir", UNSET)

        def _parse_filter_(data: object) -> list[str] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                filter_type_0 = cast(list[str], data)

                return filter_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[str] | None | Unset, data)

        filter_ = _parse_filter_(d.pop("filter", UNSET))

        def _parse_group_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        group_id = _parse_group_id(d.pop("groupId", UNSET))

        def _parse_job_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        job_id = _parse_job_id(d.pop("jobId", UNSET))

        def _parse_job_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        job_name = _parse_job_name(d.pop("jobName", UNSET))

        limit = d.pop("limit", UNSET)

        mode = d.pop("mode", UNSET)

        def _parse_molecules_per_group(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        molecules_per_group = _parse_molecules_per_group(d.pop("moleculesPerGroup", UNSET))

        def _parse_node_run_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        node_run_id = _parse_node_run_id(d.pop("nodeRunId", UNSET))

        def _parse_owner(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        owner = _parse_owner(d.pop("owner", UNSET))

        scope = d.pop("scope", UNSET)

        def _parse_search(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        search = _parse_search(d.pop("search", UNSET))

        def _parse_search_caps(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        search_caps = _parse_search_caps(d.pop("searchCaps", UNSET))

        def _parse_sequence(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        sequence = _parse_sequence(d.pop("sequence", UNSET))

        sequence_match = d.pop("sequenceMatch", UNSET)

        sort_by = d.pop("sortBy", UNSET)

        def _parse_tags(data: object) -> list[str] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                tags_type_0 = cast(list[str], data)

                return tags_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[str] | None | Unset, data)

        tags = _parse_tags(d.pop("tags", UNSET))

        def _parse_type_(
            data: object,
        ) -> list[SearchMoleculesPublicMoleculeSearchRequestMoleculeType] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                type_type_0 = []
                _type_type_0 = data
                for type_type_0_item_data in _type_type_0:
                    type_type_0_item = SearchMoleculesPublicMoleculeSearchRequestMoleculeType(
                        type_type_0_item_data
                    )

                    type_type_0.append(type_type_0_item)

                return type_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(
                list[SearchMoleculesPublicMoleculeSearchRequestMoleculeType] | None | Unset, data
            )

        type_ = _parse_type_(d.pop("type", UNSET))

        _view = d.pop("view", UNSET)
        view: SearchMoleculesPublicMoleculeSearchRequestView | Unset
        if isinstance(_view, Unset):
            view = UNSET
        else:
            view = SearchMoleculesPublicMoleculeSearchRequestView(_view)

        search_molecules_public_molecule_search_request = cls(
            cursor=cursor,
            dir_=dir_,
            filter_=filter_,
            group_id=group_id,
            job_id=job_id,
            job_name=job_name,
            limit=limit,
            mode=mode,
            molecules_per_group=molecules_per_group,
            node_run_id=node_run_id,
            owner=owner,
            scope=scope,
            search=search,
            search_caps=search_caps,
            sequence=sequence,
            sequence_match=sequence_match,
            sort_by=sort_by,
            tags=tags,
            type_=type_,
            view=view,
        )

        return search_molecules_public_molecule_search_request
