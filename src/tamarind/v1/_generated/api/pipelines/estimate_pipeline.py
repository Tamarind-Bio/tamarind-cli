from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.pipeline_estimate import PipelineEstimate
from ...models.problem import Problem
from ...models.submit_pipeline_graph_request import SubmitPipelineGraphRequest
from ...models.submit_pipeline_template_request import SubmitPipelineTemplateRequest
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    body: SubmitPipelineGraphRequest | SubmitPipelineTemplateRequest,
    tamarind_version: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(tamarind_version, Unset):
        headers["Tamarind-Version"] = tamarind_version

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/pipelines/estimate",
    }

    if isinstance(body, SubmitPipelineGraphRequest):
        _kwargs["json"] = body.to_dict()
    else:
        _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> PipelineEstimate | Problem:
    if response.status_code == 200:
        response_200 = PipelineEstimate.from_dict(response.json())

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
) -> Response[PipelineEstimate | Problem]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: SubmitPipelineGraphRequest | SubmitPipelineTemplateRequest,
    tamarind_version: str | Unset = UNSET,
) -> Response[PipelineEstimate | Problem]:
    """Estimate a pipeline run

     Estimate the compute a run would use without creating or executing it. Uses the same settings as
    `submitPipeline`, and nothing is created, saved, or charged.

    `weightedHours` is the figure your budget is checked against when the run is submitted, and
    `breakdown` has one entry per pipeline node. `estimateFailed: true` means the run could not be
    priced, so the figures are not a quote. `assumptions` lists what the estimate takes for granted,
    chiefly that every molecule passes every filter.

    It applies submit's project rule: a `projectId` you can't use, or none where your organization
    requires one, is 422 at `/projectId`.

    Args:
        tamarind_version (str | Unset):
        body (SubmitPipelineGraphRequest | SubmitPipelineTemplateRequest): Body for
            `submitPipeline`, `validatePipeline` and `estimatePipeline` (identical shape). Two modes,
            discriminated by which of `pipeline` / `templateId` you send — exactly one is required.
            Neither is 422
            `required` at `/pipeline`, both is 422 `invalid` at `/templateId`, and `version` with
            `pipeline` is 422
            `unknown_field` at `/version`:

            - INLINE: send `pipeline` (a full IR) — submit creates a template you own (unpublished)
            and runs
              it; every setting is yours to set in the IR. `name` names both the created pipeline and
            the run.
            - REFERENCE: send `templateId` (+ optional `version`) — run an existing template;
            `settings`
              overrides are limited to each tool node's `metadata.editableSettings`. `name` names the
            run.

            `name` is required and doubles as the run's display name (deduplicated per pipeline).
            `bindings` is
            required in both modes. `validate` runs the SAME body without executing/persisting.
            Example: {'bindings': {'target': {'group': '3f8a1c2e-5b7d-4e9f-a1b2-c3d4e5f6a7b8'}},
            'name': 'binder-design v2 experiment', 'projectId': 'proj_…', 'settings': {'design':
            {'numSequences': 32}}, 'templateId': '3f2a1c9e-8b7d-4e6f-a1b2-c3d4e5f60718', 'version':
            'v1'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PipelineEstimate | Problem]
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
    body: SubmitPipelineGraphRequest | SubmitPipelineTemplateRequest,
    tamarind_version: str | Unset = UNSET,
) -> PipelineEstimate | Problem | None:
    """Estimate a pipeline run

     Estimate the compute a run would use without creating or executing it. Uses the same settings as
    `submitPipeline`, and nothing is created, saved, or charged.

    `weightedHours` is the figure your budget is checked against when the run is submitted, and
    `breakdown` has one entry per pipeline node. `estimateFailed: true` means the run could not be
    priced, so the figures are not a quote. `assumptions` lists what the estimate takes for granted,
    chiefly that every molecule passes every filter.

    It applies submit's project rule: a `projectId` you can't use, or none where your organization
    requires one, is 422 at `/projectId`.

    Args:
        tamarind_version (str | Unset):
        body (SubmitPipelineGraphRequest | SubmitPipelineTemplateRequest): Body for
            `submitPipeline`, `validatePipeline` and `estimatePipeline` (identical shape). Two modes,
            discriminated by which of `pipeline` / `templateId` you send — exactly one is required.
            Neither is 422
            `required` at `/pipeline`, both is 422 `invalid` at `/templateId`, and `version` with
            `pipeline` is 422
            `unknown_field` at `/version`:

            - INLINE: send `pipeline` (a full IR) — submit creates a template you own (unpublished)
            and runs
              it; every setting is yours to set in the IR. `name` names both the created pipeline and
            the run.
            - REFERENCE: send `templateId` (+ optional `version`) — run an existing template;
            `settings`
              overrides are limited to each tool node's `metadata.editableSettings`. `name` names the
            run.

            `name` is required and doubles as the run's display name (deduplicated per pipeline).
            `bindings` is
            required in both modes. `validate` runs the SAME body without executing/persisting.
            Example: {'bindings': {'target': {'group': '3f8a1c2e-5b7d-4e9f-a1b2-c3d4e5f6a7b8'}},
            'name': 'binder-design v2 experiment', 'projectId': 'proj_…', 'settings': {'design':
            {'numSequences': 32}}, 'templateId': '3f2a1c9e-8b7d-4e6f-a1b2-c3d4e5f60718', 'version':
            'v1'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PipelineEstimate | Problem
    """

    return sync_detailed(
        client=client,
        body=body,
        tamarind_version=tamarind_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: SubmitPipelineGraphRequest | SubmitPipelineTemplateRequest,
    tamarind_version: str | Unset = UNSET,
) -> Response[PipelineEstimate | Problem]:
    """Estimate a pipeline run

     Estimate the compute a run would use without creating or executing it. Uses the same settings as
    `submitPipeline`, and nothing is created, saved, or charged.

    `weightedHours` is the figure your budget is checked against when the run is submitted, and
    `breakdown` has one entry per pipeline node. `estimateFailed: true` means the run could not be
    priced, so the figures are not a quote. `assumptions` lists what the estimate takes for granted,
    chiefly that every molecule passes every filter.

    It applies submit's project rule: a `projectId` you can't use, or none where your organization
    requires one, is 422 at `/projectId`.

    Args:
        tamarind_version (str | Unset):
        body (SubmitPipelineGraphRequest | SubmitPipelineTemplateRequest): Body for
            `submitPipeline`, `validatePipeline` and `estimatePipeline` (identical shape). Two modes,
            discriminated by which of `pipeline` / `templateId` you send — exactly one is required.
            Neither is 422
            `required` at `/pipeline`, both is 422 `invalid` at `/templateId`, and `version` with
            `pipeline` is 422
            `unknown_field` at `/version`:

            - INLINE: send `pipeline` (a full IR) — submit creates a template you own (unpublished)
            and runs
              it; every setting is yours to set in the IR. `name` names both the created pipeline and
            the run.
            - REFERENCE: send `templateId` (+ optional `version`) — run an existing template;
            `settings`
              overrides are limited to each tool node's `metadata.editableSettings`. `name` names the
            run.

            `name` is required and doubles as the run's display name (deduplicated per pipeline).
            `bindings` is
            required in both modes. `validate` runs the SAME body without executing/persisting.
            Example: {'bindings': {'target': {'group': '3f8a1c2e-5b7d-4e9f-a1b2-c3d4e5f6a7b8'}},
            'name': 'binder-design v2 experiment', 'projectId': 'proj_…', 'settings': {'design':
            {'numSequences': 32}}, 'templateId': '3f2a1c9e-8b7d-4e6f-a1b2-c3d4e5f60718', 'version':
            'v1'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PipelineEstimate | Problem]
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
    body: SubmitPipelineGraphRequest | SubmitPipelineTemplateRequest,
    tamarind_version: str | Unset = UNSET,
) -> PipelineEstimate | Problem | None:
    """Estimate a pipeline run

     Estimate the compute a run would use without creating or executing it. Uses the same settings as
    `submitPipeline`, and nothing is created, saved, or charged.

    `weightedHours` is the figure your budget is checked against when the run is submitted, and
    `breakdown` has one entry per pipeline node. `estimateFailed: true` means the run could not be
    priced, so the figures are not a quote. `assumptions` lists what the estimate takes for granted,
    chiefly that every molecule passes every filter.

    It applies submit's project rule: a `projectId` you can't use, or none where your organization
    requires one, is 422 at `/projectId`.

    Args:
        tamarind_version (str | Unset):
        body (SubmitPipelineGraphRequest | SubmitPipelineTemplateRequest): Body for
            `submitPipeline`, `validatePipeline` and `estimatePipeline` (identical shape). Two modes,
            discriminated by which of `pipeline` / `templateId` you send — exactly one is required.
            Neither is 422
            `required` at `/pipeline`, both is 422 `invalid` at `/templateId`, and `version` with
            `pipeline` is 422
            `unknown_field` at `/version`:

            - INLINE: send `pipeline` (a full IR) — submit creates a template you own (unpublished)
            and runs
              it; every setting is yours to set in the IR. `name` names both the created pipeline and
            the run.
            - REFERENCE: send `templateId` (+ optional `version`) — run an existing template;
            `settings`
              overrides are limited to each tool node's `metadata.editableSettings`. `name` names the
            run.

            `name` is required and doubles as the run's display name (deduplicated per pipeline).
            `bindings` is
            required in both modes. `validate` runs the SAME body without executing/persisting.
            Example: {'bindings': {'target': {'group': '3f8a1c2e-5b7d-4e9f-a1b2-c3d4e5f6a7b8'}},
            'name': 'binder-design v2 experiment', 'projectId': 'proj_…', 'settings': {'design':
            {'numSequences': 32}}, 'templateId': '3f2a1c9e-8b7d-4e6f-a1b2-c3d4e5f60718', 'version':
            'v1'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PipelineEstimate | Problem
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            tamarind_version=tamarind_version,
        )
    ).parsed
