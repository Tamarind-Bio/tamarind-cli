from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.public_custom_tool import PublicCustomTool
from ...models.public_problem import PublicProblem
from ...types import Response


def _get_kwargs(
    name: str,
    version: str,
    *,
    if_match: str,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["If-Match"] = if_match

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/custom-tools/{name}/versions/{version}:publish".format(
            name=quote(str(name), safe=""),
            version=quote(str(version), safe=""),
        ),
    }

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

    if response.status_code == 428:
        response_428 = PublicProblem.from_dict(response.json())

        return response_428

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
    version: str,
    *,
    client: AuthenticatedClient | Client,
    if_match: str,
) -> Response[PublicCustomTool | PublicProblem]:
    """Publish a custom tool version

     Make a completed version the tool's published runtime version.

    This also supports an explicit rollback to an older completed version.

    Args:
        name (str): The custom tool name.
        version (str): The opaque Version `id` returned in a Version representation.
        if_match (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PublicCustomTool | PublicProblem]
    """

    kwargs = _get_kwargs(
        name=name,
        version=version,
        if_match=if_match,
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
    if_match: str,
) -> PublicCustomTool | PublicProblem | None:
    """Publish a custom tool version

     Make a completed version the tool's published runtime version.

    This also supports an explicit rollback to an older completed version.

    Args:
        name (str): The custom tool name.
        version (str): The opaque Version `id` returned in a Version representation.
        if_match (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PublicCustomTool | PublicProblem
    """

    return sync_detailed(
        name=name,
        version=version,
        client=client,
        if_match=if_match,
    ).parsed


async def asyncio_detailed(
    name: str,
    version: str,
    *,
    client: AuthenticatedClient | Client,
    if_match: str,
) -> Response[PublicCustomTool | PublicProblem]:
    """Publish a custom tool version

     Make a completed version the tool's published runtime version.

    This also supports an explicit rollback to an older completed version.

    Args:
        name (str): The custom tool name.
        version (str): The opaque Version `id` returned in a Version representation.
        if_match (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PublicCustomTool | PublicProblem]
    """

    kwargs = _get_kwargs(
        name=name,
        version=version,
        if_match=if_match,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    name: str,
    version: str,
    *,
    client: AuthenticatedClient | Client,
    if_match: str,
) -> PublicCustomTool | PublicProblem | None:
    """Publish a custom tool version

     Make a completed version the tool's published runtime version.

    This also supports an explicit rollback to an older completed version.

    Args:
        name (str): The custom tool name.
        version (str): The opaque Version `id` returned in a Version representation.
        if_match (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PublicCustomTool | PublicProblem
    """

    return (
        await asyncio_detailed(
            name=name,
            version=version,
            client=client,
            if_match=if_match,
        )
    ).parsed
