from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.api_key_page import ApiKeyPage
from ...models.list_api_keys_scope import ListApiKeysScope
from ...models.problem import Problem
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    scope: ListApiKeysScope | Unset = ListApiKeysScope.MINE,
    limit: int | Unset = 50,
    cursor: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(tamarind_version, Unset):
        headers["Tamarind-Version"] = tamarind_version

    params: dict[str, Any] = {}

    json_scope: str | Unset = UNSET
    if not isinstance(scope, Unset):
        json_scope = scope.value

    params["scope"] = json_scope

    params["limit"] = limit

    params["cursor"] = cursor

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api-keys",
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ApiKeyPage | Problem:
    if response.status_code == 200:
        response_200 = ApiKeyPage.from_dict(response.json())

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
) -> Response[ApiKeyPage | Problem]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    scope: ListApiKeysScope | Unset = ListApiKeysScope.MINE,
    limit: int | Unset = 50,
    cursor: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Response[ApiKeyPage | Problem]:
    """List API keys

     Your own keys: the original one, the ones you created, and revoked ones. Never a short-lived
    key a Tamarind service made for you, and never a secret or a hash.

    With `scope=org`, an organization admin's own key lists every key of every member and service
    account in the organization, as metadata. It acts as admin only when a live check with the
    sign-in provider says you administer your organization, your account and the organization,
    read again, still say so, the organization doesn't force MFA and its access isn't disabled,
    and the key isn't a service account's. Otherwise it's 403 `org_admin_required`, or
    `mfa_required` when the organization forces MFA. An admin can see members' keys here but
    can't change them.

    Args:
        scope (ListApiKeysScope | Unset):  Default: ListApiKeysScope.MINE.
        limit (int | Unset):  Default: 50.
        cursor (str | Unset):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiKeyPage | Problem]
    """

    kwargs = _get_kwargs(
        scope=scope,
        limit=limit,
        cursor=cursor,
        tamarind_version=tamarind_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    scope: ListApiKeysScope | Unset = ListApiKeysScope.MINE,
    limit: int | Unset = 50,
    cursor: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> ApiKeyPage | Problem | None:
    """List API keys

     Your own keys: the original one, the ones you created, and revoked ones. Never a short-lived
    key a Tamarind service made for you, and never a secret or a hash.

    With `scope=org`, an organization admin's own key lists every key of every member and service
    account in the organization, as metadata. It acts as admin only when a live check with the
    sign-in provider says you administer your organization, your account and the organization,
    read again, still say so, the organization doesn't force MFA and its access isn't disabled,
    and the key isn't a service account's. Otherwise it's 403 `org_admin_required`, or
    `mfa_required` when the organization forces MFA. An admin can see members' keys here but
    can't change them.

    Args:
        scope (ListApiKeysScope | Unset):  Default: ListApiKeysScope.MINE.
        limit (int | Unset):  Default: 50.
        cursor (str | Unset):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiKeyPage | Problem
    """

    return sync_detailed(
        client=client,
        scope=scope,
        limit=limit,
        cursor=cursor,
        tamarind_version=tamarind_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    scope: ListApiKeysScope | Unset = ListApiKeysScope.MINE,
    limit: int | Unset = 50,
    cursor: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Response[ApiKeyPage | Problem]:
    """List API keys

     Your own keys: the original one, the ones you created, and revoked ones. Never a short-lived
    key a Tamarind service made for you, and never a secret or a hash.

    With `scope=org`, an organization admin's own key lists every key of every member and service
    account in the organization, as metadata. It acts as admin only when a live check with the
    sign-in provider says you administer your organization, your account and the organization,
    read again, still say so, the organization doesn't force MFA and its access isn't disabled,
    and the key isn't a service account's. Otherwise it's 403 `org_admin_required`, or
    `mfa_required` when the organization forces MFA. An admin can see members' keys here but
    can't change them.

    Args:
        scope (ListApiKeysScope | Unset):  Default: ListApiKeysScope.MINE.
        limit (int | Unset):  Default: 50.
        cursor (str | Unset):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiKeyPage | Problem]
    """

    kwargs = _get_kwargs(
        scope=scope,
        limit=limit,
        cursor=cursor,
        tamarind_version=tamarind_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    scope: ListApiKeysScope | Unset = ListApiKeysScope.MINE,
    limit: int | Unset = 50,
    cursor: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> ApiKeyPage | Problem | None:
    """List API keys

     Your own keys: the original one, the ones you created, and revoked ones. Never a short-lived
    key a Tamarind service made for you, and never a secret or a hash.

    With `scope=org`, an organization admin's own key lists every key of every member and service
    account in the organization, as metadata. It acts as admin only when a live check with the
    sign-in provider says you administer your organization, your account and the organization,
    read again, still say so, the organization doesn't force MFA and its access isn't disabled,
    and the key isn't a service account's. Otherwise it's 403 `org_admin_required`, or
    `mfa_required` when the organization forces MFA. An admin can see members' keys here but
    can't change them.

    Args:
        scope (ListApiKeysScope | Unset):  Default: ListApiKeysScope.MINE.
        limit (int | Unset):  Default: 50.
        cursor (str | Unset):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiKeyPage | Problem
    """

    return (
        await asyncio_detailed(
            client=client,
            scope=scope,
            limit=limit,
            cursor=cursor,
            tamarind_version=tamarind_version,
        )
    ).parsed
