from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.problem import Problem
from ...models.upload_molecules_request import UploadMoleculesRequest
from ...models.upload_molecules_response import UploadMoleculesResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    body: UploadMoleculesRequest,
    tamarind_version: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(tamarind_version, Unset):
        headers["Tamarind-Version"] = tamarind_version

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/molecules/upload",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Problem | UploadMoleculesResponse:
    if response.status_code == 202:
        response_202 = UploadMoleculesResponse.from_dict(response.json())

        return response_202

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

    if response.status_code == 504:
        response_504 = Problem.from_dict(response.json())

        return response_504

    response_default = Problem.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[Problem | UploadMoleculesResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: UploadMoleculesRequest,
    tamarind_version: str | Unset = UNSET,
) -> Response[Problem | UploadMoleculesResponse]:
    """Upload Molecules

     Queue molecules for JSON upload ingestion.

    Where your organization hides members' data from each other, a coworker's group answers as an
    unknown group.

    Returns HTTP 202 with the exact content-addressed molecule ids and an import id.
    Poll `GET /molecules/imports/{importId}` until the import reaches `ingested`,
    `failed`, or `cancelled`; the ids become readable only after ingestion succeeds.

    Molecules that come to more than 16 MiB of JSON are 413 `molecules_import_too_large`. A group being
    deleted is 409
    `molecule_group_deleting`. When the import was created but it can't be told whether it was
    queued, the answer is 504 `molecules_import_admission_uncertain`, with the import's id in
    `errors`: poll it, or cancel it with `DELETE /molecules/imports/{importId}`, rather than
    uploading again. An organization that can't start compute is 403
    `organization_compute_disabled`.

    Args:
        tamarind_version (str | Unset):
        body (UploadMoleculesRequest): The spec's `UploadRequest`.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Problem | UploadMoleculesResponse]
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
    body: UploadMoleculesRequest,
    tamarind_version: str | Unset = UNSET,
) -> Problem | UploadMoleculesResponse | None:
    """Upload Molecules

     Queue molecules for JSON upload ingestion.

    Where your organization hides members' data from each other, a coworker's group answers as an
    unknown group.

    Returns HTTP 202 with the exact content-addressed molecule ids and an import id.
    Poll `GET /molecules/imports/{importId}` until the import reaches `ingested`,
    `failed`, or `cancelled`; the ids become readable only after ingestion succeeds.

    Molecules that come to more than 16 MiB of JSON are 413 `molecules_import_too_large`. A group being
    deleted is 409
    `molecule_group_deleting`. When the import was created but it can't be told whether it was
    queued, the answer is 504 `molecules_import_admission_uncertain`, with the import's id in
    `errors`: poll it, or cancel it with `DELETE /molecules/imports/{importId}`, rather than
    uploading again. An organization that can't start compute is 403
    `organization_compute_disabled`.

    Args:
        tamarind_version (str | Unset):
        body (UploadMoleculesRequest): The spec's `UploadRequest`.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Problem | UploadMoleculesResponse
    """

    return sync_detailed(
        client=client,
        body=body,
        tamarind_version=tamarind_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: UploadMoleculesRequest,
    tamarind_version: str | Unset = UNSET,
) -> Response[Problem | UploadMoleculesResponse]:
    """Upload Molecules

     Queue molecules for JSON upload ingestion.

    Where your organization hides members' data from each other, a coworker's group answers as an
    unknown group.

    Returns HTTP 202 with the exact content-addressed molecule ids and an import id.
    Poll `GET /molecules/imports/{importId}` until the import reaches `ingested`,
    `failed`, or `cancelled`; the ids become readable only after ingestion succeeds.

    Molecules that come to more than 16 MiB of JSON are 413 `molecules_import_too_large`. A group being
    deleted is 409
    `molecule_group_deleting`. When the import was created but it can't be told whether it was
    queued, the answer is 504 `molecules_import_admission_uncertain`, with the import's id in
    `errors`: poll it, or cancel it with `DELETE /molecules/imports/{importId}`, rather than
    uploading again. An organization that can't start compute is 403
    `organization_compute_disabled`.

    Args:
        tamarind_version (str | Unset):
        body (UploadMoleculesRequest): The spec's `UploadRequest`.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Problem | UploadMoleculesResponse]
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
    body: UploadMoleculesRequest,
    tamarind_version: str | Unset = UNSET,
) -> Problem | UploadMoleculesResponse | None:
    """Upload Molecules

     Queue molecules for JSON upload ingestion.

    Where your organization hides members' data from each other, a coworker's group answers as an
    unknown group.

    Returns HTTP 202 with the exact content-addressed molecule ids and an import id.
    Poll `GET /molecules/imports/{importId}` until the import reaches `ingested`,
    `failed`, or `cancelled`; the ids become readable only after ingestion succeeds.

    Molecules that come to more than 16 MiB of JSON are 413 `molecules_import_too_large`. A group being
    deleted is 409
    `molecule_group_deleting`. When the import was created but it can't be told whether it was
    queued, the answer is 504 `molecules_import_admission_uncertain`, with the import's id in
    `errors`: poll it, or cancel it with `DELETE /molecules/imports/{importId}`, rather than
    uploading again. An organization that can't start compute is 403
    `organization_compute_disabled`.

    Args:
        tamarind_version (str | Unset):
        body (UploadMoleculesRequest): The spec's `UploadRequest`.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Problem | UploadMoleculesResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            tamarind_version=tamarind_version,
        )
    ).parsed
