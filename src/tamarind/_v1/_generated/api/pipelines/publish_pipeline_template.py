from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.problem import Problem
from ...models.publish_pipeline_template_request import PublishPipelineTemplateRequest
from ...models.publish_response import PublishResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    template_id: str,
    *,
    body: PublishPipelineTemplateRequest,
    tamarind_version: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(tamarind_version, Unset):
        headers["Tamarind-Version"] = tamarind_version

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/pipelines/templates/{template_id}/publish".format(
            template_id=quote(str(template_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Problem | PublishResponse:
    if response.status_code == 200:
        response_200 = PublishResponse.from_dict(response.json())

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
) -> Response[Problem | PublishResponse]:
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
    body: PublishPipelineTemplateRequest,
    tamarind_version: str | Unset = UNSET,
) -> Response[Problem | PublishResponse]:
    """Publish a template version

     Publish a version of your pipeline template to your organization.

    Others in your organization may only run pipelines published to the organization

    Only one version can be published at a time

    Args:
        template_id (str):
        tamarind_version (str | Unset):
        body (PublishPipelineTemplateRequest):  Example: {'version': 'v1'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Problem | PublishResponse]
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
    body: PublishPipelineTemplateRequest,
    tamarind_version: str | Unset = UNSET,
) -> Problem | PublishResponse | None:
    """Publish a template version

     Publish a version of your pipeline template to your organization.

    Others in your organization may only run pipelines published to the organization

    Only one version can be published at a time

    Args:
        template_id (str):
        tamarind_version (str | Unset):
        body (PublishPipelineTemplateRequest):  Example: {'version': 'v1'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Problem | PublishResponse
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
    body: PublishPipelineTemplateRequest,
    tamarind_version: str | Unset = UNSET,
) -> Response[Problem | PublishResponse]:
    """Publish a template version

     Publish a version of your pipeline template to your organization.

    Others in your organization may only run pipelines published to the organization

    Only one version can be published at a time

    Args:
        template_id (str):
        tamarind_version (str | Unset):
        body (PublishPipelineTemplateRequest):  Example: {'version': 'v1'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Problem | PublishResponse]
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
    body: PublishPipelineTemplateRequest,
    tamarind_version: str | Unset = UNSET,
) -> Problem | PublishResponse | None:
    """Publish a template version

     Publish a version of your pipeline template to your organization.

    Others in your organization may only run pipelines published to the organization

    Only one version can be published at a time

    Args:
        template_id (str):
        tamarind_version (str | Unset):
        body (PublishPipelineTemplateRequest):  Example: {'version': 'v1'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Problem | PublishResponse
    """

    return (
        await asyncio_detailed(
            template_id=template_id,
            client=client,
            body=body,
            tamarind_version=tamarind_version,
        )
    ).parsed
