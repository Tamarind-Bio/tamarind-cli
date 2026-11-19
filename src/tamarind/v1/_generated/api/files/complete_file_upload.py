from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.complete_file_upload_body import CompleteFileUploadBody
from ...models.file_entry import FileEntry
from ...models.problem import Problem
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    body: CompleteFileUploadBody,
    tamarind_version: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(tamarind_version, Unset):
        headers["Tamarind-Version"] = tamarind_version

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/files/complete",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> FileEntry | Problem:
    if response.status_code == 200:
        response_200 = FileEntry.from_dict(response.json())

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
) -> Response[FileEntry | Problem]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CompleteFileUploadBody,
    tamarind_version: str | Unset = UNSET,
) -> Response[FileEntry | Problem]:
    """Finish a multipart upload

     Send every part the upload was started with (1 to N, each once, with the ETag its PUT returned), and
    the parts must add up to its `sizeBytes`; otherwise it is 422 at `/parts` and nothing is stored. An
    `uploadId` that isn't one of your uploads, or an upload that was aborted, is 404. A retry after a
    completion whose answer was lost answers 200 with the stored file. Abandoned uploads are cleaned up
    by storage after a few days.

    Args:
        tamarind_version (str | Unset):
        body (CompleteFileUploadBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[FileEntry | Problem]
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
    body: CompleteFileUploadBody,
    tamarind_version: str | Unset = UNSET,
) -> FileEntry | Problem | None:
    """Finish a multipart upload

     Send every part the upload was started with (1 to N, each once, with the ETag its PUT returned), and
    the parts must add up to its `sizeBytes`; otherwise it is 422 at `/parts` and nothing is stored. An
    `uploadId` that isn't one of your uploads, or an upload that was aborted, is 404. A retry after a
    completion whose answer was lost answers 200 with the stored file. Abandoned uploads are cleaned up
    by storage after a few days.

    Args:
        tamarind_version (str | Unset):
        body (CompleteFileUploadBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        FileEntry | Problem
    """

    return sync_detailed(
        client=client,
        body=body,
        tamarind_version=tamarind_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CompleteFileUploadBody,
    tamarind_version: str | Unset = UNSET,
) -> Response[FileEntry | Problem]:
    """Finish a multipart upload

     Send every part the upload was started with (1 to N, each once, with the ETag its PUT returned), and
    the parts must add up to its `sizeBytes`; otherwise it is 422 at `/parts` and nothing is stored. An
    `uploadId` that isn't one of your uploads, or an upload that was aborted, is 404. A retry after a
    completion whose answer was lost answers 200 with the stored file. Abandoned uploads are cleaned up
    by storage after a few days.

    Args:
        tamarind_version (str | Unset):
        body (CompleteFileUploadBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[FileEntry | Problem]
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
    body: CompleteFileUploadBody,
    tamarind_version: str | Unset = UNSET,
) -> FileEntry | Problem | None:
    """Finish a multipart upload

     Send every part the upload was started with (1 to N, each once, with the ETag its PUT returned), and
    the parts must add up to its `sizeBytes`; otherwise it is 422 at `/parts` and nothing is stored. An
    `uploadId` that isn't one of your uploads, or an upload that was aborted, is 404. A retry after a
    completion whose answer was lost answers 200 with the stored file. Abandoned uploads are cleaned up
    by storage after a few days.

    Args:
        tamarind_version (str | Unset):
        body (CompleteFileUploadBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        FileEntry | Problem
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            tamarind_version=tamarind_version,
        )
    ).parsed
