from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.estimate import Estimate
from ...models.problem import Problem
from ...models.submit_file_batch_request import SubmitFileBatchRequest
from ...models.submit_inline_batch_request import SubmitInlineBatchRequest
from ...models.submit_job_request import SubmitJobRequest
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    body: SubmitFileBatchRequest | SubmitInlineBatchRequest | SubmitJobRequest,
    tamarind_version: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(tamarind_version, Unset):
        headers["Tamarind-Version"] = tamarind_version

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/jobs/estimate",
    }

    if isinstance(body, SubmitJobRequest):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, SubmitInlineBatchRequest):
        _kwargs["json"] = body.to_dict()
    else:
        _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Estimate | Problem:
    if response.status_code == 200:
        response_200 = Estimate.from_dict(response.json())

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
) -> Response[Estimate | Problem]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: SubmitFileBatchRequest | SubmitInlineBatchRequest | SubmitJobRequest,
    tamarind_version: str | Unset = UNSET,
) -> Response[Estimate | Problem]:
    """Estimate a job's runtime and cost without running it

     Takes the same body as `submitJob`, for a job or a batch, and returns the runtime per job, the
    weighted hours and the job count that today's estimator computes for the submit budget gate,
    fan-out included. A batch, inline or from a `source` file (read now, as on submit), is priced
    from its first 500 rows and scaled to its full row count, with a note saying so; more than
    30,000 rows is 422 `out_of_range`. Settings that can't be priced, such as a numeric field that
    isn't a finite number, are 422 `invalid_type` at `/settings`. With `lowPriority: true`,
    `weightedHours` is the low-priority price, and a caller or job that can't have the tier gets
    the same 422 error at `/lowPriority` as `submitJob`, so a quote is never at a price the submit
    would refuse.

    It prices one tool's current deployment from the settings alone, so `modelId`, `toolVersion`,
    `toolLifetimeEtag` and typed `inputs` are 422 `not_supported` at their field. A file setting
    that names a job's output under the job's name is priced at the tool's default input size,
    so send the job file's `ref` for a closer quote. A tool that runs
    as a pipeline behind the scenes (such as BinderScout) is priced as its whole pipeline, by the
    estimator `estimatePipeline` uses, after the same checks `validateJob` makes: `jobCount` counts
    every step's jobs, `perJobRuntimeSeconds` is null because the steps run different tools, and
    `notes` say how many tool steps it was priced as (and, when pricing failed, that it did, with
    `weightedHours` null). A batch of such a tool is 422 `not_supported` at `/tool`. A `tool` name
    longer than 64 characters is 422 `invalid_length` at `/tool`.
    A tool hidden from you is 404 `tool_not_found` and one you can't run is 403
    `tool_not_available`, as on submit. An unknown `projectId` is 422 at `/projectId`, as on
    submit. It doesn't check whether a name is taken, budgets, quotas or the queue: `validateJob`
    does.

    Args:
        tamarind_version (str | Unset):
        body (SubmitFileBatchRequest | SubmitInlineBatchRequest | SubmitJobRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Estimate | Problem]
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
    body: SubmitFileBatchRequest | SubmitInlineBatchRequest | SubmitJobRequest,
    tamarind_version: str | Unset = UNSET,
) -> Estimate | Problem | None:
    """Estimate a job's runtime and cost without running it

     Takes the same body as `submitJob`, for a job or a batch, and returns the runtime per job, the
    weighted hours and the job count that today's estimator computes for the submit budget gate,
    fan-out included. A batch, inline or from a `source` file (read now, as on submit), is priced
    from its first 500 rows and scaled to its full row count, with a note saying so; more than
    30,000 rows is 422 `out_of_range`. Settings that can't be priced, such as a numeric field that
    isn't a finite number, are 422 `invalid_type` at `/settings`. With `lowPriority: true`,
    `weightedHours` is the low-priority price, and a caller or job that can't have the tier gets
    the same 422 error at `/lowPriority` as `submitJob`, so a quote is never at a price the submit
    would refuse.

    It prices one tool's current deployment from the settings alone, so `modelId`, `toolVersion`,
    `toolLifetimeEtag` and typed `inputs` are 422 `not_supported` at their field. A file setting
    that names a job's output under the job's name is priced at the tool's default input size,
    so send the job file's `ref` for a closer quote. A tool that runs
    as a pipeline behind the scenes (such as BinderScout) is priced as its whole pipeline, by the
    estimator `estimatePipeline` uses, after the same checks `validateJob` makes: `jobCount` counts
    every step's jobs, `perJobRuntimeSeconds` is null because the steps run different tools, and
    `notes` say how many tool steps it was priced as (and, when pricing failed, that it did, with
    `weightedHours` null). A batch of such a tool is 422 `not_supported` at `/tool`. A `tool` name
    longer than 64 characters is 422 `invalid_length` at `/tool`.
    A tool hidden from you is 404 `tool_not_found` and one you can't run is 403
    `tool_not_available`, as on submit. An unknown `projectId` is 422 at `/projectId`, as on
    submit. It doesn't check whether a name is taken, budgets, quotas or the queue: `validateJob`
    does.

    Args:
        tamarind_version (str | Unset):
        body (SubmitFileBatchRequest | SubmitInlineBatchRequest | SubmitJobRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Estimate | Problem
    """

    return sync_detailed(
        client=client,
        body=body,
        tamarind_version=tamarind_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: SubmitFileBatchRequest | SubmitInlineBatchRequest | SubmitJobRequest,
    tamarind_version: str | Unset = UNSET,
) -> Response[Estimate | Problem]:
    """Estimate a job's runtime and cost without running it

     Takes the same body as `submitJob`, for a job or a batch, and returns the runtime per job, the
    weighted hours and the job count that today's estimator computes for the submit budget gate,
    fan-out included. A batch, inline or from a `source` file (read now, as on submit), is priced
    from its first 500 rows and scaled to its full row count, with a note saying so; more than
    30,000 rows is 422 `out_of_range`. Settings that can't be priced, such as a numeric field that
    isn't a finite number, are 422 `invalid_type` at `/settings`. With `lowPriority: true`,
    `weightedHours` is the low-priority price, and a caller or job that can't have the tier gets
    the same 422 error at `/lowPriority` as `submitJob`, so a quote is never at a price the submit
    would refuse.

    It prices one tool's current deployment from the settings alone, so `modelId`, `toolVersion`,
    `toolLifetimeEtag` and typed `inputs` are 422 `not_supported` at their field. A file setting
    that names a job's output under the job's name is priced at the tool's default input size,
    so send the job file's `ref` for a closer quote. A tool that runs
    as a pipeline behind the scenes (such as BinderScout) is priced as its whole pipeline, by the
    estimator `estimatePipeline` uses, after the same checks `validateJob` makes: `jobCount` counts
    every step's jobs, `perJobRuntimeSeconds` is null because the steps run different tools, and
    `notes` say how many tool steps it was priced as (and, when pricing failed, that it did, with
    `weightedHours` null). A batch of such a tool is 422 `not_supported` at `/tool`. A `tool` name
    longer than 64 characters is 422 `invalid_length` at `/tool`.
    A tool hidden from you is 404 `tool_not_found` and one you can't run is 403
    `tool_not_available`, as on submit. An unknown `projectId` is 422 at `/projectId`, as on
    submit. It doesn't check whether a name is taken, budgets, quotas or the queue: `validateJob`
    does.

    Args:
        tamarind_version (str | Unset):
        body (SubmitFileBatchRequest | SubmitInlineBatchRequest | SubmitJobRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Estimate | Problem]
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
    body: SubmitFileBatchRequest | SubmitInlineBatchRequest | SubmitJobRequest,
    tamarind_version: str | Unset = UNSET,
) -> Estimate | Problem | None:
    """Estimate a job's runtime and cost without running it

     Takes the same body as `submitJob`, for a job or a batch, and returns the runtime per job, the
    weighted hours and the job count that today's estimator computes for the submit budget gate,
    fan-out included. A batch, inline or from a `source` file (read now, as on submit), is priced
    from its first 500 rows and scaled to its full row count, with a note saying so; more than
    30,000 rows is 422 `out_of_range`. Settings that can't be priced, such as a numeric field that
    isn't a finite number, are 422 `invalid_type` at `/settings`. With `lowPriority: true`,
    `weightedHours` is the low-priority price, and a caller or job that can't have the tier gets
    the same 422 error at `/lowPriority` as `submitJob`, so a quote is never at a price the submit
    would refuse.

    It prices one tool's current deployment from the settings alone, so `modelId`, `toolVersion`,
    `toolLifetimeEtag` and typed `inputs` are 422 `not_supported` at their field. A file setting
    that names a job's output under the job's name is priced at the tool's default input size,
    so send the job file's `ref` for a closer quote. A tool that runs
    as a pipeline behind the scenes (such as BinderScout) is priced as its whole pipeline, by the
    estimator `estimatePipeline` uses, after the same checks `validateJob` makes: `jobCount` counts
    every step's jobs, `perJobRuntimeSeconds` is null because the steps run different tools, and
    `notes` say how many tool steps it was priced as (and, when pricing failed, that it did, with
    `weightedHours` null). A batch of such a tool is 422 `not_supported` at `/tool`. A `tool` name
    longer than 64 characters is 422 `invalid_length` at `/tool`.
    A tool hidden from you is 404 `tool_not_found` and one you can't run is 403
    `tool_not_available`, as on submit. An unknown `projectId` is 422 at `/projectId`, as on
    submit. It doesn't check whether a name is taken, budgets, quotas or the queue: `validateJob`
    does.

    Args:
        tamarind_version (str | Unset):
        body (SubmitFileBatchRequest | SubmitInlineBatchRequest | SubmitJobRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Estimate | Problem
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            tamarind_version=tamarind_version,
        )
    ).parsed
