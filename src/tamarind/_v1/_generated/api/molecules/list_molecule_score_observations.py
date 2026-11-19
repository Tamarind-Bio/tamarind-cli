from http import HTTPStatus
from typing import Any
from urllib.parse import quote
from uuid import UUID

import httpx

from ...client import AuthenticatedClient, Client
from ...models.problem import Problem
from ...models.score_observation_page import ScoreObservationPage
from ...models.score_observation_query import ScoreObservationQuery
from ...types import UNSET, Response, Unset


def _get_kwargs(
    group_id: UUID,
    *,
    body: ScoreObservationQuery,
    tamarind_version: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(tamarind_version, Unset):
        headers["Tamarind-Version"] = tamarind_version

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/molecules/groups/{group_id}/score-observations".format(
            group_id=quote(str(group_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Problem | ScoreObservationPage:
    if response.status_code == 200:
        response_200 = ScoreObservationPage.from_dict(response.json())

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

    if response.status_code == 503:
        response_503 = Problem.from_dict(response.json())

        return response_503

    response_default = Problem.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[Problem | ScoreObservationPage]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    group_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    body: ScoreObservationQuery,
    tamarind_version: str | Unset = UNSET,
) -> Response[Problem | ScoreObservationPage]:
    """List Group Score Observations

     List retained seed/sample observations for explicit concrete jobs in this group.

    Every requested job must be visible, concrete, eligible, terminally complete,
    and output-ingested. Every item carries its actual producing `jobId` and `jobName`.

    This is an advanced, read-only API. It returns observations in bulk and does not change the
    ordinary molecule sheet response or any frontend UI.

    Args:
        group_id (UUID):
        tamarind_version (str | Unset):
        body (ScoreObservationQuery): One bounded, explicit concrete-job observation read.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Problem | ScoreObservationPage]
    """

    kwargs = _get_kwargs(
        group_id=group_id,
        body=body,
        tamarind_version=tamarind_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    group_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    body: ScoreObservationQuery,
    tamarind_version: str | Unset = UNSET,
) -> Problem | ScoreObservationPage | None:
    """List Group Score Observations

     List retained seed/sample observations for explicit concrete jobs in this group.

    Every requested job must be visible, concrete, eligible, terminally complete,
    and output-ingested. Every item carries its actual producing `jobId` and `jobName`.

    This is an advanced, read-only API. It returns observations in bulk and does not change the
    ordinary molecule sheet response or any frontend UI.

    Args:
        group_id (UUID):
        tamarind_version (str | Unset):
        body (ScoreObservationQuery): One bounded, explicit concrete-job observation read.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Problem | ScoreObservationPage
    """

    return sync_detailed(
        group_id=group_id,
        client=client,
        body=body,
        tamarind_version=tamarind_version,
    ).parsed


async def asyncio_detailed(
    group_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    body: ScoreObservationQuery,
    tamarind_version: str | Unset = UNSET,
) -> Response[Problem | ScoreObservationPage]:
    """List Group Score Observations

     List retained seed/sample observations for explicit concrete jobs in this group.

    Every requested job must be visible, concrete, eligible, terminally complete,
    and output-ingested. Every item carries its actual producing `jobId` and `jobName`.

    This is an advanced, read-only API. It returns observations in bulk and does not change the
    ordinary molecule sheet response or any frontend UI.

    Args:
        group_id (UUID):
        tamarind_version (str | Unset):
        body (ScoreObservationQuery): One bounded, explicit concrete-job observation read.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Problem | ScoreObservationPage]
    """

    kwargs = _get_kwargs(
        group_id=group_id,
        body=body,
        tamarind_version=tamarind_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    group_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    body: ScoreObservationQuery,
    tamarind_version: str | Unset = UNSET,
) -> Problem | ScoreObservationPage | None:
    """List Group Score Observations

     List retained seed/sample observations for explicit concrete jobs in this group.

    Every requested job must be visible, concrete, eligible, terminally complete,
    and output-ingested. Every item carries its actual producing `jobId` and `jobName`.

    This is an advanced, read-only API. It returns observations in bulk and does not change the
    ordinary molecule sheet response or any frontend UI.

    Args:
        group_id (UUID):
        tamarind_version (str | Unset):
        body (ScoreObservationQuery): One bounded, explicit concrete-job observation read.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Problem | ScoreObservationPage
    """

    return (
        await asyncio_detailed(
            group_id=group_id,
            client=client,
            body=body,
            tamarind_version=tamarind_version,
        )
    ).parsed
