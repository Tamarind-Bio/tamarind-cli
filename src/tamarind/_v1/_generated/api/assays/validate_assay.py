from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.assay_order_check_request import AssayOrderCheckRequest
from ...models.problem import Problem
from ...models.validation_report import ValidationReport
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    body: AssayOrderCheckRequest,
    tamarind_version: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(tamarind_version, Unset):
        headers["Tamarind-Version"] = tamarind_version

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/assays/validate",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Problem | ValidationReport:
    if response.status_code == 200:
        response_200 = ValidationReport.from_dict(response.json())

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
) -> Response[Problem | ValidationReport]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: AssayOrderCheckRequest,
    tamarind_version: str | Unset = UNSET,
) -> Response[Problem | ValidationReport]:
    """Check an order. Nothing is sent to a lab

     200 means the check ran, whatever the verdict. Only a body with no `assayType`, a field of the
    wrong JSON type, an unknown field, or text that isn't valid Unicode is 422, because there is
    nothing to check. The body is `AssayOrderCheckRequest`: every other rule of `AssayOrderRequest`
    (exactly one of `sequences` or `csvFile`, `modality`, the shape of each sequence) is part of the
    verdict. Runs the portal's own
    order checks, word for word: settings, sequences, a CSV file (read from your own files only),
    targets, residues, each lab's minimums and duplicates. Nothing is created and no lab is
    contacted.

    Each problem is a `Diagnostic`, with a pointer such as `/settings/method`, `/sequences/3` or
    `/csvFile` when it's about one field. A problem in a row read from `csvFile` points at `/csvFile`,
    and its `detail` names
    the row. No Assay Portal access (`wetlab_access_required`), or an unclaimed agent trial
    credential (`unclaimed_agent_credential`), is a failed `access` check with the other checks
    skipped, not a 403. Otherwise `checks.name` is the order name and `checks.settings` is everything
    else about the order; `project` and `budget` are skipped. A target list that can't be read is
    skipped, as the lab checks again, except GenScript's: that is 502 `targets_unavailable`.

    When valid, `normalized` holds `assayType`, `provider`, `modality`, `settings` with defaults
    filled in, and `sequenceCount`. `name` is the name you sent, trimmed, unless it was blank or is
    what failed.

    Args:
        tamarind_version (str | Unset):
        body (AssayOrderCheckRequest): The body `validateAssay` takes: the fields of
            `AssayOrderRequest`, typed, without the rules between them (exactly one of `sequences` or
            `csvFile`, a `columnMapping` with `csvFile`, the shape of each sequence), which are part
            of its verdict.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Problem | ValidationReport]
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
    body: AssayOrderCheckRequest,
    tamarind_version: str | Unset = UNSET,
) -> Problem | ValidationReport | None:
    """Check an order. Nothing is sent to a lab

     200 means the check ran, whatever the verdict. Only a body with no `assayType`, a field of the
    wrong JSON type, an unknown field, or text that isn't valid Unicode is 422, because there is
    nothing to check. The body is `AssayOrderCheckRequest`: every other rule of `AssayOrderRequest`
    (exactly one of `sequences` or `csvFile`, `modality`, the shape of each sequence) is part of the
    verdict. Runs the portal's own
    order checks, word for word: settings, sequences, a CSV file (read from your own files only),
    targets, residues, each lab's minimums and duplicates. Nothing is created and no lab is
    contacted.

    Each problem is a `Diagnostic`, with a pointer such as `/settings/method`, `/sequences/3` or
    `/csvFile` when it's about one field. A problem in a row read from `csvFile` points at `/csvFile`,
    and its `detail` names
    the row. No Assay Portal access (`wetlab_access_required`), or an unclaimed agent trial
    credential (`unclaimed_agent_credential`), is a failed `access` check with the other checks
    skipped, not a 403. Otherwise `checks.name` is the order name and `checks.settings` is everything
    else about the order; `project` and `budget` are skipped. A target list that can't be read is
    skipped, as the lab checks again, except GenScript's: that is 502 `targets_unavailable`.

    When valid, `normalized` holds `assayType`, `provider`, `modality`, `settings` with defaults
    filled in, and `sequenceCount`. `name` is the name you sent, trimmed, unless it was blank or is
    what failed.

    Args:
        tamarind_version (str | Unset):
        body (AssayOrderCheckRequest): The body `validateAssay` takes: the fields of
            `AssayOrderRequest`, typed, without the rules between them (exactly one of `sequences` or
            `csvFile`, a `columnMapping` with `csvFile`, the shape of each sequence), which are part
            of its verdict.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Problem | ValidationReport
    """

    return sync_detailed(
        client=client,
        body=body,
        tamarind_version=tamarind_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: AssayOrderCheckRequest,
    tamarind_version: str | Unset = UNSET,
) -> Response[Problem | ValidationReport]:
    """Check an order. Nothing is sent to a lab

     200 means the check ran, whatever the verdict. Only a body with no `assayType`, a field of the
    wrong JSON type, an unknown field, or text that isn't valid Unicode is 422, because there is
    nothing to check. The body is `AssayOrderCheckRequest`: every other rule of `AssayOrderRequest`
    (exactly one of `sequences` or `csvFile`, `modality`, the shape of each sequence) is part of the
    verdict. Runs the portal's own
    order checks, word for word: settings, sequences, a CSV file (read from your own files only),
    targets, residues, each lab's minimums and duplicates. Nothing is created and no lab is
    contacted.

    Each problem is a `Diagnostic`, with a pointer such as `/settings/method`, `/sequences/3` or
    `/csvFile` when it's about one field. A problem in a row read from `csvFile` points at `/csvFile`,
    and its `detail` names
    the row. No Assay Portal access (`wetlab_access_required`), or an unclaimed agent trial
    credential (`unclaimed_agent_credential`), is a failed `access` check with the other checks
    skipped, not a 403. Otherwise `checks.name` is the order name and `checks.settings` is everything
    else about the order; `project` and `budget` are skipped. A target list that can't be read is
    skipped, as the lab checks again, except GenScript's: that is 502 `targets_unavailable`.

    When valid, `normalized` holds `assayType`, `provider`, `modality`, `settings` with defaults
    filled in, and `sequenceCount`. `name` is the name you sent, trimmed, unless it was blank or is
    what failed.

    Args:
        tamarind_version (str | Unset):
        body (AssayOrderCheckRequest): The body `validateAssay` takes: the fields of
            `AssayOrderRequest`, typed, without the rules between them (exactly one of `sequences` or
            `csvFile`, a `columnMapping` with `csvFile`, the shape of each sequence), which are part
            of its verdict.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Problem | ValidationReport]
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
    body: AssayOrderCheckRequest,
    tamarind_version: str | Unset = UNSET,
) -> Problem | ValidationReport | None:
    """Check an order. Nothing is sent to a lab

     200 means the check ran, whatever the verdict. Only a body with no `assayType`, a field of the
    wrong JSON type, an unknown field, or text that isn't valid Unicode is 422, because there is
    nothing to check. The body is `AssayOrderCheckRequest`: every other rule of `AssayOrderRequest`
    (exactly one of `sequences` or `csvFile`, `modality`, the shape of each sequence) is part of the
    verdict. Runs the portal's own
    order checks, word for word: settings, sequences, a CSV file (read from your own files only),
    targets, residues, each lab's minimums and duplicates. Nothing is created and no lab is
    contacted.

    Each problem is a `Diagnostic`, with a pointer such as `/settings/method`, `/sequences/3` or
    `/csvFile` when it's about one field. A problem in a row read from `csvFile` points at `/csvFile`,
    and its `detail` names
    the row. No Assay Portal access (`wetlab_access_required`), or an unclaimed agent trial
    credential (`unclaimed_agent_credential`), is a failed `access` check with the other checks
    skipped, not a 403. Otherwise `checks.name` is the order name and `checks.settings` is everything
    else about the order; `project` and `budget` are skipped. A target list that can't be read is
    skipped, as the lab checks again, except GenScript's: that is 502 `targets_unavailable`.

    When valid, `normalized` holds `assayType`, `provider`, `modality`, `settings` with defaults
    filled in, and `sequenceCount`. `name` is the name you sent, trimmed, unless it was blank or is
    what failed.

    Args:
        tamarind_version (str | Unset):
        body (AssayOrderCheckRequest): The body `validateAssay` takes: the fields of
            `AssayOrderRequest`, typed, without the rules between them (exactly one of `sequences` or
            `csvFile`, a `columnMapping` with `csvFile`, the shape of each sequence), which are part
            of its verdict.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Problem | ValidationReport
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            tamarind_version=tamarind_version,
        )
    ).parsed
