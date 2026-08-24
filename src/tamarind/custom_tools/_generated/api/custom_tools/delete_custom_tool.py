from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.public_problem import PublicProblem
from ...types import Response


def _get_kwargs(
    name: str,
    *,
    if_match: str,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["If-Match"] = if_match

    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": "/custom-tools/{name}".format(
            name=quote(str(name), safe=""),
        ),
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Any | PublicProblem:
    if response.status_code == 204:
        response_204 = cast(Any, None)
        return response_204

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
) -> Response[Any | PublicProblem]:
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
    if_match: str,
) -> Response[Any | PublicProblem]:
    """Delete a custom tool

     Delete this generation and release its name for reuse.

    Args:
        name (str): The custom tool name.
        if_match (str): The strong ETag returned by `GET /custom-tools/{name}`, including its
            double quotes.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | PublicProblem]
    """

    kwargs = _get_kwargs(
        name=name,
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
    if_match: str,
) -> Any | PublicProblem | None:
    """Delete a custom tool

     Delete this generation and release its name for reuse.

    Args:
        name (str): The custom tool name.
        if_match (str): The strong ETag returned by `GET /custom-tools/{name}`, including its
            double quotes.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | PublicProblem
    """

    return sync_detailed(
        name=name,
        client=client,
        if_match=if_match,
    ).parsed


async def asyncio_detailed(
    name: str,
    *,
    client: AuthenticatedClient | Client,
    if_match: str,
) -> Response[Any | PublicProblem]:
    """Delete a custom tool

     Delete this generation and release its name for reuse.

    Args:
        name (str): The custom tool name.
        if_match (str): The strong ETag returned by `GET /custom-tools/{name}`, including its
            double quotes.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | PublicProblem]
    """

    kwargs = _get_kwargs(
        name=name,
        if_match=if_match,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    name: str,
    *,
    client: AuthenticatedClient | Client,
    if_match: str,
) -> Any | PublicProblem | None:
    """Delete a custom tool

     Delete this generation and release its name for reuse.

    Args:
        name (str): The custom tool name.
        if_match (str): The strong ETag returned by `GET /custom-tools/{name}`, including its
            double quotes.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | PublicProblem
    """

    return (
        await asyncio_detailed(
            name=name,
            client=client,
            if_match=if_match,
        )
    ).parsed
