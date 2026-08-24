from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.public_problem import PublicProblem
from ...models.public_version_page import PublicVersionPage
from ...models.public_version_status import PublicVersionStatus
from ...types import UNSET, Response, Unset


def _get_kwargs(
    name: str,
    generation: str,
    *,
    status: None | PublicVersionStatus | Unset = UNSET,
    limit: int | Unset = 50,
    cursor: None | str | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    json_status: None | str | Unset
    if isinstance(status, Unset):
        json_status = UNSET
    elif isinstance(status, PublicVersionStatus):
        json_status = status.value
    else:
        json_status = status
    params["status"] = json_status

    params["limit"] = limit

    json_cursor: None | str | Unset
    if isinstance(cursor, Unset):
        json_cursor = UNSET
    else:
        json_cursor = cursor
    params["cursor"] = json_cursor

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/custom-tools/{name}/generations/{generation}/versions".format(
            name=quote(str(name), safe=""),
            generation=quote(str(generation), safe=""),
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> PublicProblem | PublicVersionPage:
    if response.status_code == 200:
        response_200 = PublicVersionPage.from_dict(response.json())

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
) -> Response[PublicProblem | PublicVersionPage]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    name: str,
    generation: str,
    *,
    client: AuthenticatedClient | Client,
    status: None | PublicVersionStatus | Unset = UNSET,
    limit: int | Unset = 50,
    cursor: None | str | Unset = UNSET,
) -> Response[PublicProblem | PublicVersionPage]:
    """List custom tool versions

     List versions of a custom tool.

    Filter by build status. Paginated — follow `nextCursor` until it is null.

    Args:
        name (str): The custom tool name.
        generation (str): The immutable Tool generation identifier.
        status (None | PublicVersionStatus | Unset): Filter by build status.
        limit (int | Unset): Maximum number of versions to return in one page. Default: 50.
        cursor (None | str | Unset): Pagination token from the previous response's `nextCursor`.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PublicProblem | PublicVersionPage]
    """

    kwargs = _get_kwargs(
        name=name,
        generation=generation,
        status=status,
        limit=limit,
        cursor=cursor,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    name: str,
    generation: str,
    *,
    client: AuthenticatedClient | Client,
    status: None | PublicVersionStatus | Unset = UNSET,
    limit: int | Unset = 50,
    cursor: None | str | Unset = UNSET,
) -> PublicProblem | PublicVersionPage | None:
    """List custom tool versions

     List versions of a custom tool.

    Filter by build status. Paginated — follow `nextCursor` until it is null.

    Args:
        name (str): The custom tool name.
        generation (str): The immutable Tool generation identifier.
        status (None | PublicVersionStatus | Unset): Filter by build status.
        limit (int | Unset): Maximum number of versions to return in one page. Default: 50.
        cursor (None | str | Unset): Pagination token from the previous response's `nextCursor`.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PublicProblem | PublicVersionPage
    """

    return sync_detailed(
        name=name,
        generation=generation,
        client=client,
        status=status,
        limit=limit,
        cursor=cursor,
    ).parsed


async def asyncio_detailed(
    name: str,
    generation: str,
    *,
    client: AuthenticatedClient | Client,
    status: None | PublicVersionStatus | Unset = UNSET,
    limit: int | Unset = 50,
    cursor: None | str | Unset = UNSET,
) -> Response[PublicProblem | PublicVersionPage]:
    """List custom tool versions

     List versions of a custom tool.

    Filter by build status. Paginated — follow `nextCursor` until it is null.

    Args:
        name (str): The custom tool name.
        generation (str): The immutable Tool generation identifier.
        status (None | PublicVersionStatus | Unset): Filter by build status.
        limit (int | Unset): Maximum number of versions to return in one page. Default: 50.
        cursor (None | str | Unset): Pagination token from the previous response's `nextCursor`.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PublicProblem | PublicVersionPage]
    """

    kwargs = _get_kwargs(
        name=name,
        generation=generation,
        status=status,
        limit=limit,
        cursor=cursor,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    name: str,
    generation: str,
    *,
    client: AuthenticatedClient | Client,
    status: None | PublicVersionStatus | Unset = UNSET,
    limit: int | Unset = 50,
    cursor: None | str | Unset = UNSET,
) -> PublicProblem | PublicVersionPage | None:
    """List custom tool versions

     List versions of a custom tool.

    Filter by build status. Paginated — follow `nextCursor` until it is null.

    Args:
        name (str): The custom tool name.
        generation (str): The immutable Tool generation identifier.
        status (None | PublicVersionStatus | Unset): Filter by build status.
        limit (int | Unset): Maximum number of versions to return in one page. Default: 50.
        cursor (None | str | Unset): Pagination token from the previous response's `nextCursor`.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PublicProblem | PublicVersionPage
    """

    return (
        await asyncio_detailed(
            name=name,
            generation=generation,
            client=client,
            status=status,
            limit=limit,
            cursor=cursor,
        )
    ).parsed
