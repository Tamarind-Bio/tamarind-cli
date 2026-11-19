from http import HTTPStatus
from typing import Any
from urllib.parse import quote
from uuid import UUID

import httpx

from ...client import AuthenticatedClient, Client
from ...models.molecule_schema import MoleculeSchema
from ...models.problem import Problem
from ...types import UNSET, Response, Unset


def _get_kwargs(
    schema_id: UUID,
    *,
    tamarind_version: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(tamarind_version, Unset):
        headers["Tamarind-Version"] = tamarind_version

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/molecules/schemas/{schema_id}".format(
            schema_id=quote(str(schema_id), safe=""),
        ),
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> MoleculeSchema | Problem:
    if response.status_code == 200:
        response_200 = MoleculeSchema.from_dict(response.json())

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
) -> Response[MoleculeSchema | Problem]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    schema_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    tamarind_version: str | Unset = UNSET,
) -> Response[MoleculeSchema | Problem]:
    """Get Schema

     Fetch one schema by id. Where your organization hides members' data from each other, a coworker's
    schema answers as an unknown schema.

    Args:
        schema_id (UUID):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[MoleculeSchema | Problem]
    """

    kwargs = _get_kwargs(
        schema_id=schema_id,
        tamarind_version=tamarind_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    schema_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    tamarind_version: str | Unset = UNSET,
) -> MoleculeSchema | Problem | None:
    """Get Schema

     Fetch one schema by id. Where your organization hides members' data from each other, a coworker's
    schema answers as an unknown schema.

    Args:
        schema_id (UUID):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        MoleculeSchema | Problem
    """

    return sync_detailed(
        schema_id=schema_id,
        client=client,
        tamarind_version=tamarind_version,
    ).parsed


async def asyncio_detailed(
    schema_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    tamarind_version: str | Unset = UNSET,
) -> Response[MoleculeSchema | Problem]:
    """Get Schema

     Fetch one schema by id. Where your organization hides members' data from each other, a coworker's
    schema answers as an unknown schema.

    Args:
        schema_id (UUID):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[MoleculeSchema | Problem]
    """

    kwargs = _get_kwargs(
        schema_id=schema_id,
        tamarind_version=tamarind_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    schema_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    tamarind_version: str | Unset = UNSET,
) -> MoleculeSchema | Problem | None:
    """Get Schema

     Fetch one schema by id. Where your organization hides members' data from each other, a coworker's
    schema answers as an unknown schema.

    Args:
        schema_id (UUID):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        MoleculeSchema | Problem
    """

    return (
        await asyncio_detailed(
            schema_id=schema_id,
            client=client,
            tamarind_version=tamarind_version,
        )
    ).parsed
