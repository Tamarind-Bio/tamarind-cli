from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.batch import Batch
from ...models.job import Job
from ...models.pipeline_run_item import PipelineRunItem
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
        "method": "get",
        "url": "/jobs/{job_id}".format(
            job_id=quote(str(job_id), safe=""),
        ),
    }

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
    tamarind_version: str | Unset = UNSET,
) -> Response[Batch | Job | PipelineRunItem | Problem]:
    """Get a job, a batch or a pipeline run

     Takes a `job_`, `batch_` or `run_` id and answers with that item; `kind` says which. A job
    comes with `settings`; a batch with its `counts`; a pipeline run with `counts` of its steps
    and `jobCounts` of the jobs they launched, read at most 60 seconds ago (its steps and
    molecules are under `/pipelines/runs/{runId}`). A job a run's step launched is readable here
    too, though only `pipelineRunId=` lists it. A single-tool run's `run_` id answers its job, the
    item the list shows for it (`kind` `job`, with its `job_` id). Anything you can't read is the
    same 404 as an id that doesn't exist: someone else's item, a deleted one, a malformed id or a
    wrong prefix, and for a run also an archived run, a run with no start time, and a benchmark
    run.

    Args:
        job_id (str):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Batch | Job | PipelineRunItem | Problem]
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
) -> Batch | Job | PipelineRunItem | Problem | None:
    """Get a job, a batch or a pipeline run

     Takes a `job_`, `batch_` or `run_` id and answers with that item; `kind` says which. A job
    comes with `settings`; a batch with its `counts`; a pipeline run with `counts` of its steps
    and `jobCounts` of the jobs they launched, read at most 60 seconds ago (its steps and
    molecules are under `/pipelines/runs/{runId}`). A job a run's step launched is readable here
    too, though only `pipelineRunId=` lists it. A single-tool run's `run_` id answers its job, the
    item the list shows for it (`kind` `job`, with its `job_` id). Anything you can't read is the
    same 404 as an id that doesn't exist: someone else's item, a deleted one, a malformed id or a
    wrong prefix, and for a run also an archived run, a run with no start time, and a benchmark
    run.

    Args:
        job_id (str):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Batch | Job | PipelineRunItem | Problem
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
) -> Response[Batch | Job | PipelineRunItem | Problem]:
    """Get a job, a batch or a pipeline run

     Takes a `job_`, `batch_` or `run_` id and answers with that item; `kind` says which. A job
    comes with `settings`; a batch with its `counts`; a pipeline run with `counts` of its steps
    and `jobCounts` of the jobs they launched, read at most 60 seconds ago (its steps and
    molecules are under `/pipelines/runs/{runId}`). A job a run's step launched is readable here
    too, though only `pipelineRunId=` lists it. A single-tool run's `run_` id answers its job, the
    item the list shows for it (`kind` `job`, with its `job_` id). Anything you can't read is the
    same 404 as an id that doesn't exist: someone else's item, a deleted one, a malformed id or a
    wrong prefix, and for a run also an archived run, a run with no start time, and a benchmark
    run.

    Args:
        job_id (str):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Batch | Job | PipelineRunItem | Problem]
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
) -> Batch | Job | PipelineRunItem | Problem | None:
    """Get a job, a batch or a pipeline run

     Takes a `job_`, `batch_` or `run_` id and answers with that item; `kind` says which. A job
    comes with `settings`; a batch with its `counts`; a pipeline run with `counts` of its steps
    and `jobCounts` of the jobs they launched, read at most 60 seconds ago (its steps and
    molecules are under `/pipelines/runs/{runId}`). A job a run's step launched is readable here
    too, though only `pipelineRunId=` lists it. A single-tool run's `run_` id answers its job, the
    item the list shows for it (`kind` `job`, with its `job_` id). Anything you can't read is the
    same 404 as an id that doesn't exist: someone else's item, a deleted one, a malformed id or a
    wrong prefix, and for a run also an archived run, a run with no start time, and a benchmark
    run.

    Args:
        job_id (str):
        tamarind_version (str | Unset):

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
            tamarind_version=tamarind_version,
        )
    ).parsed
