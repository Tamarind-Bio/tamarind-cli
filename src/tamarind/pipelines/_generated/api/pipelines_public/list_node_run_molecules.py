from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.public_node_run_molecule_page import PublicNodeRunMoleculePage
from ...models.public_problem import PublicProblem
from ...types import UNSET, Response, Unset


def _get_kwargs(
    run_id: str,
    node_run_id: str,
    *,
    limit: int | Unset = 25,
    cursor: None | str | Unset = UNSET,
) -> dict[str, Any]:

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

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> PublicNodeRunMoleculePage | PublicProblem:
    if response.status_code == 200:
        response_200 = PublicNodeRunMoleculePage.from_dict(response.json())

        return response_200

    if response.status_code == 401:
        response_401 = PublicProblem.from_dict(response.json())

        return response_401

    if response.status_code == 404:
        response_404 = PublicProblem.from_dict(response.json())

        return response_404

    if response.status_code == 422:
        response_422 = PublicProblem.from_dict(response.json())

        return response_422

    response_default = PublicProblem.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[PublicNodeRunMoleculePage | PublicProblem]:
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
    limit: int | Unset = 25,
    cursor: None | str | Unset = UNSET,
) -> Response[PublicNodeRunMoleculePage | PublicProblem]:
    """List the molecules a node run produced

     The molecules one node run produced, with their scores.

    Read a node run's results through this, not through `PublicNodeRun.outputGroup`. `outputGroup` is
    the group a node MINTED, and two common kinds of node mint none: a node that enriches its inputs in
    place (scoring, structure prediction) leaves its molecules in the group they came from, and a filter
    node's survivors exist only as node-run outputs. For both, `outputGroup` is correctly `null` —
    reading results by group reports 'produced nothing' for exactly the node runs whose output you asked
    for. This endpoint answers for every kind of node.

    `node_run_id` is the `id` of an entry in the run's `nodeRuns`.

    Args:
        run_id (str):
        node_run_id (str):
        limit (int | Unset): Molecules per page. Default: 25.
        cursor (None | str | Unset): Pagination token from the previous response's `nextCursor`.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PublicNodeRunMoleculePage | PublicProblem]
    """

    kwargs = _get_kwargs(
        run_id=run_id,
        node_run_id=node_run_id,
        limit=limit,
        cursor=cursor,
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
    limit: int | Unset = 25,
    cursor: None | str | Unset = UNSET,
) -> PublicNodeRunMoleculePage | PublicProblem | None:
    """List the molecules a node run produced

     The molecules one node run produced, with their scores.

    Read a node run's results through this, not through `PublicNodeRun.outputGroup`. `outputGroup` is
    the group a node MINTED, and two common kinds of node mint none: a node that enriches its inputs in
    place (scoring, structure prediction) leaves its molecules in the group they came from, and a filter
    node's survivors exist only as node-run outputs. For both, `outputGroup` is correctly `null` —
    reading results by group reports 'produced nothing' for exactly the node runs whose output you asked
    for. This endpoint answers for every kind of node.

    `node_run_id` is the `id` of an entry in the run's `nodeRuns`.

    Args:
        run_id (str):
        node_run_id (str):
        limit (int | Unset): Molecules per page. Default: 25.
        cursor (None | str | Unset): Pagination token from the previous response's `nextCursor`.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PublicNodeRunMoleculePage | PublicProblem
    """

    return sync_detailed(
        run_id=run_id,
        node_run_id=node_run_id,
        client=client,
        limit=limit,
        cursor=cursor,
    ).parsed


async def asyncio_detailed(
    run_id: str,
    node_run_id: str,
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = 25,
    cursor: None | str | Unset = UNSET,
) -> Response[PublicNodeRunMoleculePage | PublicProblem]:
    """List the molecules a node run produced

     The molecules one node run produced, with their scores.

    Read a node run's results through this, not through `PublicNodeRun.outputGroup`. `outputGroup` is
    the group a node MINTED, and two common kinds of node mint none: a node that enriches its inputs in
    place (scoring, structure prediction) leaves its molecules in the group they came from, and a filter
    node's survivors exist only as node-run outputs. For both, `outputGroup` is correctly `null` —
    reading results by group reports 'produced nothing' for exactly the node runs whose output you asked
    for. This endpoint answers for every kind of node.

    `node_run_id` is the `id` of an entry in the run's `nodeRuns`.

    Args:
        run_id (str):
        node_run_id (str):
        limit (int | Unset): Molecules per page. Default: 25.
        cursor (None | str | Unset): Pagination token from the previous response's `nextCursor`.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PublicNodeRunMoleculePage | PublicProblem]
    """

    kwargs = _get_kwargs(
        run_id=run_id,
        node_run_id=node_run_id,
        limit=limit,
        cursor=cursor,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    run_id: str,
    node_run_id: str,
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = 25,
    cursor: None | str | Unset = UNSET,
) -> PublicNodeRunMoleculePage | PublicProblem | None:
    """List the molecules a node run produced

     The molecules one node run produced, with their scores.

    Read a node run's results through this, not through `PublicNodeRun.outputGroup`. `outputGroup` is
    the group a node MINTED, and two common kinds of node mint none: a node that enriches its inputs in
    place (scoring, structure prediction) leaves its molecules in the group they came from, and a filter
    node's survivors exist only as node-run outputs. For both, `outputGroup` is correctly `null` —
    reading results by group reports 'produced nothing' for exactly the node runs whose output you asked
    for. This endpoint answers for every kind of node.

    `node_run_id` is the `id` of an entry in the run's `nodeRuns`.

    Args:
        run_id (str):
        node_run_id (str):
        limit (int | Unset): Molecules per page. Default: 25.
        cursor (None | str | Unset): Pagination token from the previous response's `nextCursor`.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PublicNodeRunMoleculePage | PublicProblem
    """

    return (
        await asyncio_detailed(
            run_id=run_id,
            node_run_id=node_run_id,
            client=client,
            limit=limit,
            cursor=cursor,
        )
    ).parsed
