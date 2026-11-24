from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.problem import Problem
from ...models.tool import Tool
from ...types import UNSET, Response, Unset


def _get_kwargs(
    tool: str,
    *,
    tamarind_version: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(tamarind_version, Unset):
        headers["Tamarind-Version"] = tamarind_version

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/tools/{tool}".format(
            tool=quote(str(tool), safe=""),
        ),
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Problem | Tool:
    if response.status_code == 200:
        response_200 = Tool.from_dict(response.json())

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
) -> Response[Problem | Tool]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    tool: str,
    *,
    client: AuthenticatedClient | Client,
    tamarind_version: str | Unset = UNSET,
) -> Response[Problem | Tool]:
    """Get a tool

     A built-in tool as `listTools` shows it to you, including one `listTools` leaves out only as today's
    list does (no display name of its own, or hidden from the app's tool pages). A tool hidden from you,
    or one your submit would be refused, answers exactly as an unknown name does, 404 `tool_not_found`,
    and so does a custom tool's name (`getToolSchema` takes one). The four Rosetta tools `listTools`
    lists without the Rosetta licence answer here too.

    Args:
        tool (str):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Problem | Tool]
    """

    kwargs = _get_kwargs(
        tool=tool,
        tamarind_version=tamarind_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    tool: str,
    *,
    client: AuthenticatedClient | Client,
    tamarind_version: str | Unset = UNSET,
) -> Problem | Tool | None:
    """Get a tool

     A built-in tool as `listTools` shows it to you, including one `listTools` leaves out only as today's
    list does (no display name of its own, or hidden from the app's tool pages). A tool hidden from you,
    or one your submit would be refused, answers exactly as an unknown name does, 404 `tool_not_found`,
    and so does a custom tool's name (`getToolSchema` takes one). The four Rosetta tools `listTools`
    lists without the Rosetta licence answer here too.

    Args:
        tool (str):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Problem | Tool
    """

    return sync_detailed(
        tool=tool,
        client=client,
        tamarind_version=tamarind_version,
    ).parsed


async def asyncio_detailed(
    tool: str,
    *,
    client: AuthenticatedClient | Client,
    tamarind_version: str | Unset = UNSET,
) -> Response[Problem | Tool]:
    """Get a tool

     A built-in tool as `listTools` shows it to you, including one `listTools` leaves out only as today's
    list does (no display name of its own, or hidden from the app's tool pages). A tool hidden from you,
    or one your submit would be refused, answers exactly as an unknown name does, 404 `tool_not_found`,
    and so does a custom tool's name (`getToolSchema` takes one). The four Rosetta tools `listTools`
    lists without the Rosetta licence answer here too.

    Args:
        tool (str):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Problem | Tool]
    """

    kwargs = _get_kwargs(
        tool=tool,
        tamarind_version=tamarind_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    tool: str,
    *,
    client: AuthenticatedClient | Client,
    tamarind_version: str | Unset = UNSET,
) -> Problem | Tool | None:
    """Get a tool

     A built-in tool as `listTools` shows it to you, including one `listTools` leaves out only as today's
    list does (no display name of its own, or hidden from the app's tool pages). A tool hidden from you,
    or one your submit would be refused, answers exactly as an unknown name does, 404 `tool_not_found`,
    and so does a custom tool's name (`getToolSchema` takes one). The four Rosetta tools `listTools`
    lists without the Rosetta licence answer here too.

    Args:
        tool (str):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Problem | Tool
    """

    return (
        await asyncio_detailed(
            tool=tool,
            client=client,
            tamarind_version=tamarind_version,
        )
    ).parsed
