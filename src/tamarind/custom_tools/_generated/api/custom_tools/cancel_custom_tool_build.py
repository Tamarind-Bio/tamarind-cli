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
    generation: str,
    version_name: str,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/custom-tools/{name}/generations/{generation}/versions/{version_name}/cancel".format(
            name=quote(str(name), safe=""),
            generation=quote(str(generation), safe=""),
            version_name=quote(str(version_name), safe=""),
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
    generation: str,
    version_name: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[PublicProblem | PublicVersion]:
    """Cancel a custom tool build

     Request cancellation of an active build.

    Completed and stopped builds cannot be canceled.

    Args:
        name (str): The custom tool name.
        generation (str): The immutable Tool generation identifier.
        version_name (str): A numbered version handle, such as `v3`.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PublicProblem | PublicVersion]
    """

    kwargs = _get_kwargs(
        name=name,
        generation=generation,
        version_name=version_name,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    name: str,
    generation: str,
    version_name: str,
    *,
    client: AuthenticatedClient | Client,
) -> PublicProblem | PublicVersion | None:
    """Cancel a custom tool build

     Request cancellation of an active build.

    Completed and stopped builds cannot be canceled.

    Args:
        name (str): The custom tool name.
        generation (str): The immutable Tool generation identifier.
        version_name (str): A numbered version handle, such as `v3`.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PublicProblem | PublicVersion
    """

    return sync_detailed(
        name=name,
        generation=generation,
        version_name=version_name,
        client=client,
    ).parsed


async def asyncio_detailed(
    name: str,
    generation: str,
    version_name: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[PublicProblem | PublicVersion]:
    """Cancel a custom tool build

     Request cancellation of an active build.

    Completed and stopped builds cannot be canceled.

    Args:
        name (str): The custom tool name.
        generation (str): The immutable Tool generation identifier.
        version_name (str): A numbered version handle, such as `v3`.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PublicProblem | PublicVersion]
    """

    kwargs = _get_kwargs(
        name=name,
        generation=generation,
        version_name=version_name,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    name: str,
    generation: str,
    version_name: str,
    *,
    client: AuthenticatedClient | Client,
) -> PublicProblem | PublicVersion | None:
    """Cancel a custom tool build

     Request cancellation of an active build.

    Completed and stopped builds cannot be canceled.

    Args:
        name (str): The custom tool name.
        generation (str): The immutable Tool generation identifier.
        version_name (str): A numbered version handle, such as `v3`.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PublicProblem | PublicVersion
    """

    return (
        await asyncio_detailed(
            name=name,
            generation=generation,
            version_name=version_name,
            client=client,
        )
    ).parsed
