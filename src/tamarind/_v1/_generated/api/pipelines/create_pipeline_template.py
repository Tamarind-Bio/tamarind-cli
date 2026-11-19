from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.create_pipeline_template_request import CreatePipelineTemplateRequest
from ...models.pipeline_template import PipelineTemplate
from ...models.problem import Problem
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    body: CreatePipelineTemplateRequest,
    tamarind_version: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(tamarind_version, Unset):
        headers["Tamarind-Version"] = tamarind_version

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/pipelines/templates",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> PipelineTemplate | Problem:
    if response.status_code == 201:
        response_201 = PipelineTemplate.from_dict(response.json())

        return response_201

    if response.status_code == 400:
        response_400 = Problem.from_dict(response.json())

        return response_400

    if response.status_code == 401:
        response_401 = Problem.from_dict(response.json())

        return response_401

    if response.status_code == 403:
        response_403 = Problem.from_dict(response.json())

        return response_403

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
) -> Response[PipelineTemplate | Problem]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreatePipelineTemplateRequest,
    tamarind_version: str | Unset = UNSET,
) -> Response[PipelineTemplate | Problem]:
    """Create a pipeline template

     Create a pipeline template from a `pipeline` graph of inputs, tools, and filters.

    - The graph is validated on create
    - This first save becomes the template's first version; every later save adds a new immutable
    version

    Args:
        tamarind_version (str | Unset):
        body (CreatePipelineTemplateRequest):  Example: {'description': 'AF2 + ProteinMPNN',
            'name': 'binder-design', 'pipeline': {'nodes': {'af2': {'inputs': {'sequence': [{'node':
            'target'}]}, 'kind': 'tool', 'tool': 'tamarind://alphafold'}, 'target': {'flow':
            'molecule', 'kind': 'user_input', 'metadata': {'defaultGroup':
            '3f8a1c2e-5b7d-4e9f-a1b2-c3d4e5f6a7b8'}, 'molecule_type': 'protein'}}, 'schema_version':
            '1.0'}}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PipelineTemplate | Problem]
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
    body: CreatePipelineTemplateRequest,
    tamarind_version: str | Unset = UNSET,
) -> PipelineTemplate | Problem | None:
    """Create a pipeline template

     Create a pipeline template from a `pipeline` graph of inputs, tools, and filters.

    - The graph is validated on create
    - This first save becomes the template's first version; every later save adds a new immutable
    version

    Args:
        tamarind_version (str | Unset):
        body (CreatePipelineTemplateRequest):  Example: {'description': 'AF2 + ProteinMPNN',
            'name': 'binder-design', 'pipeline': {'nodes': {'af2': {'inputs': {'sequence': [{'node':
            'target'}]}, 'kind': 'tool', 'tool': 'tamarind://alphafold'}, 'target': {'flow':
            'molecule', 'kind': 'user_input', 'metadata': {'defaultGroup':
            '3f8a1c2e-5b7d-4e9f-a1b2-c3d4e5f6a7b8'}, 'molecule_type': 'protein'}}, 'schema_version':
            '1.0'}}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PipelineTemplate | Problem
    """

    return sync_detailed(
        client=client,
        body=body,
        tamarind_version=tamarind_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreatePipelineTemplateRequest,
    tamarind_version: str | Unset = UNSET,
) -> Response[PipelineTemplate | Problem]:
    """Create a pipeline template

     Create a pipeline template from a `pipeline` graph of inputs, tools, and filters.

    - The graph is validated on create
    - This first save becomes the template's first version; every later save adds a new immutable
    version

    Args:
        tamarind_version (str | Unset):
        body (CreatePipelineTemplateRequest):  Example: {'description': 'AF2 + ProteinMPNN',
            'name': 'binder-design', 'pipeline': {'nodes': {'af2': {'inputs': {'sequence': [{'node':
            'target'}]}, 'kind': 'tool', 'tool': 'tamarind://alphafold'}, 'target': {'flow':
            'molecule', 'kind': 'user_input', 'metadata': {'defaultGroup':
            '3f8a1c2e-5b7d-4e9f-a1b2-c3d4e5f6a7b8'}, 'molecule_type': 'protein'}}, 'schema_version':
            '1.0'}}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PipelineTemplate | Problem]
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
    body: CreatePipelineTemplateRequest,
    tamarind_version: str | Unset = UNSET,
) -> PipelineTemplate | Problem | None:
    """Create a pipeline template

     Create a pipeline template from a `pipeline` graph of inputs, tools, and filters.

    - The graph is validated on create
    - This first save becomes the template's first version; every later save adds a new immutable
    version

    Args:
        tamarind_version (str | Unset):
        body (CreatePipelineTemplateRequest):  Example: {'description': 'AF2 + ProteinMPNN',
            'name': 'binder-design', 'pipeline': {'nodes': {'af2': {'inputs': {'sequence': [{'node':
            'target'}]}, 'kind': 'tool', 'tool': 'tamarind://alphafold'}, 'target': {'flow':
            'molecule', 'kind': 'user_input', 'metadata': {'defaultGroup':
            '3f8a1c2e-5b7d-4e9f-a1b2-c3d4e5f6a7b8'}, 'molecule_type': 'protein'}}, 'schema_version':
            '1.0'}}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PipelineTemplate | Problem
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            tamarind_version=tamarind_version,
        )
    ).parsed
