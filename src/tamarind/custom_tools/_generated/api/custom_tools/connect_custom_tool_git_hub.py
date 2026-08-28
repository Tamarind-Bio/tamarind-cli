from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.public_connect_git_hub_request import PublicConnectGitHubRequest
from ...models.public_git_hub_connection import PublicGitHubConnection
from ...models.public_problem import PublicProblem
from ...types import Response


def _get_kwargs(
    name: str,
    *,
    body: PublicConnectGitHubRequest,
    if_match: str,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["If-Match"] = if_match

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/custom-tools/{name}/github".format(
            name=quote(str(name), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> PublicGitHubConnection | PublicProblem:
    if response.status_code == 202:
        response_202 = PublicGitHubConnection.from_dict(response.json())

        return response_202

    if response.status_code == 401:
        response_401 = PublicProblem.from_dict(response.json())

        return response_401

    if response.status_code == 403:
        response_403 = PublicProblem.from_dict(response.json())

        return response_403

    if response.status_code == 404:
        response_404 = PublicProblem.from_dict(response.json())

        return response_404

    if response.status_code == 412:
        response_412 = PublicProblem.from_dict(response.json())

        return response_412

    if response.status_code == 422:
        response_422 = PublicProblem.from_dict(response.json())

        return response_422

    if response.status_code == 428:
        response_428 = PublicProblem.from_dict(response.json())

        return response_428

    response_default = PublicProblem.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[PublicGitHubConnection | PublicProblem]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    name: str,
    *,
    client: AuthenticatedClient | Client,
    body: PublicConnectGitHubRequest,
    if_match: str,
) -> Response[PublicGitHubConnection | PublicProblem]:
    """Connect a custom tool to GitHub

     Connect a GitHub repository, returning a resumable authorization action when consent is needed.

    Args:
        name (str): The custom tool name.
        if_match (str):
        body (PublicConnectGitHubRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PublicGitHubConnection | PublicProblem]
    """

    kwargs = _get_kwargs(
        name=name,
        body=body,
        if_match=if_match,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    name: str,
    *,
    client: AuthenticatedClient | Client,
    body: PublicConnectGitHubRequest,
    if_match: str,
) -> PublicGitHubConnection | PublicProblem | None:
    """Connect a custom tool to GitHub

     Connect a GitHub repository, returning a resumable authorization action when consent is needed.

    Args:
        name (str): The custom tool name.
        if_match (str):
        body (PublicConnectGitHubRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PublicGitHubConnection | PublicProblem
    """

    return sync_detailed(
        name=name,
        client=client,
        body=body,
        if_match=if_match,
    ).parsed


async def asyncio_detailed(
    name: str,
    *,
    client: AuthenticatedClient | Client,
    body: PublicConnectGitHubRequest,
    if_match: str,
) -> Response[PublicGitHubConnection | PublicProblem]:
    """Connect a custom tool to GitHub

     Connect a GitHub repository, returning a resumable authorization action when consent is needed.

    Args:
        name (str): The custom tool name.
        if_match (str):
        body (PublicConnectGitHubRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PublicGitHubConnection | PublicProblem]
    """

    kwargs = _get_kwargs(
        name=name,
        body=body,
        if_match=if_match,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    name: str,
    *,
    client: AuthenticatedClient | Client,
    body: PublicConnectGitHubRequest,
    if_match: str,
) -> PublicGitHubConnection | PublicProblem | None:
    """Connect a custom tool to GitHub

     Connect a GitHub repository, returning a resumable authorization action when consent is needed.

    Args:
        name (str): The custom tool name.
        if_match (str):
        body (PublicConnectGitHubRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PublicGitHubConnection | PublicProblem
    """

    return (
        await asyncio_detailed(
            name=name,
            client=client,
            body=body,
            if_match=if_match,
        )
    ).parsed
