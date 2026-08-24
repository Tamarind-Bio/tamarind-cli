from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.public_custom_tool import PublicCustomTool
from ...models.public_problem import PublicProblem
from ...models.public_update_custom_tool_request import PublicUpdateCustomToolRequest
from ...types import Response


def _get_kwargs(
    name: str,
    *,
    body: PublicUpdateCustomToolRequest,
    if_match: str,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["If-Match"] = if_match

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": "/custom-tools/{name}".format(
            name=quote(str(name), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> PublicCustomTool | PublicProblem:
    if response.status_code == 200:
        response_200 = PublicCustomTool.from_dict(response.json())

        return response_200

    if response.status_code == 401:
        response_401 = PublicProblem.from_dict(response.json())

        return response_401

    if response.status_code == 404:
        response_404 = PublicProblem.from_dict(response.json())

        return response_404

    if response.status_code == 412:
        response_412 = PublicProblem.from_dict(response.json())

        return response_412

    if response.status_code == 422:
        response_422 = PublicProblem.from_dict(response.json())

        return response_422

    response_default = PublicProblem.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[PublicCustomTool | PublicProblem]:
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
    body: PublicUpdateCustomToolRequest,
    if_match: str,
) -> Response[PublicCustomTool | PublicProblem]:
    """Update a custom tool

     Update a custom tool's metadata or compute resources.

    Fields you omit are left unchanged.

    Args:
        name (str): The custom tool name.
        if_match (str): The strong ETag returned by `GET /custom-tools/{name}`, including its
            double quotes.
        body (PublicUpdateCustomToolRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PublicCustomTool | PublicProblem]
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
    body: PublicUpdateCustomToolRequest,
    if_match: str,
) -> PublicCustomTool | PublicProblem | None:
    """Update a custom tool

     Update a custom tool's metadata or compute resources.

    Fields you omit are left unchanged.

    Args:
        name (str): The custom tool name.
        if_match (str): The strong ETag returned by `GET /custom-tools/{name}`, including its
            double quotes.
        body (PublicUpdateCustomToolRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PublicCustomTool | PublicProblem
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
    body: PublicUpdateCustomToolRequest,
    if_match: str,
) -> Response[PublicCustomTool | PublicProblem]:
    """Update a custom tool

     Update a custom tool's metadata or compute resources.

    Fields you omit are left unchanged.

    Args:
        name (str): The custom tool name.
        if_match (str): The strong ETag returned by `GET /custom-tools/{name}`, including its
            double quotes.
        body (PublicUpdateCustomToolRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PublicCustomTool | PublicProblem]
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
    body: PublicUpdateCustomToolRequest,
    if_match: str,
) -> PublicCustomTool | PublicProblem | None:
    """Update a custom tool

     Update a custom tool's metadata or compute resources.

    Fields you omit are left unchanged.

    Args:
        name (str): The custom tool name.
        if_match (str): The strong ETag returned by `GET /custom-tools/{name}`, including its
            double quotes.
        body (PublicUpdateCustomToolRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PublicCustomTool | PublicProblem
    """

    return (
        await asyncio_detailed(
            name=name,
            client=client,
            body=body,
            if_match=if_match,
        )
    ).parsed
