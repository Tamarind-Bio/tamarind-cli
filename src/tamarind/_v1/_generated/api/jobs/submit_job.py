from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.problem import Problem
from ...models.submit_file_batch_request import SubmitFileBatchRequest
from ...models.submit_inline_batch_request import SubmitInlineBatchRequest
from ...models.submit_job_request import SubmitJobRequest
from ...models.submitted_batch import SubmittedBatch
from ...models.submitted_job import SubmittedJob
from ...models.submitted_pipeline_run import SubmittedPipelineRun
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    body: SubmitFileBatchRequest | SubmitInlineBatchRequest | SubmitJobRequest,
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
        "url": "/jobs",
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
) -> Problem | SubmittedBatch | SubmittedPipelineRun | SubmittedJob | SubmittedPipelineRun:
    if response.status_code == 201:

        def _parse_response_201(data: object) -> SubmittedJob | SubmittedPipelineRun:
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                response_201_type_0 = SubmittedJob.from_dict(data)

                return response_201_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            if not isinstance(data, dict):
                raise TypeError()
            response_201_type_1 = SubmittedPipelineRun.from_dict(data)

            return response_201_type_1

        response_201 = _parse_response_201(response.json())

        return response_201

    if response.status_code == 202:

        def _parse_response_202(data: object) -> SubmittedBatch | SubmittedPipelineRun:
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                response_202_type_0 = SubmittedBatch.from_dict(data)

                return response_202_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            if not isinstance(data, dict):
                raise TypeError()
            response_202_type_1 = SubmittedPipelineRun.from_dict(data)

            return response_202_type_1

        response_202 = _parse_response_202(response.json())

        return response_202

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

    if response.status_code == 413:
        response_413 = Problem.from_dict(response.json())

        return response_413

    if response.status_code == 422:
        response_422 = Problem.from_dict(response.json())

        return response_422

    if response.status_code == 429:
        response_429 = Problem.from_dict(response.json())

        return response_429

    if response.status_code == 500:
        response_500 = Problem.from_dict(response.json())

        return response_500

    if response.status_code == 503:
        response_503 = Problem.from_dict(response.json())

        return response_503

    response_default = Problem.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    Problem | SubmittedBatch | SubmittedPipelineRun | SubmittedJob | SubmittedPipelineRun
]:
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
    idempotency_key: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Response[
    Problem | SubmittedBatch | SubmittedPipelineRun | SubmittedJob | SubmittedPipelineRun
]:
    """Submit a job or a batch

     `kind` says what to create, the same word responses use: `job` (the default) with `settings`
    as an object, or `batch` with `settings` as an array (one object per job) or `source` to read
    the rows from an uploaded FASTA, CSV or JSONL file; `sharedSettings` apply to every row. A
    batch is never inferred from the shape of `settings`: a list of `settings` without `kind` is
    422 at `/settings`. SDK, CLI and MCP always send `kind`. Use a batch for more than one input,
    not a loop of this call.

    A job runs the same checks as `validateJob`, then is created. On failure, the 422 lists every
    problem at once. A job answers 201, with `Location: /jobs/job_<id>`. A job whose tool splits
    it into several jobs (a custom tool's design batching, or a design count over the tool's
    per-job size) answers 202 with the batch it created.

    A batch answers 202 with `jobsCreated: false` and `Location: /jobs/batch_<id>`, and its jobs
    (up to 30,000) are created in the background, so follow `jobsCreated`, `status` and
    `stopReason.errors` on `getJob`. At submit, the checks on the request as a whole run once: its
    shape, the tool and access to it, the project, whether you may ask for `lowPriority`, the
    batch's `name` and the rows' `names`, the `weightedHoursBudget` you set, and on the Free tier,
    room in your monthly job limit for every row (402 `quota_exceeded`). A `source` file is read
    at submit, so a problem with the file itself is 422 at the `source` member at fault. Each
    row's settings are checked after the 202, because 30,000 rows can't be checked inside the
    gateway's 30 seconds. Any row problem fails the whole batch with nothing created: `Failed`,
    `stopReason.code` `invalid_input`, and every problem in `stopReason.errors` with pointers like
    `/settings/17/numRecycles` (for a file, the file's rows, counted from 0). Then the rows' total
    is checked against your budgets, monthly limit and queue limit; a refusal there stops the
    batch with nothing created (`Stopped`, `stopReason.kind` `limit`). A Free account's monthly
    limit is reserved when the jobs are written, so batches submitted together can't go over it.
    Check rows first with `validateJob`, which takes up to 1,000 at once. A row may not split into
    several jobs; submit such a row as its own job. A batch's settings, with `sharedSettings`
    applied to every row, are at most 64 MiB of JSON (422 `out_of_range`), and a `NaN` or
    `Infinity` in them is 422 `invalid_format` at its pointer. If the batch can't be queued for
    creation, the answer is 503 `service_unavailable` with nothing created; retry it. Where batch
    creation isn't set up (some dedicated deployments), `kind: batch` is 422 `not_supported` at
    `/kind`. A batch's `warnings` are always empty; `validateJob` returns each row's.

    `Idempotency-Key` works the same for both kinds. A retry of a completed request answers as the
    original did (201 with the job, or 202 with the batch, and the original `warnings`), with
    `Idempotent-Replayed: true`. A replay reads the job as `getJob` does, so a job that now
    belongs to another account is 404.

    A `name` must match `^[A-Za-z0-9_.-]{1,220}$`, and is refused rather than cleaned. Without
    one, the job or batch is named `<tool>-<UTC timestamp>-<6 hex characters>`. A name you already
    use is 409 `job_name_conflict`, whose `existingId` is the id of your job or batch that has it
    (`job_...` or `batch_...`), when it can be read: fetch it with `getJob` instead of submitting again.

    Settings checks are the central validator's. v1 refuses exactly what today's routes refuse
    (the checks a worker would also refuse), and returns its other, non-blocking findings inline,
    as `warnings` on the created job.

    `lowPriority: true` asks for the low-priority tier, as on today's routes. It's refused before
    anything is created, with 422 `validation_failed` and one error at `/lowPriority` whose
    `code` says why: `requires_premium_org` (only Premium organizations, not personal accounts),
    `not_enabled` (the tier isn't turned on for your organization), `unsupported_tool` (custom
    tools), `tool_not_eligible` (not a T2 GPU tool with low-priority capacity), `no_lane` (the GPU or
    mode it needs has no low-priority capacity), `unsupported_route` (a pipeline-backed tool) or
    `unsupported_deployment`. A refusal never falls back to full price. On a batch, whether you may
    ask is checked at submit, and whether each row's job can run at the tier (`tool_not_eligible`,
    `no_lane`) is a row problem found after the 202.

    A tool that runs as a pipeline behind the scenes (such as BinderScout or protein-solubilization)
    is submitted like any other, and what it starts is a pipeline run. The answer is that run as
    `getJob` shows it (`kind` `pipeline`, a `run_` id), with `warnings`, and
    `Location: /jobs/run_<id>`. Submit waits a few seconds for the pipeline engine to record the run
    and answers 201; if it isn't recorded by then, 202 with the run `In Queue` and `Retry-After`.
    Poll it with `getJob` as usual. A retry with the same `Idempotency-Key` answers the run as
    `getJob` reads it; while the run isn't recorded yet, it is 409 `idempotency_in_progress`. Such a
    tool can't be a batch: `kind: batch` is 422 `not_supported` at `/tool`.

    Not yet, each 422 `not_supported` at its field: `gpu`, and typed `inputs` on a batch (put the
    values in each row's settings). There is
    no business maximum on `maxRuntimeSeconds` or `weightedHoursBudget`. Only a number a job can't
    store (more than 38 significant digits, or outside 1e-130 to 9.99e125) is 422 `out_of_range`,
    before anything is written.

    To train a model, send a tool from `listTools?finetune=true`. To run a trained model, send
    its `inferenceTool` as `tool` and its id as `modelId`. There is no separate endpoint for either.

    Args:
        idempotency_key (str | Unset):
        tamarind_version (str | Unset):
        body (SubmitFileBatchRequest | SubmitInlineBatchRequest | SubmitJobRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Problem | SubmittedBatch | SubmittedPipelineRun | SubmittedJob | SubmittedPipelineRun]
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
    body: SubmitFileBatchRequest | SubmitInlineBatchRequest | SubmitJobRequest,
    idempotency_key: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Problem | SubmittedBatch | SubmittedPipelineRun | SubmittedJob | SubmittedPipelineRun | None:
    """Submit a job or a batch

     `kind` says what to create, the same word responses use: `job` (the default) with `settings`
    as an object, or `batch` with `settings` as an array (one object per job) or `source` to read
    the rows from an uploaded FASTA, CSV or JSONL file; `sharedSettings` apply to every row. A
    batch is never inferred from the shape of `settings`: a list of `settings` without `kind` is
    422 at `/settings`. SDK, CLI and MCP always send `kind`. Use a batch for more than one input,
    not a loop of this call.

    A job runs the same checks as `validateJob`, then is created. On failure, the 422 lists every
    problem at once. A job answers 201, with `Location: /jobs/job_<id>`. A job whose tool splits
    it into several jobs (a custom tool's design batching, or a design count over the tool's
    per-job size) answers 202 with the batch it created.

    A batch answers 202 with `jobsCreated: false` and `Location: /jobs/batch_<id>`, and its jobs
    (up to 30,000) are created in the background, so follow `jobsCreated`, `status` and
    `stopReason.errors` on `getJob`. At submit, the checks on the request as a whole run once: its
    shape, the tool and access to it, the project, whether you may ask for `lowPriority`, the
    batch's `name` and the rows' `names`, the `weightedHoursBudget` you set, and on the Free tier,
    room in your monthly job limit for every row (402 `quota_exceeded`). A `source` file is read
    at submit, so a problem with the file itself is 422 at the `source` member at fault. Each
    row's settings are checked after the 202, because 30,000 rows can't be checked inside the
    gateway's 30 seconds. Any row problem fails the whole batch with nothing created: `Failed`,
    `stopReason.code` `invalid_input`, and every problem in `stopReason.errors` with pointers like
    `/settings/17/numRecycles` (for a file, the file's rows, counted from 0). Then the rows' total
    is checked against your budgets, monthly limit and queue limit; a refusal there stops the
    batch with nothing created (`Stopped`, `stopReason.kind` `limit`). A Free account's monthly
    limit is reserved when the jobs are written, so batches submitted together can't go over it.
    Check rows first with `validateJob`, which takes up to 1,000 at once. A row may not split into
    several jobs; submit such a row as its own job. A batch's settings, with `sharedSettings`
    applied to every row, are at most 64 MiB of JSON (422 `out_of_range`), and a `NaN` or
    `Infinity` in them is 422 `invalid_format` at its pointer. If the batch can't be queued for
    creation, the answer is 503 `service_unavailable` with nothing created; retry it. Where batch
    creation isn't set up (some dedicated deployments), `kind: batch` is 422 `not_supported` at
    `/kind`. A batch's `warnings` are always empty; `validateJob` returns each row's.

    `Idempotency-Key` works the same for both kinds. A retry of a completed request answers as the
    original did (201 with the job, or 202 with the batch, and the original `warnings`), with
    `Idempotent-Replayed: true`. A replay reads the job as `getJob` does, so a job that now
    belongs to another account is 404.

    A `name` must match `^[A-Za-z0-9_.-]{1,220}$`, and is refused rather than cleaned. Without
    one, the job or batch is named `<tool>-<UTC timestamp>-<6 hex characters>`. A name you already
    use is 409 `job_name_conflict`, whose `existingId` is the id of your job or batch that has it
    (`job_...` or `batch_...`), when it can be read: fetch it with `getJob` instead of submitting again.

    Settings checks are the central validator's. v1 refuses exactly what today's routes refuse
    (the checks a worker would also refuse), and returns its other, non-blocking findings inline,
    as `warnings` on the created job.

    `lowPriority: true` asks for the low-priority tier, as on today's routes. It's refused before
    anything is created, with 422 `validation_failed` and one error at `/lowPriority` whose
    `code` says why: `requires_premium_org` (only Premium organizations, not personal accounts),
    `not_enabled` (the tier isn't turned on for your organization), `unsupported_tool` (custom
    tools), `tool_not_eligible` (not a T2 GPU tool with low-priority capacity), `no_lane` (the GPU or
    mode it needs has no low-priority capacity), `unsupported_route` (a pipeline-backed tool) or
    `unsupported_deployment`. A refusal never falls back to full price. On a batch, whether you may
    ask is checked at submit, and whether each row's job can run at the tier (`tool_not_eligible`,
    `no_lane`) is a row problem found after the 202.

    A tool that runs as a pipeline behind the scenes (such as BinderScout or protein-solubilization)
    is submitted like any other, and what it starts is a pipeline run. The answer is that run as
    `getJob` shows it (`kind` `pipeline`, a `run_` id), with `warnings`, and
    `Location: /jobs/run_<id>`. Submit waits a few seconds for the pipeline engine to record the run
    and answers 201; if it isn't recorded by then, 202 with the run `In Queue` and `Retry-After`.
    Poll it with `getJob` as usual. A retry with the same `Idempotency-Key` answers the run as
    `getJob` reads it; while the run isn't recorded yet, it is 409 `idempotency_in_progress`. Such a
    tool can't be a batch: `kind: batch` is 422 `not_supported` at `/tool`.

    Not yet, each 422 `not_supported` at its field: `gpu`, and typed `inputs` on a batch (put the
    values in each row's settings). There is
    no business maximum on `maxRuntimeSeconds` or `weightedHoursBudget`. Only a number a job can't
    store (more than 38 significant digits, or outside 1e-130 to 9.99e125) is 422 `out_of_range`,
    before anything is written.

    To train a model, send a tool from `listTools?finetune=true`. To run a trained model, send
    its `inferenceTool` as `tool` and its id as `modelId`. There is no separate endpoint for either.

    Args:
        idempotency_key (str | Unset):
        tamarind_version (str | Unset):
        body (SubmitFileBatchRequest | SubmitInlineBatchRequest | SubmitJobRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Problem | SubmittedBatch | SubmittedPipelineRun | SubmittedJob | SubmittedPipelineRun
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
    body: SubmitFileBatchRequest | SubmitInlineBatchRequest | SubmitJobRequest,
    idempotency_key: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Response[
    Problem | SubmittedBatch | SubmittedPipelineRun | SubmittedJob | SubmittedPipelineRun
]:
    """Submit a job or a batch

     `kind` says what to create, the same word responses use: `job` (the default) with `settings`
    as an object, or `batch` with `settings` as an array (one object per job) or `source` to read
    the rows from an uploaded FASTA, CSV or JSONL file; `sharedSettings` apply to every row. A
    batch is never inferred from the shape of `settings`: a list of `settings` without `kind` is
    422 at `/settings`. SDK, CLI and MCP always send `kind`. Use a batch for more than one input,
    not a loop of this call.

    A job runs the same checks as `validateJob`, then is created. On failure, the 422 lists every
    problem at once. A job answers 201, with `Location: /jobs/job_<id>`. A job whose tool splits
    it into several jobs (a custom tool's design batching, or a design count over the tool's
    per-job size) answers 202 with the batch it created.

    A batch answers 202 with `jobsCreated: false` and `Location: /jobs/batch_<id>`, and its jobs
    (up to 30,000) are created in the background, so follow `jobsCreated`, `status` and
    `stopReason.errors` on `getJob`. At submit, the checks on the request as a whole run once: its
    shape, the tool and access to it, the project, whether you may ask for `lowPriority`, the
    batch's `name` and the rows' `names`, the `weightedHoursBudget` you set, and on the Free tier,
    room in your monthly job limit for every row (402 `quota_exceeded`). A `source` file is read
    at submit, so a problem with the file itself is 422 at the `source` member at fault. Each
    row's settings are checked after the 202, because 30,000 rows can't be checked inside the
    gateway's 30 seconds. Any row problem fails the whole batch with nothing created: `Failed`,
    `stopReason.code` `invalid_input`, and every problem in `stopReason.errors` with pointers like
    `/settings/17/numRecycles` (for a file, the file's rows, counted from 0). Then the rows' total
    is checked against your budgets, monthly limit and queue limit; a refusal there stops the
    batch with nothing created (`Stopped`, `stopReason.kind` `limit`). A Free account's monthly
    limit is reserved when the jobs are written, so batches submitted together can't go over it.
    Check rows first with `validateJob`, which takes up to 1,000 at once. A row may not split into
    several jobs; submit such a row as its own job. A batch's settings, with `sharedSettings`
    applied to every row, are at most 64 MiB of JSON (422 `out_of_range`), and a `NaN` or
    `Infinity` in them is 422 `invalid_format` at its pointer. If the batch can't be queued for
    creation, the answer is 503 `service_unavailable` with nothing created; retry it. Where batch
    creation isn't set up (some dedicated deployments), `kind: batch` is 422 `not_supported` at
    `/kind`. A batch's `warnings` are always empty; `validateJob` returns each row's.

    `Idempotency-Key` works the same for both kinds. A retry of a completed request answers as the
    original did (201 with the job, or 202 with the batch, and the original `warnings`), with
    `Idempotent-Replayed: true`. A replay reads the job as `getJob` does, so a job that now
    belongs to another account is 404.

    A `name` must match `^[A-Za-z0-9_.-]{1,220}$`, and is refused rather than cleaned. Without
    one, the job or batch is named `<tool>-<UTC timestamp>-<6 hex characters>`. A name you already
    use is 409 `job_name_conflict`, whose `existingId` is the id of your job or batch that has it
    (`job_...` or `batch_...`), when it can be read: fetch it with `getJob` instead of submitting again.

    Settings checks are the central validator's. v1 refuses exactly what today's routes refuse
    (the checks a worker would also refuse), and returns its other, non-blocking findings inline,
    as `warnings` on the created job.

    `lowPriority: true` asks for the low-priority tier, as on today's routes. It's refused before
    anything is created, with 422 `validation_failed` and one error at `/lowPriority` whose
    `code` says why: `requires_premium_org` (only Premium organizations, not personal accounts),
    `not_enabled` (the tier isn't turned on for your organization), `unsupported_tool` (custom
    tools), `tool_not_eligible` (not a T2 GPU tool with low-priority capacity), `no_lane` (the GPU or
    mode it needs has no low-priority capacity), `unsupported_route` (a pipeline-backed tool) or
    `unsupported_deployment`. A refusal never falls back to full price. On a batch, whether you may
    ask is checked at submit, and whether each row's job can run at the tier (`tool_not_eligible`,
    `no_lane`) is a row problem found after the 202.

    A tool that runs as a pipeline behind the scenes (such as BinderScout or protein-solubilization)
    is submitted like any other, and what it starts is a pipeline run. The answer is that run as
    `getJob` shows it (`kind` `pipeline`, a `run_` id), with `warnings`, and
    `Location: /jobs/run_<id>`. Submit waits a few seconds for the pipeline engine to record the run
    and answers 201; if it isn't recorded by then, 202 with the run `In Queue` and `Retry-After`.
    Poll it with `getJob` as usual. A retry with the same `Idempotency-Key` answers the run as
    `getJob` reads it; while the run isn't recorded yet, it is 409 `idempotency_in_progress`. Such a
    tool can't be a batch: `kind: batch` is 422 `not_supported` at `/tool`.

    Not yet, each 422 `not_supported` at its field: `gpu`, and typed `inputs` on a batch (put the
    values in each row's settings). There is
    no business maximum on `maxRuntimeSeconds` or `weightedHoursBudget`. Only a number a job can't
    store (more than 38 significant digits, or outside 1e-130 to 9.99e125) is 422 `out_of_range`,
    before anything is written.

    To train a model, send a tool from `listTools?finetune=true`. To run a trained model, send
    its `inferenceTool` as `tool` and its id as `modelId`. There is no separate endpoint for either.

    Args:
        idempotency_key (str | Unset):
        tamarind_version (str | Unset):
        body (SubmitFileBatchRequest | SubmitInlineBatchRequest | SubmitJobRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Problem | SubmittedBatch | SubmittedPipelineRun | SubmittedJob | SubmittedPipelineRun]
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
    body: SubmitFileBatchRequest | SubmitInlineBatchRequest | SubmitJobRequest,
    idempotency_key: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Problem | SubmittedBatch | SubmittedPipelineRun | SubmittedJob | SubmittedPipelineRun | None:
    """Submit a job or a batch

     `kind` says what to create, the same word responses use: `job` (the default) with `settings`
    as an object, or `batch` with `settings` as an array (one object per job) or `source` to read
    the rows from an uploaded FASTA, CSV or JSONL file; `sharedSettings` apply to every row. A
    batch is never inferred from the shape of `settings`: a list of `settings` without `kind` is
    422 at `/settings`. SDK, CLI and MCP always send `kind`. Use a batch for more than one input,
    not a loop of this call.

    A job runs the same checks as `validateJob`, then is created. On failure, the 422 lists every
    problem at once. A job answers 201, with `Location: /jobs/job_<id>`. A job whose tool splits
    it into several jobs (a custom tool's design batching, or a design count over the tool's
    per-job size) answers 202 with the batch it created.

    A batch answers 202 with `jobsCreated: false` and `Location: /jobs/batch_<id>`, and its jobs
    (up to 30,000) are created in the background, so follow `jobsCreated`, `status` and
    `stopReason.errors` on `getJob`. At submit, the checks on the request as a whole run once: its
    shape, the tool and access to it, the project, whether you may ask for `lowPriority`, the
    batch's `name` and the rows' `names`, the `weightedHoursBudget` you set, and on the Free tier,
    room in your monthly job limit for every row (402 `quota_exceeded`). A `source` file is read
    at submit, so a problem with the file itself is 422 at the `source` member at fault. Each
    row's settings are checked after the 202, because 30,000 rows can't be checked inside the
    gateway's 30 seconds. Any row problem fails the whole batch with nothing created: `Failed`,
    `stopReason.code` `invalid_input`, and every problem in `stopReason.errors` with pointers like
    `/settings/17/numRecycles` (for a file, the file's rows, counted from 0). Then the rows' total
    is checked against your budgets, monthly limit and queue limit; a refusal there stops the
    batch with nothing created (`Stopped`, `stopReason.kind` `limit`). A Free account's monthly
    limit is reserved when the jobs are written, so batches submitted together can't go over it.
    Check rows first with `validateJob`, which takes up to 1,000 at once. A row may not split into
    several jobs; submit such a row as its own job. A batch's settings, with `sharedSettings`
    applied to every row, are at most 64 MiB of JSON (422 `out_of_range`), and a `NaN` or
    `Infinity` in them is 422 `invalid_format` at its pointer. If the batch can't be queued for
    creation, the answer is 503 `service_unavailable` with nothing created; retry it. Where batch
    creation isn't set up (some dedicated deployments), `kind: batch` is 422 `not_supported` at
    `/kind`. A batch's `warnings` are always empty; `validateJob` returns each row's.

    `Idempotency-Key` works the same for both kinds. A retry of a completed request answers as the
    original did (201 with the job, or 202 with the batch, and the original `warnings`), with
    `Idempotent-Replayed: true`. A replay reads the job as `getJob` does, so a job that now
    belongs to another account is 404.

    A `name` must match `^[A-Za-z0-9_.-]{1,220}$`, and is refused rather than cleaned. Without
    one, the job or batch is named `<tool>-<UTC timestamp>-<6 hex characters>`. A name you already
    use is 409 `job_name_conflict`, whose `existingId` is the id of your job or batch that has it
    (`job_...` or `batch_...`), when it can be read: fetch it with `getJob` instead of submitting again.

    Settings checks are the central validator's. v1 refuses exactly what today's routes refuse
    (the checks a worker would also refuse), and returns its other, non-blocking findings inline,
    as `warnings` on the created job.

    `lowPriority: true` asks for the low-priority tier, as on today's routes. It's refused before
    anything is created, with 422 `validation_failed` and one error at `/lowPriority` whose
    `code` says why: `requires_premium_org` (only Premium organizations, not personal accounts),
    `not_enabled` (the tier isn't turned on for your organization), `unsupported_tool` (custom
    tools), `tool_not_eligible` (not a T2 GPU tool with low-priority capacity), `no_lane` (the GPU or
    mode it needs has no low-priority capacity), `unsupported_route` (a pipeline-backed tool) or
    `unsupported_deployment`. A refusal never falls back to full price. On a batch, whether you may
    ask is checked at submit, and whether each row's job can run at the tier (`tool_not_eligible`,
    `no_lane`) is a row problem found after the 202.

    A tool that runs as a pipeline behind the scenes (such as BinderScout or protein-solubilization)
    is submitted like any other, and what it starts is a pipeline run. The answer is that run as
    `getJob` shows it (`kind` `pipeline`, a `run_` id), with `warnings`, and
    `Location: /jobs/run_<id>`. Submit waits a few seconds for the pipeline engine to record the run
    and answers 201; if it isn't recorded by then, 202 with the run `In Queue` and `Retry-After`.
    Poll it with `getJob` as usual. A retry with the same `Idempotency-Key` answers the run as
    `getJob` reads it; while the run isn't recorded yet, it is 409 `idempotency_in_progress`. Such a
    tool can't be a batch: `kind: batch` is 422 `not_supported` at `/tool`.

    Not yet, each 422 `not_supported` at its field: `gpu`, and typed `inputs` on a batch (put the
    values in each row's settings). There is
    no business maximum on `maxRuntimeSeconds` or `weightedHoursBudget`. Only a number a job can't
    store (more than 38 significant digits, or outside 1e-130 to 9.99e125) is 422 `out_of_range`,
    before anything is written.

    To train a model, send a tool from `listTools?finetune=true`. To run a trained model, send
    its `inferenceTool` as `tool` and its id as `modelId`. There is no separate endpoint for either.

    Args:
        idempotency_key (str | Unset):
        tamarind_version (str | Unset):
        body (SubmitFileBatchRequest | SubmitInlineBatchRequest | SubmitJobRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Problem | SubmittedBatch | SubmittedPipelineRun | SubmittedJob | SubmittedPipelineRun
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            idempotency_key=idempotency_key,
            tamarind_version=tamarind_version,
        )
    ).parsed
