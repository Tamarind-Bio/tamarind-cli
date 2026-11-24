from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.problem import Problem
from ...models.search_jobs_response_200 import SearchJobsResponse200
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    body: Any,
    tamarind_version: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(tamarind_version, Unset):
        headers["Tamarind-Version"] = tamarind_version

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/jobs/search",
    }

    _kwargs["json"] = body

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Problem | SearchJobsResponse200:
    if response.status_code == 200:
        response_200 = SearchJobsResponse200.from_dict(response.json())

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
) -> Response[Problem | SearchJobsResponse200]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: Any,
    tamarind_version: str | Unset = UNSET,
) -> Response[Problem | SearchJobsResponse200]:
    """Look up many jobs by name or id in one call

     For polling or fetching a set of jobs, batches and pipeline runs. Use this instead of many
    `getJob` calls. Up to 200 `ids` and 200 `names`. An id is looked up as `getJob` looks it up
    (`job_`, `batch_` or `run_`), and a name as `listJobs?name=` does: the newest job, batch or run
    with that name, jobs inside a batch included, and a job a
    pipeline run's step launched wherever `listJobs?name=` finds one. Items come back ids first,
    then names, each item
    once however many values found it. Values with no match are in `notFound`.

    With `includeSettings`, a job comes back as `Job`, and the request takes at most 50 distinct
    values and 4.3 MB of settings in all; past either it's 422 at `/includeSettings`. A name over
    2,048 bytes is 422 at `/names/{i}`. `scope: org` and another member's `createdBy` look up
    `names` among the jobs `listJobs?scope=org` shows you: `ids` and `includeSettings` are 422
    `not_supported` with them, another member's `createdBy` without `scope: org` is 422
    `needs_scope_org`, and a member whose jobs you can't see is 403 `forbidden`. The batches one
    request counts share one budget of 40,000 jobs; past it the answer is 503
    `jobs_dependency_unavailable`. A search of up to 4 values runs in the job-detail lane, four
    per account, as a `listJobs?name=` lookup does; a bigger one runs in the same lane as a
    `listJobs` page, so a second one from your account while the first runs is 429.

    Args:
        tamarind_version (str | Unset):
        body (Any):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Problem | SearchJobsResponse200]
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
    body: Any,
    tamarind_version: str | Unset = UNSET,
) -> Problem | SearchJobsResponse200 | None:
    """Look up many jobs by name or id in one call

     For polling or fetching a set of jobs, batches and pipeline runs. Use this instead of many
    `getJob` calls. Up to 200 `ids` and 200 `names`. An id is looked up as `getJob` looks it up
    (`job_`, `batch_` or `run_`), and a name as `listJobs?name=` does: the newest job, batch or run
    with that name, jobs inside a batch included, and a job a
    pipeline run's step launched wherever `listJobs?name=` finds one. Items come back ids first,
    then names, each item
    once however many values found it. Values with no match are in `notFound`.

    With `includeSettings`, a job comes back as `Job`, and the request takes at most 50 distinct
    values and 4.3 MB of settings in all; past either it's 422 at `/includeSettings`. A name over
    2,048 bytes is 422 at `/names/{i}`. `scope: org` and another member's `createdBy` look up
    `names` among the jobs `listJobs?scope=org` shows you: `ids` and `includeSettings` are 422
    `not_supported` with them, another member's `createdBy` without `scope: org` is 422
    `needs_scope_org`, and a member whose jobs you can't see is 403 `forbidden`. The batches one
    request counts share one budget of 40,000 jobs; past it the answer is 503
    `jobs_dependency_unavailable`. A search of up to 4 values runs in the job-detail lane, four
    per account, as a `listJobs?name=` lookup does; a bigger one runs in the same lane as a
    `listJobs` page, so a second one from your account while the first runs is 429.

    Args:
        tamarind_version (str | Unset):
        body (Any):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Problem | SearchJobsResponse200
    """

    return sync_detailed(
        client=client,
        body=body,
        tamarind_version=tamarind_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: Any,
    tamarind_version: str | Unset = UNSET,
) -> Response[Problem | SearchJobsResponse200]:
    """Look up many jobs by name or id in one call

     For polling or fetching a set of jobs, batches and pipeline runs. Use this instead of many
    `getJob` calls. Up to 200 `ids` and 200 `names`. An id is looked up as `getJob` looks it up
    (`job_`, `batch_` or `run_`), and a name as `listJobs?name=` does: the newest job, batch or run
    with that name, jobs inside a batch included, and a job a
    pipeline run's step launched wherever `listJobs?name=` finds one. Items come back ids first,
    then names, each item
    once however many values found it. Values with no match are in `notFound`.

    With `includeSettings`, a job comes back as `Job`, and the request takes at most 50 distinct
    values and 4.3 MB of settings in all; past either it's 422 at `/includeSettings`. A name over
    2,048 bytes is 422 at `/names/{i}`. `scope: org` and another member's `createdBy` look up
    `names` among the jobs `listJobs?scope=org` shows you: `ids` and `includeSettings` are 422
    `not_supported` with them, another member's `createdBy` without `scope: org` is 422
    `needs_scope_org`, and a member whose jobs you can't see is 403 `forbidden`. The batches one
    request counts share one budget of 40,000 jobs; past it the answer is 503
    `jobs_dependency_unavailable`. A search of up to 4 values runs in the job-detail lane, four
    per account, as a `listJobs?name=` lookup does; a bigger one runs in the same lane as a
    `listJobs` page, so a second one from your account while the first runs is 429.

    Args:
        tamarind_version (str | Unset):
        body (Any):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Problem | SearchJobsResponse200]
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
    body: Any,
    tamarind_version: str | Unset = UNSET,
) -> Problem | SearchJobsResponse200 | None:
    """Look up many jobs by name or id in one call

     For polling or fetching a set of jobs, batches and pipeline runs. Use this instead of many
    `getJob` calls. Up to 200 `ids` and 200 `names`. An id is looked up as `getJob` looks it up
    (`job_`, `batch_` or `run_`), and a name as `listJobs?name=` does: the newest job, batch or run
    with that name, jobs inside a batch included, and a job a
    pipeline run's step launched wherever `listJobs?name=` finds one. Items come back ids first,
    then names, each item
    once however many values found it. Values with no match are in `notFound`.

    With `includeSettings`, a job comes back as `Job`, and the request takes at most 50 distinct
    values and 4.3 MB of settings in all; past either it's 422 at `/includeSettings`. A name over
    2,048 bytes is 422 at `/names/{i}`. `scope: org` and another member's `createdBy` look up
    `names` among the jobs `listJobs?scope=org` shows you: `ids` and `includeSettings` are 422
    `not_supported` with them, another member's `createdBy` without `scope: org` is 422
    `needs_scope_org`, and a member whose jobs you can't see is 403 `forbidden`. The batches one
    request counts share one budget of 40,000 jobs; past it the answer is 503
    `jobs_dependency_unavailable`. A search of up to 4 values runs in the job-detail lane, four
    per account, as a `listJobs?name=` lookup does; a bigger one runs in the same lane as a
    `listJobs` page, so a second one from your account while the first runs is 429.

    Args:
        tamarind_version (str | Unset):
        body (Any):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Problem | SearchJobsResponse200
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            tamarind_version=tamarind_version,
        )
    ).parsed
