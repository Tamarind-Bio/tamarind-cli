from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.problem import Problem
from ...types import UNSET, Response, Unset


def _get_kwargs(
    job_id: str,
    *,
    tamarind_version: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(tamarind_version, Unset):
        headers["Tamarind-Version"] = tamarind_version

    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": "/jobs/{job_id}".format(
            job_id=quote(str(job_id), safe=""),
        ),
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Any | Problem:
    if response.status_code == 204:
        response_204 = cast(Any, None)
        return response_204

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
) -> Response[Any | Problem]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    job_id: str,
    *,
    client: AuthenticatedClient | Client,
    tamarind_version: str | Unset = UNSET,
) -> Response[Any | Problem]:
    """Delete a job, a batch or a pipeline run's job row

     Takes a `job_`, `batch_` or `run_` id. This is the app's Delete button: the job,
    or a batch with every job in it, is marked deleted and reads as 404 everywhere from then on,
    so deleting it again is 404 too. Its outputs stay in storage. A tool run that is still running
    is stopped first; if stopping its jobs isn't confirmed, the answer is 502
    `upstream_unavailable` and nothing is deleted yet, so delete again.

    A batch's jobs go first and the batch last, so a partial failure leaves the batch in place
    with 503 `service_unavailable`, and repeating the call finishes it. Deleting a batch's jobs one
    by one until none is left stops the batch. A tool run submitted less than 15 minutes ago,
    whose run can't be reached yet, is 409 `job_still_starting` with `Retry-After: 60`.

    A `run_` id does what today's `DELETE /delete-job` does
    for a name only a pipeline run has. It deletes the run's row in the jobs table, the one the
    app's Results list shows, so deleting it again is 404. The run isn't stopped or archived, its
    jobs stay, and `getJob`, `listJobs` and `listPipelineRuns` still show it; the run's own
    Archive in the app removes it from those. `getPipelineRunResults`, which finds the run through
    that row, is 404 from then on. Someone else's run, and a run with no such row, are 404. A
    single-tool run has no such row: it's listed as its job, so delete the `job_` id.

    Args:
        job_id (str):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | Problem]
    """

    kwargs = _get_kwargs(
        job_id=job_id,
        tamarind_version=tamarind_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    job_id: str,
    *,
    client: AuthenticatedClient | Client,
    tamarind_version: str | Unset = UNSET,
) -> Any | Problem | None:
    """Delete a job, a batch or a pipeline run's job row

     Takes a `job_`, `batch_` or `run_` id. This is the app's Delete button: the job,
    or a batch with every job in it, is marked deleted and reads as 404 everywhere from then on,
    so deleting it again is 404 too. Its outputs stay in storage. A tool run that is still running
    is stopped first; if stopping its jobs isn't confirmed, the answer is 502
    `upstream_unavailable` and nothing is deleted yet, so delete again.

    A batch's jobs go first and the batch last, so a partial failure leaves the batch in place
    with 503 `service_unavailable`, and repeating the call finishes it. Deleting a batch's jobs one
    by one until none is left stops the batch. A tool run submitted less than 15 minutes ago,
    whose run can't be reached yet, is 409 `job_still_starting` with `Retry-After: 60`.

    A `run_` id does what today's `DELETE /delete-job` does
    for a name only a pipeline run has. It deletes the run's row in the jobs table, the one the
    app's Results list shows, so deleting it again is 404. The run isn't stopped or archived, its
    jobs stay, and `getJob`, `listJobs` and `listPipelineRuns` still show it; the run's own
    Archive in the app removes it from those. `getPipelineRunResults`, which finds the run through
    that row, is 404 from then on. Someone else's run, and a run with no such row, are 404. A
    single-tool run has no such row: it's listed as its job, so delete the `job_` id.

    Args:
        job_id (str):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | Problem
    """

    return sync_detailed(
        job_id=job_id,
        client=client,
        tamarind_version=tamarind_version,
    ).parsed


async def asyncio_detailed(
    job_id: str,
    *,
    client: AuthenticatedClient | Client,
    tamarind_version: str | Unset = UNSET,
) -> Response[Any | Problem]:
    """Delete a job, a batch or a pipeline run's job row

     Takes a `job_`, `batch_` or `run_` id. This is the app's Delete button: the job,
    or a batch with every job in it, is marked deleted and reads as 404 everywhere from then on,
    so deleting it again is 404 too. Its outputs stay in storage. A tool run that is still running
    is stopped first; if stopping its jobs isn't confirmed, the answer is 502
    `upstream_unavailable` and nothing is deleted yet, so delete again.

    A batch's jobs go first and the batch last, so a partial failure leaves the batch in place
    with 503 `service_unavailable`, and repeating the call finishes it. Deleting a batch's jobs one
    by one until none is left stops the batch. A tool run submitted less than 15 minutes ago,
    whose run can't be reached yet, is 409 `job_still_starting` with `Retry-After: 60`.

    A `run_` id does what today's `DELETE /delete-job` does
    for a name only a pipeline run has. It deletes the run's row in the jobs table, the one the
    app's Results list shows, so deleting it again is 404. The run isn't stopped or archived, its
    jobs stay, and `getJob`, `listJobs` and `listPipelineRuns` still show it; the run's own
    Archive in the app removes it from those. `getPipelineRunResults`, which finds the run through
    that row, is 404 from then on. Someone else's run, and a run with no such row, are 404. A
    single-tool run has no such row: it's listed as its job, so delete the `job_` id.

    Args:
        job_id (str):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | Problem]
    """

    kwargs = _get_kwargs(
        job_id=job_id,
        tamarind_version=tamarind_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    job_id: str,
    *,
    client: AuthenticatedClient | Client,
    tamarind_version: str | Unset = UNSET,
) -> Any | Problem | None:
    """Delete a job, a batch or a pipeline run's job row

     Takes a `job_`, `batch_` or `run_` id. This is the app's Delete button: the job,
    or a batch with every job in it, is marked deleted and reads as 404 everywhere from then on,
    so deleting it again is 404 too. Its outputs stay in storage. A tool run that is still running
    is stopped first; if stopping its jobs isn't confirmed, the answer is 502
    `upstream_unavailable` and nothing is deleted yet, so delete again.

    A batch's jobs go first and the batch last, so a partial failure leaves the batch in place
    with 503 `service_unavailable`, and repeating the call finishes it. Deleting a batch's jobs one
    by one until none is left stops the batch. A tool run submitted less than 15 minutes ago,
    whose run can't be reached yet, is 409 `job_still_starting` with `Retry-After: 60`.

    A `run_` id does what today's `DELETE /delete-job` does
    for a name only a pipeline run has. It deletes the run's row in the jobs table, the one the
    app's Results list shows, so deleting it again is 404. The run isn't stopped or archived, its
    jobs stay, and `getJob`, `listJobs` and `listPipelineRuns` still show it; the run's own
    Archive in the app removes it from those. `getPipelineRunResults`, which finds the run through
    that row, is 404 from then on. Someone else's run, and a run with no such row, are 404. A
    single-tool run has no such row: it's listed as its job, so delete the `job_` id.

    Args:
        job_id (str):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | Problem
    """

    return (
        await asyncio_detailed(
            job_id=job_id,
            client=client,
            tamarind_version=tamarind_version,
        )
    ).parsed
