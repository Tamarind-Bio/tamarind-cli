from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.assay_order import AssayOrder
from ...models.assay_order_csv_request import AssayOrderCsvRequest
from ...models.assay_order_inline_request import AssayOrderInlineRequest
from ...models.problem import Problem
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    body: AssayOrderCsvRequest | AssayOrderInlineRequest,
    idempotency_key: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(idempotency_key, Unset):
        headers["Idempotency-Key"] = idempotency_key

    if not isinstance(tamarind_version, Unset):
        headers["Tamarind-Version"] = tamarind_version

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/assays",
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
) -> AssayOrder | Problem:
    if response.status_code == 201:
        response_201 = AssayOrder.from_dict(response.json())

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

    if response.status_code == 500:
        response_500 = Problem.from_dict(response.json())

        return response_500

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
) -> Response[AssayOrder | Problem]:
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
    idempotency_key: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Response[AssayOrder | Problem]:
    """Place an assay order

     This commits real money and lab work. Confirm with the user first. Use `validateAssay` beforehand.

    Today's submit, ported: the order lands awaiting Tamarind's approval, and a Tamarind admin reviews
    it,
    arranges payment and only then sends it to the lab. Adaptyv is sent the order now, for review and a
    quote; A-Alpha is asked for a quote first; GenScript is asked for its estimate. Nothing is charged
    here.
    201 has `Location: /assays/{assayId}`. With `Idempotency-Key`, a retry replays the order (or the
    failure it ended in) with `Idempotent-Replayed: true`.

    Refusals, after the same checks as `validateAssay` (422 `validation_failed`):
    - 409 `duplicate_order`: the same assays and sequence count in the last 30 minutes; `detail` names
      the earlier order. Send `confirmDuplicate: true` to place it anyway.
    - 409 `assays_blocked`: an assay can't be ordered until Tamarind clears it.
    - 409 `assays_in_flight` (retryable): another submit holds one of these assays; `detail` names them.
    - 409 `idempotency_order_unavailable`: this key's order can't be read back.
    - 422 `quote_rejected` or 502 `lab_unavailable`: A-Alpha refused or couldn't quote.
    - 502 `order_incomplete` or `provider_error`: the order or the lab's draft failed, and nothing is
      pending.
    - 500 `outcome_unknown`: it may have been placed; read `GET /assays/{assayId}` before sending it
    again.
    - 503 `service_unavailable`: retryable with `Retry-After`, or not retryable when Tamarind was paged.

    Args:
        idempotency_key (str | Unset):
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
        Response[AssayOrder | Problem]
    """

    kwargs = _get_kwargs(
        body=body,
        idempotency_key=idempotency_key,
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
    idempotency_key: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> AssayOrder | Problem | None:
    """Place an assay order

     This commits real money and lab work. Confirm with the user first. Use `validateAssay` beforehand.

    Today's submit, ported: the order lands awaiting Tamarind's approval, and a Tamarind admin reviews
    it,
    arranges payment and only then sends it to the lab. Adaptyv is sent the order now, for review and a
    quote; A-Alpha is asked for a quote first; GenScript is asked for its estimate. Nothing is charged
    here.
    201 has `Location: /assays/{assayId}`. With `Idempotency-Key`, a retry replays the order (or the
    failure it ended in) with `Idempotent-Replayed: true`.

    Refusals, after the same checks as `validateAssay` (422 `validation_failed`):
    - 409 `duplicate_order`: the same assays and sequence count in the last 30 minutes; `detail` names
      the earlier order. Send `confirmDuplicate: true` to place it anyway.
    - 409 `assays_blocked`: an assay can't be ordered until Tamarind clears it.
    - 409 `assays_in_flight` (retryable): another submit holds one of these assays; `detail` names them.
    - 409 `idempotency_order_unavailable`: this key's order can't be read back.
    - 422 `quote_rejected` or 502 `lab_unavailable`: A-Alpha refused or couldn't quote.
    - 502 `order_incomplete` or `provider_error`: the order or the lab's draft failed, and nothing is
      pending.
    - 500 `outcome_unknown`: it may have been placed; read `GET /assays/{assayId}` before sending it
    again.
    - 503 `service_unavailable`: retryable with `Retry-After`, or not retryable when Tamarind was paged.

    Args:
        idempotency_key (str | Unset):
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
        AssayOrder | Problem
    """

    return sync_detailed(
        client=client,
        body=body,
        idempotency_key=idempotency_key,
        tamarind_version=tamarind_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: AssayOrderCsvRequest | AssayOrderInlineRequest,
    idempotency_key: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Response[AssayOrder | Problem]:
    """Place an assay order

     This commits real money and lab work. Confirm with the user first. Use `validateAssay` beforehand.

    Today's submit, ported: the order lands awaiting Tamarind's approval, and a Tamarind admin reviews
    it,
    arranges payment and only then sends it to the lab. Adaptyv is sent the order now, for review and a
    quote; A-Alpha is asked for a quote first; GenScript is asked for its estimate. Nothing is charged
    here.
    201 has `Location: /assays/{assayId}`. With `Idempotency-Key`, a retry replays the order (or the
    failure it ended in) with `Idempotent-Replayed: true`.

    Refusals, after the same checks as `validateAssay` (422 `validation_failed`):
    - 409 `duplicate_order`: the same assays and sequence count in the last 30 minutes; `detail` names
      the earlier order. Send `confirmDuplicate: true` to place it anyway.
    - 409 `assays_blocked`: an assay can't be ordered until Tamarind clears it.
    - 409 `assays_in_flight` (retryable): another submit holds one of these assays; `detail` names them.
    - 409 `idempotency_order_unavailable`: this key's order can't be read back.
    - 422 `quote_rejected` or 502 `lab_unavailable`: A-Alpha refused or couldn't quote.
    - 502 `order_incomplete` or `provider_error`: the order or the lab's draft failed, and nothing is
      pending.
    - 500 `outcome_unknown`: it may have been placed; read `GET /assays/{assayId}` before sending it
    again.
    - 503 `service_unavailable`: retryable with `Retry-After`, or not retryable when Tamarind was paged.

    Args:
        idempotency_key (str | Unset):
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
        Response[AssayOrder | Problem]
    """

    kwargs = _get_kwargs(
        body=body,
        idempotency_key=idempotency_key,
        tamarind_version=tamarind_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: AssayOrderCsvRequest | AssayOrderInlineRequest,
    idempotency_key: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> AssayOrder | Problem | None:
    """Place an assay order

     This commits real money and lab work. Confirm with the user first. Use `validateAssay` beforehand.

    Today's submit, ported: the order lands awaiting Tamarind's approval, and a Tamarind admin reviews
    it,
    arranges payment and only then sends it to the lab. Adaptyv is sent the order now, for review and a
    quote; A-Alpha is asked for a quote first; GenScript is asked for its estimate. Nothing is charged
    here.
    201 has `Location: /assays/{assayId}`. With `Idempotency-Key`, a retry replays the order (or the
    failure it ended in) with `Idempotent-Replayed: true`.

    Refusals, after the same checks as `validateAssay` (422 `validation_failed`):
    - 409 `duplicate_order`: the same assays and sequence count in the last 30 minutes; `detail` names
      the earlier order. Send `confirmDuplicate: true` to place it anyway.
    - 409 `assays_blocked`: an assay can't be ordered until Tamarind clears it.
    - 409 `assays_in_flight` (retryable): another submit holds one of these assays; `detail` names them.
    - 409 `idempotency_order_unavailable`: this key's order can't be read back.
    - 422 `quote_rejected` or 502 `lab_unavailable`: A-Alpha refused or couldn't quote.
    - 502 `order_incomplete` or `provider_error`: the order or the lab's draft failed, and nothing is
      pending.
    - 500 `outcome_unknown`: it may have been placed; read `GET /assays/{assayId}` before sending it
    again.
    - 503 `service_unavailable`: retryable with `Retry-After`, or not retryable when Tamarind was paged.

    Args:
        idempotency_key (str | Unset):
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
        AssayOrder | Problem
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            idempotency_key=idempotency_key,
            tamarind_version=tamarind_version,
        )
    ).parsed
