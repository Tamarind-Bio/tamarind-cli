from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.problem import Problem
from ...models.project_page import ProjectPage
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    include_counts: bool | Unset = False,
    limit: int | Unset = 50,
    cursor: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(tamarind_version, Unset):
        headers["Tamarind-Version"] = tamarind_version

    params: dict[str, Any] = {}

    params["includeCounts"] = include_counts

    params["limit"] = limit

    params["cursor"] = cursor

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/projects",
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Problem | ProjectPage:
    if response.status_code == 200:
        response_200 = ProjectPage.from_dict(response.json())

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
) -> Response[Problem | ProjectPage]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    include_counts: bool | Unset = False,
    limit: int | Unset = 50,
    cursor: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Response[Problem | ProjectPage]:
    """List projects

     Your organization's projects, your own personal ones, then projects shared with you, each
    group by name. When your organization hides members' data from each other, only the
    organization projects you created or were added to. A shared project counts only while its
    creator's sharing still allows it, and an organization project only while you are in that
    organization. Archived projects are left out. When your organization's settings can't be
    read the answer is 503; retry.

    Args:
        include_counts (bool | Unset):  Default: False.
        limit (int | Unset):  Default: 50.
        cursor (str | Unset):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Problem | ProjectPage]
    """

    kwargs = _get_kwargs(
        include_counts=include_counts,
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
    include_counts: bool | Unset = False,
    limit: int | Unset = 50,
    cursor: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Problem | ProjectPage | None:
    """List projects

     Your organization's projects, your own personal ones, then projects shared with you, each
    group by name. When your organization hides members' data from each other, only the
    organization projects you created or were added to. A shared project counts only while its
    creator's sharing still allows it, and an organization project only while you are in that
    organization. Archived projects are left out. When your organization's settings can't be
    read the answer is 503; retry.

    Args:
        include_counts (bool | Unset):  Default: False.
        limit (int | Unset):  Default: 50.
        cursor (str | Unset):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Problem | ProjectPage
    """

    return sync_detailed(
        client=client,
        include_counts=include_counts,
        limit=limit,
        cursor=cursor,
        tamarind_version=tamarind_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    include_counts: bool | Unset = False,
    limit: int | Unset = 50,
    cursor: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Response[Problem | ProjectPage]:
    """List projects

     Your organization's projects, your own personal ones, then projects shared with you, each
    group by name. When your organization hides members' data from each other, only the
    organization projects you created or were added to. A shared project counts only while its
    creator's sharing still allows it, and an organization project only while you are in that
    organization. Archived projects are left out. When your organization's settings can't be
    read the answer is 503; retry.

    Args:
        include_counts (bool | Unset):  Default: False.
        limit (int | Unset):  Default: 50.
        cursor (str | Unset):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Problem | ProjectPage]
    """

    kwargs = _get_kwargs(
        include_counts=include_counts,
        limit=limit,
        cursor=cursor,
        tamarind_version=tamarind_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    include_counts: bool | Unset = False,
    limit: int | Unset = 50,
    cursor: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Problem | ProjectPage | None:
    """List projects

     Your organization's projects, your own personal ones, then projects shared with you, each
    group by name. When your organization hides members' data from each other, only the
    organization projects you created or were added to. A shared project counts only while its
    creator's sharing still allows it, and an organization project only while you are in that
    organization. Archived projects are left out. When your organization's settings can't be
    read the answer is 503; retry.

    Args:
        include_counts (bool | Unset):  Default: False.
        limit (int | Unset):  Default: 50.
        cursor (str | Unset):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Problem | ProjectPage
    """

    return (
        await asyncio_detailed(
            client=client,
            include_counts=include_counts,
            limit=limit,
            cursor=cursor,
            tamarind_version=tamarind_version,
        )
    ).parsed
