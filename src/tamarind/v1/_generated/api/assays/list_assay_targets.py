from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.list_assay_targets_provider import ListAssayTargetsProvider
from ...models.list_assay_targets_response_200 import ListAssayTargetsResponse200
from ...models.problem import Problem
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    provider: ListAssayTargetsProvider,
    search: str | Unset = UNSET,
    limit: int | Unset = 50,
    cursor: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(tamarind_version, Unset):
        headers["Tamarind-Version"] = tamarind_version

    params: dict[str, Any] = {}

    json_provider = provider.value
    params["provider"] = json_provider

    params["search"] = search

    params["limit"] = limit

    params["cursor"] = cursor

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/assay-targets",
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ListAssayTargetsResponse200 | Problem:
    if response.status_code == 200:
        response_200 = ListAssayTargetsResponse200.from_dict(response.json())

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

    if response.status_code == 502:
        response_502 = Problem.from_dict(response.json())

        return response_502

    if response.status_code == 503:
        response_503 = Problem.from_dict(response.json())

        return response_503

    response_default = Problem.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ListAssayTargetsResponse200 | Problem]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    provider: ListAssayTargetsProvider,
    search: str | Unset = UNSET,
    limit: int | Unset = 50,
    cursor: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Response[ListAssayTargetsResponse200 | Problem]:
    """Search the targets a binding assay can measure against

     Needs Assay Portal access: without it, 403 `wetlab_access_required`. A lab the portal doesn't
    offer you (Ginkgo where it isn't enabled, say) is 400 `validation_failed`. A lab's target list
    that can't be read is 502 `targets_unavailable`; retry shortly. The cursor is bound to
    `provider` and `search`.

    Args:
        provider (ListAssayTargetsProvider):
        search (str | Unset):
        limit (int | Unset):  Default: 50.
        cursor (str | Unset):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ListAssayTargetsResponse200 | Problem]
    """

    kwargs = _get_kwargs(
        provider=provider,
        search=search,
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
    provider: ListAssayTargetsProvider,
    search: str | Unset = UNSET,
    limit: int | Unset = 50,
    cursor: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> ListAssayTargetsResponse200 | Problem | None:
    """Search the targets a binding assay can measure against

     Needs Assay Portal access: without it, 403 `wetlab_access_required`. A lab the portal doesn't
    offer you (Ginkgo where it isn't enabled, say) is 400 `validation_failed`. A lab's target list
    that can't be read is 502 `targets_unavailable`; retry shortly. The cursor is bound to
    `provider` and `search`.

    Args:
        provider (ListAssayTargetsProvider):
        search (str | Unset):
        limit (int | Unset):  Default: 50.
        cursor (str | Unset):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ListAssayTargetsResponse200 | Problem
    """

    return sync_detailed(
        client=client,
        provider=provider,
        search=search,
        limit=limit,
        cursor=cursor,
        tamarind_version=tamarind_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    provider: ListAssayTargetsProvider,
    search: str | Unset = UNSET,
    limit: int | Unset = 50,
    cursor: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Response[ListAssayTargetsResponse200 | Problem]:
    """Search the targets a binding assay can measure against

     Needs Assay Portal access: without it, 403 `wetlab_access_required`. A lab the portal doesn't
    offer you (Ginkgo where it isn't enabled, say) is 400 `validation_failed`. A lab's target list
    that can't be read is 502 `targets_unavailable`; retry shortly. The cursor is bound to
    `provider` and `search`.

    Args:
        provider (ListAssayTargetsProvider):
        search (str | Unset):
        limit (int | Unset):  Default: 50.
        cursor (str | Unset):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ListAssayTargetsResponse200 | Problem]
    """

    kwargs = _get_kwargs(
        provider=provider,
        search=search,
        limit=limit,
        cursor=cursor,
        tamarind_version=tamarind_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    provider: ListAssayTargetsProvider,
    search: str | Unset = UNSET,
    limit: int | Unset = 50,
    cursor: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> ListAssayTargetsResponse200 | Problem | None:
    """Search the targets a binding assay can measure against

     Needs Assay Portal access: without it, 403 `wetlab_access_required`. A lab the portal doesn't
    offer you (Ginkgo where it isn't enabled, say) is 400 `validation_failed`. A lab's target list
    that can't be read is 502 `targets_unavailable`; retry shortly. The cursor is bound to
    `provider` and `search`.

    Args:
        provider (ListAssayTargetsProvider):
        search (str | Unset):
        limit (int | Unset):  Default: 50.
        cursor (str | Unset):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ListAssayTargetsResponse200 | Problem
    """

    return (
        await asyncio_detailed(
            client=client,
            provider=provider,
            search=search,
            limit=limit,
            cursor=cursor,
            tamarind_version=tamarind_version,
        )
    ).parsed
