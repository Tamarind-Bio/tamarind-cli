from http import HTTPStatus
from typing import Any, cast

import httpx

from ...client import AuthenticatedClient, Client
from ...models.download_link import DownloadLink
from ...models.get_file_delivery import GetFileDelivery
from ...models.problem import Problem
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    path: str,
    delivery: GetFileDelivery | Unset = GetFileDelivery.URL,
    tamarind_version: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(tamarind_version, Unset):
        headers["Tamarind-Version"] = tamarind_version

    params: dict[str, Any] = {}

    params["path"] = path

    json_delivery: str | Unset = UNSET
    if not isinstance(delivery, Unset):
        json_delivery = delivery.value

    params["delivery"] = json_delivery

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/files/content",
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Any | DownloadLink | Problem:
    if response.status_code == 200:
        response_200 = DownloadLink.from_dict(response.json())

        return response_200

    if response.status_code == 302:
        response_302 = cast(Any, None)
        return response_302

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

    if response.status_code == 413:
        response_413 = Problem.from_dict(response.json())

        return response_413

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
) -> Response[Any | DownloadLink | Problem]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    path: str,
    delivery: GetFileDelivery | Unset = GetFileDelivery.URL,
    tamarind_version: str | Unset = UNSET,
) -> Response[Any | DownloadLink | Problem]:
    """Download a workspace file

     Any file in your workspace by its exact path, hidden ones included. A private export is the same 404
    as a missing file.

    Args:
        path (str):
        delivery (GetFileDelivery | Unset):  Default: GetFileDelivery.URL.
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | DownloadLink | Problem]
    """

    kwargs = _get_kwargs(
        path=path,
        delivery=delivery,
        tamarind_version=tamarind_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    path: str,
    delivery: GetFileDelivery | Unset = GetFileDelivery.URL,
    tamarind_version: str | Unset = UNSET,
) -> Any | DownloadLink | Problem | None:
    """Download a workspace file

     Any file in your workspace by its exact path, hidden ones included. A private export is the same 404
    as a missing file.

    Args:
        path (str):
        delivery (GetFileDelivery | Unset):  Default: GetFileDelivery.URL.
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | DownloadLink | Problem
    """

    return sync_detailed(
        client=client,
        path=path,
        delivery=delivery,
        tamarind_version=tamarind_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    path: str,
    delivery: GetFileDelivery | Unset = GetFileDelivery.URL,
    tamarind_version: str | Unset = UNSET,
) -> Response[Any | DownloadLink | Problem]:
    """Download a workspace file

     Any file in your workspace by its exact path, hidden ones included. A private export is the same 404
    as a missing file.

    Args:
        path (str):
        delivery (GetFileDelivery | Unset):  Default: GetFileDelivery.URL.
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | DownloadLink | Problem]
    """

    kwargs = _get_kwargs(
        path=path,
        delivery=delivery,
        tamarind_version=tamarind_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    path: str,
    delivery: GetFileDelivery | Unset = GetFileDelivery.URL,
    tamarind_version: str | Unset = UNSET,
) -> Any | DownloadLink | Problem | None:
    """Download a workspace file

     Any file in your workspace by its exact path, hidden ones included. A private export is the same 404
    as a missing file.

    Args:
        path (str):
        delivery (GetFileDelivery | Unset):  Default: GetFileDelivery.URL.
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | DownloadLink | Problem
    """

    return (
        await asyncio_detailed(
            client=client,
            path=path,
            delivery=delivery,
            tamarind_version=tamarind_version,
        )
    ).parsed
