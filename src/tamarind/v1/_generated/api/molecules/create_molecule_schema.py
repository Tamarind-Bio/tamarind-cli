from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.create_molecule_schema_request import CreateMoleculeSchemaRequest
from ...models.molecule_schema import MoleculeSchema
from ...models.problem import Problem
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    body: CreateMoleculeSchemaRequest,
    tamarind_version: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(tamarind_version, Unset):
        headers["Tamarind-Version"] = tamarind_version

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/molecules/schemas",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> MoleculeSchema | Problem:
    if response.status_code == 201:
        response_201 = MoleculeSchema.from_dict(response.json())

        return response_201

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
) -> Response[MoleculeSchema | Problem]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateMoleculeSchemaRequest,
    tamarind_version: str | Unset = UNSET,
) -> Response[MoleculeSchema | Problem]:
    """Create Schema

     Define a reusable set of typed fields you can bind to a group.

    Scalar fields (`string`, `integer`, `float`, `boolean`, `category`) constrain a molecule's metadata.

    A `chain` field describes a required chain, named by its `name`.

    Args:
        tamarind_version (str | Unset):
        body (CreateMoleculeSchemaRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[MoleculeSchema | Problem]
    """

    kwargs = _get_kwargs(
        body=body,
        tamarind_version=tamarind_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    body: CreateMoleculeSchemaRequest,
    tamarind_version: str | Unset = UNSET,
) -> MoleculeSchema | Problem | None:
    """Create Schema

     Define a reusable set of typed fields you can bind to a group.

    Scalar fields (`string`, `integer`, `float`, `boolean`, `category`) constrain a molecule's metadata.

    A `chain` field describes a required chain, named by its `name`.

    Args:
        tamarind_version (str | Unset):
        body (CreateMoleculeSchemaRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        MoleculeSchema | Problem
    """

    return sync_detailed(
        client=client,
        body=body,
        tamarind_version=tamarind_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateMoleculeSchemaRequest,
    tamarind_version: str | Unset = UNSET,
) -> Response[MoleculeSchema | Problem]:
    """Create Schema

     Define a reusable set of typed fields you can bind to a group.

    Scalar fields (`string`, `integer`, `float`, `boolean`, `category`) constrain a molecule's metadata.

    A `chain` field describes a required chain, named by its `name`.

    Args:
        tamarind_version (str | Unset):
        body (CreateMoleculeSchemaRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[MoleculeSchema | Problem]
    """

    kwargs = _get_kwargs(
        body=body,
        tamarind_version=tamarind_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: CreateMoleculeSchemaRequest,
    tamarind_version: str | Unset = UNSET,
) -> MoleculeSchema | Problem | None:
    """Create Schema

     Define a reusable set of typed fields you can bind to a group.

    Scalar fields (`string`, `integer`, `float`, `boolean`, `category`) constrain a molecule's metadata.

    A `chain` field describes a required chain, named by its `name`.

    Args:
        tamarind_version (str | Unset):
        body (CreateMoleculeSchemaRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        MoleculeSchema | Problem
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            tamarind_version=tamarind_version,
        )
    ).parsed
