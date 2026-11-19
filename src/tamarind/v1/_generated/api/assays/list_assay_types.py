from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.assay_type_page import AssayTypePage
from ...models.list_assay_types_provider import ListAssayTypesProvider
from ...models.problem import Problem
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    provider: ListAssayTypesProvider | Unset = UNSET,
    limit: int | Unset = 50,
    cursor: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(tamarind_version, Unset):
        headers["Tamarind-Version"] = tamarind_version

    params: dict[str, Any] = {}

    json_provider: str | Unset = UNSET
    if not isinstance(provider, Unset):
        json_provider = provider.value

    params["provider"] = json_provider

    params["limit"] = limit

    params["cursor"] = cursor

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/assay-types",
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> AssayTypePage | Problem:
    if response.status_code == 200:
        response_200 = AssayTypePage.from_dict(response.json())

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
) -> Response[AssayTypePage | Problem]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    provider: ListAssayTypesProvider | Unset = UNSET,
    limit: int | Unset = 50,
    cursor: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Response[AssayTypePage | Problem]:
    """List the wet-lab assays you can order

     Any key can read the catalogue. A lab the portal doesn't offer you is left out, and naming it
    as `provider` is 400 `validation_failed`. `wetLabAccess` says whether you can place orders:
    Assay Portal access, on a credential that isn't an unclaimed agent trial. `requestAccessUrl` is
    where to ask for access.

    Args:
        provider (ListAssayTypesProvider | Unset):
        limit (int | Unset):  Default: 50.
        cursor (str | Unset):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AssayTypePage | Problem]
    """

    kwargs = _get_kwargs(
        provider=provider,
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
    provider: ListAssayTypesProvider | Unset = UNSET,
    limit: int | Unset = 50,
    cursor: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> AssayTypePage | Problem | None:
    """List the wet-lab assays you can order

     Any key can read the catalogue. A lab the portal doesn't offer you is left out, and naming it
    as `provider` is 400 `validation_failed`. `wetLabAccess` says whether you can place orders:
    Assay Portal access, on a credential that isn't an unclaimed agent trial. `requestAccessUrl` is
    where to ask for access.

    Args:
        provider (ListAssayTypesProvider | Unset):
        limit (int | Unset):  Default: 50.
        cursor (str | Unset):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AssayTypePage | Problem
    """

    return sync_detailed(
        client=client,
        provider=provider,
        limit=limit,
        cursor=cursor,
        tamarind_version=tamarind_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    provider: ListAssayTypesProvider | Unset = UNSET,
    limit: int | Unset = 50,
    cursor: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Response[AssayTypePage | Problem]:
    """List the wet-lab assays you can order

     Any key can read the catalogue. A lab the portal doesn't offer you is left out, and naming it
    as `provider` is 400 `validation_failed`. `wetLabAccess` says whether you can place orders:
    Assay Portal access, on a credential that isn't an unclaimed agent trial. `requestAccessUrl` is
    where to ask for access.

    Args:
        provider (ListAssayTypesProvider | Unset):
        limit (int | Unset):  Default: 50.
        cursor (str | Unset):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AssayTypePage | Problem]
    """

    kwargs = _get_kwargs(
        provider=provider,
        limit=limit,
        cursor=cursor,
        tamarind_version=tamarind_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    provider: ListAssayTypesProvider | Unset = UNSET,
    limit: int | Unset = 50,
    cursor: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> AssayTypePage | Problem | None:
    """List the wet-lab assays you can order

     Any key can read the catalogue. A lab the portal doesn't offer you is left out, and naming it
    as `provider` is 400 `validation_failed`. `wetLabAccess` says whether you can place orders:
    Assay Portal access, on a credential that isn't an unclaimed agent trial. `requestAccessUrl` is
    where to ask for access.

    Args:
        provider (ListAssayTypesProvider | Unset):
        limit (int | Unset):  Default: 50.
        cursor (str | Unset):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AssayTypePage | Problem
    """

    return (
        await asyncio_detailed(
            client=client,
            provider=provider,
            limit=limit,
            cursor=cursor,
            tamarind_version=tamarind_version,
        )
    ).parsed
