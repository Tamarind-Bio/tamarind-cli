from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.contract import Contract
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
        "url": "/organization/contract",
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Contract | Problem:
    if response.status_code == 200:
        response_200 = Contract.from_dict(response.json())

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
) -> Response[Contract | Problem]:
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
) -> Response[Contract | Problem]:
    """Get contract terms and the compute balance

     Every contract term, with contracted, promotional, rollover, effective, used and remaining
    hours, newest start first. The same people who see shared budgets on `GET /me` can read it:
    the organization's service account, or any member when the organization shares its budget
    with members. Anyone else is 403 `forbidden`, and a personal account is 404.

    Args:
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Contract | Problem]
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
) -> Contract | Problem | None:
    """Get contract terms and the compute balance

     Every contract term, with contracted, promotional, rollover, effective, used and remaining
    hours, newest start first. The same people who see shared budgets on `GET /me` can read it:
    the organization's service account, or any member when the organization shares its budget
    with members. Anyone else is 403 `forbidden`, and a personal account is 404.

    Args:
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Contract | Problem
    """

    return sync_detailed(
        client=client,
        tamarind_version=tamarind_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    tamarind_version: str | Unset = UNSET,
) -> Response[Contract | Problem]:
    """Get contract terms and the compute balance

     Every contract term, with contracted, promotional, rollover, effective, used and remaining
    hours, newest start first. The same people who see shared budgets on `GET /me` can read it:
    the organization's service account, or any member when the organization shares its budget
    with members. Anyone else is 403 `forbidden`, and a personal account is 404.

    Args:
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Contract | Problem]
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
) -> Contract | Problem | None:
    """Get contract terms and the compute balance

     Every contract term, with contracted, promotional, rollover, effective, used and remaining
    hours, newest start first. The same people who see shared budgets on `GET /me` can read it:
    the organization's service account, or any member when the organization shares its budget
    with members. Anyone else is 403 `forbidden`, and a personal account is 404.

    Args:
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Contract | Problem
    """

    return (
        await asyncio_detailed(
            client=client,
            tamarind_version=tamarind_version,
        )
    ).parsed
