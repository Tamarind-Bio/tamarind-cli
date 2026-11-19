from http import HTTPStatus
from typing import Any, cast

import httpx

from ...client import AuthenticatedClient, Client
from ...models.problem import Problem
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    path: str | Unset = UNSET,
    folder: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(tamarind_version, Unset):
        headers["Tamarind-Version"] = tamarind_version

    params: dict[str, Any] = {}

    params["path"] = path

    params["folder"] = folder

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": "/files",
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Any | Problem:
    if response.status_code == 204:
        response_204 = cast(Any, None)
        return response_204

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
) -> Response[Any | Problem]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    path: str | Unset = UNSET,
    folder: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Response[Any | Problem]:
    """Delete a file or a whole folder

     Send exactly one of `path` or `folder`. Sending neither or both answers 422, and nothing is
    deleted. Names are literal: `folder` may be a job's output folder, by its folder name. A path
    or folder that doesn't exist is 404. The root can't be deleted (422). A folder of more than
    10,000 files is 422 `folder_too_large`, refused before anything is touched. A file's sharing
    and links end before it is deleted, so a file uploaded again at that path is never reachable
    through an old share. If files keep arriving in a folder after three passes, the answer is 409
    `folder_changed`. A private export is the same 404 as a missing file. When storage or the
    sharing records can't be updated the answer is 503; a folder may then be partly deleted, and
    sending the delete again finishes it.

    Args:
        path (str | Unset):
        folder (str | Unset):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | Problem]
    """

    kwargs = _get_kwargs(
        path=path,
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
    path: str | Unset = UNSET,
    folder: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Any | Problem | None:
    """Delete a file or a whole folder

     Send exactly one of `path` or `folder`. Sending neither or both answers 422, and nothing is
    deleted. Names are literal: `folder` may be a job's output folder, by its folder name. A path
    or folder that doesn't exist is 404. The root can't be deleted (422). A folder of more than
    10,000 files is 422 `folder_too_large`, refused before anything is touched. A file's sharing
    and links end before it is deleted, so a file uploaded again at that path is never reachable
    through an old share. If files keep arriving in a folder after three passes, the answer is 409
    `folder_changed`. A private export is the same 404 as a missing file. When storage or the
    sharing records can't be updated the answer is 503; a folder may then be partly deleted, and
    sending the delete again finishes it.

    Args:
        path (str | Unset):
        folder (str | Unset):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | Problem
    """

    return sync_detailed(
        client=client,
        path=path,
        folder=folder,
        tamarind_version=tamarind_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    path: str | Unset = UNSET,
    folder: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Response[Any | Problem]:
    """Delete a file or a whole folder

     Send exactly one of `path` or `folder`. Sending neither or both answers 422, and nothing is
    deleted. Names are literal: `folder` may be a job's output folder, by its folder name. A path
    or folder that doesn't exist is 404. The root can't be deleted (422). A folder of more than
    10,000 files is 422 `folder_too_large`, refused before anything is touched. A file's sharing
    and links end before it is deleted, so a file uploaded again at that path is never reachable
    through an old share. If files keep arriving in a folder after three passes, the answer is 409
    `folder_changed`. A private export is the same 404 as a missing file. When storage or the
    sharing records can't be updated the answer is 503; a folder may then be partly deleted, and
    sending the delete again finishes it.

    Args:
        path (str | Unset):
        folder (str | Unset):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | Problem]
    """

    kwargs = _get_kwargs(
        path=path,
        folder=folder,
        tamarind_version=tamarind_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    path: str | Unset = UNSET,
    folder: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Any | Problem | None:
    """Delete a file or a whole folder

     Send exactly one of `path` or `folder`. Sending neither or both answers 422, and nothing is
    deleted. Names are literal: `folder` may be a job's output folder, by its folder name. A path
    or folder that doesn't exist is 404. The root can't be deleted (422). A folder of more than
    10,000 files is 422 `folder_too_large`, refused before anything is touched. A file's sharing
    and links end before it is deleted, so a file uploaded again at that path is never reachable
    through an old share. If files keep arriving in a folder after three passes, the answer is 409
    `folder_changed`. A private export is the same 404 as a missing file. When storage or the
    sharing records can't be updated the answer is 503; a folder may then be partly deleted, and
    sending the delete again finishes it.

    Args:
        path (str | Unset):
        folder (str | Unset):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | Problem
    """

    return (
        await asyncio_detailed(
            client=client,
            path=path,
            folder=folder,
            tamarind_version=tamarind_version,
        )
    ).parsed
