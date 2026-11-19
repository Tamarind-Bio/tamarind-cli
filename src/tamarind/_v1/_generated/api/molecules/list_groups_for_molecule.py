from http import HTTPStatus
from typing import Any
from urllib.parse import quote
from uuid import UUID

import httpx

from ...client import AuthenticatedClient, Client
from ...models.molecule_group_page import MoleculeGroupPage
from ...models.problem import Problem
from ...types import UNSET, Response, Unset


def _get_kwargs(
    molecule_id: UUID,
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
        "url": "/molecules/{molecule_id}/groups".format(
            molecule_id=quote(str(molecule_id), safe=""),
        ),
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> MoleculeGroupPage | Problem:
    if response.status_code == 200:
        response_200 = MoleculeGroupPage.from_dict(response.json())

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
) -> Response[MoleculeGroupPage | Problem]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    molecule_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = 50,
    cursor: None | str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Response[MoleculeGroupPage | Problem]:
    """List Molecule Groups

     List every group a molecule belongs to.

    Use this when `GET /molecules/{moleculeId}` marks `groups` as truncated. Only your own groups are
    listed.

    Paginated — follow `nextCursor` until it is null.

    Args:
        molecule_id (UUID):
        limit (int | Unset): Maximum number of items to return in one page. Default: 50.
        cursor (None | str | Unset): Pagination token from the previous response's `nextCursor`.
            Omit for the first page; follow `nextCursor` until null (an empty `items` page while
            `nextCursor` is set is normal).
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[MoleculeGroupPage | Problem]
    """

    kwargs = _get_kwargs(
        molecule_id=molecule_id,
        limit=limit,
        cursor=cursor,
        tamarind_version=tamarind_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    molecule_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = 50,
    cursor: None | str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> MoleculeGroupPage | Problem | None:
    """List Molecule Groups

     List every group a molecule belongs to.

    Use this when `GET /molecules/{moleculeId}` marks `groups` as truncated. Only your own groups are
    listed.

    Paginated — follow `nextCursor` until it is null.

    Args:
        molecule_id (UUID):
        limit (int | Unset): Maximum number of items to return in one page. Default: 50.
        cursor (None | str | Unset): Pagination token from the previous response's `nextCursor`.
            Omit for the first page; follow `nextCursor` until null (an empty `items` page while
            `nextCursor` is set is normal).
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        MoleculeGroupPage | Problem
    """

    return sync_detailed(
        molecule_id=molecule_id,
        client=client,
        limit=limit,
        cursor=cursor,
        tamarind_version=tamarind_version,
    ).parsed


async def asyncio_detailed(
    molecule_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = 50,
    cursor: None | str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Response[MoleculeGroupPage | Problem]:
    """List Molecule Groups

     List every group a molecule belongs to.

    Use this when `GET /molecules/{moleculeId}` marks `groups` as truncated. Only your own groups are
    listed.

    Paginated — follow `nextCursor` until it is null.

    Args:
        molecule_id (UUID):
        limit (int | Unset): Maximum number of items to return in one page. Default: 50.
        cursor (None | str | Unset): Pagination token from the previous response's `nextCursor`.
            Omit for the first page; follow `nextCursor` until null (an empty `items` page while
            `nextCursor` is set is normal).
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[MoleculeGroupPage | Problem]
    """

    kwargs = _get_kwargs(
        molecule_id=molecule_id,
        limit=limit,
        cursor=cursor,
        tamarind_version=tamarind_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    molecule_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = 50,
    cursor: None | str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> MoleculeGroupPage | Problem | None:
    """List Molecule Groups

     List every group a molecule belongs to.

    Use this when `GET /molecules/{moleculeId}` marks `groups` as truncated. Only your own groups are
    listed.

    Paginated — follow `nextCursor` until it is null.

    Args:
        molecule_id (UUID):
        limit (int | Unset): Maximum number of items to return in one page. Default: 50.
        cursor (None | str | Unset): Pagination token from the previous response's `nextCursor`.
            Omit for the first page; follow `nextCursor` until null (an empty `items` page while
            `nextCursor` is set is normal).
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        MoleculeGroupPage | Problem
    """

    return (
        await asyncio_detailed(
            molecule_id=molecule_id,
            client=client,
            limit=limit,
            cursor=cursor,
            tamarind_version=tamarind_version,
        )
    ).parsed
