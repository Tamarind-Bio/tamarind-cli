from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.public_build_result import PublicBuildResult
from ...models.public_create_version_request import PublicCreateVersionRequest
from ...models.public_problem import PublicProblem
from ...types import Response


def _get_kwargs(
    name: str,
    *,
    body: PublicCreateVersionRequest,
    x_tamarind_tool_generation: str,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["X-Tamarind-Tool-Generation"] = x_tamarind_tool_generation

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/custom-tools/{name}/versions".format(
            name=quote(str(name), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> PublicBuildResult | PublicProblem:
    if response.status_code == 202:
        response_202 = PublicBuildResult.from_dict(response.json())

        return response_202

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
) -> Response[PublicBuildResult | PublicProblem]:
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
    body: PublicCreateVersionRequest,
    x_tamarind_tool_generation: str,
) -> Response[PublicBuildResult | PublicProblem]:
    """Build a custom tool version

     Build a version from an uploaded source archive.

    Returns immediately with the numbered version and its current status.

    Args:
        name (str): The custom tool name.
        x_tamarind_tool_generation (str): The immutable generation returned as `generation` by the
            Tool resource. It prevents a stale request from acting on a deleted and recreated Tool
            with the same name.
        body (PublicCreateVersionRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PublicBuildResult | PublicProblem]
    """

    kwargs = _get_kwargs(
        name=name,
        body=body,
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
    body: PublicCreateVersionRequest,
    x_tamarind_tool_generation: str,
) -> PublicBuildResult | PublicProblem | None:
    """Build a custom tool version

     Build a version from an uploaded source archive.

    Returns immediately with the numbered version and its current status.

    Args:
        name (str): The custom tool name.
        x_tamarind_tool_generation (str): The immutable generation returned as `generation` by the
            Tool resource. It prevents a stale request from acting on a deleted and recreated Tool
            with the same name.
        body (PublicCreateVersionRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PublicBuildResult | PublicProblem
    """

    return sync_detailed(
        name=name,
        client=client,
        body=body,
        x_tamarind_tool_generation=x_tamarind_tool_generation,
    ).parsed


async def asyncio_detailed(
    name: str,
    *,
    client: AuthenticatedClient | Client,
    body: PublicCreateVersionRequest,
    x_tamarind_tool_generation: str,
) -> Response[PublicBuildResult | PublicProblem]:
    """Build a custom tool version

     Build a version from an uploaded source archive.

    Returns immediately with the numbered version and its current status.

    Args:
        name (str): The custom tool name.
        x_tamarind_tool_generation (str): The immutable generation returned as `generation` by the
            Tool resource. It prevents a stale request from acting on a deleted and recreated Tool
            with the same name.
        body (PublicCreateVersionRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PublicBuildResult | PublicProblem]
    """

    kwargs = _get_kwargs(
        name=name,
        body=body,
        x_tamarind_tool_generation=x_tamarind_tool_generation,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    name: str,
    *,
    client: AuthenticatedClient | Client,
    body: PublicCreateVersionRequest,
    x_tamarind_tool_generation: str,
) -> PublicBuildResult | PublicProblem | None:
    """Build a custom tool version

     Build a version from an uploaded source archive.

    Returns immediately with the numbered version and its current status.

    Args:
        name (str): The custom tool name.
        x_tamarind_tool_generation (str): The immutable generation returned as `generation` by the
            Tool resource. It prevents a stale request from acting on a deleted and recreated Tool
            with the same name.
        body (PublicCreateVersionRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PublicBuildResult | PublicProblem
    """

    return (
        await asyncio_detailed(
            name=name,
            client=client,
            body=body,
            x_tamarind_tool_generation=x_tamarind_tool_generation,
        )
    ).parsed
