from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.list_assays_response_200 import ListAssaysResponse200
from ...models.list_assays_scope import ListAssaysScope
from ...models.list_assays_status import ListAssaysStatus
from ...models.problem import Problem
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    status: ListAssaysStatus | Unset = UNSET,
    scope: ListAssaysScope | Unset = ListAssaysScope.MINE,
    limit: int | Unset = 50,
    cursor: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(tamarind_version, Unset):
        headers["Tamarind-Version"] = tamarind_version

    params: dict[str, Any] = {}

    json_status: str | Unset = UNSET
    if not isinstance(status, Unset):
        json_status = status.value

    params["status"] = json_status

    json_scope: str | Unset = UNSET
    if not isinstance(scope, Unset):
        json_scope = scope.value

    params["scope"] = json_scope

    params["limit"] = limit

    params["cursor"] = cursor

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/assays",
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ListAssaysResponse200 | Problem:
    if response.status_code == 200:
        response_200 = ListAssaysResponse200.from_dict(response.json())

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
) -> Response[ListAssaysResponse200 | Problem]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    status: ListAssaysStatus | Unset = UNSET,
    scope: ListAssaysScope | Unset = ListAssaysScope.MINE,
    limit: int | Unset = 50,
    cursor: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Response[ListAssaysResponse200 | Problem]:
    """List your assay orders

     The orders you placed, newest first. Portal drafts and deleted orders are left out. The cursor
    is bound to `status`. Where assay orders aren't available on a deployment, this and the other
    order operations answer 503 `service_unavailable`.

    Args:
        status (ListAssaysStatus | Unset):
        scope (ListAssaysScope | Unset):  Default: ListAssaysScope.MINE.
        limit (int | Unset):  Default: 50.
        cursor (str | Unset):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ListAssaysResponse200 | Problem]
    """

    kwargs = _get_kwargs(
        status=status,
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
    status: ListAssaysStatus | Unset = UNSET,
    scope: ListAssaysScope | Unset = ListAssaysScope.MINE,
    limit: int | Unset = 50,
    cursor: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> ListAssaysResponse200 | Problem | None:
    """List your assay orders

     The orders you placed, newest first. Portal drafts and deleted orders are left out. The cursor
    is bound to `status`. Where assay orders aren't available on a deployment, this and the other
    order operations answer 503 `service_unavailable`.

    Args:
        status (ListAssaysStatus | Unset):
        scope (ListAssaysScope | Unset):  Default: ListAssaysScope.MINE.
        limit (int | Unset):  Default: 50.
        cursor (str | Unset):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ListAssaysResponse200 | Problem
    """

    return sync_detailed(
        client=client,
        status=status,
        scope=scope,
        limit=limit,
        cursor=cursor,
        tamarind_version=tamarind_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    status: ListAssaysStatus | Unset = UNSET,
    scope: ListAssaysScope | Unset = ListAssaysScope.MINE,
    limit: int | Unset = 50,
    cursor: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Response[ListAssaysResponse200 | Problem]:
    """List your assay orders

     The orders you placed, newest first. Portal drafts and deleted orders are left out. The cursor
    is bound to `status`. Where assay orders aren't available on a deployment, this and the other
    order operations answer 503 `service_unavailable`.

    Args:
        status (ListAssaysStatus | Unset):
        scope (ListAssaysScope | Unset):  Default: ListAssaysScope.MINE.
        limit (int | Unset):  Default: 50.
        cursor (str | Unset):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ListAssaysResponse200 | Problem]
    """

    kwargs = _get_kwargs(
        status=status,
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
    status: ListAssaysStatus | Unset = UNSET,
    scope: ListAssaysScope | Unset = ListAssaysScope.MINE,
    limit: int | Unset = 50,
    cursor: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> ListAssaysResponse200 | Problem | None:
    """List your assay orders

     The orders you placed, newest first. Portal drafts and deleted orders are left out. The cursor
    is bound to `status`. Where assay orders aren't available on a deployment, this and the other
    order operations answer 503 `service_unavailable`.

    Args:
        status (ListAssaysStatus | Unset):
        scope (ListAssaysScope | Unset):  Default: ListAssaysScope.MINE.
        limit (int | Unset):  Default: 50.
        cursor (str | Unset):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ListAssaysResponse200 | Problem
    """

    return (
        await asyncio_detailed(
            client=client,
            status=status,
            scope=scope,
            limit=limit,
            cursor=cursor,
            tamarind_version=tamarind_version,
        )
    ).parsed
