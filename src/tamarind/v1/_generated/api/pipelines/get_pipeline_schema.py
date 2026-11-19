from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.get_pipeline_schema_response_200 import GetPipelineSchemaResponse200
from ...models.problem import Problem
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    tamarind_version: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(tamarind_version, Unset):
        headers["Tamarind-Version"] = tamarind_version

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/pipelines/schema",
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> GetPipelineSchemaResponse200 | Problem:
    if response.status_code == 200:
        response_200 = GetPipelineSchemaResponse200.from_dict(response.json())

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
) -> Response[GetPipelineSchemaResponse200 | Problem]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    tamarind_version: str | Unset = UNSET,
) -> Response[GetPipelineSchemaResponse200 | Problem]:
    """Get the pipeline graph schema and authoring guide

     Read this before writing a `pipeline` graph. The guide's API walkthrough is written for this API. At
    launch it answers without a key, as today's public pipeline guide does, and requests without a key
    share one overall rate limit. Until launch it needs a key (401 without one) and, while v1 is behind
    the `api-v1` flag, a caller the flag covers.

    Args:
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetPipelineSchemaResponse200 | Problem]
    """

    kwargs = _get_kwargs(
        tamarind_version=tamarind_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    tamarind_version: str | Unset = UNSET,
) -> GetPipelineSchemaResponse200 | Problem | None:
    """Get the pipeline graph schema and authoring guide

     Read this before writing a `pipeline` graph. The guide's API walkthrough is written for this API. At
    launch it answers without a key, as today's public pipeline guide does, and requests without a key
    share one overall rate limit. Until launch it needs a key (401 without one) and, while v1 is behind
    the `api-v1` flag, a caller the flag covers.

    Args:
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetPipelineSchemaResponse200 | Problem
    """

    return sync_detailed(
        client=client,
        tamarind_version=tamarind_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    tamarind_version: str | Unset = UNSET,
) -> Response[GetPipelineSchemaResponse200 | Problem]:
    """Get the pipeline graph schema and authoring guide

     Read this before writing a `pipeline` graph. The guide's API walkthrough is written for this API. At
    launch it answers without a key, as today's public pipeline guide does, and requests without a key
    share one overall rate limit. Until launch it needs a key (401 without one) and, while v1 is behind
    the `api-v1` flag, a caller the flag covers.

    Args:
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetPipelineSchemaResponse200 | Problem]
    """

    kwargs = _get_kwargs(
        tamarind_version=tamarind_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    tamarind_version: str | Unset = UNSET,
) -> GetPipelineSchemaResponse200 | Problem | None:
    """Get the pipeline graph schema and authoring guide

     Read this before writing a `pipeline` graph. The guide's API walkthrough is written for this API. At
    launch it answers without a key, as today's public pipeline guide does, and requests without a key
    share one overall rate limit. Until launch it needs a key (401 without one) and, while v1 is behind
    the `api-v1` flag, a caller the flag covers.

    Args:
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetPipelineSchemaResponse200 | Problem
    """

    return (
        await asyncio_detailed(
            client=client,
            tamarind_version=tamarind_version,
        )
    ).parsed
