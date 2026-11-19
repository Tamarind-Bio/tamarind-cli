from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.pipeline_run import PipelineRun
from ...models.problem import Problem
from ...models.submit_pipeline_graph_request import SubmitPipelineGraphRequest
from ...models.submit_pipeline_template_request import SubmitPipelineTemplateRequest
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    body: SubmitPipelineGraphRequest | SubmitPipelineTemplateRequest,
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
        "url": "/pipelines/runs",
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
) -> PipelineRun | Problem:
    if response.status_code == 201:
        response_201 = PipelineRun.from_dict(response.json())

        return response_201

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

    if response.status_code == 500:
        response_500 = Problem.from_dict(response.json())

        return response_500

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
    *,
    client: AuthenticatedClient | Client,
    body: SubmitPipelineGraphRequest | SubmitPipelineTemplateRequest,
    idempotency_key: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Response[PipelineRun | Problem]:
    """Submit a pipeline run

     Submit a pipeline run from an existing template, or from a new pipeline graph.

    Provide a `bindings` map, which defines the molecules/files you want to use for each input node in
    your pipeline. If your input contains chains, define the mapping of chain IDs between your molecule
    and the pipeline's reference/default (if running against an existing template).

    Bindings may be defined as an array of sequences, smiles, or sdf/pdb files (uploaded using `POST
    /files`), or an existing molecule group id (created using /molecules/groups below).

    If applicable, put residue selections inside each binding's `residuesByChain` for the tools that
    require hotspots / designed residues. Two shapes, auto-detected by the value: SIMPLE `{chain:
    ranges}` (a chain maps to a range string) fans one selection to every residue field the input feeds;
    ADVANCED `{toolNodeId: {field: {chain: ranges}}}` (a node maps to a per-field object) picks per
    (tool node, field). An inline submit is stamped Simplified/Advanced from the shape you send; picks
    under each binding are merged. Chain and residue selections can also be supplied in tool-node
    `settings` or top-level per-node `settings`. Reference chain labels follow `chainMapping`.
    Conflicting inline and binding residue selections are rejected.

    The engine records a run a moment after accepting it, so submit reads it back for up to about 4.5
    seconds. The 201 is then the run as `GET /pipelines/runs/{runId}` reads it, which can already be
    `running` with node runs. If it isn't readable yet, the 201 is the accepted run: `queued`, with no
    node runs. Poll `GET /pipelines/runs/{runId}` for progress. Problems found while the engine resolves
    the run are reported there as a failed run.

    The run records the channel it came from (`api`, or the `X-Tamarind-Client-Channel` you declare), as
    `POST /jobs` does. A `projectId` you can't use is 422 at `/projectId`, never silently dropped. An
    `Idempotency-Key` is this operation's own, separate from `POST /jobs`; today's `POST
    /pipelines/submit` is the same operation, so a key and request first sent there replay that run
    here. A replay whose run isn't readable yet is 409 `idempotency_in_progress` (retry shortly); one
    whose run you can no longer read is 404.

    Choose from your pipelines or example templates to view example scripts.

    Args:
        idempotency_key (str | Unset):
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
        Response[PipelineRun | Problem]
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
    body: SubmitPipelineGraphRequest | SubmitPipelineTemplateRequest,
    idempotency_key: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> PipelineRun | Problem | None:
    """Submit a pipeline run

     Submit a pipeline run from an existing template, or from a new pipeline graph.

    Provide a `bindings` map, which defines the molecules/files you want to use for each input node in
    your pipeline. If your input contains chains, define the mapping of chain IDs between your molecule
    and the pipeline's reference/default (if running against an existing template).

    Bindings may be defined as an array of sequences, smiles, or sdf/pdb files (uploaded using `POST
    /files`), or an existing molecule group id (created using /molecules/groups below).

    If applicable, put residue selections inside each binding's `residuesByChain` for the tools that
    require hotspots / designed residues. Two shapes, auto-detected by the value: SIMPLE `{chain:
    ranges}` (a chain maps to a range string) fans one selection to every residue field the input feeds;
    ADVANCED `{toolNodeId: {field: {chain: ranges}}}` (a node maps to a per-field object) picks per
    (tool node, field). An inline submit is stamped Simplified/Advanced from the shape you send; picks
    under each binding are merged. Chain and residue selections can also be supplied in tool-node
    `settings` or top-level per-node `settings`. Reference chain labels follow `chainMapping`.
    Conflicting inline and binding residue selections are rejected.

    The engine records a run a moment after accepting it, so submit reads it back for up to about 4.5
    seconds. The 201 is then the run as `GET /pipelines/runs/{runId}` reads it, which can already be
    `running` with node runs. If it isn't readable yet, the 201 is the accepted run: `queued`, with no
    node runs. Poll `GET /pipelines/runs/{runId}` for progress. Problems found while the engine resolves
    the run are reported there as a failed run.

    The run records the channel it came from (`api`, or the `X-Tamarind-Client-Channel` you declare), as
    `POST /jobs` does. A `projectId` you can't use is 422 at `/projectId`, never silently dropped. An
    `Idempotency-Key` is this operation's own, separate from `POST /jobs`; today's `POST
    /pipelines/submit` is the same operation, so a key and request first sent there replay that run
    here. A replay whose run isn't readable yet is 409 `idempotency_in_progress` (retry shortly); one
    whose run you can no longer read is 404.

    Choose from your pipelines or example templates to view example scripts.

    Args:
        idempotency_key (str | Unset):
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
        PipelineRun | Problem
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
    body: SubmitPipelineGraphRequest | SubmitPipelineTemplateRequest,
    idempotency_key: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Response[PipelineRun | Problem]:
    """Submit a pipeline run

     Submit a pipeline run from an existing template, or from a new pipeline graph.

    Provide a `bindings` map, which defines the molecules/files you want to use for each input node in
    your pipeline. If your input contains chains, define the mapping of chain IDs between your molecule
    and the pipeline's reference/default (if running against an existing template).

    Bindings may be defined as an array of sequences, smiles, or sdf/pdb files (uploaded using `POST
    /files`), or an existing molecule group id (created using /molecules/groups below).

    If applicable, put residue selections inside each binding's `residuesByChain` for the tools that
    require hotspots / designed residues. Two shapes, auto-detected by the value: SIMPLE `{chain:
    ranges}` (a chain maps to a range string) fans one selection to every residue field the input feeds;
    ADVANCED `{toolNodeId: {field: {chain: ranges}}}` (a node maps to a per-field object) picks per
    (tool node, field). An inline submit is stamped Simplified/Advanced from the shape you send; picks
    under each binding are merged. Chain and residue selections can also be supplied in tool-node
    `settings` or top-level per-node `settings`. Reference chain labels follow `chainMapping`.
    Conflicting inline and binding residue selections are rejected.

    The engine records a run a moment after accepting it, so submit reads it back for up to about 4.5
    seconds. The 201 is then the run as `GET /pipelines/runs/{runId}` reads it, which can already be
    `running` with node runs. If it isn't readable yet, the 201 is the accepted run: `queued`, with no
    node runs. Poll `GET /pipelines/runs/{runId}` for progress. Problems found while the engine resolves
    the run are reported there as a failed run.

    The run records the channel it came from (`api`, or the `X-Tamarind-Client-Channel` you declare), as
    `POST /jobs` does. A `projectId` you can't use is 422 at `/projectId`, never silently dropped. An
    `Idempotency-Key` is this operation's own, separate from `POST /jobs`; today's `POST
    /pipelines/submit` is the same operation, so a key and request first sent there replay that run
    here. A replay whose run isn't readable yet is 409 `idempotency_in_progress` (retry shortly); one
    whose run you can no longer read is 404.

    Choose from your pipelines or example templates to view example scripts.

    Args:
        idempotency_key (str | Unset):
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
        Response[PipelineRun | Problem]
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
    body: SubmitPipelineGraphRequest | SubmitPipelineTemplateRequest,
    idempotency_key: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> PipelineRun | Problem | None:
    """Submit a pipeline run

     Submit a pipeline run from an existing template, or from a new pipeline graph.

    Provide a `bindings` map, which defines the molecules/files you want to use for each input node in
    your pipeline. If your input contains chains, define the mapping of chain IDs between your molecule
    and the pipeline's reference/default (if running against an existing template).

    Bindings may be defined as an array of sequences, smiles, or sdf/pdb files (uploaded using `POST
    /files`), or an existing molecule group id (created using /molecules/groups below).

    If applicable, put residue selections inside each binding's `residuesByChain` for the tools that
    require hotspots / designed residues. Two shapes, auto-detected by the value: SIMPLE `{chain:
    ranges}` (a chain maps to a range string) fans one selection to every residue field the input feeds;
    ADVANCED `{toolNodeId: {field: {chain: ranges}}}` (a node maps to a per-field object) picks per
    (tool node, field). An inline submit is stamped Simplified/Advanced from the shape you send; picks
    under each binding are merged. Chain and residue selections can also be supplied in tool-node
    `settings` or top-level per-node `settings`. Reference chain labels follow `chainMapping`.
    Conflicting inline and binding residue selections are rejected.

    The engine records a run a moment after accepting it, so submit reads it back for up to about 4.5
    seconds. The 201 is then the run as `GET /pipelines/runs/{runId}` reads it, which can already be
    `running` with node runs. If it isn't readable yet, the 201 is the accepted run: `queued`, with no
    node runs. Poll `GET /pipelines/runs/{runId}` for progress. Problems found while the engine resolves
    the run are reported there as a failed run.

    The run records the channel it came from (`api`, or the `X-Tamarind-Client-Channel` you declare), as
    `POST /jobs` does. A `projectId` you can't use is 422 at `/projectId`, never silently dropped. An
    `Idempotency-Key` is this operation's own, separate from `POST /jobs`; today's `POST
    /pipelines/submit` is the same operation, so a key and request first sent there replay that run
    here. A replay whose run isn't readable yet is 409 `idempotency_in_progress` (retry shortly); one
    whose run you can no longer read is 404.

    Choose from your pipelines or example templates to view example scripts.

    Args:
        idempotency_key (str | Unset):
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
        PipelineRun | Problem
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            idempotency_key=idempotency_key,
            tamarind_version=tamarind_version,
        )
    ).parsed
