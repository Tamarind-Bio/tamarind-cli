from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.pipeline_node_run_molecule_page import PipelineNodeRunMoleculePage
from ...models.problem import Problem
from ...types import UNSET, Response, Unset


def _get_kwargs(
    run_id: str,
    node_run_id: str,
    *,
    limit: int | Unset = 50,
    cursor: None | str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(tamarind_version, Unset):
        headers["Tamarind-Version"] = tamarind_version

    params: dict[str, Any] = {}

    params["limit"] = limit

    json_cursor: None | str | Unset
    if isinstance(cursor, Unset):
        json_cursor = UNSET
    else:
        json_cursor = cursor
    params["cursor"] = json_cursor

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/pipelines/runs/{run_id}/node-runs/{node_run_id}/molecules".format(
            run_id=quote(str(run_id), safe=""),
            node_run_id=quote(str(node_run_id), safe=""),
        ),
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> PipelineNodeRunMoleculePage | Problem:
    if response.status_code == 200:
        response_200 = PipelineNodeRunMoleculePage.from_dict(response.json())

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

    if response.status_code == 404:
        response_404 = Problem.from_dict(response.json())

        return response_404

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
) -> Response[PipelineNodeRunMoleculePage | Problem]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    run_id: str,
    node_run_id: str,
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = 50,
    cursor: None | str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Response[PipelineNodeRunMoleculePage | Problem]:
    """List the molecules a node run produced

     The molecules one node run produced, with their scores.

    Read a node run's results through this, not through `PipelineNodeRun.outputGroup`. `outputGroup` is
    the group a node MINTED, and two common kinds of node mint none: a node that enriches its inputs in
    place (scoring, structure prediction) leaves its molecules in the group they came from, and a filter
    node's survivors exist only as node-run outputs. For both, `outputGroup` is correctly `null` —
    reading results by group reports 'produced nothing' for exactly the node runs whose output you asked
    for. This endpoint answers for every kind of node.

    `nodeRunId` is the `id` of an entry in the run's `nodeRuns`. `limit` is a maximum and a page may be
    shorter when rows are large; follow `nextCursor`.

    A molecule too large for a page is 422 `node_run_molecule_response_too_large`, naming
    `moleculeEndpoint` (`/molecules/{id}`) and a `nextCursor` to skip past it.

    This is the COMPACT view: identity, sequence and scores, scoped to the RUN. For the same molecules
    with their groups, tags and provenance — and to threshold or rank them by a score — pass the same id
    to `GET /molecules?nodeRunId=...`, which supports `filter`, `sortBy`, `search` and 200 per page.
    That endpoint reads through your molecule library rather than through the run, so its `nodeRunId`
    parameter documents where the two differ; this one is the authority on what the node run produced.

    Args:
        run_id (str):
        node_run_id (str):
        limit (int | Unset): Molecules per page. Default: 50.
        cursor (None | str | Unset): Pagination token from the previous response's `nextCursor`.
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PipelineNodeRunMoleculePage | Problem]
    """

    kwargs = _get_kwargs(
        run_id=run_id,
        node_run_id=node_run_id,
        limit=limit,
        cursor=cursor,
        tamarind_version=tamarind_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    run_id: str,
    node_run_id: str,
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = 50,
    cursor: None | str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> PipelineNodeRunMoleculePage | Problem | None:
    """List the molecules a node run produced

     The molecules one node run produced, with their scores.

    Read a node run's results through this, not through `PipelineNodeRun.outputGroup`. `outputGroup` is
    the group a node MINTED, and two common kinds of node mint none: a node that enriches its inputs in
    place (scoring, structure prediction) leaves its molecules in the group they came from, and a filter
    node's survivors exist only as node-run outputs. For both, `outputGroup` is correctly `null` —
    reading results by group reports 'produced nothing' for exactly the node runs whose output you asked
    for. This endpoint answers for every kind of node.

    `nodeRunId` is the `id` of an entry in the run's `nodeRuns`. `limit` is a maximum and a page may be
    shorter when rows are large; follow `nextCursor`.

    A molecule too large for a page is 422 `node_run_molecule_response_too_large`, naming
    `moleculeEndpoint` (`/molecules/{id}`) and a `nextCursor` to skip past it.

    This is the COMPACT view: identity, sequence and scores, scoped to the RUN. For the same molecules
    with their groups, tags and provenance — and to threshold or rank them by a score — pass the same id
    to `GET /molecules?nodeRunId=...`, which supports `filter`, `sortBy`, `search` and 200 per page.
    That endpoint reads through your molecule library rather than through the run, so its `nodeRunId`
    parameter documents where the two differ; this one is the authority on what the node run produced.

    Args:
        run_id (str):
        node_run_id (str):
        limit (int | Unset): Molecules per page. Default: 50.
        cursor (None | str | Unset): Pagination token from the previous response's `nextCursor`.
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PipelineNodeRunMoleculePage | Problem
    """

    return sync_detailed(
        run_id=run_id,
        node_run_id=node_run_id,
        client=client,
        limit=limit,
        cursor=cursor,
        tamarind_version=tamarind_version,
    ).parsed


async def asyncio_detailed(
    run_id: str,
    node_run_id: str,
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = 50,
    cursor: None | str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Response[PipelineNodeRunMoleculePage | Problem]:
    """List the molecules a node run produced

     The molecules one node run produced, with their scores.

    Read a node run's results through this, not through `PipelineNodeRun.outputGroup`. `outputGroup` is
    the group a node MINTED, and two common kinds of node mint none: a node that enriches its inputs in
    place (scoring, structure prediction) leaves its molecules in the group they came from, and a filter
    node's survivors exist only as node-run outputs. For both, `outputGroup` is correctly `null` —
    reading results by group reports 'produced nothing' for exactly the node runs whose output you asked
    for. This endpoint answers for every kind of node.

    `nodeRunId` is the `id` of an entry in the run's `nodeRuns`. `limit` is a maximum and a page may be
    shorter when rows are large; follow `nextCursor`.

    A molecule too large for a page is 422 `node_run_molecule_response_too_large`, naming
    `moleculeEndpoint` (`/molecules/{id}`) and a `nextCursor` to skip past it.

    This is the COMPACT view: identity, sequence and scores, scoped to the RUN. For the same molecules
    with their groups, tags and provenance — and to threshold or rank them by a score — pass the same id
    to `GET /molecules?nodeRunId=...`, which supports `filter`, `sortBy`, `search` and 200 per page.
    That endpoint reads through your molecule library rather than through the run, so its `nodeRunId`
    parameter documents where the two differ; this one is the authority on what the node run produced.

    Args:
        run_id (str):
        node_run_id (str):
        limit (int | Unset): Molecules per page. Default: 50.
        cursor (None | str | Unset): Pagination token from the previous response's `nextCursor`.
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PipelineNodeRunMoleculePage | Problem]
    """

    kwargs = _get_kwargs(
        run_id=run_id,
        node_run_id=node_run_id,
        limit=limit,
        cursor=cursor,
        tamarind_version=tamarind_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    run_id: str,
    node_run_id: str,
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = 50,
    cursor: None | str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> PipelineNodeRunMoleculePage | Problem | None:
    """List the molecules a node run produced

     The molecules one node run produced, with their scores.

    Read a node run's results through this, not through `PipelineNodeRun.outputGroup`. `outputGroup` is
    the group a node MINTED, and two common kinds of node mint none: a node that enriches its inputs in
    place (scoring, structure prediction) leaves its molecules in the group they came from, and a filter
    node's survivors exist only as node-run outputs. For both, `outputGroup` is correctly `null` —
    reading results by group reports 'produced nothing' for exactly the node runs whose output you asked
    for. This endpoint answers for every kind of node.

    `nodeRunId` is the `id` of an entry in the run's `nodeRuns`. `limit` is a maximum and a page may be
    shorter when rows are large; follow `nextCursor`.

    A molecule too large for a page is 422 `node_run_molecule_response_too_large`, naming
    `moleculeEndpoint` (`/molecules/{id}`) and a `nextCursor` to skip past it.

    This is the COMPACT view: identity, sequence and scores, scoped to the RUN. For the same molecules
    with their groups, tags and provenance — and to threshold or rank them by a score — pass the same id
    to `GET /molecules?nodeRunId=...`, which supports `filter`, `sortBy`, `search` and 200 per page.
    That endpoint reads through your molecule library rather than through the run, so its `nodeRunId`
    parameter documents where the two differ; this one is the authority on what the node run produced.

    Args:
        run_id (str):
        node_run_id (str):
        limit (int | Unset): Molecules per page. Default: 50.
        cursor (None | str | Unset): Pagination token from the previous response's `nextCursor`.
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PipelineNodeRunMoleculePage | Problem
    """

    return (
        await asyncio_detailed(
            run_id=run_id,
            node_run_id=node_run_id,
            client=client,
            limit=limit,
            cursor=cursor,
            tamarind_version=tamarind_version,
        )
    ).parsed
