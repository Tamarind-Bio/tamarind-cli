from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.public_problem import PublicProblem
from ...models.public_upload_session import PublicUploadSession
from ...types import Response


def _get_kwargs(
    name: str,
    *,
    x_tamarind_tool_generation: str,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["X-Tamarind-Tool-Generation"] = x_tamarind_tool_generation

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/custom-tools/{name}/uploads".format(
            name=quote(str(name), safe=""),
        ),
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> PublicProblem | PublicUploadSession:
    if response.status_code == 201:
        response_201 = PublicUploadSession.from_dict(response.json())

        return response_201

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
) -> Response[PublicProblem | PublicUploadSession]:
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
    x_tamarind_tool_generation: str,
) -> Response[PublicProblem | PublicUploadSession]:
    """Create a source upload

     Create a temporary upload for a source archive.

    Upload the file to `uploadUrl` using `uploadMethod` and every value in `uploadHeaders`, then use
    `uploadId` to build a version.

    Args:
        name (str): The custom tool name.
        x_tamarind_tool_generation (str): The immutable generation returned as `generation` by the
            Tool resource. It prevents a stale request from acting on a deleted and recreated Tool
            with the same name.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PublicProblem | PublicUploadSession]
    """

    kwargs = _get_kwargs(
        name=name,
        x_tamarind_tool_generation=x_tamarind_tool_generation,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    name: str,
    *,
    client: AuthenticatedClient | Client,
    x_tamarind_tool_generation: str,
) -> PublicProblem | PublicUploadSession | None:
    """Create a source upload

     Create a temporary upload for a source archive.

    Upload the file to `uploadUrl` using `uploadMethod` and every value in `uploadHeaders`, then use
    `uploadId` to build a version.

    Args:
        name (str): The custom tool name.
        x_tamarind_tool_generation (str): The immutable generation returned as `generation` by the
            Tool resource. It prevents a stale request from acting on a deleted and recreated Tool
            with the same name.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PublicProblem | PublicUploadSession
    """

    return sync_detailed(
        name=name,
        client=client,
        x_tamarind_tool_generation=x_tamarind_tool_generation,
    ).parsed


async def asyncio_detailed(
    name: str,
    *,
    client: AuthenticatedClient | Client,
    x_tamarind_tool_generation: str,
) -> Response[PublicProblem | PublicUploadSession]:
    """Create a source upload

     Create a temporary upload for a source archive.

    Upload the file to `uploadUrl` using `uploadMethod` and every value in `uploadHeaders`, then use
    `uploadId` to build a version.

    Args:
        name (str): The custom tool name.
        x_tamarind_tool_generation (str): The immutable generation returned as `generation` by the
            Tool resource. It prevents a stale request from acting on a deleted and recreated Tool
            with the same name.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PublicProblem | PublicUploadSession]
    """

    kwargs = _get_kwargs(
        name=name,
        x_tamarind_tool_generation=x_tamarind_tool_generation,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    name: str,
    *,
    client: AuthenticatedClient | Client,
    x_tamarind_tool_generation: str,
) -> PublicProblem | PublicUploadSession | None:
    """Create a source upload

     Create a temporary upload for a source archive.

    Upload the file to `uploadUrl` using `uploadMethod` and every value in `uploadHeaders`, then use
    `uploadId` to build a version.

    Args:
        name (str): The custom tool name.
        x_tamarind_tool_generation (str): The immutable generation returned as `generation` by the
            Tool resource. It prevents a stale request from acting on a deleted and recreated Tool
            with the same name.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PublicProblem | PublicUploadSession
    """

    return (
        await asyncio_detailed(
            name=name,
            client=client,
            x_tamarind_tool_generation=x_tamarind_tool_generation,
        )
    ).parsed
