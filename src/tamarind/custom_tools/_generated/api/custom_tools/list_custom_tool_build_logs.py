from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.public_build_log_page import PublicBuildLogPage
from ...models.public_problem import PublicProblem
from ...types import UNSET, Response, Unset


def _get_kwargs(
    name: str,
    version: str,
    *,
    cursor: None | str | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    json_cursor: None | str | Unset
    if isinstance(cursor, Unset):
        json_cursor = UNSET
    else:
        json_cursor = cursor
    params["cursor"] = json_cursor

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/custom-tools/{name}/versions/{version}/logs".format(
            name=quote(str(name), safe=""),
            version=quote(str(version), safe=""),
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> PublicBuildLogPage | PublicProblem:
    if response.status_code == 200:
        response_200 = PublicBuildLogPage.from_dict(response.json())

        return response_200

    if response.status_code == 401:
        response_401 = PublicProblem.from_dict(response.json())

        return response_401

    if response.status_code == 404:
        response_404 = PublicProblem.from_dict(response.json())

        return response_404

    if response.status_code == 422:
        response_422 = PublicProblem.from_dict(response.json())

        return response_422

    response_default = PublicProblem.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[PublicBuildLogPage | PublicProblem]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    name: str,
    version: str,
    *,
    client: AuthenticatedClient | Client,
    cursor: None | str | Unset = UNSET,
) -> Response[PublicBuildLogPage | PublicProblem]:
    """List build logs

     List build log events for a version.

    Paginated — follow `nextCursor` until it is null.

    Args:
        name (str): The custom tool name.
        version (str): The opaque Version `id` returned in a Version representation. Numbered
            names such as `v3` remain accepted for migration compatibility.
        cursor (None | str | Unset): Pagination token from the previous response's `nextCursor`.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PublicBuildLogPage | PublicProblem]
    """

    kwargs = _get_kwargs(
        name=name,
        version=version,
        cursor=cursor,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    name: str,
    version: str,
    *,
    client: AuthenticatedClient | Client,
    cursor: None | str | Unset = UNSET,
) -> PublicBuildLogPage | PublicProblem | None:
    """List build logs

     List build log events for a version.

    Paginated — follow `nextCursor` until it is null.

    Args:
        name (str): The custom tool name.
        version (str): The opaque Version `id` returned in a Version representation. Numbered
            names such as `v3` remain accepted for migration compatibility.
        cursor (None | str | Unset): Pagination token from the previous response's `nextCursor`.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PublicBuildLogPage | PublicProblem
    """

    return sync_detailed(
        name=name,
        version=version,
        client=client,
        cursor=cursor,
    ).parsed


async def asyncio_detailed(
    name: str,
    version: str,
    *,
    client: AuthenticatedClient | Client,
    cursor: None | str | Unset = UNSET,
) -> Response[PublicBuildLogPage | PublicProblem]:
    """List build logs

     List build log events for a version.

    Paginated — follow `nextCursor` until it is null.

    Args:
        name (str): The custom tool name.
        version (str): The opaque Version `id` returned in a Version representation. Numbered
            names such as `v3` remain accepted for migration compatibility.
        cursor (None | str | Unset): Pagination token from the previous response's `nextCursor`.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PublicBuildLogPage | PublicProblem]
    """

    kwargs = _get_kwargs(
        name=name,
        version=version,
        cursor=cursor,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    name: str,
    version: str,
    *,
    client: AuthenticatedClient | Client,
    cursor: None | str | Unset = UNSET,
) -> PublicBuildLogPage | PublicProblem | None:
    """List build logs

     List build log events for a version.

    Paginated — follow `nextCursor` until it is null.

    Args:
        name (str): The custom tool name.
        version (str): The opaque Version `id` returned in a Version representation. Numbered
            names such as `v3` remain accepted for migration compatibility.
        cursor (None | str | Unset): Pagination token from the previous response's `nextCursor`.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PublicBuildLogPage | PublicProblem
    """

    return (
        await asyncio_detailed(
            name=name,
            version=version,
            client=client,
            cursor=cursor,
        )
    ).parsed
