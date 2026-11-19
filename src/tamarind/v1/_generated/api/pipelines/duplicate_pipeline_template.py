from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.duplicate_pipeline_template_request import DuplicatePipelineTemplateRequest
from ...models.pipeline_template import PipelineTemplate
from ...models.problem import Problem
from ...types import UNSET, Response, Unset


def _get_kwargs(
    template_id: str,
    *,
    body: DuplicatePipelineTemplateRequest | None | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(tamarind_version, Unset):
        headers["Tamarind-Version"] = tamarind_version

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/pipelines/templates/{template_id}/duplicate".format(
            template_id=quote(str(template_id), safe=""),
        ),
    }

    if isinstance(body, DuplicatePipelineTemplateRequest):
        _kwargs["json"] = body.to_dict()
    else:
        _kwargs["json"] = body

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
) -> Response[PipelineTemplate | Problem]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    template_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: DuplicatePipelineTemplateRequest | None | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Response[PipelineTemplate | Problem]:
    """Duplicate a pipeline template

     Create a copy of a version of your existing pipeline (latest by default).

    Args:
        template_id (str):
        tamarind_version (str | Unset):
        body (DuplicatePipelineTemplateRequest | None | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PipelineTemplate | Problem]
    """

    kwargs = _get_kwargs(
        template_id=template_id,
        body=body,
        tamarind_version=tamarind_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    template_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: DuplicatePipelineTemplateRequest | None | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> PipelineTemplate | Problem | None:
    """Duplicate a pipeline template

     Create a copy of a version of your existing pipeline (latest by default).

    Args:
        template_id (str):
        tamarind_version (str | Unset):
        body (DuplicatePipelineTemplateRequest | None | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PipelineTemplate | Problem
    """

    return sync_detailed(
        template_id=template_id,
        client=client,
        body=body,
        tamarind_version=tamarind_version,
    ).parsed


async def asyncio_detailed(
    template_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: DuplicatePipelineTemplateRequest | None | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Response[PipelineTemplate | Problem]:
    """Duplicate a pipeline template

     Create a copy of a version of your existing pipeline (latest by default).

    Args:
        template_id (str):
        tamarind_version (str | Unset):
        body (DuplicatePipelineTemplateRequest | None | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PipelineTemplate | Problem]
    """

    kwargs = _get_kwargs(
        template_id=template_id,
        body=body,
        tamarind_version=tamarind_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    template_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: DuplicatePipelineTemplateRequest | None | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> PipelineTemplate | Problem | None:
    """Duplicate a pipeline template

     Create a copy of a version of your existing pipeline (latest by default).

    Args:
        template_id (str):
        tamarind_version (str | Unset):
        body (DuplicatePipelineTemplateRequest | None | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PipelineTemplate | Problem
    """

    return (
        await asyncio_detailed(
            template_id=template_id,
            client=client,
            body=body,
            tamarind_version=tamarind_version,
        )
    ).parsed
