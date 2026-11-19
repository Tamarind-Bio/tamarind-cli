from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.create_service_account_body import CreateServiceAccountBody
from ...models.problem import Problem
from ...models.service_account import ServiceAccount
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    body: CreateServiceAccountBody,
    tamarind_version: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(tamarind_version, Unset):
        headers["Tamarind-Version"] = tamarind_version

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/service-accounts",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Problem | ServiceAccount:
    if response.status_code == 201:
        response_201 = ServiceAccount.from_dict(response.json())

        return response_201

    if response.status_code == 400:
        response_400 = Problem.from_dict(response.json())

        return response_400

    if response.status_code == 401:
        response_401 = Problem.from_dict(response.json())

        return response_401

    if response.status_code == 403:
        response_403 = Problem.from_dict(response.json())

        return response_403

    if response.status_code == 409:
        response_409 = Problem.from_dict(response.json())

        return response_409

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
) -> Response[Problem | ServiceAccount]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateServiceAccountBody,
    tamarind_version: str | Unset = UNSET,
) -> Response[Problem | ServiceAccount]:
    """Create a service account

     Create its keys with `POST /api-keys` and `serviceAccountId`. Organization admins only, with their
    own key. The account starts with no key. Its `email` is the name, trimmed, lower-cased and with each
    run of spaces made one hyphen, at `<organization slug>.serviceaccount`. A name whose email is
    already taken (`Nightly Sync` and `nightly  sync` are the same) is 409 `service_account_exists`.

    Args:
        tamarind_version (str | Unset):
        body (CreateServiceAccountBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Problem | ServiceAccount]
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
    body: CreateServiceAccountBody,
    tamarind_version: str | Unset = UNSET,
) -> Problem | ServiceAccount | None:
    """Create a service account

     Create its keys with `POST /api-keys` and `serviceAccountId`. Organization admins only, with their
    own key. The account starts with no key. Its `email` is the name, trimmed, lower-cased and with each
    run of spaces made one hyphen, at `<organization slug>.serviceaccount`. A name whose email is
    already taken (`Nightly Sync` and `nightly  sync` are the same) is 409 `service_account_exists`.

    Args:
        tamarind_version (str | Unset):
        body (CreateServiceAccountBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Problem | ServiceAccount
    """

    return sync_detailed(
        client=client,
        body=body,
        tamarind_version=tamarind_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateServiceAccountBody,
    tamarind_version: str | Unset = UNSET,
) -> Response[Problem | ServiceAccount]:
    """Create a service account

     Create its keys with `POST /api-keys` and `serviceAccountId`. Organization admins only, with their
    own key. The account starts with no key. Its `email` is the name, trimmed, lower-cased and with each
    run of spaces made one hyphen, at `<organization slug>.serviceaccount`. A name whose email is
    already taken (`Nightly Sync` and `nightly  sync` are the same) is 409 `service_account_exists`.

    Args:
        tamarind_version (str | Unset):
        body (CreateServiceAccountBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Problem | ServiceAccount]
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
    body: CreateServiceAccountBody,
    tamarind_version: str | Unset = UNSET,
) -> Problem | ServiceAccount | None:
    """Create a service account

     Create its keys with `POST /api-keys` and `serviceAccountId`. Organization admins only, with their
    own key. The account starts with no key. Its `email` is the name, trimmed, lower-cased and with each
    run of spaces made one hyphen, at `<organization slug>.serviceaccount`. A name whose email is
    already taken (`Nightly Sync` and `nightly  sync` are the same) is 409 `service_account_exists`.

    Args:
        tamarind_version (str | Unset):
        body (CreateServiceAccountBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Problem | ServiceAccount
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            tamarind_version=tamarind_version,
        )
    ).parsed
