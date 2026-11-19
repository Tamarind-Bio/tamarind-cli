from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.file_stats import FileStats
from ...models.problem import Problem
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    folder: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(tamarind_version, Unset):
        headers["Tamarind-Version"] = tamarind_version

    params: dict[str, Any] = {}

    params["folder"] = folder

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/files/stats",
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> FileStats | Problem:
    if response.status_code == 200:
        response_200 = FileStats.from_dict(response.json())

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
) -> Response[FileStats | Problem]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    folder: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Response[FileStats | Problem]:
    r"""Count workspace files and bytes, by extension

     Counts the files directly in `folder`, not its subfolders: what a listing of it without
    `recursive` shows. At the root that's your top-level uploads, read from the file catalog, the
    number today's MCP `getFileStats` gives; it follows storage by a few seconds. A file with no
    extension, or a suffix over 32 characters, counts under `\"\"`. A folder holding more than
    250,000 files and folders (at the root, more than 250,000 uploads), or files with more than
    1,000 distinct extensions, is 422 `folder_too_large`. A folder that doesn't exist counts zero.

    Args:
        folder (str | Unset):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[FileStats | Problem]
    """

    kwargs = _get_kwargs(
        folder=folder,
        tamarind_version=tamarind_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    folder: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> FileStats | Problem | None:
    r"""Count workspace files and bytes, by extension

     Counts the files directly in `folder`, not its subfolders: what a listing of it without
    `recursive` shows. At the root that's your top-level uploads, read from the file catalog, the
    number today's MCP `getFileStats` gives; it follows storage by a few seconds. A file with no
    extension, or a suffix over 32 characters, counts under `\"\"`. A folder holding more than
    250,000 files and folders (at the root, more than 250,000 uploads), or files with more than
    1,000 distinct extensions, is 422 `folder_too_large`. A folder that doesn't exist counts zero.

    Args:
        folder (str | Unset):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        FileStats | Problem
    """

    return sync_detailed(
        client=client,
        folder=folder,
        tamarind_version=tamarind_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    folder: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Response[FileStats | Problem]:
    r"""Count workspace files and bytes, by extension

     Counts the files directly in `folder`, not its subfolders: what a listing of it without
    `recursive` shows. At the root that's your top-level uploads, read from the file catalog, the
    number today's MCP `getFileStats` gives; it follows storage by a few seconds. A file with no
    extension, or a suffix over 32 characters, counts under `\"\"`. A folder holding more than
    250,000 files and folders (at the root, more than 250,000 uploads), or files with more than
    1,000 distinct extensions, is 422 `folder_too_large`. A folder that doesn't exist counts zero.

    Args:
        folder (str | Unset):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[FileStats | Problem]
    """

    kwargs = _get_kwargs(
        folder=folder,
        tamarind_version=tamarind_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    folder: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> FileStats | Problem | None:
    r"""Count workspace files and bytes, by extension

     Counts the files directly in `folder`, not its subfolders: what a listing of it without
    `recursive` shows. At the root that's your top-level uploads, read from the file catalog, the
    number today's MCP `getFileStats` gives; it follows storage by a few seconds. A file with no
    extension, or a suffix over 32 characters, counts under `\"\"`. A folder holding more than
    250,000 files and folders (at the root, more than 250,000 uploads), or files with more than
    1,000 distinct extensions, is 422 `folder_too_large`. A folder that doesn't exist counts zero.

    Args:
        folder (str | Unset):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        FileStats | Problem
    """

    return (
        await asyncio_detailed(
            client=client,
            folder=folder,
            tamarind_version=tamarind_version,
        )
    ).parsed
