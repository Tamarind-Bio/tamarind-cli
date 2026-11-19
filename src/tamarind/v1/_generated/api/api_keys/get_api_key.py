from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.api_key import ApiKey
from ...models.problem import Problem
from ...types import UNSET, Response, Unset


def _get_kwargs(
    key_id: str,
    *,
    tamarind_version: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(tamarind_version, Unset):
        headers["Tamarind-Version"] = tamarind_version

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api-keys/{key_id}".format(
            key_id=quote(str(key_id), safe=""),
        ),
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ApiKey | Problem:
    if response.status_code == 200:
        response_200 = ApiKey.from_dict(response.json())

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
) -> Response[ApiKey | Problem]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    key_id: str,
    *,
    client: AuthenticatedClient | Client,
    tamarind_version: str | Unset = UNSET,
) -> Response[ApiKey | Problem]:
    """Get an API key

     One of your own keys or, for an organization admin, one of your organization's service accounts'
    keys. A member's key is 404 here, even to an admin, who sees it only in `scope=org`.

    Args:
        key_id (str):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiKey | Problem]
    """

    kwargs = _get_kwargs(
        key_id=key_id,
        tamarind_version=tamarind_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    key_id: str,
    *,
    client: AuthenticatedClient | Client,
    tamarind_version: str | Unset = UNSET,
) -> ApiKey | Problem | None:
    """Get an API key

     One of your own keys or, for an organization admin, one of your organization's service accounts'
    keys. A member's key is 404 here, even to an admin, who sees it only in `scope=org`.

    Args:
        key_id (str):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiKey | Problem
    """

    return sync_detailed(
        key_id=key_id,
        client=client,
        tamarind_version=tamarind_version,
    ).parsed


async def asyncio_detailed(
    key_id: str,
    *,
    client: AuthenticatedClient | Client,
    tamarind_version: str | Unset = UNSET,
) -> Response[ApiKey | Problem]:
    """Get an API key

     One of your own keys or, for an organization admin, one of your organization's service accounts'
    keys. A member's key is 404 here, even to an admin, who sees it only in `scope=org`.

    Args:
        key_id (str):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiKey | Problem]
    """

    kwargs = _get_kwargs(
        key_id=key_id,
        tamarind_version=tamarind_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    key_id: str,
    *,
    client: AuthenticatedClient | Client,
    tamarind_version: str | Unset = UNSET,
) -> ApiKey | Problem | None:
    """Get an API key

     One of your own keys or, for an organization admin, one of your organization's service accounts'
    keys. A member's key is 404 here, even to an admin, who sees it only in `scope=org`.

    Args:
        key_id (str):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiKey | Problem
    """

    return (
        await asyncio_detailed(
            key_id=key_id,
            client=client,
            tamarind_version=tamarind_version,
        )
    ).parsed
