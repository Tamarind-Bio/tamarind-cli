from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.public_custom_tool_page import PublicCustomToolPage
from ...models.public_custom_tool_status import PublicCustomToolStatus
from ...models.public_problem import PublicProblem
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    status: None | PublicCustomToolStatus | Unset = UNSET,
    published: bool | None | Unset = UNSET,
    limit: int | Unset = 50,
    cursor: None | str | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    json_status: None | str | Unset
    if isinstance(status, Unset):
        json_status = UNSET
    elif isinstance(status, PublicCustomToolStatus):
        json_status = status.value
    else:
        json_status = status
    params["status"] = json_status

    json_published: bool | None | Unset
    if isinstance(published, Unset):
        json_published = UNSET
    else:
        json_published = published
    params["published"] = json_published

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
        "url": "/custom-tools",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> PublicCustomToolPage | PublicProblem:
    if response.status_code == 200:
        response_200 = PublicCustomToolPage.from_dict(response.json())

        return response_200

    if response.status_code == 401:
        response_401 = PublicProblem.from_dict(response.json())

        return response_401

    if response.status_code == 422:
        response_422 = PublicProblem.from_dict(response.json())

        return response_422

    response_default = PublicProblem.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[PublicCustomToolPage | PublicProblem]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    status: None | PublicCustomToolStatus | Unset = UNSET,
    published: bool | None | Unset = UNSET,
    limit: int | Unset = 50,
    cursor: None | str | Unset = UNSET,
) -> Response[PublicCustomToolPage | PublicProblem]:
    """List custom tools

     List custom tools in your organization.

    Filter by status or publication state. Paginated — follow `nextCursor` until it is null.

    Args:
        status (None | PublicCustomToolStatus | Unset): Filter by status.
        published (bool | None | Unset): Filter to published (`true`) or unpublished (`false`)
            tools.
        limit (int | Unset): Maximum number of tools to return in one page. Default: 50.
        cursor (None | str | Unset): Pagination token from the previous response's `nextCursor`.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PublicCustomToolPage | PublicProblem]
    """

    kwargs = _get_kwargs(
        status=status,
        published=published,
        limit=limit,
        cursor=cursor,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    status: None | PublicCustomToolStatus | Unset = UNSET,
    published: bool | None | Unset = UNSET,
    limit: int | Unset = 50,
    cursor: None | str | Unset = UNSET,
) -> PublicCustomToolPage | PublicProblem | None:
    """List custom tools

     List custom tools in your organization.

    Filter by status or publication state. Paginated — follow `nextCursor` until it is null.

    Args:
        status (None | PublicCustomToolStatus | Unset): Filter by status.
        published (bool | None | Unset): Filter to published (`true`) or unpublished (`false`)
            tools.
        limit (int | Unset): Maximum number of tools to return in one page. Default: 50.
        cursor (None | str | Unset): Pagination token from the previous response's `nextCursor`.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PublicCustomToolPage | PublicProblem
    """

    return sync_detailed(
        client=client,
        status=status,
        published=published,
        limit=limit,
        cursor=cursor,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    status: None | PublicCustomToolStatus | Unset = UNSET,
    published: bool | None | Unset = UNSET,
    limit: int | Unset = 50,
    cursor: None | str | Unset = UNSET,
) -> Response[PublicCustomToolPage | PublicProblem]:
    """List custom tools

     List custom tools in your organization.

    Filter by status or publication state. Paginated — follow `nextCursor` until it is null.

    Args:
        status (None | PublicCustomToolStatus | Unset): Filter by status.
        published (bool | None | Unset): Filter to published (`true`) or unpublished (`false`)
            tools.
        limit (int | Unset): Maximum number of tools to return in one page. Default: 50.
        cursor (None | str | Unset): Pagination token from the previous response's `nextCursor`.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PublicCustomToolPage | PublicProblem]
    """

    kwargs = _get_kwargs(
        status=status,
        published=published,
        limit=limit,
        cursor=cursor,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    status: None | PublicCustomToolStatus | Unset = UNSET,
    published: bool | None | Unset = UNSET,
    limit: int | Unset = 50,
    cursor: None | str | Unset = UNSET,
) -> PublicCustomToolPage | PublicProblem | None:
    """List custom tools

     List custom tools in your organization.

    Filter by status or publication state. Paginated — follow `nextCursor` until it is null.

    Args:
        status (None | PublicCustomToolStatus | Unset): Filter by status.
        published (bool | None | Unset): Filter to published (`true`) or unpublished (`false`)
            tools.
        limit (int | Unset): Maximum number of tools to return in one page. Default: 50.
        cursor (None | str | Unset): Pagination token from the previous response's `nextCursor`.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PublicCustomToolPage | PublicProblem
    """

    return (
        await asyncio_detailed(
            client=client,
            status=status,
            published=published,
            limit=limit,
            cursor=cursor,
        )
    ).parsed
