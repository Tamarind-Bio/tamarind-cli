from http import HTTPStatus
from typing import Any
from urllib.parse import quote
from uuid import UUID

import httpx

from ...client import AuthenticatedClient, Client
from ...models.commit_molecule_import_request import CommitMoleculeImportRequest
from ...models.molecule_import_commit_queued import MoleculeImportCommitQueued
from ...models.problem import Problem
from ...types import UNSET, Response, Unset


def _get_kwargs(
    import_id: UUID,
    *,
    body: CommitMoleculeImportRequest | None | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(tamarind_version, Unset):
        headers["Tamarind-Version"] = tamarind_version

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/molecules/imports/{import_id}/commit".format(
            import_id=quote(str(import_id), safe=""),
        ),
    }

    if isinstance(body, CommitMoleculeImportRequest):
        _kwargs["json"] = body.to_dict()
    else:
        _kwargs["json"] = body

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> MoleculeImportCommitQueued | Problem:
    if response.status_code == 200:
        response_200 = MoleculeImportCommitQueued.from_dict(response.json())

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
) -> Response[MoleculeImportCommitQueued | Problem]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    import_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    body: CommitMoleculeImportRequest | None | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Response[MoleculeImportCommitQueued | Problem]:
    r"""Commit an import

     Step 3 of 3: enqueue ingestion for the uploaded file. It answers 200 with the import `queued`,
    before
    ingestion runs; poll `getMoleculeImport` for the outcome.

    The target group's visibility is checked again here, because hiding can be turned on between start
    and commit.

    - Returns `status: \"queued\"` immediately by default — poll `GET /molecules/imports/{importId}`.
    - Committing an import that isn't waiting for its commit (committed already, or cancelled) is 409
      `molecules_import_already_dispatched`; committing before the bytes were PUT is 409
      `molecule_file_not_uploaded`.
    - A file over 2 GiB, or a non-CSV file over 16 MiB, is 413 `molecules_import_too_large`.
    - A `columnMapping` role outside the listed ones is 422 `molecule_csv_parse_invalid` here.
    - An organization that can't start compute is 403 `organization_compute_disabled`.

    Args:
        import_id (UUID):
        tamarind_version (str | Unset):
        body (CommitMoleculeImportRequest | None | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[MoleculeImportCommitQueued | Problem]
    """

    kwargs = _get_kwargs(
        import_id=import_id,
        body=body,
        tamarind_version=tamarind_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    import_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    body: CommitMoleculeImportRequest | None | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> MoleculeImportCommitQueued | Problem | None:
    r"""Commit an import

     Step 3 of 3: enqueue ingestion for the uploaded file. It answers 200 with the import `queued`,
    before
    ingestion runs; poll `getMoleculeImport` for the outcome.

    The target group's visibility is checked again here, because hiding can be turned on between start
    and commit.

    - Returns `status: \"queued\"` immediately by default — poll `GET /molecules/imports/{importId}`.
    - Committing an import that isn't waiting for its commit (committed already, or cancelled) is 409
      `molecules_import_already_dispatched`; committing before the bytes were PUT is 409
      `molecule_file_not_uploaded`.
    - A file over 2 GiB, or a non-CSV file over 16 MiB, is 413 `molecules_import_too_large`.
    - A `columnMapping` role outside the listed ones is 422 `molecule_csv_parse_invalid` here.
    - An organization that can't start compute is 403 `organization_compute_disabled`.

    Args:
        import_id (UUID):
        tamarind_version (str | Unset):
        body (CommitMoleculeImportRequest | None | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        MoleculeImportCommitQueued | Problem
    """

    return sync_detailed(
        import_id=import_id,
        client=client,
        body=body,
        tamarind_version=tamarind_version,
    ).parsed


async def asyncio_detailed(
    import_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    body: CommitMoleculeImportRequest | None | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Response[MoleculeImportCommitQueued | Problem]:
    r"""Commit an import

     Step 3 of 3: enqueue ingestion for the uploaded file. It answers 200 with the import `queued`,
    before
    ingestion runs; poll `getMoleculeImport` for the outcome.

    The target group's visibility is checked again here, because hiding can be turned on between start
    and commit.

    - Returns `status: \"queued\"` immediately by default — poll `GET /molecules/imports/{importId}`.
    - Committing an import that isn't waiting for its commit (committed already, or cancelled) is 409
      `molecules_import_already_dispatched`; committing before the bytes were PUT is 409
      `molecule_file_not_uploaded`.
    - A file over 2 GiB, or a non-CSV file over 16 MiB, is 413 `molecules_import_too_large`.
    - A `columnMapping` role outside the listed ones is 422 `molecule_csv_parse_invalid` here.
    - An organization that can't start compute is 403 `organization_compute_disabled`.

    Args:
        import_id (UUID):
        tamarind_version (str | Unset):
        body (CommitMoleculeImportRequest | None | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[MoleculeImportCommitQueued | Problem]
    """

    kwargs = _get_kwargs(
        import_id=import_id,
        body=body,
        tamarind_version=tamarind_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    import_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    body: CommitMoleculeImportRequest | None | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> MoleculeImportCommitQueued | Problem | None:
    r"""Commit an import

     Step 3 of 3: enqueue ingestion for the uploaded file. It answers 200 with the import `queued`,
    before
    ingestion runs; poll `getMoleculeImport` for the outcome.

    The target group's visibility is checked again here, because hiding can be turned on between start
    and commit.

    - Returns `status: \"queued\"` immediately by default — poll `GET /molecules/imports/{importId}`.
    - Committing an import that isn't waiting for its commit (committed already, or cancelled) is 409
      `molecules_import_already_dispatched`; committing before the bytes were PUT is 409
      `molecule_file_not_uploaded`.
    - A file over 2 GiB, or a non-CSV file over 16 MiB, is 413 `molecules_import_too_large`.
    - A `columnMapping` role outside the listed ones is 422 `molecule_csv_parse_invalid` here.
    - An organization that can't start compute is 403 `organization_compute_disabled`.

    Args:
        import_id (UUID):
        tamarind_version (str | Unset):
        body (CommitMoleculeImportRequest | None | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        MoleculeImportCommitQueued | Problem
    """

    return (
        await asyncio_detailed(
            import_id=import_id,
            client=client,
            body=body,
            tamarind_version=tamarind_version,
        )
    ).parsed
