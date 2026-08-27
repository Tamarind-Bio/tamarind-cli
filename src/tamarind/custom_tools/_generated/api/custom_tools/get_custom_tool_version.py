from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.public_problem import PublicProblem
from ...models.public_version import PublicVersion
from ...types import Response


def _get_kwargs(
    name: str,
    version: str,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/custom-tools/{name}/versions/{version}".format(
            name=quote(str(name), safe=""),
            version=quote(str(version), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> PublicProblem | PublicVersion:
    if response.status_code == 200:
        response_200 = PublicVersion.from_dict(response.json())

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
) -> Response[PublicProblem | PublicVersion]:
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
) -> Response[PublicProblem | PublicVersion]:
    """Get a custom tool version

     Get a version's source, build status, and error details.

    Args:
        name (str): The custom tool name.
        version (str): The opaque Version `id` returned in a Version representation. Numbered
            names remain accepted for previously generated v1 clients when paired with their
            generation header.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PublicProblem | PublicVersion]
    """

    kwargs = _get_kwargs(
        name=name,
        version=version,
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
) -> PublicProblem | PublicVersion | None:
    """Get a custom tool version

     Get a version's source, build status, and error details.

    Args:
        name (str): The custom tool name.
        version (str): The opaque Version `id` returned in a Version representation. Numbered
            names remain accepted for previously generated v1 clients when paired with their
            generation header.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PublicProblem | PublicVersion
    """

    return sync_detailed(
        name=name,
        version=version,
        client=client,
    ).parsed


async def asyncio_detailed(
    name: str,
    version: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[PublicProblem | PublicVersion]:
    """Get a custom tool version

     Get a version's source, build status, and error details.

    Args:
        name (str): The custom tool name.
        version (str): The opaque Version `id` returned in a Version representation. Numbered
            names remain accepted for previously generated v1 clients when paired with their
            generation header.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PublicProblem | PublicVersion]
    """

    kwargs = _get_kwargs(
        name=name,
        version=version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    name: str,
    version: str,
    *,
    client: AuthenticatedClient | Client,
) -> PublicProblem | PublicVersion | None:
    """Get a custom tool version

     Get a version's source, build status, and error details.

    Args:
        name (str): The custom tool name.
        version (str): The opaque Version `id` returned in a Version representation. Numbered
            names remain accepted for previously generated v1 clients when paired with their
            generation header.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PublicProblem | PublicVersion
    """

    return (
        await asyncio_detailed(
            name=name,
            version=version,
            client=client,
        )
    ).parsed
