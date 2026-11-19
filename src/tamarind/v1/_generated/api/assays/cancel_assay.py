from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.assay_order import AssayOrder
from ...models.cancel_assay_body import CancelAssayBody
from ...models.problem import Problem
from ...types import UNSET, Response, Unset


def _get_kwargs(
    assay_id: str,
    *,
    body: CancelAssayBody | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(tamarind_version, Unset):
        headers["Tamarind-Version"] = tamarind_version

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/assays/{assay_id}/cancel".format(
            assay_id=quote(str(assay_id), safe=""),
        ),
    }

    if not isinstance(body, Unset):
        _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> AssayOrder | Problem:
    if response.status_code == 200:
        response_200 = AssayOrder.from_dict(response.json())

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

    if response.status_code == 409:
        response_409 = Problem.from_dict(response.json())

        return response_409

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
) -> Response[AssayOrder | Problem]:
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
    body: CancelAssayBody | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Response[AssayOrder | Problem]:
    """Cancel an assay order. This cannot be undone

     Confirm with the user first. The order's `cancellable` field says whether this will work now.
    Safe to repeat: an order already `cancelled` or `cancelling` answers 200 as it is. When the lab
    holds the order it is told: Ginkgo confirms later, so the order reads `cancelling`; A-Alpha
    confirms at once. An order no lab holds yet is only recorded as `cancelled`. Ginkgo orders can
    be cancelled only before work starts, A-Alpha orders until they finish, and Adaptyv and
    GenScript orders only through Tamarind support.

    - 409 `not_cancellable`: the lab won't cancel the order in its current status, cancels only
      through support, or isn't set up on this deployment.
    - 409 `approval_in_progress`: Tamarind is approving the order right now. Check its status again
      in a minute.
    - 409 `approval_under_review`: someone at Tamarind has to look at the order first. Contact
      support.
    - 409 `order_changed`: the order changed while it was being cancelled, so the cancel wasn't
      recorded. Read the order.
    - 502 `cancel_unconfirmed`: the cancel may or may not have happened. Read the order before
      retrying or telling anyone it is cancelled.

    Args:
        assay_id (str):
        tamarind_version (str | Unset):
        body (CancelAssayBody | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AssayOrder | Problem]
    """

    kwargs = _get_kwargs(
        assay_id=assay_id,
        body=body,
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
    body: CancelAssayBody | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> AssayOrder | Problem | None:
    """Cancel an assay order. This cannot be undone

     Confirm with the user first. The order's `cancellable` field says whether this will work now.
    Safe to repeat: an order already `cancelled` or `cancelling` answers 200 as it is. When the lab
    holds the order it is told: Ginkgo confirms later, so the order reads `cancelling`; A-Alpha
    confirms at once. An order no lab holds yet is only recorded as `cancelled`. Ginkgo orders can
    be cancelled only before work starts, A-Alpha orders until they finish, and Adaptyv and
    GenScript orders only through Tamarind support.

    - 409 `not_cancellable`: the lab won't cancel the order in its current status, cancels only
      through support, or isn't set up on this deployment.
    - 409 `approval_in_progress`: Tamarind is approving the order right now. Check its status again
      in a minute.
    - 409 `approval_under_review`: someone at Tamarind has to look at the order first. Contact
      support.
    - 409 `order_changed`: the order changed while it was being cancelled, so the cancel wasn't
      recorded. Read the order.
    - 502 `cancel_unconfirmed`: the cancel may or may not have happened. Read the order before
      retrying or telling anyone it is cancelled.

    Args:
        assay_id (str):
        tamarind_version (str | Unset):
        body (CancelAssayBody | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AssayOrder | Problem
    """

    return sync_detailed(
        assay_id=assay_id,
        client=client,
        body=body,
        tamarind_version=tamarind_version,
    ).parsed


async def asyncio_detailed(
    assay_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: CancelAssayBody | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Response[AssayOrder | Problem]:
    """Cancel an assay order. This cannot be undone

     Confirm with the user first. The order's `cancellable` field says whether this will work now.
    Safe to repeat: an order already `cancelled` or `cancelling` answers 200 as it is. When the lab
    holds the order it is told: Ginkgo confirms later, so the order reads `cancelling`; A-Alpha
    confirms at once. An order no lab holds yet is only recorded as `cancelled`. Ginkgo orders can
    be cancelled only before work starts, A-Alpha orders until they finish, and Adaptyv and
    GenScript orders only through Tamarind support.

    - 409 `not_cancellable`: the lab won't cancel the order in its current status, cancels only
      through support, or isn't set up on this deployment.
    - 409 `approval_in_progress`: Tamarind is approving the order right now. Check its status again
      in a minute.
    - 409 `approval_under_review`: someone at Tamarind has to look at the order first. Contact
      support.
    - 409 `order_changed`: the order changed while it was being cancelled, so the cancel wasn't
      recorded. Read the order.
    - 502 `cancel_unconfirmed`: the cancel may or may not have happened. Read the order before
      retrying or telling anyone it is cancelled.

    Args:
        assay_id (str):
        tamarind_version (str | Unset):
        body (CancelAssayBody | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AssayOrder | Problem]
    """

    kwargs = _get_kwargs(
        assay_id=assay_id,
        body=body,
        tamarind_version=tamarind_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    assay_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: CancelAssayBody | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> AssayOrder | Problem | None:
    """Cancel an assay order. This cannot be undone

     Confirm with the user first. The order's `cancellable` field says whether this will work now.
    Safe to repeat: an order already `cancelled` or `cancelling` answers 200 as it is. When the lab
    holds the order it is told: Ginkgo confirms later, so the order reads `cancelling`; A-Alpha
    confirms at once. An order no lab holds yet is only recorded as `cancelled`. Ginkgo orders can
    be cancelled only before work starts, A-Alpha orders until they finish, and Adaptyv and
    GenScript orders only through Tamarind support.

    - 409 `not_cancellable`: the lab won't cancel the order in its current status, cancels only
      through support, or isn't set up on this deployment.
    - 409 `approval_in_progress`: Tamarind is approving the order right now. Check its status again
      in a minute.
    - 409 `approval_under_review`: someone at Tamarind has to look at the order first. Contact
      support.
    - 409 `order_changed`: the order changed while it was being cancelled, so the cancel wasn't
      recorded. Read the order.
    - 502 `cancel_unconfirmed`: the cancel may or may not have happened. Read the order before
      retrying or telling anyone it is cancelled.

    Args:
        assay_id (str):
        tamarind_version (str | Unset):
        body (CancelAssayBody | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AssayOrder | Problem
    """

    return (
        await asyncio_detailed(
            assay_id=assay_id,
            client=client,
            body=body,
            tamarind_version=tamarind_version,
        )
    ).parsed
