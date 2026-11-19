from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.organization import Organization
from ...models.problem import Problem
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    tamarind_version: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(tamarind_version, Unset):
        headers["Tamarind-Version"] = tamarind_version

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/organization",
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Organization | Problem:
    if response.status_code == 200:
        response_200 = Organization.from_dict(response.json())

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
) -> Response[Organization | Problem]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    tamarind_version: str | Unset = UNSET,
) -> Response[Organization | Problem]:
    """Get your organization

     Any member of an organization can read it. A personal account is 404. `name` is the organization's
    slug for now, as on `GET /me`. Every `/organization` route first confirms your membership against
    your account, read fresh; when it can't, the answer is 503 and retryable, never the old
    organization's data.

    Args:
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Organization | Problem]
    """

    kwargs = _get_kwargs(
        tamarind_version=tamarind_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    tamarind_version: str | Unset = UNSET,
) -> Organization | Problem | None:
    """Get your organization

     Any member of an organization can read it. A personal account is 404. `name` is the organization's
    slug for now, as on `GET /me`. Every `/organization` route first confirms your membership against
    your account, read fresh; when it can't, the answer is 503 and retryable, never the old
    organization's data.

    Args:
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Organization | Problem
    """

    return sync_detailed(
        client=client,
        tamarind_version=tamarind_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    tamarind_version: str | Unset = UNSET,
) -> Response[Organization | Problem]:
    """Get your organization

     Any member of an organization can read it. A personal account is 404. `name` is the organization's
    slug for now, as on `GET /me`. Every `/organization` route first confirms your membership against
    your account, read fresh; when it can't, the answer is 503 and retryable, never the old
    organization's data.

    Args:
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Organization | Problem]
    """

    kwargs = _get_kwargs(
        tamarind_version=tamarind_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    tamarind_version: str | Unset = UNSET,
) -> Organization | Problem | None:
    """Get your organization

     Any member of an organization can read it. A personal account is 404. `name` is the organization's
    slug for now, as on `GET /me`. Every `/organization` route first confirms your membership against
    your account, read fresh; when it can't, the answer is 503 and retryable, never the old
    organization's data.

    Args:
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Organization | Problem
    """

    return (
        await asyncio_detailed(
            client=client,
            tamarind_version=tamarind_version,
        )
    ).parsed
