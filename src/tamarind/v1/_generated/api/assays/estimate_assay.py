from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.assay_estimate import AssayEstimate
from ...models.assay_order_csv_request import AssayOrderCsvRequest
from ...models.assay_order_inline_request import AssayOrderInlineRequest
from ...models.problem import Problem
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    body: AssayOrderCsvRequest | AssayOrderInlineRequest,
    tamarind_version: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(tamarind_version, Unset):
        headers["Tamarind-Version"] = tamarind_version

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/assays/estimate",
    }

    if isinstance(body, AssayOrderInlineRequest):
        _kwargs["json"] = body.to_dict()
    else:
        _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> AssayEstimate | Problem:
    if response.status_code == 200:
        response_200 = AssayEstimate.from_dict(response.json())

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
) -> Response[AssayEstimate | Problem]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: AssayOrderCsvRequest | AssayOrderInlineRequest,
    tamarind_version: str | Unset = UNSET,
) -> Response[AssayEstimate | Problem]:
    """Get a price and turnaround. This DOES send the sequences to the lab

     No order is created and nothing is charged, but the lab is sent your sequences, and A-Alpha
    keeps a quote on file. The order gets the same checks as `validateAssay` first: one that fails
    them is 422 `validation_failed` with the same problems in `errors`, and nothing reaches the
    lab. No Assay Portal access is 403 `wetlab_access_required`; an unclaimed agent trial
    credential is 403 `forbidden`. When Ginkgo gives no price, its catalog price is used.

    - 422 `quote_rejected`: the lab refused the order as it is. Its own reasons, when it gave any,
      are in `errors` (code `quote_rejected`), with a `rejected_sequences` problem at `/sequences`
      when it named some. Asking again gets the same answer.
    - 502 `lab_unavailable`: the lab couldn't be reached, failed, refused Tamarind's credentials,
      or isn't set up on this deployment. Retry shortly; you can place the order without an estimate.
    - 502 `targets_unavailable`: GenScript's target list couldn't be read to check the target.

    Args:
        tamarind_version (str | Unset):
        body (AssayOrderCsvRequest | AssayOrderInlineRequest): An assay order. `POST /assays` and
            `POST /assays/estimate` take this body, and `POST /assays/validate` takes the same fields
            (`AssayOrderCheckRequest`) and reports these rules in its verdict. Send exactly one of
            `sequences` or `csvFile`. An optional field sent as null counts as left out. A body with
            no `assayType`, a field of the wrong JSON type, an unknown field or text that isn't valid
            Unicode is refused as it arrives (422). Every other rule here, and each assay type's own,
            is checked by the order checks: `validateAssay` reports their problems in its verdict, and
            `estimateAssay` answers 422 `validation_failed` with the same problems.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AssayEstimate | Problem]
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
    body: AssayOrderCsvRequest | AssayOrderInlineRequest,
    tamarind_version: str | Unset = UNSET,
) -> AssayEstimate | Problem | None:
    """Get a price and turnaround. This DOES send the sequences to the lab

     No order is created and nothing is charged, but the lab is sent your sequences, and A-Alpha
    keeps a quote on file. The order gets the same checks as `validateAssay` first: one that fails
    them is 422 `validation_failed` with the same problems in `errors`, and nothing reaches the
    lab. No Assay Portal access is 403 `wetlab_access_required`; an unclaimed agent trial
    credential is 403 `forbidden`. When Ginkgo gives no price, its catalog price is used.

    - 422 `quote_rejected`: the lab refused the order as it is. Its own reasons, when it gave any,
      are in `errors` (code `quote_rejected`), with a `rejected_sequences` problem at `/sequences`
      when it named some. Asking again gets the same answer.
    - 502 `lab_unavailable`: the lab couldn't be reached, failed, refused Tamarind's credentials,
      or isn't set up on this deployment. Retry shortly; you can place the order without an estimate.
    - 502 `targets_unavailable`: GenScript's target list couldn't be read to check the target.

    Args:
        tamarind_version (str | Unset):
        body (AssayOrderCsvRequest | AssayOrderInlineRequest): An assay order. `POST /assays` and
            `POST /assays/estimate` take this body, and `POST /assays/validate` takes the same fields
            (`AssayOrderCheckRequest`) and reports these rules in its verdict. Send exactly one of
            `sequences` or `csvFile`. An optional field sent as null counts as left out. A body with
            no `assayType`, a field of the wrong JSON type, an unknown field or text that isn't valid
            Unicode is refused as it arrives (422). Every other rule here, and each assay type's own,
            is checked by the order checks: `validateAssay` reports their problems in its verdict, and
            `estimateAssay` answers 422 `validation_failed` with the same problems.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AssayEstimate | Problem
    """

    return sync_detailed(
        client=client,
        body=body,
        tamarind_version=tamarind_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: AssayOrderCsvRequest | AssayOrderInlineRequest,
    tamarind_version: str | Unset = UNSET,
) -> Response[AssayEstimate | Problem]:
    """Get a price and turnaround. This DOES send the sequences to the lab

     No order is created and nothing is charged, but the lab is sent your sequences, and A-Alpha
    keeps a quote on file. The order gets the same checks as `validateAssay` first: one that fails
    them is 422 `validation_failed` with the same problems in `errors`, and nothing reaches the
    lab. No Assay Portal access is 403 `wetlab_access_required`; an unclaimed agent trial
    credential is 403 `forbidden`. When Ginkgo gives no price, its catalog price is used.

    - 422 `quote_rejected`: the lab refused the order as it is. Its own reasons, when it gave any,
      are in `errors` (code `quote_rejected`), with a `rejected_sequences` problem at `/sequences`
      when it named some. Asking again gets the same answer.
    - 502 `lab_unavailable`: the lab couldn't be reached, failed, refused Tamarind's credentials,
      or isn't set up on this deployment. Retry shortly; you can place the order without an estimate.
    - 502 `targets_unavailable`: GenScript's target list couldn't be read to check the target.

    Args:
        tamarind_version (str | Unset):
        body (AssayOrderCsvRequest | AssayOrderInlineRequest): An assay order. `POST /assays` and
            `POST /assays/estimate` take this body, and `POST /assays/validate` takes the same fields
            (`AssayOrderCheckRequest`) and reports these rules in its verdict. Send exactly one of
            `sequences` or `csvFile`. An optional field sent as null counts as left out. A body with
            no `assayType`, a field of the wrong JSON type, an unknown field or text that isn't valid
            Unicode is refused as it arrives (422). Every other rule here, and each assay type's own,
            is checked by the order checks: `validateAssay` reports their problems in its verdict, and
            `estimateAssay` answers 422 `validation_failed` with the same problems.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AssayEstimate | Problem]
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
    body: AssayOrderCsvRequest | AssayOrderInlineRequest,
    tamarind_version: str | Unset = UNSET,
) -> AssayEstimate | Problem | None:
    """Get a price and turnaround. This DOES send the sequences to the lab

     No order is created and nothing is charged, but the lab is sent your sequences, and A-Alpha
    keeps a quote on file. The order gets the same checks as `validateAssay` first: one that fails
    them is 422 `validation_failed` with the same problems in `errors`, and nothing reaches the
    lab. No Assay Portal access is 403 `wetlab_access_required`; an unclaimed agent trial
    credential is 403 `forbidden`. When Ginkgo gives no price, its catalog price is used.

    - 422 `quote_rejected`: the lab refused the order as it is. Its own reasons, when it gave any,
      are in `errors` (code `quote_rejected`), with a `rejected_sequences` problem at `/sequences`
      when it named some. Asking again gets the same answer.
    - 502 `lab_unavailable`: the lab couldn't be reached, failed, refused Tamarind's credentials,
      or isn't set up on this deployment. Retry shortly; you can place the order without an estimate.
    - 502 `targets_unavailable`: GenScript's target list couldn't be read to check the target.

    Args:
        tamarind_version (str | Unset):
        body (AssayOrderCsvRequest | AssayOrderInlineRequest): An assay order. `POST /assays` and
            `POST /assays/estimate` take this body, and `POST /assays/validate` takes the same fields
            (`AssayOrderCheckRequest`) and reports these rules in its verdict. Send exactly one of
            `sequences` or `csvFile`. An optional field sent as null counts as left out. A body with
            no `assayType`, a field of the wrong JSON type, an unknown field or text that isn't valid
            Unicode is refused as it arrives (422). Every other rule here, and each assay type's own,
            is checked by the order checks: `validateAssay` reports their problems in its verdict, and
            `estimateAssay` answers 422 `validation_failed` with the same problems.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AssayEstimate | Problem
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            tamarind_version=tamarind_version,
        )
    ).parsed
