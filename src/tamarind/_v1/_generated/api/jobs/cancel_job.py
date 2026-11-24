from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.batch import Batch
from ...models.cancel_job_body import CancelJobBody
from ...models.job import Job
from ...models.pipeline_run_item import PipelineRunItem
from ...models.problem import Problem
from ...types import UNSET, Response, Unset


def _get_kwargs(
    job_id: str,
    *,
    body: CancelJobBody | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(tamarind_version, Unset):
        headers["Tamarind-Version"] = tamarind_version

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/jobs/{job_id}/cancel".format(
            job_id=quote(str(job_id), safe=""),
        ),
    }

    if not isinstance(body, Unset):
        _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Batch | Job | PipelineRunItem | Problem:
    if response.status_code == 200:

        def _parse_response_200(data: object) -> Batch | Job | PipelineRunItem:
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                response_200_type_0 = Job.from_dict(data)

                return response_200_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                response_200_type_1 = Batch.from_dict(data)

                return response_200_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            if not isinstance(data, dict):
                raise TypeError()
            response_200_type_2 = PipelineRunItem.from_dict(data)

            return response_200_type_2

        response_200 = _parse_response_200(response.json())

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
) -> Response[Batch | Job | PipelineRunItem | Problem]:
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
    body: CancelJobBody | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Response[Batch | Job | PipelineRunItem | Problem]:
    """Stop an unfinished job, batch or pipeline run and keep its outputs

     Takes a `job_`, `batch_` or `run_` id. A batch stops every unfinished job in it; a run stops
    its unfinished steps, through the same cancel as `cancelPipelineRun`. A single-tool run's
    `run_` id stops that run and answers its job, as `getJob` does. Safe to repeat: canceling
    something already `Stopped` with `stopReason.kind` `canceled` returns it (a batch or a run is
    swept again for anything still running). Anything else that has finished (`Complete`,
    `Stopped` or `Failed`) is 409 `job_already_finished`. Also stops any child work it started.

    If some of a batch's jobs couldn't be stopped, the answer is 503 `service_unavailable`
    (retryable), and canceling again stops the rest. If a run stopped but stopping its jobs
    wasn't confirmed, or the pipeline engine didn't answer, the answer is 502
    `upstream_unavailable`; cancel again. A `reason` on a pipeline run or a tool run is 422 at
    `/reason`, because the run has nowhere to keep it.

    Another member's job follows today's API (decision 74): only in an organization that doesn't
    share within itself, for its live admin's own key, or for a key the job is shared with, and
    only while the job's owner is on the organization's roster. A refusal of a job you can read is
    403 `forbidden`, otherwise 404. On another member's job, the answer's `settings` is `{}` and
    `modelId` null. Another member's batch, wrapper or tool run stays theirs. A roster that can't
    be read is 503 `jobs_dependency_unavailable`, retryable.

    Args:
        job_id (str):
        tamarind_version (str | Unset):
        body (CancelJobBody | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Batch | Job | PipelineRunItem | Problem]
    """

    kwargs = _get_kwargs(
        job_id=job_id,
        body=body,
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
    body: CancelJobBody | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Batch | Job | PipelineRunItem | Problem | None:
    """Stop an unfinished job, batch or pipeline run and keep its outputs

     Takes a `job_`, `batch_` or `run_` id. A batch stops every unfinished job in it; a run stops
    its unfinished steps, through the same cancel as `cancelPipelineRun`. A single-tool run's
    `run_` id stops that run and answers its job, as `getJob` does. Safe to repeat: canceling
    something already `Stopped` with `stopReason.kind` `canceled` returns it (a batch or a run is
    swept again for anything still running). Anything else that has finished (`Complete`,
    `Stopped` or `Failed`) is 409 `job_already_finished`. Also stops any child work it started.

    If some of a batch's jobs couldn't be stopped, the answer is 503 `service_unavailable`
    (retryable), and canceling again stops the rest. If a run stopped but stopping its jobs
    wasn't confirmed, or the pipeline engine didn't answer, the answer is 502
    `upstream_unavailable`; cancel again. A `reason` on a pipeline run or a tool run is 422 at
    `/reason`, because the run has nowhere to keep it.

    Another member's job follows today's API (decision 74): only in an organization that doesn't
    share within itself, for its live admin's own key, or for a key the job is shared with, and
    only while the job's owner is on the organization's roster. A refusal of a job you can read is
    403 `forbidden`, otherwise 404. On another member's job, the answer's `settings` is `{}` and
    `modelId` null. Another member's batch, wrapper or tool run stays theirs. A roster that can't
    be read is 503 `jobs_dependency_unavailable`, retryable.

    Args:
        job_id (str):
        tamarind_version (str | Unset):
        body (CancelJobBody | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Batch | Job | PipelineRunItem | Problem
    """

    return sync_detailed(
        job_id=job_id,
        client=client,
        body=body,
        tamarind_version=tamarind_version,
    ).parsed


async def asyncio_detailed(
    job_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: CancelJobBody | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Response[Batch | Job | PipelineRunItem | Problem]:
    """Stop an unfinished job, batch or pipeline run and keep its outputs

     Takes a `job_`, `batch_` or `run_` id. A batch stops every unfinished job in it; a run stops
    its unfinished steps, through the same cancel as `cancelPipelineRun`. A single-tool run's
    `run_` id stops that run and answers its job, as `getJob` does. Safe to repeat: canceling
    something already `Stopped` with `stopReason.kind` `canceled` returns it (a batch or a run is
    swept again for anything still running). Anything else that has finished (`Complete`,
    `Stopped` or `Failed`) is 409 `job_already_finished`. Also stops any child work it started.

    If some of a batch's jobs couldn't be stopped, the answer is 503 `service_unavailable`
    (retryable), and canceling again stops the rest. If a run stopped but stopping its jobs
    wasn't confirmed, or the pipeline engine didn't answer, the answer is 502
    `upstream_unavailable`; cancel again. A `reason` on a pipeline run or a tool run is 422 at
    `/reason`, because the run has nowhere to keep it.

    Another member's job follows today's API (decision 74): only in an organization that doesn't
    share within itself, for its live admin's own key, or for a key the job is shared with, and
    only while the job's owner is on the organization's roster. A refusal of a job you can read is
    403 `forbidden`, otherwise 404. On another member's job, the answer's `settings` is `{}` and
    `modelId` null. Another member's batch, wrapper or tool run stays theirs. A roster that can't
    be read is 503 `jobs_dependency_unavailable`, retryable.

    Args:
        job_id (str):
        tamarind_version (str | Unset):
        body (CancelJobBody | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Batch | Job | PipelineRunItem | Problem]
    """

    kwargs = _get_kwargs(
        job_id=job_id,
        body=body,
        tamarind_version=tamarind_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    job_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: CancelJobBody | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Batch | Job | PipelineRunItem | Problem | None:
    """Stop an unfinished job, batch or pipeline run and keep its outputs

     Takes a `job_`, `batch_` or `run_` id. A batch stops every unfinished job in it; a run stops
    its unfinished steps, through the same cancel as `cancelPipelineRun`. A single-tool run's
    `run_` id stops that run and answers its job, as `getJob` does. Safe to repeat: canceling
    something already `Stopped` with `stopReason.kind` `canceled` returns it (a batch or a run is
    swept again for anything still running). Anything else that has finished (`Complete`,
    `Stopped` or `Failed`) is 409 `job_already_finished`. Also stops any child work it started.

    If some of a batch's jobs couldn't be stopped, the answer is 503 `service_unavailable`
    (retryable), and canceling again stops the rest. If a run stopped but stopping its jobs
    wasn't confirmed, or the pipeline engine didn't answer, the answer is 502
    `upstream_unavailable`; cancel again. A `reason` on a pipeline run or a tool run is 422 at
    `/reason`, because the run has nowhere to keep it.

    Another member's job follows today's API (decision 74): only in an organization that doesn't
    share within itself, for its live admin's own key, or for a key the job is shared with, and
    only while the job's owner is on the organization's roster. A refusal of a job you can read is
    403 `forbidden`, otherwise 404. On another member's job, the answer's `settings` is `{}` and
    `modelId` null. Another member's batch, wrapper or tool run stays theirs. A roster that can't
    be read is 503 `jobs_dependency_unavailable`, retryable.

    Args:
        job_id (str):
        tamarind_version (str | Unset):
        body (CancelJobBody | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Batch | Job | PipelineRunItem | Problem
    """

    return (
        await asyncio_detailed(
            job_id=job_id,
            client=client,
            body=body,
            tamarind_version=tamarind_version,
        )
    ).parsed
