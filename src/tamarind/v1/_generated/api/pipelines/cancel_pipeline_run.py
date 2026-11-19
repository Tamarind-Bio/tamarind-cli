from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.pipeline_run import PipelineRun
from ...models.problem import Problem
from ...types import UNSET, Response, Unset


def _get_kwargs(
    run_id: str,
    *,
    tamarind_version: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(tamarind_version, Unset):
        headers["Tamarind-Version"] = tamarind_version

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/pipelines/runs/{run_id}/cancel".format(
            run_id=quote(str(run_id), safe=""),
        ),
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> PipelineRun | Problem:
    if response.status_code == 200:
        response_200 = PipelineRun.from_dict(response.json())

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
) -> Response[PipelineRun | Problem]:
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
    tamarind_version: str | Unset = UNSET,
) -> Response[PipelineRun | Problem]:
    """Stop a pipeline run

     Stop a pipeline run.

    Any jobs which have not yet completed are stopped, including running jobs.
    Outputs of any completed jobs are saved and may be viewed.

    Canceling a run that already ended answers 200 with the status it ended with. If the run stopped but
    stopping its jobs failed, the answer is 502 `upstream_unavailable`: cancel again, which sweeps them
    again. `POST /jobs/{runId}/cancel` runs the same cancel.

    Args:
        run_id (str):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PipelineRun | Problem]
    """

    kwargs = _get_kwargs(
        run_id=run_id,
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
    tamarind_version: str | Unset = UNSET,
) -> PipelineRun | Problem | None:
    """Stop a pipeline run

     Stop a pipeline run.

    Any jobs which have not yet completed are stopped, including running jobs.
    Outputs of any completed jobs are saved and may be viewed.

    Canceling a run that already ended answers 200 with the status it ended with. If the run stopped but
    stopping its jobs failed, the answer is 502 `upstream_unavailable`: cancel again, which sweeps them
    again. `POST /jobs/{runId}/cancel` runs the same cancel.

    Args:
        run_id (str):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PipelineRun | Problem
    """

    return sync_detailed(
        run_id=run_id,
        client=client,
        tamarind_version=tamarind_version,
    ).parsed


async def asyncio_detailed(
    run_id: str,
    *,
    client: AuthenticatedClient | Client,
    tamarind_version: str | Unset = UNSET,
) -> Response[PipelineRun | Problem]:
    """Stop a pipeline run

     Stop a pipeline run.

    Any jobs which have not yet completed are stopped, including running jobs.
    Outputs of any completed jobs are saved and may be viewed.

    Canceling a run that already ended answers 200 with the status it ended with. If the run stopped but
    stopping its jobs failed, the answer is 502 `upstream_unavailable`: cancel again, which sweeps them
    again. `POST /jobs/{runId}/cancel` runs the same cancel.

    Args:
        run_id (str):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PipelineRun | Problem]
    """

    kwargs = _get_kwargs(
        run_id=run_id,
        tamarind_version=tamarind_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    run_id: str,
    *,
    client: AuthenticatedClient | Client,
    tamarind_version: str | Unset = UNSET,
) -> PipelineRun | Problem | None:
    """Stop a pipeline run

     Stop a pipeline run.

    Any jobs which have not yet completed are stopped, including running jobs.
    Outputs of any completed jobs are saved and may be viewed.

    Canceling a run that already ended answers 200 with the status it ended with. If the run stopped but
    stopping its jobs failed, the answer is 502 `upstream_unavailable`: cancel again, which sweeps them
    again. `POST /jobs/{runId}/cancel` runs the same cancel.

    Args:
        run_id (str):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PipelineRun | Problem
    """

    return (
        await asyncio_detailed(
            run_id=run_id,
            client=client,
            tamarind_version=tamarind_version,
        )
    ).parsed
