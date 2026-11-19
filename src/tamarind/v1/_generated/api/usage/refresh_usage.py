from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.problem import Problem
from ...models.refresh_usage_body import RefreshUsageBody
from ...models.refresh_usage_response_202 import RefreshUsageResponse202
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    body: RefreshUsageBody,
    tamarind_version: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(tamarind_version, Unset):
        headers["Tamarind-Version"] = tamarind_version

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/usage/refresh",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Problem | RefreshUsageResponse202:
    if response.status_code == 202:
        response_202 = RefreshUsageResponse202.from_dict(response.json())

        return response_202

    if response.status_code == 400:
        response_400 = Problem.from_dict(response.json())

        return response_400

    if response.status_code == 401:
        response_401 = Problem.from_dict(response.json())

        return response_401

    if response.status_code == 403:
        response_403 = Problem.from_dict(response.json())

        return response_403

    if response.status_code == 422:
        response_422 = Problem.from_dict(response.json())

        return response_422

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
) -> Response[Problem | RefreshUsageResponse202]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: RefreshUsageBody,
    tamarind_version: str | Unset = UNSET,
) -> Response[Problem | RefreshUsageResponse202]:
    """Request a fresh usage calculation

     Starts the usage refresh once for each named person, as the portal's refresh button does, then
    answers 202. Poll `getUsage` and watch `asOf`. You can name yourself; you can name another
    member when your organization shares within itself or you are its service account. Anyone else
    (another organization, a different spelling of an address) is 403 `forbidden`, naming them,
    before anything starts. Addresses are matched exactly. Another refresh from the same account
    still running is 429. A start that fails is 503 and retryable, since a refresh is safe to
    repeat. A deployment without the refresh function answers 503, not retryable.

    Args:
        tamarind_version (str | Unset):
        body (RefreshUsageBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Problem | RefreshUsageResponse202]
    """

    kwargs = _get_kwargs(
        body=body,
        tamarind_version=tamarind_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    body: RefreshUsageBody,
    tamarind_version: str | Unset = UNSET,
) -> Problem | RefreshUsageResponse202 | None:
    """Request a fresh usage calculation

     Starts the usage refresh once for each named person, as the portal's refresh button does, then
    answers 202. Poll `getUsage` and watch `asOf`. You can name yourself; you can name another
    member when your organization shares within itself or you are its service account. Anyone else
    (another organization, a different spelling of an address) is 403 `forbidden`, naming them,
    before anything starts. Addresses are matched exactly. Another refresh from the same account
    still running is 429. A start that fails is 503 and retryable, since a refresh is safe to
    repeat. A deployment without the refresh function answers 503, not retryable.

    Args:
        tamarind_version (str | Unset):
        body (RefreshUsageBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Problem | RefreshUsageResponse202
    """

    return sync_detailed(
        client=client,
        body=body,
        tamarind_version=tamarind_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: RefreshUsageBody,
    tamarind_version: str | Unset = UNSET,
) -> Response[Problem | RefreshUsageResponse202]:
    """Request a fresh usage calculation

     Starts the usage refresh once for each named person, as the portal's refresh button does, then
    answers 202. Poll `getUsage` and watch `asOf`. You can name yourself; you can name another
    member when your organization shares within itself or you are its service account. Anyone else
    (another organization, a different spelling of an address) is 403 `forbidden`, naming them,
    before anything starts. Addresses are matched exactly. Another refresh from the same account
    still running is 429. A start that fails is 503 and retryable, since a refresh is safe to
    repeat. A deployment without the refresh function answers 503, not retryable.

    Args:
        tamarind_version (str | Unset):
        body (RefreshUsageBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Problem | RefreshUsageResponse202]
    """

    kwargs = _get_kwargs(
        body=body,
        tamarind_version=tamarind_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: RefreshUsageBody,
    tamarind_version: str | Unset = UNSET,
) -> Problem | RefreshUsageResponse202 | None:
    """Request a fresh usage calculation

     Starts the usage refresh once for each named person, as the portal's refresh button does, then
    answers 202. Poll `getUsage` and watch `asOf`. You can name yourself; you can name another
    member when your organization shares within itself or you are its service account. Anyone else
    (another organization, a different spelling of an address) is 403 `forbidden`, naming them,
    before anything starts. Addresses are matched exactly. Another refresh from the same account
    still running is 429. A start that fails is 503 and retryable, since a refresh is safe to
    repeat. A deployment without the refresh function answers 503, not retryable.

    Args:
        tamarind_version (str | Unset):
        body (RefreshUsageBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Problem | RefreshUsageResponse202
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            tamarind_version=tamarind_version,
        )
    ).parsed
