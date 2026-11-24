from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.batch_validation_report import BatchValidationReport
from ...models.problem import Problem
from ...models.submit_inline_batch_request import SubmitInlineBatchRequest
from ...models.submit_job_request import SubmitJobRequest
from ...models.validation_report import ValidationReport
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    body: SubmitInlineBatchRequest | SubmitJobRequest,
    tamarind_version: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(tamarind_version, Unset):
        headers["Tamarind-Version"] = tamarind_version

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/jobs/validate",
    }

    if isinstance(body, SubmitJobRequest):
        _kwargs["json"] = body.to_dict()
    else:
        _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> BatchValidationReport | ValidationReport | Problem:
    if response.status_code == 200:

        def _parse_response_200(data: object) -> BatchValidationReport | ValidationReport:
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                response_200_type_0 = ValidationReport.from_dict(data)

                return response_200_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            if not isinstance(data, dict):
                raise TypeError()
            response_200_type_1 = BatchValidationReport.from_dict(data)

            return response_200_type_1

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

    if response.status_code == 413:
        response_413 = Problem.from_dict(response.json())

        return response_413

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
) -> Response[BatchValidationReport | ValidationReport | Problem]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: SubmitInlineBatchRequest | SubmitJobRequest,
    tamarind_version: str | Unset = UNSET,
) -> Response[BatchValidationReport | ValidationReport | Problem]:
    """Check a job without running it

     Takes the same body as `submitJob` (a batch only inline) and runs every check `submitJob`
    runs, read-only: settings, tool access and licence (including a stale `toolLifetimeEtag`), the
    name, the project (an unknown `projectId` is a failed `project` check with an `invalid_option`
    error at `/projectId`), budgets and quotas. If this says `valid: true`, `submitJob` can only
    refuse for a reason that changed in between, or because its `Idempotency-Key` was already used
    with a different body, which this doesn't see. Spends nothing and writes nothing.

    200 means the check ran, whatever the verdict, and problems with `settings` are reported in it:
    blocking ones in `errors`, and the validator's non-blocking findings in `warnings`, the same
    `warnings` `submitJob` returns. A required setting left out, or sent as null, is an error
    (`required` at its pointer), as today's JS routes refuse it, a batch's rows included. A tool
    hidden from you is a `tool_not_found` error in the
    verdict. With `lowPriority: true`, a caller or job that can't have the tier is an error at
    `/lowPriority` with the same `code` `submitJob` would refuse with. A body that fails this
    request schema, such as one with no `tool` or an unknown top-level field, is 422, because there
    is nothing to check; so is a `gpu` (not built yet). Any other non-2xx response means it could
    not run.

    Validation stops at its first refusal, so the family that refused is `failed` and the families
    it didn't reach are `skipped`. A tool that runs as a pipeline behind the scenes (such as
    BinderScout) is checked like any other tool and then by its pipeline's own rules, which
    `submitJob` applies too: BinderScout with `binderLengthMin` above `binderLengthMax`, say, is an
    `out_of_range` error at `/settings/binderLengthMax`. A caller with no account yet gets
    503 `account_not_ready` rather than having one created, because validate writes nothing.
    `normalized` is the settings as a submit would take them; a CIF converted for a PDB-only
    setting comes back as you sent it, since a submit converts it again, and a molecule reference
    comes back as the sequence, SMILES or structure name it names, as `getJob` shows it. A file
    setting comes back as the stored key: under your email, and a job name's path as the job's
    folder. Validate checks that you may read each file, not that it exists, so a missing file
    in your own workspace is still `valid`.

    `kind: batch` checks an inline batch of up to 1,000 rows completely: the request as a whole,
    every row as the submit's background creation would, then the rows' total against your
    budgets, monthly limit and queue limit. It returns a `BatchValidationReport`, with no `checks`:
    problems with the batch as a whole (a refusal of the request, such as an unknown tool, included)
    in `errors`, and the rows with an error or a warning in `results`, with row pointers like
    `/settings/17/numRecycles` and `/names/17`. More than 1,000 rows is a failed verdict, an
    `out_of_range` error at `/settings`, not a 422. A file batch (`source`) is 422 `not_supported`
    at `/source`: send its rows as `settings`.

    Args:
        tamarind_version (str | Unset):
        body (SubmitInlineBatchRequest | SubmitJobRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[BatchValidationReport | ValidationReport | Problem]
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
    body: SubmitInlineBatchRequest | SubmitJobRequest,
    tamarind_version: str | Unset = UNSET,
) -> BatchValidationReport | ValidationReport | Problem | None:
    """Check a job without running it

     Takes the same body as `submitJob` (a batch only inline) and runs every check `submitJob`
    runs, read-only: settings, tool access and licence (including a stale `toolLifetimeEtag`), the
    name, the project (an unknown `projectId` is a failed `project` check with an `invalid_option`
    error at `/projectId`), budgets and quotas. If this says `valid: true`, `submitJob` can only
    refuse for a reason that changed in between, or because its `Idempotency-Key` was already used
    with a different body, which this doesn't see. Spends nothing and writes nothing.

    200 means the check ran, whatever the verdict, and problems with `settings` are reported in it:
    blocking ones in `errors`, and the validator's non-blocking findings in `warnings`, the same
    `warnings` `submitJob` returns. A required setting left out, or sent as null, is an error
    (`required` at its pointer), as today's JS routes refuse it, a batch's rows included. A tool
    hidden from you is a `tool_not_found` error in the
    verdict. With `lowPriority: true`, a caller or job that can't have the tier is an error at
    `/lowPriority` with the same `code` `submitJob` would refuse with. A body that fails this
    request schema, such as one with no `tool` or an unknown top-level field, is 422, because there
    is nothing to check; so is a `gpu` (not built yet). Any other non-2xx response means it could
    not run.

    Validation stops at its first refusal, so the family that refused is `failed` and the families
    it didn't reach are `skipped`. A tool that runs as a pipeline behind the scenes (such as
    BinderScout) is checked like any other tool and then by its pipeline's own rules, which
    `submitJob` applies too: BinderScout with `binderLengthMin` above `binderLengthMax`, say, is an
    `out_of_range` error at `/settings/binderLengthMax`. A caller with no account yet gets
    503 `account_not_ready` rather than having one created, because validate writes nothing.
    `normalized` is the settings as a submit would take them; a CIF converted for a PDB-only
    setting comes back as you sent it, since a submit converts it again, and a molecule reference
    comes back as the sequence, SMILES or structure name it names, as `getJob` shows it. A file
    setting comes back as the stored key: under your email, and a job name's path as the job's
    folder. Validate checks that you may read each file, not that it exists, so a missing file
    in your own workspace is still `valid`.

    `kind: batch` checks an inline batch of up to 1,000 rows completely: the request as a whole,
    every row as the submit's background creation would, then the rows' total against your
    budgets, monthly limit and queue limit. It returns a `BatchValidationReport`, with no `checks`:
    problems with the batch as a whole (a refusal of the request, such as an unknown tool, included)
    in `errors`, and the rows with an error or a warning in `results`, with row pointers like
    `/settings/17/numRecycles` and `/names/17`. More than 1,000 rows is a failed verdict, an
    `out_of_range` error at `/settings`, not a 422. A file batch (`source`) is 422 `not_supported`
    at `/source`: send its rows as `settings`.

    Args:
        tamarind_version (str | Unset):
        body (SubmitInlineBatchRequest | SubmitJobRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        BatchValidationReport | ValidationReport | Problem
    """

    return sync_detailed(
        client=client,
        body=body,
        tamarind_version=tamarind_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: SubmitInlineBatchRequest | SubmitJobRequest,
    tamarind_version: str | Unset = UNSET,
) -> Response[BatchValidationReport | ValidationReport | Problem]:
    """Check a job without running it

     Takes the same body as `submitJob` (a batch only inline) and runs every check `submitJob`
    runs, read-only: settings, tool access and licence (including a stale `toolLifetimeEtag`), the
    name, the project (an unknown `projectId` is a failed `project` check with an `invalid_option`
    error at `/projectId`), budgets and quotas. If this says `valid: true`, `submitJob` can only
    refuse for a reason that changed in between, or because its `Idempotency-Key` was already used
    with a different body, which this doesn't see. Spends nothing and writes nothing.

    200 means the check ran, whatever the verdict, and problems with `settings` are reported in it:
    blocking ones in `errors`, and the validator's non-blocking findings in `warnings`, the same
    `warnings` `submitJob` returns. A required setting left out, or sent as null, is an error
    (`required` at its pointer), as today's JS routes refuse it, a batch's rows included. A tool
    hidden from you is a `tool_not_found` error in the
    verdict. With `lowPriority: true`, a caller or job that can't have the tier is an error at
    `/lowPriority` with the same `code` `submitJob` would refuse with. A body that fails this
    request schema, such as one with no `tool` or an unknown top-level field, is 422, because there
    is nothing to check; so is a `gpu` (not built yet). Any other non-2xx response means it could
    not run.

    Validation stops at its first refusal, so the family that refused is `failed` and the families
    it didn't reach are `skipped`. A tool that runs as a pipeline behind the scenes (such as
    BinderScout) is checked like any other tool and then by its pipeline's own rules, which
    `submitJob` applies too: BinderScout with `binderLengthMin` above `binderLengthMax`, say, is an
    `out_of_range` error at `/settings/binderLengthMax`. A caller with no account yet gets
    503 `account_not_ready` rather than having one created, because validate writes nothing.
    `normalized` is the settings as a submit would take them; a CIF converted for a PDB-only
    setting comes back as you sent it, since a submit converts it again, and a molecule reference
    comes back as the sequence, SMILES or structure name it names, as `getJob` shows it. A file
    setting comes back as the stored key: under your email, and a job name's path as the job's
    folder. Validate checks that you may read each file, not that it exists, so a missing file
    in your own workspace is still `valid`.

    `kind: batch` checks an inline batch of up to 1,000 rows completely: the request as a whole,
    every row as the submit's background creation would, then the rows' total against your
    budgets, monthly limit and queue limit. It returns a `BatchValidationReport`, with no `checks`:
    problems with the batch as a whole (a refusal of the request, such as an unknown tool, included)
    in `errors`, and the rows with an error or a warning in `results`, with row pointers like
    `/settings/17/numRecycles` and `/names/17`. More than 1,000 rows is a failed verdict, an
    `out_of_range` error at `/settings`, not a 422. A file batch (`source`) is 422 `not_supported`
    at `/source`: send its rows as `settings`.

    Args:
        tamarind_version (str | Unset):
        body (SubmitInlineBatchRequest | SubmitJobRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[BatchValidationReport | ValidationReport | Problem]
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
    body: SubmitInlineBatchRequest | SubmitJobRequest,
    tamarind_version: str | Unset = UNSET,
) -> BatchValidationReport | ValidationReport | Problem | None:
    """Check a job without running it

     Takes the same body as `submitJob` (a batch only inline) and runs every check `submitJob`
    runs, read-only: settings, tool access and licence (including a stale `toolLifetimeEtag`), the
    name, the project (an unknown `projectId` is a failed `project` check with an `invalid_option`
    error at `/projectId`), budgets and quotas. If this says `valid: true`, `submitJob` can only
    refuse for a reason that changed in between, or because its `Idempotency-Key` was already used
    with a different body, which this doesn't see. Spends nothing and writes nothing.

    200 means the check ran, whatever the verdict, and problems with `settings` are reported in it:
    blocking ones in `errors`, and the validator's non-blocking findings in `warnings`, the same
    `warnings` `submitJob` returns. A required setting left out, or sent as null, is an error
    (`required` at its pointer), as today's JS routes refuse it, a batch's rows included. A tool
    hidden from you is a `tool_not_found` error in the
    verdict. With `lowPriority: true`, a caller or job that can't have the tier is an error at
    `/lowPriority` with the same `code` `submitJob` would refuse with. A body that fails this
    request schema, such as one with no `tool` or an unknown top-level field, is 422, because there
    is nothing to check; so is a `gpu` (not built yet). Any other non-2xx response means it could
    not run.

    Validation stops at its first refusal, so the family that refused is `failed` and the families
    it didn't reach are `skipped`. A tool that runs as a pipeline behind the scenes (such as
    BinderScout) is checked like any other tool and then by its pipeline's own rules, which
    `submitJob` applies too: BinderScout with `binderLengthMin` above `binderLengthMax`, say, is an
    `out_of_range` error at `/settings/binderLengthMax`. A caller with no account yet gets
    503 `account_not_ready` rather than having one created, because validate writes nothing.
    `normalized` is the settings as a submit would take them; a CIF converted for a PDB-only
    setting comes back as you sent it, since a submit converts it again, and a molecule reference
    comes back as the sequence, SMILES or structure name it names, as `getJob` shows it. A file
    setting comes back as the stored key: under your email, and a job name's path as the job's
    folder. Validate checks that you may read each file, not that it exists, so a missing file
    in your own workspace is still `valid`.

    `kind: batch` checks an inline batch of up to 1,000 rows completely: the request as a whole,
    every row as the submit's background creation would, then the rows' total against your
    budgets, monthly limit and queue limit. It returns a `BatchValidationReport`, with no `checks`:
    problems with the batch as a whole (a refusal of the request, such as an unknown tool, included)
    in `errors`, and the rows with an error or a warning in `results`, with row pointers like
    `/settings/17/numRecycles` and `/names/17`. More than 1,000 rows is a failed verdict, an
    `out_of_range` error at `/settings`, not a 422. A file batch (`source`) is 422 `not_supported`
    at `/source`: send its rows as `settings`.

    Args:
        tamarind_version (str | Unset):
        body (SubmitInlineBatchRequest | SubmitJobRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        BatchValidationReport | ValidationReport | Problem
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            tamarind_version=tamarind_version,
        )
    ).parsed
