from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.assay_results import AssayResults
from ...models.problem import Problem
from ...types import UNSET, Response, Unset


def _get_kwargs(
    assay_id: str,
    *,
    tamarind_version: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(tamarind_version, Unset):
        headers["Tamarind-Version"] = tamarind_version

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/assays/{assay_id}/results".format(
            assay_id=quote(str(assay_id), safe=""),
        ),
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> AssayResults | Problem:
    if response.status_code == 200:
        response_200 = AssayResults.from_dict(response.json())

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
) -> Response[AssayResults | Problem]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    assay_id: str,
    *,
    client: AuthenticatedClient | Client,
    tamarind_version: str | Unset = UNSET,
) -> Response[AssayResults | Problem]:
    """Get an order's results and download links

     Links to what the lab delivered; `expiresAt` says when they stop working. Results stored with
    Tamarind are listed whatever the order's `status` says now; otherwise nothing is ready until
    the order is `completed`. A completed order with nothing stored yet asks the lab once more:
    GenScript's report or Adaptyv's results are fetched, stored and recorded on the order. Ginkgo
    and A-Alpha deliver on their own, so there is nothing to ask. An Adaptyv order's own
    data-package links are fetched again on each read, waiting at most 5 seconds. These lab calls
    only read: nothing is ordered, changed or charged.

    502 `results_unavailable` means the results can't be loaded. With `retryable: true`, retry
    shortly. With `retryable: false`, the lab's delivery failed and Tamarind recorded it, or the
    stored results can't be linked: contact Tamarind support.

    Args:
        assay_id (str):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AssayResults | Problem]
    """

    kwargs = _get_kwargs(
        assay_id=assay_id,
        tamarind_version=tamarind_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    assay_id: str,
    *,
    client: AuthenticatedClient | Client,
    tamarind_version: str | Unset = UNSET,
) -> AssayResults | Problem | None:
    """Get an order's results and download links

     Links to what the lab delivered; `expiresAt` says when they stop working. Results stored with
    Tamarind are listed whatever the order's `status` says now; otherwise nothing is ready until
    the order is `completed`. A completed order with nothing stored yet asks the lab once more:
    GenScript's report or Adaptyv's results are fetched, stored and recorded on the order. Ginkgo
    and A-Alpha deliver on their own, so there is nothing to ask. An Adaptyv order's own
    data-package links are fetched again on each read, waiting at most 5 seconds. These lab calls
    only read: nothing is ordered, changed or charged.

    502 `results_unavailable` means the results can't be loaded. With `retryable: true`, retry
    shortly. With `retryable: false`, the lab's delivery failed and Tamarind recorded it, or the
    stored results can't be linked: contact Tamarind support.

    Args:
        assay_id (str):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AssayResults | Problem
    """

    return sync_detailed(
        assay_id=assay_id,
        client=client,
        tamarind_version=tamarind_version,
    ).parsed


async def asyncio_detailed(
    assay_id: str,
    *,
    client: AuthenticatedClient | Client,
    tamarind_version: str | Unset = UNSET,
) -> Response[AssayResults | Problem]:
    """Get an order's results and download links

     Links to what the lab delivered; `expiresAt` says when they stop working. Results stored with
    Tamarind are listed whatever the order's `status` says now; otherwise nothing is ready until
    the order is `completed`. A completed order with nothing stored yet asks the lab once more:
    GenScript's report or Adaptyv's results are fetched, stored and recorded on the order. Ginkgo
    and A-Alpha deliver on their own, so there is nothing to ask. An Adaptyv order's own
    data-package links are fetched again on each read, waiting at most 5 seconds. These lab calls
    only read: nothing is ordered, changed or charged.

    502 `results_unavailable` means the results can't be loaded. With `retryable: true`, retry
    shortly. With `retryable: false`, the lab's delivery failed and Tamarind recorded it, or the
    stored results can't be linked: contact Tamarind support.

    Args:
        assay_id (str):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AssayResults | Problem]
    """

    kwargs = _get_kwargs(
        assay_id=assay_id,
        tamarind_version=tamarind_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    assay_id: str,
    *,
    client: AuthenticatedClient | Client,
    tamarind_version: str | Unset = UNSET,
) -> AssayResults | Problem | None:
    """Get an order's results and download links

     Links to what the lab delivered; `expiresAt` says when they stop working. Results stored with
    Tamarind are listed whatever the order's `status` says now; otherwise nothing is ready until
    the order is `completed`. A completed order with nothing stored yet asks the lab once more:
    GenScript's report or Adaptyv's results are fetched, stored and recorded on the order. Ginkgo
    and A-Alpha deliver on their own, so there is nothing to ask. An Adaptyv order's own
    data-package links are fetched again on each read, waiting at most 5 seconds. These lab calls
    only read: nothing is ordered, changed or charged.

    502 `results_unavailable` means the results can't be loaded. With `retryable: true`, retry
    shortly. With `retryable: false`, the lab's delivery failed and Tamarind recorded it, or the
    stored results can't be linked: contact Tamarind support.

    Args:
        assay_id (str):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AssayResults | Problem
    """

    return (
        await asyncio_detailed(
            assay_id=assay_id,
            client=client,
            tamarind_version=tamarind_version,
        )
    ).parsed
