from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.batch import Batch
from ...models.job import Job
from ...models.problem import Problem
from ...models.rerun_job_body import RerunJobBody
from ...types import UNSET, Response, Unset


def _get_kwargs(
    job_id: str,
    *,
    body: RerunJobBody | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(tamarind_version, Unset):
        headers["Tamarind-Version"] = tamarind_version

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/jobs/{job_id}/rerun".format(
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
) -> Batch | Job | Problem:
    if response.status_code == 200:

        def _parse_response_200(data: object) -> Batch | Job:
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                response_200_type_0 = Job.from_dict(data)

                return response_200_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            if not isinstance(data, dict):
                raise TypeError()
            response_200_type_1 = Batch.from_dict(data)

            return response_200_type_1

        response_200 = _parse_response_200(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = Problem.from_dict(response.json())

        return response_400

    if response.status_code == 401:
        response_401 = Problem.from_dict(response.json())

        return response_401

    if response.status_code == 402:
        response_402 = Problem.from_dict(response.json())

        return response_402

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
) -> Response[Batch | Job | Problem]:
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
    body: RerunJobBody | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Response[Batch | Job | Problem]:
    """Run a finished job, or a finished batch's jobs, again in place

     Puts a finished job back in the queue as the same job, as the app's Rerun does: the same id,
    tool, settings and project, and its earlier outputs are overwritten as it runs. Takes a `job_`
    or `batch_` id; a `run_` id is 404. Answers 200 with the job back `In Queue`; poll it with
    `getJob` as usual.

    A batch reruns its jobs, as the batch page's Rerun All Jobs and Rerun Only Incomplete Jobs do:
    `only: all` (the default) reruns every job, and `only: incomplete` every job that isn't
    `Complete`. It answers 200 with the batch. A design batch's parent reruns itself. On a job id,
    `only` other than `all` is 422 `not_supported` at `/only`.

    Nothing is overridden: the body takes only `only` (any other field is 422), the job keeps its
    name, and no new job is created, so there's no `rerunOf`. There's no `Idempotency-Key`:
    repeating a rerun finds the job queued and is 409 `job_not_finished`. The checks a submit makes
    run again, for the job's owner as things are now, before anything is written:

    - 403 `forbidden`: only Premium accounts can rerun, as in the app. Submit it again instead.
    - 409 `job_not_finished` (retryable): the job hasn't finished (`Complete` or `Stopped`; a
      pipeline step's job only once `Stopped`), or a batch still has a job queued or running.
    - 422 `not_supported`: a batch of pipeline jobs (rerun its pipeline run instead), a pipeline
      step's job whose retry record is incomplete, or a deployment that can't queue the job.
    - 403 `organization_compute_disabled`: your organization can't start compute.
    - 403 `tool_not_available`: the owner can no longer run the job's tool: it's gone from the
      catalog or its access, organization or team policy changed, its licence (Rosetta, Bindome) is
      missing, or a custom tool's pinned version can't run.
    - 409 `tool_lifetime_changed`: a custom tool was deleted and re-created under its name since
      the job ran, or the job is older than custom tool lifetimes, so that can't be ruled out.
      Submit it again.
    - 422 `validation_failed`: a low-priority job when the tier is no longer on for you
      (`not_enabled`); a stored `parentModelId` or inference model you can no longer use
      (`invalid_option` at `/settings/parentModelId` or `/settings/model`); a molecule or file in
      its settings you can no longer read (`not_owned` at its `/settings` field).
    - 429 `queue_full` and 402 `budget_exceeded`: the queue limit and your budgets, counted over
      every job the rerun puts back.
    - 409 `inputs_still_ingesting`: its molecule inputs are still being ingested; it runs on its
      own once they are. 409 `inputs_not_ingested`: they failed to ingest, or it was stopped while
      they were held, so it can't be rerun in place: submit it again.
    - 409 `nothing_to_rerun`: a batch with no job to rerun (with `only: incomplete`, every job is
      `Complete`).
    - 503 `service_unavailable` (retryable): the job was put back but couldn't be handed to the
      queue. It stays `In Queue`, and asking again sends it. 503 `organization_access_unavailable`
      or `jobs_dependency_unavailable` (retryable): something it checks couldn't be read.
    - 502 `upstream_error`: a pipeline step's job whose run was reopened but whose rerun couldn't
      be confirmed. Read the job before asking again.

    A batch reruns every job it can. Jobs whose inputs are still held are left to run on their own.
    If some jobs couldn't be rerun (inputs never ingested, or a job that changed or couldn't be
    queued), the rest still rerun and the answer is 409 `rerun_incomplete`, naming each job missed
    in `errors` (code `not_rerun`, at most 50); rerun each with this operation. A very large batch
    (tens of thousands of jobs) can take longer than the gateway waits, so the request may time out
    while the rerun goes on. Nothing is lost: read the batch with `getJob` before asking again.

    Args:
        job_id (str):
        tamarind_version (str | Unset):
        body (RerunJobBody | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Batch | Job | Problem]
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
    body: RerunJobBody | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Batch | Job | Problem | None:
    """Run a finished job, or a finished batch's jobs, again in place

     Puts a finished job back in the queue as the same job, as the app's Rerun does: the same id,
    tool, settings and project, and its earlier outputs are overwritten as it runs. Takes a `job_`
    or `batch_` id; a `run_` id is 404. Answers 200 with the job back `In Queue`; poll it with
    `getJob` as usual.

    A batch reruns its jobs, as the batch page's Rerun All Jobs and Rerun Only Incomplete Jobs do:
    `only: all` (the default) reruns every job, and `only: incomplete` every job that isn't
    `Complete`. It answers 200 with the batch. A design batch's parent reruns itself. On a job id,
    `only` other than `all` is 422 `not_supported` at `/only`.

    Nothing is overridden: the body takes only `only` (any other field is 422), the job keeps its
    name, and no new job is created, so there's no `rerunOf`. There's no `Idempotency-Key`:
    repeating a rerun finds the job queued and is 409 `job_not_finished`. The checks a submit makes
    run again, for the job's owner as things are now, before anything is written:

    - 403 `forbidden`: only Premium accounts can rerun, as in the app. Submit it again instead.
    - 409 `job_not_finished` (retryable): the job hasn't finished (`Complete` or `Stopped`; a
      pipeline step's job only once `Stopped`), or a batch still has a job queued or running.
    - 422 `not_supported`: a batch of pipeline jobs (rerun its pipeline run instead), a pipeline
      step's job whose retry record is incomplete, or a deployment that can't queue the job.
    - 403 `organization_compute_disabled`: your organization can't start compute.
    - 403 `tool_not_available`: the owner can no longer run the job's tool: it's gone from the
      catalog or its access, organization or team policy changed, its licence (Rosetta, Bindome) is
      missing, or a custom tool's pinned version can't run.
    - 409 `tool_lifetime_changed`: a custom tool was deleted and re-created under its name since
      the job ran, or the job is older than custom tool lifetimes, so that can't be ruled out.
      Submit it again.
    - 422 `validation_failed`: a low-priority job when the tier is no longer on for you
      (`not_enabled`); a stored `parentModelId` or inference model you can no longer use
      (`invalid_option` at `/settings/parentModelId` or `/settings/model`); a molecule or file in
      its settings you can no longer read (`not_owned` at its `/settings` field).
    - 429 `queue_full` and 402 `budget_exceeded`: the queue limit and your budgets, counted over
      every job the rerun puts back.
    - 409 `inputs_still_ingesting`: its molecule inputs are still being ingested; it runs on its
      own once they are. 409 `inputs_not_ingested`: they failed to ingest, or it was stopped while
      they were held, so it can't be rerun in place: submit it again.
    - 409 `nothing_to_rerun`: a batch with no job to rerun (with `only: incomplete`, every job is
      `Complete`).
    - 503 `service_unavailable` (retryable): the job was put back but couldn't be handed to the
      queue. It stays `In Queue`, and asking again sends it. 503 `organization_access_unavailable`
      or `jobs_dependency_unavailable` (retryable): something it checks couldn't be read.
    - 502 `upstream_error`: a pipeline step's job whose run was reopened but whose rerun couldn't
      be confirmed. Read the job before asking again.

    A batch reruns every job it can. Jobs whose inputs are still held are left to run on their own.
    If some jobs couldn't be rerun (inputs never ingested, or a job that changed or couldn't be
    queued), the rest still rerun and the answer is 409 `rerun_incomplete`, naming each job missed
    in `errors` (code `not_rerun`, at most 50); rerun each with this operation. A very large batch
    (tens of thousands of jobs) can take longer than the gateway waits, so the request may time out
    while the rerun goes on. Nothing is lost: read the batch with `getJob` before asking again.

    Args:
        job_id (str):
        tamarind_version (str | Unset):
        body (RerunJobBody | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Batch | Job | Problem
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
    body: RerunJobBody | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Response[Batch | Job | Problem]:
    """Run a finished job, or a finished batch's jobs, again in place

     Puts a finished job back in the queue as the same job, as the app's Rerun does: the same id,
    tool, settings and project, and its earlier outputs are overwritten as it runs. Takes a `job_`
    or `batch_` id; a `run_` id is 404. Answers 200 with the job back `In Queue`; poll it with
    `getJob` as usual.

    A batch reruns its jobs, as the batch page's Rerun All Jobs and Rerun Only Incomplete Jobs do:
    `only: all` (the default) reruns every job, and `only: incomplete` every job that isn't
    `Complete`. It answers 200 with the batch. A design batch's parent reruns itself. On a job id,
    `only` other than `all` is 422 `not_supported` at `/only`.

    Nothing is overridden: the body takes only `only` (any other field is 422), the job keeps its
    name, and no new job is created, so there's no `rerunOf`. There's no `Idempotency-Key`:
    repeating a rerun finds the job queued and is 409 `job_not_finished`. The checks a submit makes
    run again, for the job's owner as things are now, before anything is written:

    - 403 `forbidden`: only Premium accounts can rerun, as in the app. Submit it again instead.
    - 409 `job_not_finished` (retryable): the job hasn't finished (`Complete` or `Stopped`; a
      pipeline step's job only once `Stopped`), or a batch still has a job queued or running.
    - 422 `not_supported`: a batch of pipeline jobs (rerun its pipeline run instead), a pipeline
      step's job whose retry record is incomplete, or a deployment that can't queue the job.
    - 403 `organization_compute_disabled`: your organization can't start compute.
    - 403 `tool_not_available`: the owner can no longer run the job's tool: it's gone from the
      catalog or its access, organization or team policy changed, its licence (Rosetta, Bindome) is
      missing, or a custom tool's pinned version can't run.
    - 409 `tool_lifetime_changed`: a custom tool was deleted and re-created under its name since
      the job ran, or the job is older than custom tool lifetimes, so that can't be ruled out.
      Submit it again.
    - 422 `validation_failed`: a low-priority job when the tier is no longer on for you
      (`not_enabled`); a stored `parentModelId` or inference model you can no longer use
      (`invalid_option` at `/settings/parentModelId` or `/settings/model`); a molecule or file in
      its settings you can no longer read (`not_owned` at its `/settings` field).
    - 429 `queue_full` and 402 `budget_exceeded`: the queue limit and your budgets, counted over
      every job the rerun puts back.
    - 409 `inputs_still_ingesting`: its molecule inputs are still being ingested; it runs on its
      own once they are. 409 `inputs_not_ingested`: they failed to ingest, or it was stopped while
      they were held, so it can't be rerun in place: submit it again.
    - 409 `nothing_to_rerun`: a batch with no job to rerun (with `only: incomplete`, every job is
      `Complete`).
    - 503 `service_unavailable` (retryable): the job was put back but couldn't be handed to the
      queue. It stays `In Queue`, and asking again sends it. 503 `organization_access_unavailable`
      or `jobs_dependency_unavailable` (retryable): something it checks couldn't be read.
    - 502 `upstream_error`: a pipeline step's job whose run was reopened but whose rerun couldn't
      be confirmed. Read the job before asking again.

    A batch reruns every job it can. Jobs whose inputs are still held are left to run on their own.
    If some jobs couldn't be rerun (inputs never ingested, or a job that changed or couldn't be
    queued), the rest still rerun and the answer is 409 `rerun_incomplete`, naming each job missed
    in `errors` (code `not_rerun`, at most 50); rerun each with this operation. A very large batch
    (tens of thousands of jobs) can take longer than the gateway waits, so the request may time out
    while the rerun goes on. Nothing is lost: read the batch with `getJob` before asking again.

    Args:
        job_id (str):
        tamarind_version (str | Unset):
        body (RerunJobBody | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Batch | Job | Problem]
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
    body: RerunJobBody | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Batch | Job | Problem | None:
    """Run a finished job, or a finished batch's jobs, again in place

     Puts a finished job back in the queue as the same job, as the app's Rerun does: the same id,
    tool, settings and project, and its earlier outputs are overwritten as it runs. Takes a `job_`
    or `batch_` id; a `run_` id is 404. Answers 200 with the job back `In Queue`; poll it with
    `getJob` as usual.

    A batch reruns its jobs, as the batch page's Rerun All Jobs and Rerun Only Incomplete Jobs do:
    `only: all` (the default) reruns every job, and `only: incomplete` every job that isn't
    `Complete`. It answers 200 with the batch. A design batch's parent reruns itself. On a job id,
    `only` other than `all` is 422 `not_supported` at `/only`.

    Nothing is overridden: the body takes only `only` (any other field is 422), the job keeps its
    name, and no new job is created, so there's no `rerunOf`. There's no `Idempotency-Key`:
    repeating a rerun finds the job queued and is 409 `job_not_finished`. The checks a submit makes
    run again, for the job's owner as things are now, before anything is written:

    - 403 `forbidden`: only Premium accounts can rerun, as in the app. Submit it again instead.
    - 409 `job_not_finished` (retryable): the job hasn't finished (`Complete` or `Stopped`; a
      pipeline step's job only once `Stopped`), or a batch still has a job queued or running.
    - 422 `not_supported`: a batch of pipeline jobs (rerun its pipeline run instead), a pipeline
      step's job whose retry record is incomplete, or a deployment that can't queue the job.
    - 403 `organization_compute_disabled`: your organization can't start compute.
    - 403 `tool_not_available`: the owner can no longer run the job's tool: it's gone from the
      catalog or its access, organization or team policy changed, its licence (Rosetta, Bindome) is
      missing, or a custom tool's pinned version can't run.
    - 409 `tool_lifetime_changed`: a custom tool was deleted and re-created under its name since
      the job ran, or the job is older than custom tool lifetimes, so that can't be ruled out.
      Submit it again.
    - 422 `validation_failed`: a low-priority job when the tier is no longer on for you
      (`not_enabled`); a stored `parentModelId` or inference model you can no longer use
      (`invalid_option` at `/settings/parentModelId` or `/settings/model`); a molecule or file in
      its settings you can no longer read (`not_owned` at its `/settings` field).
    - 429 `queue_full` and 402 `budget_exceeded`: the queue limit and your budgets, counted over
      every job the rerun puts back.
    - 409 `inputs_still_ingesting`: its molecule inputs are still being ingested; it runs on its
      own once they are. 409 `inputs_not_ingested`: they failed to ingest, or it was stopped while
      they were held, so it can't be rerun in place: submit it again.
    - 409 `nothing_to_rerun`: a batch with no job to rerun (with `only: incomplete`, every job is
      `Complete`).
    - 503 `service_unavailable` (retryable): the job was put back but couldn't be handed to the
      queue. It stays `In Queue`, and asking again sends it. 503 `organization_access_unavailable`
      or `jobs_dependency_unavailable` (retryable): something it checks couldn't be read.
    - 502 `upstream_error`: a pipeline step's job whose run was reopened but whose rerun couldn't
      be confirmed. Read the job before asking again.

    A batch reruns every job it can. Jobs whose inputs are still held are left to run on their own.
    If some jobs couldn't be rerun (inputs never ingested, or a job that changed or couldn't be
    queued), the rest still rerun and the answer is 409 `rerun_incomplete`, naming each job missed
    in `errors` (code `not_rerun`, at most 50); rerun each with this operation. A very large batch
    (tens of thousands of jobs) can take longer than the gateway waits, so the request may time out
    while the rerun goes on. Nothing is lost: read the batch with `getJob` before asking again.

    Args:
        job_id (str):
        tamarind_version (str | Unset):
        body (RerunJobBody | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Batch | Job | Problem
    """

    return (
        await asyncio_detailed(
            job_id=job_id,
            client=client,
            body=body,
            tamarind_version=tamarind_version,
        )
    ).parsed
