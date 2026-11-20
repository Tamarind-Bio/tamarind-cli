from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.file_entry_page import FileEntryPage
from ...models.list_files_type import ListFilesType
from ...models.problem import Problem
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    folder: str | Unset = UNSET,
    recursive: bool | Unset = False,
    extension: list[str] | Unset = UNSET,
    type_: ListFilesType | Unset = UNSET,
    search: str | Unset = UNSET,
    limit: int | Unset = 50,
    cursor: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(tamarind_version, Unset):
        headers["Tamarind-Version"] = tamarind_version

    params: dict[str, Any] = {}

    params["folder"] = folder

    params["recursive"] = recursive

    json_extension: list[str] | Unset = UNSET
    if not isinstance(extension, Unset):
        json_extension = extension

    params["extension"] = json_extension

    json_type_: str | Unset = UNSET
    if not isinstance(type_, Unset):
        json_type_ = type_.value

    params["type"] = json_type_

    params["search"] = search

    params["limit"] = limit

    params["cursor"] = cursor

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/files",
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> FileEntryPage | Problem:
    if response.status_code == 200:
        response_200 = FileEntryPage.from_dict(response.json())

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
) -> Response[FileEntryPage | Problem]:
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
    recursive: bool | Unset = False,
    extension: list[str] | Unset = UNSET,
    type_: ListFilesType | Unset = UNSET,
    search: str | Unset = UNSET,
    limit: int | Unset = 50,
    cursor: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Response[FileEntryPage | Problem]:
    """List workspace files and folders

     Every filter is applied by the server. Each item's `type` is `file` or `folder`. Paths are
    literal and relative to your workspace; job output folders are folders like any other.

    Below the root, the listing reads storage directly, so it is current the moment an upload or
    delete finishes, in path order. Each page reads at most 5,000 stored keys, so a sparse filter
    or a pile of archives can end a page short, or even empty, with a `nextCursor`. The root, listed
    without `recursive`, comes from the file catalog instead: your uploads newest first, then your
    top-level folders by name, reading at most 5,000 catalog rows a page. It follows storage by a
    few seconds. An organization that keeps files in its own bucket is always read from storage.
    Stop when `nextCursor` is null, not when a page is short. A cursor works only with the filters
    it came from; with others it is 400 `invalid_cursor`.

    Hidden files aren't listed or counted, as the app hides them: `.part` files, generated
    `result-*.zip` archives at the root, zips inside folders, and the top-level `msas-*` and
    `.git*` folders. You can still read or delete one by its exact path. Private export caches
    answer 404 and nothing inside one is listed. Where the app lists it, the `_extract_features`
    folder that holds them is listed by name (website#7801, not merged yet).

    Args:
        folder (str | Unset):
        recursive (bool | Unset):  Default: False.
        extension (list[str] | Unset):
        type_ (ListFilesType | Unset):
        search (str | Unset):
        limit (int | Unset):  Default: 50.
        cursor (str | Unset):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[FileEntryPage | Problem]
    """

    kwargs = _get_kwargs(
        folder=folder,
        recursive=recursive,
        extension=extension,
        type_=type_,
        search=search,
        limit=limit,
        cursor=cursor,
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
    recursive: bool | Unset = False,
    extension: list[str] | Unset = UNSET,
    type_: ListFilesType | Unset = UNSET,
    search: str | Unset = UNSET,
    limit: int | Unset = 50,
    cursor: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> FileEntryPage | Problem | None:
    """List workspace files and folders

     Every filter is applied by the server. Each item's `type` is `file` or `folder`. Paths are
    literal and relative to your workspace; job output folders are folders like any other.

    Below the root, the listing reads storage directly, so it is current the moment an upload or
    delete finishes, in path order. Each page reads at most 5,000 stored keys, so a sparse filter
    or a pile of archives can end a page short, or even empty, with a `nextCursor`. The root, listed
    without `recursive`, comes from the file catalog instead: your uploads newest first, then your
    top-level folders by name, reading at most 5,000 catalog rows a page. It follows storage by a
    few seconds. An organization that keeps files in its own bucket is always read from storage.
    Stop when `nextCursor` is null, not when a page is short. A cursor works only with the filters
    it came from; with others it is 400 `invalid_cursor`.

    Hidden files aren't listed or counted, as the app hides them: `.part` files, generated
    `result-*.zip` archives at the root, zips inside folders, and the top-level `msas-*` and
    `.git*` folders. You can still read or delete one by its exact path. Private export caches
    answer 404 and nothing inside one is listed. Where the app lists it, the `_extract_features`
    folder that holds them is listed by name (website#7801, not merged yet).

    Args:
        folder (str | Unset):
        recursive (bool | Unset):  Default: False.
        extension (list[str] | Unset):
        type_ (ListFilesType | Unset):
        search (str | Unset):
        limit (int | Unset):  Default: 50.
        cursor (str | Unset):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        FileEntryPage | Problem
    """

    return sync_detailed(
        client=client,
        folder=folder,
        recursive=recursive,
        extension=extension,
        type_=type_,
        search=search,
        limit=limit,
        cursor=cursor,
        tamarind_version=tamarind_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    folder: str | Unset = UNSET,
    recursive: bool | Unset = False,
    extension: list[str] | Unset = UNSET,
    type_: ListFilesType | Unset = UNSET,
    search: str | Unset = UNSET,
    limit: int | Unset = 50,
    cursor: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Response[FileEntryPage | Problem]:
    """List workspace files and folders

     Every filter is applied by the server. Each item's `type` is `file` or `folder`. Paths are
    literal and relative to your workspace; job output folders are folders like any other.

    Below the root, the listing reads storage directly, so it is current the moment an upload or
    delete finishes, in path order. Each page reads at most 5,000 stored keys, so a sparse filter
    or a pile of archives can end a page short, or even empty, with a `nextCursor`. The root, listed
    without `recursive`, comes from the file catalog instead: your uploads newest first, then your
    top-level folders by name, reading at most 5,000 catalog rows a page. It follows storage by a
    few seconds. An organization that keeps files in its own bucket is always read from storage.
    Stop when `nextCursor` is null, not when a page is short. A cursor works only with the filters
    it came from; with others it is 400 `invalid_cursor`.

    Hidden files aren't listed or counted, as the app hides them: `.part` files, generated
    `result-*.zip` archives at the root, zips inside folders, and the top-level `msas-*` and
    `.git*` folders. You can still read or delete one by its exact path. Private export caches
    answer 404 and nothing inside one is listed. Where the app lists it, the `_extract_features`
    folder that holds them is listed by name (website#7801, not merged yet).

    Args:
        folder (str | Unset):
        recursive (bool | Unset):  Default: False.
        extension (list[str] | Unset):
        type_ (ListFilesType | Unset):
        search (str | Unset):
        limit (int | Unset):  Default: 50.
        cursor (str | Unset):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[FileEntryPage | Problem]
    """

    kwargs = _get_kwargs(
        folder=folder,
        recursive=recursive,
        extension=extension,
        type_=type_,
        search=search,
        limit=limit,
        cursor=cursor,
        tamarind_version=tamarind_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    folder: str | Unset = UNSET,
    recursive: bool | Unset = False,
    extension: list[str] | Unset = UNSET,
    type_: ListFilesType | Unset = UNSET,
    search: str | Unset = UNSET,
    limit: int | Unset = 50,
    cursor: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> FileEntryPage | Problem | None:
    """List workspace files and folders

     Every filter is applied by the server. Each item's `type` is `file` or `folder`. Paths are
    literal and relative to your workspace; job output folders are folders like any other.

    Below the root, the listing reads storage directly, so it is current the moment an upload or
    delete finishes, in path order. Each page reads at most 5,000 stored keys, so a sparse filter
    or a pile of archives can end a page short, or even empty, with a `nextCursor`. The root, listed
    without `recursive`, comes from the file catalog instead: your uploads newest first, then your
    top-level folders by name, reading at most 5,000 catalog rows a page. It follows storage by a
    few seconds. An organization that keeps files in its own bucket is always read from storage.
    Stop when `nextCursor` is null, not when a page is short. A cursor works only with the filters
    it came from; with others it is 400 `invalid_cursor`.

    Hidden files aren't listed or counted, as the app hides them: `.part` files, generated
    `result-*.zip` archives at the root, zips inside folders, and the top-level `msas-*` and
    `.git*` folders. You can still read or delete one by its exact path. Private export caches
    answer 404 and nothing inside one is listed. Where the app lists it, the `_extract_features`
    folder that holds them is listed by name (website#7801, not merged yet).

    Args:
        folder (str | Unset):
        recursive (bool | Unset):  Default: False.
        extension (list[str] | Unset):
        type_ (ListFilesType | Unset):
        search (str | Unset):
        limit (int | Unset):  Default: 50.
        cursor (str | Unset):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        FileEntryPage | Problem
    """

    return (
        await asyncio_detailed(
            client=client,
            folder=folder,
            recursive=recursive,
            extension=extension,
            type_=type_,
            search=search,
            limit=limit,
            cursor=cursor,
            tamarind_version=tamarind_version,
        )
    ).parsed
