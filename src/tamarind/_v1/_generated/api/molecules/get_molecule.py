from http import HTTPStatus
from typing import Any
from urllib.parse import quote
from uuid import UUID

import httpx

from ...client import AuthenticatedClient, Client
from ...models.molecule import Molecule
from ...models.problem import Problem
from ...types import UNSET, Response, Unset


def _get_kwargs(
    molecule_id: UUID,
    *,
    group_id: None | str | Unset = UNSET,
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

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/molecules/{molecule_id}".format(
            molecule_id=quote(str(molecule_id), safe=""),
        ),
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Molecule | Problem:
    if response.status_code == 200:
        response_200 = Molecule.from_dict(response.json())

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
) -> Response[Molecule | Problem]:
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
    group_id: None | str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Response[Molecule | Problem]:
    """Get Molecule

     Get one molecule — its chains, scores, files, provenance, and groups, all inline.

    Addressed by its id; no group needed.

    Chain labels are per-group, so pass `groupId` to choose which group's labels you get, else the most
    recent group wins.

    Args:
        molecule_id (UUID):
        group_id (None | str | Unset):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Molecule | Problem]
    """

    kwargs = _get_kwargs(
        molecule_id=molecule_id,
        group_id=group_id,
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
    group_id: None | str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Molecule | Problem | None:
    """Get Molecule

     Get one molecule — its chains, scores, files, provenance, and groups, all inline.

    Addressed by its id; no group needed.

    Chain labels are per-group, so pass `groupId` to choose which group's labels you get, else the most
    recent group wins.

    Args:
        molecule_id (UUID):
        group_id (None | str | Unset):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Molecule | Problem
    """

    return sync_detailed(
        molecule_id=molecule_id,
        client=client,
        group_id=group_id,
        tamarind_version=tamarind_version,
    ).parsed


async def asyncio_detailed(
    molecule_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    group_id: None | str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Response[Molecule | Problem]:
    """Get Molecule

     Get one molecule — its chains, scores, files, provenance, and groups, all inline.

    Addressed by its id; no group needed.

    Chain labels are per-group, so pass `groupId` to choose which group's labels you get, else the most
    recent group wins.

    Args:
        molecule_id (UUID):
        group_id (None | str | Unset):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Molecule | Problem]
    """

    kwargs = _get_kwargs(
        molecule_id=molecule_id,
        group_id=group_id,
        tamarind_version=tamarind_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    molecule_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    group_id: None | str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Molecule | Problem | None:
    """Get Molecule

     Get one molecule — its chains, scores, files, provenance, and groups, all inline.

    Addressed by its id; no group needed.

    Chain labels are per-group, so pass `groupId` to choose which group's labels you get, else the most
    recent group wins.

    Args:
        molecule_id (UUID):
        group_id (None | str | Unset):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Molecule | Problem
    """

    return (
        await asyncio_detailed(
            molecule_id=molecule_id,
            client=client,
            group_id=group_id,
            tamarind_version=tamarind_version,
        )
    ).parsed
