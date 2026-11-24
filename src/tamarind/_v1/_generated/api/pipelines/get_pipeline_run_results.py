from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.get_pipeline_run_results_body_type_0 import GetPipelineRunResultsBodyType0
from ...models.problem import Problem
from ...models.results_preparing import ResultsPreparing
from ...models.results_ready import ResultsReady
from ...types import UNSET, Response, Unset


def _get_kwargs(
    run_id: str,
    *,
    body: GetPipelineRunResultsBodyType0 | None | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(tamarind_version, Unset):
        headers["Tamarind-Version"] = tamarind_version

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/pipelines/runs/{run_id}/results".format(
            run_id=quote(str(run_id), safe=""),
        ),
    }

    if isinstance(body, GetPipelineRunResultsBodyType0):
        _kwargs["json"] = body.to_dict()
    else:
        _kwargs["json"] = body

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Problem | ResultsPreparing | ResultsReady:
    if response.status_code == 200:
        response_200 = ResultsReady.from_dict(response.json())

        return response_200

    if response.status_code == 202:
        response_202 = ResultsPreparing.from_dict(response.json())

        return response_202

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
) -> Response[Problem | ResultsPreparing | ResultsReady]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    run_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: GetPipelineRunResultsBodyType0 | None | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Response[Problem | ResultsPreparing | ResultsReady]:
    """Get a zip of a pipeline run's outputs

     Until the rename from `/archive` merges (decision 75, not yet), the server answers at
    `POST /pipelines/runs/{runId}/archive`. Waits up to 25 seconds for the zip. 200 means ready,
    with the zip's size and the link's expiry; `fileCount` and `truncated` are null, because
    nothing records them for a run's zip.
    202 means still preparing, so call again after `retryAfterSeconds` (10, also sent as
    `Retry-After`). It is also 202 while the run (or the node run you named) hasn't finished: the
    zip is built only once it has. A zip that could not be built is 409 `archive_failed`,
    retryable after `Retry-After` (90 seconds), when the results service builds again. An
    organization that has lost read access gets 403 `organization_export_disabled` unless the zip
    already exists. A suspended or inactive organization still gets its zip.

    Args:
        run_id (str):
        tamarind_version (str | Unset):
        body (GetPipelineRunResultsBodyType0 | None | Unset): Optional; no body, `null` or `{}` is
            the whole run's zip.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Problem | ResultsPreparing | ResultsReady]
    """

    kwargs = _get_kwargs(
        run_id=run_id,
        body=body,
        tamarind_version=tamarind_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    run_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: GetPipelineRunResultsBodyType0 | None | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Problem | ResultsPreparing | ResultsReady | None:
    """Get a zip of a pipeline run's outputs

     Until the rename from `/archive` merges (decision 75, not yet), the server answers at
    `POST /pipelines/runs/{runId}/archive`. Waits up to 25 seconds for the zip. 200 means ready,
    with the zip's size and the link's expiry; `fileCount` and `truncated` are null, because
    nothing records them for a run's zip.
    202 means still preparing, so call again after `retryAfterSeconds` (10, also sent as
    `Retry-After`). It is also 202 while the run (or the node run you named) hasn't finished: the
    zip is built only once it has. A zip that could not be built is 409 `archive_failed`,
    retryable after `Retry-After` (90 seconds), when the results service builds again. An
    organization that has lost read access gets 403 `organization_export_disabled` unless the zip
    already exists. A suspended or inactive organization still gets its zip.

    Args:
        run_id (str):
        tamarind_version (str | Unset):
        body (GetPipelineRunResultsBodyType0 | None | Unset): Optional; no body, `null` or `{}` is
            the whole run's zip.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Problem | ResultsPreparing | ResultsReady
    """

    return sync_detailed(
        run_id=run_id,
        client=client,
        body=body,
        tamarind_version=tamarind_version,
    ).parsed


async def asyncio_detailed(
    run_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: GetPipelineRunResultsBodyType0 | None | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Response[Problem | ResultsPreparing | ResultsReady]:
    """Get a zip of a pipeline run's outputs

     Until the rename from `/archive` merges (decision 75, not yet), the server answers at
    `POST /pipelines/runs/{runId}/archive`. Waits up to 25 seconds for the zip. 200 means ready,
    with the zip's size and the link's expiry; `fileCount` and `truncated` are null, because
    nothing records them for a run's zip.
    202 means still preparing, so call again after `retryAfterSeconds` (10, also sent as
    `Retry-After`). It is also 202 while the run (or the node run you named) hasn't finished: the
    zip is built only once it has. A zip that could not be built is 409 `archive_failed`,
    retryable after `Retry-After` (90 seconds), when the results service builds again. An
    organization that has lost read access gets 403 `organization_export_disabled` unless the zip
    already exists. A suspended or inactive organization still gets its zip.

    Args:
        run_id (str):
        tamarind_version (str | Unset):
        body (GetPipelineRunResultsBodyType0 | None | Unset): Optional; no body, `null` or `{}` is
            the whole run's zip.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Problem | ResultsPreparing | ResultsReady]
    """

    kwargs = _get_kwargs(
        run_id=run_id,
        body=body,
        tamarind_version=tamarind_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    run_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: GetPipelineRunResultsBodyType0 | None | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Problem | ResultsPreparing | ResultsReady | None:
    """Get a zip of a pipeline run's outputs

     Until the rename from `/archive` merges (decision 75, not yet), the server answers at
    `POST /pipelines/runs/{runId}/archive`. Waits up to 25 seconds for the zip. 200 means ready,
    with the zip's size and the link's expiry; `fileCount` and `truncated` are null, because
    nothing records them for a run's zip.
    202 means still preparing, so call again after `retryAfterSeconds` (10, also sent as
    `Retry-After`). It is also 202 while the run (or the node run you named) hasn't finished: the
    zip is built only once it has. A zip that could not be built is 409 `archive_failed`,
    retryable after `Retry-After` (90 seconds), when the results service builds again. An
    organization that has lost read access gets 403 `organization_export_disabled` unless the zip
    already exists. A suspended or inactive organization still gets its zip.

    Args:
        run_id (str):
        tamarind_version (str | Unset):
        body (GetPipelineRunResultsBodyType0 | None | Unset): Optional; no body, `null` or `{}` is
            the whole run's zip.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Problem | ResultsPreparing | ResultsReady
    """

    return (
        await asyncio_detailed(
            run_id=run_id,
            client=client,
            body=body,
            tamarind_version=tamarind_version,
        )
    ).parsed
