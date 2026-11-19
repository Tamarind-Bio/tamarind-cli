from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.list_molecules_view import ListMoleculesView
from ...models.molecule_caps_page import MoleculeCapsPage
from ...models.molecule_card_caps_page import MoleculeCardCapsPage
from ...models.molecule_card_page import MoleculeCardPage
from ...models.molecule_page import MoleculePage
from ...models.molecule_type import MoleculeType
from ...models.problem import Problem
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    group_id: None | str | Unset = UNSET,
    job_id: None | str | Unset = UNSET,
    owner: None | str | Unset = UNSET,
    node_run_id: None | str | Unset = UNSET,
    type_: list[MoleculeType] | None | Unset = UNSET,
    search: None | str | Unset = UNSET,
    mode: str | Unset = "default",
    sequence_match: str | Unset = "subsequence",
    molecules_per_group: int | None | Unset = UNSET,
    examples_per_group: int | None | Unset = UNSET,
    sequence: None | str | Unset = UNSET,
    filter_: list[str] | None | Unset = UNSET,
    tags: list[str] | None | Unset = UNSET,
    scope: str | Unset = "mine",
    sort_by: str | Unset = "added",
    dir_: str | Unset = "desc",
    limit: int | Unset = 50,
    cursor: None | str | Unset = UNSET,
    view: ListMoleculesView | Unset = ListMoleculesView.FULL,
    search_caps: None | str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(tamarind_version, Unset):
        headers["Tamarind-Version"] = tamarind_version

    params: dict[str, Any] = {}

    json_group_id: None | str | Unset
    if isinstance(group_id, Unset):
        json_group_id = UNSET
    else:
        json_group_id = group_id
    params["groupId"] = json_group_id

    json_job_id: None | str | Unset
    if isinstance(job_id, Unset):
        json_job_id = UNSET
    else:
        json_job_id = job_id
    params["jobId"] = json_job_id

    json_owner: None | str | Unset
    if isinstance(owner, Unset):
        json_owner = UNSET
    else:
        json_owner = owner
    params["owner"] = json_owner

    json_node_run_id: None | str | Unset
    if isinstance(node_run_id, Unset):
        json_node_run_id = UNSET
    else:
        json_node_run_id = node_run_id
    params["nodeRunId"] = json_node_run_id

    json_type_: list[str] | None | Unset
    if isinstance(type_, Unset):
        json_type_ = UNSET
    elif isinstance(type_, list):
        json_type_ = []
        for type_type_0_item_data in type_:
            type_type_0_item = type_type_0_item_data.value
            json_type_.append(type_type_0_item)

    else:
        json_type_ = type_
    params["type"] = json_type_

    json_search: None | str | Unset
    if isinstance(search, Unset):
        json_search = UNSET
    else:
        json_search = search
    params["search"] = json_search

    params["mode"] = mode

    params["sequenceMatch"] = sequence_match

    json_molecules_per_group: int | None | Unset
    if isinstance(molecules_per_group, Unset):
        json_molecules_per_group = UNSET
    else:
        json_molecules_per_group = molecules_per_group
    params["moleculesPerGroup"] = json_molecules_per_group

    json_examples_per_group: int | None | Unset
    if isinstance(examples_per_group, Unset):
        json_examples_per_group = UNSET
    else:
        json_examples_per_group = examples_per_group
    params["examplesPerGroup"] = json_examples_per_group

    json_sequence: None | str | Unset
    if isinstance(sequence, Unset):
        json_sequence = UNSET
    else:
        json_sequence = sequence
    params["sequence"] = json_sequence

    json_filter_: list[str] | None | Unset
    if isinstance(filter_, Unset):
        json_filter_ = UNSET
    elif isinstance(filter_, list):
        json_filter_ = filter_

    else:
        json_filter_ = filter_
    params["filter"] = json_filter_

    json_tags: list[str] | None | Unset
    if isinstance(tags, Unset):
        json_tags = UNSET
    elif isinstance(tags, list):
        json_tags = tags

    else:
        json_tags = tags
    params["tags"] = json_tags

    params["scope"] = scope

    params["sortBy"] = sort_by

    params["dir"] = dir_

    params["limit"] = limit

    json_cursor: None | str | Unset
    if isinstance(cursor, Unset):
        json_cursor = UNSET
    else:
        json_cursor = cursor
    params["cursor"] = json_cursor

    json_view: str | Unset = UNSET
    if not isinstance(view, Unset):
        json_view = view.value

    params["view"] = json_view

    json_search_caps: None | str | Unset
    if isinstance(search_caps, Unset):
        json_search_caps = UNSET
    else:
        json_search_caps = search_caps
    params["searchCaps"] = json_search_caps

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/molecules",
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> MoleculeCapsPage | MoleculeCardCapsPage | MoleculeCardPage | MoleculePage | Problem:
    if response.status_code == 200:

        def _parse_response_200(
            data: object,
        ) -> MoleculeCapsPage | MoleculeCardCapsPage | MoleculeCardPage | MoleculePage:
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                response_200_type_0 = MoleculePage.from_dict(data)

                return response_200_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                response_200_type_1 = MoleculeCardPage.from_dict(data)

                return response_200_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                response_200_type_2 = MoleculeCapsPage.from_dict(data)

                return response_200_type_2
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            if not isinstance(data, dict):
                raise TypeError()
            response_200_type_3 = MoleculeCardCapsPage.from_dict(data)

            return response_200_type_3

        response_200 = _parse_response_200(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = Problem.from_dict(response.json())

        return response_400

    if response.status_code == 401:
        response_401 = Problem.from_dict(response.json())

        return response_401

    if response.status_code == 403:
        response_403 = Problem.from_dict(response.json())

        return response_403

    if response.status_code == 422:
        response_422 = Problem.from_dict(response.json())

        return response_422

    if response.status_code == 429:
        response_429 = Problem.from_dict(response.json())

        return response_429

    if response.status_code == 503:
        response_503 = Problem.from_dict(response.json())

        return response_503

    response_default = Problem.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[MoleculeCapsPage | MoleculeCardCapsPage | MoleculeCardPage | MoleculePage | Problem]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    group_id: None | str | Unset = UNSET,
    job_id: None | str | Unset = UNSET,
    owner: None | str | Unset = UNSET,
    node_run_id: None | str | Unset = UNSET,
    type_: list[MoleculeType] | None | Unset = UNSET,
    search: None | str | Unset = UNSET,
    mode: str | Unset = "default",
    sequence_match: str | Unset = "subsequence",
    molecules_per_group: int | None | Unset = UNSET,
    examples_per_group: int | None | Unset = UNSET,
    sequence: None | str | Unset = UNSET,
    filter_: list[str] | None | Unset = UNSET,
    tags: list[str] | None | Unset = UNSET,
    scope: str | Unset = "mine",
    sort_by: str | Unset = "added",
    dir_: str | Unset = "desc",
    limit: int | Unset = 50,
    cursor: None | str | Unset = UNSET,
    view: ListMoleculesView | Unset = ListMoleculesView.FULL,
    search_caps: None | str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Response[MoleculeCapsPage | MoleculeCardCapsPage | MoleculeCardPage | MoleculePage | Problem]:
    """List Molecules

     List molecules in your organization. Set `scope=org` to search your organization.

    In the full view, each molecule includes its chains, scores, metadata, and files inline. Search
    by name or sequence, or filter by group, `owner`, `jobId`, property, or score.

    Today's spellings `group` and `jobName` are 400 `validation_failed` naming the v1 parameter, rather
    than being ignored and giving an unfiltered list.

    Results are returned in pages. Use `nextCursor` to retrieve more results.

    Args:
        group_id (None | str | Unset): Limit results to one group by ID (retrieve ID using
            `/molecules/groups`).
        job_id (None | str | Unset): Limit results to one job's input and output molecules by ID.
            For batches, use the batch's ID to retrieve molecules for all jobs within the batch.
        owner (None | str | Unset): Only groups whose owner equals this value, as the owners list
            returns it.
        node_run_id (None | str | Unset): Limit results to one pipeline step's output molecules by
            node run ID (retrieve ID using `/pipelines/runs/{runId}`).
        type_ (list[MoleculeType] | None | Unset): Filter by molecule type, such as `protein`,
            `small_molecule`, or `nucleic_acid`.
        search (None | str | Unset): Enter a search term to find molecule names, user-uploaded
            property names, or tool score names. To search chains instead, set `mode=sequence` and
            enter a sequence or exact SMILES. Use at least 3 characters for sequence searches or when
            searching without a group.
        mode (str | Unset): Choose what `search` matches: `sequence` searches amino acid chains by
            exact or subsequence match, while `sequenceMatch=exact_smiles` matches a small molecule's
            stored SMILES exactly. `default`/`name` match molecule, property, and score names.
            Default: 'default'.
        sequence_match (str | Unset): Only available with `mode=sequence`: `subsequence` matches
            part of an amino-acid chain; `exact` matches a whole amino-acid chain; `exact_smiles`
            matches a whole small-molecule chain exactly, including case. Default: 'subsequence'.
        molecules_per_group (int | None | Unset): Maximum molecules per group across the whole
            result set. Requires `sortBy=groupName`; unavailable with `mode=sequence`.
        examples_per_group (int | None | Unset): Deprecated: the old name for `moleculesPerGroup`.
        sequence (None | str | Unset): Match molecules containing this amino-acid subsequence in
            any chain (case-insensitive, at least 3 characters).
        filter_ (list[str] | None | Unset): String in format `field:operator:value`. "field" can
            be user-uploaded properties or tool scores (in format `tool-id.score`). Supported
            operators: `gt`, `gte`, `lt`, `lte`, `eq`, `neq`, `iequals`, `includes`, `in` (any of a
            `|`-separated set of at most 64 members, e.g. `stage:in:lead|backup`), `exists` (written
            `field:exists`, no value). Append `:jobId` to a tool score (not with `in` or `exists`) to
            filter only from tool scores from a particular job. Repeat `filter` to combine conditions;
            a molecule must match all of them. See `/tools` endpoint for list of output scores for
            each tool.
        tags (list[str] | None | Unset): Limit results to molecules carrying this tag. Repeat it
            to require several tags.
        scope (str | Unset): `mine` (the default) shows molecules in groups you created; `org`
            shows everything across your organization. Default: 'mine'.
        sort_by (str | Unset): Sort by `id`, `added`, `type`, `groupName`, a property, or a score
            such as `alphafold.ptm`. Scores use the tool's "best run." `groupName` keeps each group
            together; use `moleculesPerGroup` to limit its results. Default: 'added'.
        dir_ (str | Unset): `asc`: ascending order. `desc`: descending order. Default: 'desc'.
        limit (int | Unset): Maximum number of items to return in one page. Default: 50.
        cursor (None | str | Unset): Omit for your first request. To get the next page, copy the
            `nextCursor` value from the response into this parameter and send another request with the
            same filters. Repeat until `nextCursor` is null, even if a page is empty.
        view (ListMoleculesView | Unset): Return full molecules (default) or molecule cards.
            Default: ListMoleculesView.FULL.
        search_caps (None | str | Unset): Comma-separated list of capabilities. The response's
            `caps` field lists the values the API supports from your request.
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[MoleculeCapsPage | MoleculeCardCapsPage | MoleculeCardPage | MoleculePage | Problem]
    """

    kwargs = _get_kwargs(
        group_id=group_id,
        job_id=job_id,
        owner=owner,
        node_run_id=node_run_id,
        type_=type_,
        search=search,
        mode=mode,
        sequence_match=sequence_match,
        molecules_per_group=molecules_per_group,
        examples_per_group=examples_per_group,
        sequence=sequence,
        filter_=filter_,
        tags=tags,
        scope=scope,
        sort_by=sort_by,
        dir_=dir_,
        limit=limit,
        cursor=cursor,
        view=view,
        search_caps=search_caps,
        tamarind_version=tamarind_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    group_id: None | str | Unset = UNSET,
    job_id: None | str | Unset = UNSET,
    owner: None | str | Unset = UNSET,
    node_run_id: None | str | Unset = UNSET,
    type_: list[MoleculeType] | None | Unset = UNSET,
    search: None | str | Unset = UNSET,
    mode: str | Unset = "default",
    sequence_match: str | Unset = "subsequence",
    molecules_per_group: int | None | Unset = UNSET,
    examples_per_group: int | None | Unset = UNSET,
    sequence: None | str | Unset = UNSET,
    filter_: list[str] | None | Unset = UNSET,
    tags: list[str] | None | Unset = UNSET,
    scope: str | Unset = "mine",
    sort_by: str | Unset = "added",
    dir_: str | Unset = "desc",
    limit: int | Unset = 50,
    cursor: None | str | Unset = UNSET,
    view: ListMoleculesView | Unset = ListMoleculesView.FULL,
    search_caps: None | str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> MoleculeCapsPage | MoleculeCardCapsPage | MoleculeCardPage | MoleculePage | Problem | None:
    """List Molecules

     List molecules in your organization. Set `scope=org` to search your organization.

    In the full view, each molecule includes its chains, scores, metadata, and files inline. Search
    by name or sequence, or filter by group, `owner`, `jobId`, property, or score.

    Today's spellings `group` and `jobName` are 400 `validation_failed` naming the v1 parameter, rather
    than being ignored and giving an unfiltered list.

    Results are returned in pages. Use `nextCursor` to retrieve more results.

    Args:
        group_id (None | str | Unset): Limit results to one group by ID (retrieve ID using
            `/molecules/groups`).
        job_id (None | str | Unset): Limit results to one job's input and output molecules by ID.
            For batches, use the batch's ID to retrieve molecules for all jobs within the batch.
        owner (None | str | Unset): Only groups whose owner equals this value, as the owners list
            returns it.
        node_run_id (None | str | Unset): Limit results to one pipeline step's output molecules by
            node run ID (retrieve ID using `/pipelines/runs/{runId}`).
        type_ (list[MoleculeType] | None | Unset): Filter by molecule type, such as `protein`,
            `small_molecule`, or `nucleic_acid`.
        search (None | str | Unset): Enter a search term to find molecule names, user-uploaded
            property names, or tool score names. To search chains instead, set `mode=sequence` and
            enter a sequence or exact SMILES. Use at least 3 characters for sequence searches or when
            searching without a group.
        mode (str | Unset): Choose what `search` matches: `sequence` searches amino acid chains by
            exact or subsequence match, while `sequenceMatch=exact_smiles` matches a small molecule's
            stored SMILES exactly. `default`/`name` match molecule, property, and score names.
            Default: 'default'.
        sequence_match (str | Unset): Only available with `mode=sequence`: `subsequence` matches
            part of an amino-acid chain; `exact` matches a whole amino-acid chain; `exact_smiles`
            matches a whole small-molecule chain exactly, including case. Default: 'subsequence'.
        molecules_per_group (int | None | Unset): Maximum molecules per group across the whole
            result set. Requires `sortBy=groupName`; unavailable with `mode=sequence`.
        examples_per_group (int | None | Unset): Deprecated: the old name for `moleculesPerGroup`.
        sequence (None | str | Unset): Match molecules containing this amino-acid subsequence in
            any chain (case-insensitive, at least 3 characters).
        filter_ (list[str] | None | Unset): String in format `field:operator:value`. "field" can
            be user-uploaded properties or tool scores (in format `tool-id.score`). Supported
            operators: `gt`, `gte`, `lt`, `lte`, `eq`, `neq`, `iequals`, `includes`, `in` (any of a
            `|`-separated set of at most 64 members, e.g. `stage:in:lead|backup`), `exists` (written
            `field:exists`, no value). Append `:jobId` to a tool score (not with `in` or `exists`) to
            filter only from tool scores from a particular job. Repeat `filter` to combine conditions;
            a molecule must match all of them. See `/tools` endpoint for list of output scores for
            each tool.
        tags (list[str] | None | Unset): Limit results to molecules carrying this tag. Repeat it
            to require several tags.
        scope (str | Unset): `mine` (the default) shows molecules in groups you created; `org`
            shows everything across your organization. Default: 'mine'.
        sort_by (str | Unset): Sort by `id`, `added`, `type`, `groupName`, a property, or a score
            such as `alphafold.ptm`. Scores use the tool's "best run." `groupName` keeps each group
            together; use `moleculesPerGroup` to limit its results. Default: 'added'.
        dir_ (str | Unset): `asc`: ascending order. `desc`: descending order. Default: 'desc'.
        limit (int | Unset): Maximum number of items to return in one page. Default: 50.
        cursor (None | str | Unset): Omit for your first request. To get the next page, copy the
            `nextCursor` value from the response into this parameter and send another request with the
            same filters. Repeat until `nextCursor` is null, even if a page is empty.
        view (ListMoleculesView | Unset): Return full molecules (default) or molecule cards.
            Default: ListMoleculesView.FULL.
        search_caps (None | str | Unset): Comma-separated list of capabilities. The response's
            `caps` field lists the values the API supports from your request.
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        MoleculeCapsPage | MoleculeCardCapsPage | MoleculeCardPage | MoleculePage | Problem
    """

    return sync_detailed(
        client=client,
        group_id=group_id,
        job_id=job_id,
        owner=owner,
        node_run_id=node_run_id,
        type_=type_,
        search=search,
        mode=mode,
        sequence_match=sequence_match,
        molecules_per_group=molecules_per_group,
        examples_per_group=examples_per_group,
        sequence=sequence,
        filter_=filter_,
        tags=tags,
        scope=scope,
        sort_by=sort_by,
        dir_=dir_,
        limit=limit,
        cursor=cursor,
        view=view,
        search_caps=search_caps,
        tamarind_version=tamarind_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    group_id: None | str | Unset = UNSET,
    job_id: None | str | Unset = UNSET,
    owner: None | str | Unset = UNSET,
    node_run_id: None | str | Unset = UNSET,
    type_: list[MoleculeType] | None | Unset = UNSET,
    search: None | str | Unset = UNSET,
    mode: str | Unset = "default",
    sequence_match: str | Unset = "subsequence",
    molecules_per_group: int | None | Unset = UNSET,
    examples_per_group: int | None | Unset = UNSET,
    sequence: None | str | Unset = UNSET,
    filter_: list[str] | None | Unset = UNSET,
    tags: list[str] | None | Unset = UNSET,
    scope: str | Unset = "mine",
    sort_by: str | Unset = "added",
    dir_: str | Unset = "desc",
    limit: int | Unset = 50,
    cursor: None | str | Unset = UNSET,
    view: ListMoleculesView | Unset = ListMoleculesView.FULL,
    search_caps: None | str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Response[MoleculeCapsPage | MoleculeCardCapsPage | MoleculeCardPage | MoleculePage | Problem]:
    """List Molecules

     List molecules in your organization. Set `scope=org` to search your organization.

    In the full view, each molecule includes its chains, scores, metadata, and files inline. Search
    by name or sequence, or filter by group, `owner`, `jobId`, property, or score.

    Today's spellings `group` and `jobName` are 400 `validation_failed` naming the v1 parameter, rather
    than being ignored and giving an unfiltered list.

    Results are returned in pages. Use `nextCursor` to retrieve more results.

    Args:
        group_id (None | str | Unset): Limit results to one group by ID (retrieve ID using
            `/molecules/groups`).
        job_id (None | str | Unset): Limit results to one job's input and output molecules by ID.
            For batches, use the batch's ID to retrieve molecules for all jobs within the batch.
        owner (None | str | Unset): Only groups whose owner equals this value, as the owners list
            returns it.
        node_run_id (None | str | Unset): Limit results to one pipeline step's output molecules by
            node run ID (retrieve ID using `/pipelines/runs/{runId}`).
        type_ (list[MoleculeType] | None | Unset): Filter by molecule type, such as `protein`,
            `small_molecule`, or `nucleic_acid`.
        search (None | str | Unset): Enter a search term to find molecule names, user-uploaded
            property names, or tool score names. To search chains instead, set `mode=sequence` and
            enter a sequence or exact SMILES. Use at least 3 characters for sequence searches or when
            searching without a group.
        mode (str | Unset): Choose what `search` matches: `sequence` searches amino acid chains by
            exact or subsequence match, while `sequenceMatch=exact_smiles` matches a small molecule's
            stored SMILES exactly. `default`/`name` match molecule, property, and score names.
            Default: 'default'.
        sequence_match (str | Unset): Only available with `mode=sequence`: `subsequence` matches
            part of an amino-acid chain; `exact` matches a whole amino-acid chain; `exact_smiles`
            matches a whole small-molecule chain exactly, including case. Default: 'subsequence'.
        molecules_per_group (int | None | Unset): Maximum molecules per group across the whole
            result set. Requires `sortBy=groupName`; unavailable with `mode=sequence`.
        examples_per_group (int | None | Unset): Deprecated: the old name for `moleculesPerGroup`.
        sequence (None | str | Unset): Match molecules containing this amino-acid subsequence in
            any chain (case-insensitive, at least 3 characters).
        filter_ (list[str] | None | Unset): String in format `field:operator:value`. "field" can
            be user-uploaded properties or tool scores (in format `tool-id.score`). Supported
            operators: `gt`, `gte`, `lt`, `lte`, `eq`, `neq`, `iequals`, `includes`, `in` (any of a
            `|`-separated set of at most 64 members, e.g. `stage:in:lead|backup`), `exists` (written
            `field:exists`, no value). Append `:jobId` to a tool score (not with `in` or `exists`) to
            filter only from tool scores from a particular job. Repeat `filter` to combine conditions;
            a molecule must match all of them. See `/tools` endpoint for list of output scores for
            each tool.
        tags (list[str] | None | Unset): Limit results to molecules carrying this tag. Repeat it
            to require several tags.
        scope (str | Unset): `mine` (the default) shows molecules in groups you created; `org`
            shows everything across your organization. Default: 'mine'.
        sort_by (str | Unset): Sort by `id`, `added`, `type`, `groupName`, a property, or a score
            such as `alphafold.ptm`. Scores use the tool's "best run." `groupName` keeps each group
            together; use `moleculesPerGroup` to limit its results. Default: 'added'.
        dir_ (str | Unset): `asc`: ascending order. `desc`: descending order. Default: 'desc'.
        limit (int | Unset): Maximum number of items to return in one page. Default: 50.
        cursor (None | str | Unset): Omit for your first request. To get the next page, copy the
            `nextCursor` value from the response into this parameter and send another request with the
            same filters. Repeat until `nextCursor` is null, even if a page is empty.
        view (ListMoleculesView | Unset): Return full molecules (default) or molecule cards.
            Default: ListMoleculesView.FULL.
        search_caps (None | str | Unset): Comma-separated list of capabilities. The response's
            `caps` field lists the values the API supports from your request.
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[MoleculeCapsPage | MoleculeCardCapsPage | MoleculeCardPage | MoleculePage | Problem]
    """

    kwargs = _get_kwargs(
        group_id=group_id,
        job_id=job_id,
        owner=owner,
        node_run_id=node_run_id,
        type_=type_,
        search=search,
        mode=mode,
        sequence_match=sequence_match,
        molecules_per_group=molecules_per_group,
        examples_per_group=examples_per_group,
        sequence=sequence,
        filter_=filter_,
        tags=tags,
        scope=scope,
        sort_by=sort_by,
        dir_=dir_,
        limit=limit,
        cursor=cursor,
        view=view,
        search_caps=search_caps,
        tamarind_version=tamarind_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    group_id: None | str | Unset = UNSET,
    job_id: None | str | Unset = UNSET,
    owner: None | str | Unset = UNSET,
    node_run_id: None | str | Unset = UNSET,
    type_: list[MoleculeType] | None | Unset = UNSET,
    search: None | str | Unset = UNSET,
    mode: str | Unset = "default",
    sequence_match: str | Unset = "subsequence",
    molecules_per_group: int | None | Unset = UNSET,
    examples_per_group: int | None | Unset = UNSET,
    sequence: None | str | Unset = UNSET,
    filter_: list[str] | None | Unset = UNSET,
    tags: list[str] | None | Unset = UNSET,
    scope: str | Unset = "mine",
    sort_by: str | Unset = "added",
    dir_: str | Unset = "desc",
    limit: int | Unset = 50,
    cursor: None | str | Unset = UNSET,
    view: ListMoleculesView | Unset = ListMoleculesView.FULL,
    search_caps: None | str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> MoleculeCapsPage | MoleculeCardCapsPage | MoleculeCardPage | MoleculePage | Problem | None:
    """List Molecules

     List molecules in your organization. Set `scope=org` to search your organization.

    In the full view, each molecule includes its chains, scores, metadata, and files inline. Search
    by name or sequence, or filter by group, `owner`, `jobId`, property, or score.

    Today's spellings `group` and `jobName` are 400 `validation_failed` naming the v1 parameter, rather
    than being ignored and giving an unfiltered list.

    Results are returned in pages. Use `nextCursor` to retrieve more results.

    Args:
        group_id (None | str | Unset): Limit results to one group by ID (retrieve ID using
            `/molecules/groups`).
        job_id (None | str | Unset): Limit results to one job's input and output molecules by ID.
            For batches, use the batch's ID to retrieve molecules for all jobs within the batch.
        owner (None | str | Unset): Only groups whose owner equals this value, as the owners list
            returns it.
        node_run_id (None | str | Unset): Limit results to one pipeline step's output molecules by
            node run ID (retrieve ID using `/pipelines/runs/{runId}`).
        type_ (list[MoleculeType] | None | Unset): Filter by molecule type, such as `protein`,
            `small_molecule`, or `nucleic_acid`.
        search (None | str | Unset): Enter a search term to find molecule names, user-uploaded
            property names, or tool score names. To search chains instead, set `mode=sequence` and
            enter a sequence or exact SMILES. Use at least 3 characters for sequence searches or when
            searching without a group.
        mode (str | Unset): Choose what `search` matches: `sequence` searches amino acid chains by
            exact or subsequence match, while `sequenceMatch=exact_smiles` matches a small molecule's
            stored SMILES exactly. `default`/`name` match molecule, property, and score names.
            Default: 'default'.
        sequence_match (str | Unset): Only available with `mode=sequence`: `subsequence` matches
            part of an amino-acid chain; `exact` matches a whole amino-acid chain; `exact_smiles`
            matches a whole small-molecule chain exactly, including case. Default: 'subsequence'.
        molecules_per_group (int | None | Unset): Maximum molecules per group across the whole
            result set. Requires `sortBy=groupName`; unavailable with `mode=sequence`.
        examples_per_group (int | None | Unset): Deprecated: the old name for `moleculesPerGroup`.
        sequence (None | str | Unset): Match molecules containing this amino-acid subsequence in
            any chain (case-insensitive, at least 3 characters).
        filter_ (list[str] | None | Unset): String in format `field:operator:value`. "field" can
            be user-uploaded properties or tool scores (in format `tool-id.score`). Supported
            operators: `gt`, `gte`, `lt`, `lte`, `eq`, `neq`, `iequals`, `includes`, `in` (any of a
            `|`-separated set of at most 64 members, e.g. `stage:in:lead|backup`), `exists` (written
            `field:exists`, no value). Append `:jobId` to a tool score (not with `in` or `exists`) to
            filter only from tool scores from a particular job. Repeat `filter` to combine conditions;
            a molecule must match all of them. See `/tools` endpoint for list of output scores for
            each tool.
        tags (list[str] | None | Unset): Limit results to molecules carrying this tag. Repeat it
            to require several tags.
        scope (str | Unset): `mine` (the default) shows molecules in groups you created; `org`
            shows everything across your organization. Default: 'mine'.
        sort_by (str | Unset): Sort by `id`, `added`, `type`, `groupName`, a property, or a score
            such as `alphafold.ptm`. Scores use the tool's "best run." `groupName` keeps each group
            together; use `moleculesPerGroup` to limit its results. Default: 'added'.
        dir_ (str | Unset): `asc`: ascending order. `desc`: descending order. Default: 'desc'.
        limit (int | Unset): Maximum number of items to return in one page. Default: 50.
        cursor (None | str | Unset): Omit for your first request. To get the next page, copy the
            `nextCursor` value from the response into this parameter and send another request with the
            same filters. Repeat until `nextCursor` is null, even if a page is empty.
        view (ListMoleculesView | Unset): Return full molecules (default) or molecule cards.
            Default: ListMoleculesView.FULL.
        search_caps (None | str | Unset): Comma-separated list of capabilities. The response's
            `caps` field lists the values the API supports from your request.
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        MoleculeCapsPage | MoleculeCardCapsPage | MoleculeCardPage | MoleculePage | Problem
    """

    return (
        await asyncio_detailed(
            client=client,
            group_id=group_id,
            job_id=job_id,
            owner=owner,
            node_run_id=node_run_id,
            type_=type_,
            search=search,
            mode=mode,
            sequence_match=sequence_match,
            molecules_per_group=molecules_per_group,
            examples_per_group=examples_per_group,
            sequence=sequence,
            filter_=filter_,
            tags=tags,
            scope=scope,
            sort_by=sort_by,
            dir_=dir_,
            limit=limit,
            cursor=cursor,
            view=view,
            search_caps=search_caps,
            tamarind_version=tamarind_version,
        )
    ).parsed
