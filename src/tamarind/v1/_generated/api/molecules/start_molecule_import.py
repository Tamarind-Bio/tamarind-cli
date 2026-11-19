from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.molecule_import_request import MoleculeImportRequest
from ...models.molecule_import_start import MoleculeImportStart
from ...models.problem import Problem
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    body: MoleculeImportRequest,
    tamarind_version: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(tamarind_version, Unset):
        headers["Tamarind-Version"] = tamarind_version

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/molecules/imports",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> MoleculeImportStart | Problem:
    if response.status_code == 201:
        response_201 = MoleculeImportStart.from_dict(response.json())

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

    if response.status_code == 404:
        response_404 = Problem.from_dict(response.json())

        return response_404

    if response.status_code == 409:
        response_409 = Problem.from_dict(response.json())

        return response_409

    if response.status_code == 413:
        response_413 = Problem.from_dict(response.json())

        return response_413

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
) -> Response[MoleculeImportStart | Problem]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: MoleculeImportRequest,
    tamarind_version: str | Unset = UNSET,
) -> Response[MoleculeImportStart | Problem]:
    """Start a file import

     Import molecules from a file. Step 1 of 3.

    Where your organization hides members' data from each other, a coworker's group answers as an
    unknown group. The group is checked again at commit.

    Then `PUT` the bytes to `uploadUrl`, and `POST
    /molecules/imports/{importId}/commit` to enqueue ingestion.

    For a CSV, describe your chain columns with `chainMapping` (keyed by chain id);
    `columnMapping` handles the scalar columns only. For `pdb`/`sdf`/`fasta`/`zip`
    the chains are read from the file.

    A `sizeBytes` over 16 MiB for any format but CSV is 413 `molecules_import_too_large` (CSV
    streams, up to 2 GiB). A group being deleted is 409 `molecule_group_deleting`.

    Args:
        tamarind_version (str | Unset):
        body (MoleculeImportRequest): The spec's `FileImportRequest`.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[MoleculeImportStart | Problem]
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
    body: MoleculeImportRequest,
    tamarind_version: str | Unset = UNSET,
) -> MoleculeImportStart | Problem | None:
    """Start a file import

     Import molecules from a file. Step 1 of 3.

    Where your organization hides members' data from each other, a coworker's group answers as an
    unknown group. The group is checked again at commit.

    Then `PUT` the bytes to `uploadUrl`, and `POST
    /molecules/imports/{importId}/commit` to enqueue ingestion.

    For a CSV, describe your chain columns with `chainMapping` (keyed by chain id);
    `columnMapping` handles the scalar columns only. For `pdb`/`sdf`/`fasta`/`zip`
    the chains are read from the file.

    A `sizeBytes` over 16 MiB for any format but CSV is 413 `molecules_import_too_large` (CSV
    streams, up to 2 GiB). A group being deleted is 409 `molecule_group_deleting`.

    Args:
        tamarind_version (str | Unset):
        body (MoleculeImportRequest): The spec's `FileImportRequest`.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        MoleculeImportStart | Problem
    """

    return sync_detailed(
        client=client,
        body=body,
        tamarind_version=tamarind_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: MoleculeImportRequest,
    tamarind_version: str | Unset = UNSET,
) -> Response[MoleculeImportStart | Problem]:
    """Start a file import

     Import molecules from a file. Step 1 of 3.

    Where your organization hides members' data from each other, a coworker's group answers as an
    unknown group. The group is checked again at commit.

    Then `PUT` the bytes to `uploadUrl`, and `POST
    /molecules/imports/{importId}/commit` to enqueue ingestion.

    For a CSV, describe your chain columns with `chainMapping` (keyed by chain id);
    `columnMapping` handles the scalar columns only. For `pdb`/`sdf`/`fasta`/`zip`
    the chains are read from the file.

    A `sizeBytes` over 16 MiB for any format but CSV is 413 `molecules_import_too_large` (CSV
    streams, up to 2 GiB). A group being deleted is 409 `molecule_group_deleting`.

    Args:
        tamarind_version (str | Unset):
        body (MoleculeImportRequest): The spec's `FileImportRequest`.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[MoleculeImportStart | Problem]
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
    body: MoleculeImportRequest,
    tamarind_version: str | Unset = UNSET,
) -> MoleculeImportStart | Problem | None:
    """Start a file import

     Import molecules from a file. Step 1 of 3.

    Where your organization hides members' data from each other, a coworker's group answers as an
    unknown group. The group is checked again at commit.

    Then `PUT` the bytes to `uploadUrl`, and `POST
    /molecules/imports/{importId}/commit` to enqueue ingestion.

    For a CSV, describe your chain columns with `chainMapping` (keyed by chain id);
    `columnMapping` handles the scalar columns only. For `pdb`/`sdf`/`fasta`/`zip`
    the chains are read from the file.

    A `sizeBytes` over 16 MiB for any format but CSV is 413 `molecules_import_too_large` (CSV
    streams, up to 2 GiB). A group being deleted is 409 `molecule_group_deleting`.

    Args:
        tamarind_version (str | Unset):
        body (MoleculeImportRequest): The spec's `FileImportRequest`.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        MoleculeImportStart | Problem
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            tamarind_version=tamarind_version,
        )
    ).parsed
