from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.pipeline_template import PipelineTemplate
from ...models.problem import Problem
from ...types import UNSET, Response, Unset


def _get_kwargs(
    template_id: str,
    *,
    version: None | str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(tamarind_version, Unset):
        headers["Tamarind-Version"] = tamarind_version

    params: dict[str, Any] = {}

    json_version: None | str | Unset
    if isinstance(version, Unset):
        json_version = UNSET
    else:
        json_version = version
    params["version"] = json_version

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/pipelines/templates/{template_id}".format(
            template_id=quote(str(template_id), safe=""),
        ),
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> PipelineTemplate | Problem:
    if response.status_code == 200:
        response_200 = PipelineTemplate.from_dict(response.json())

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
    version: None | str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Response[PipelineTemplate | Problem]:
    """Get a pipeline template

     Retrieve a template by id to view its nodes and required inputs.

    Args:
        template_id (str):
        version (None | str | Unset): A specific version to view (a `vN` handle); omit for the
            current version.
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PipelineTemplate | Problem]
    """

    kwargs = _get_kwargs(
        template_id=template_id,
        version=version,
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
    version: None | str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> PipelineTemplate | Problem | None:
    """Get a pipeline template

     Retrieve a template by id to view its nodes and required inputs.

    Args:
        template_id (str):
        version (None | str | Unset): A specific version to view (a `vN` handle); omit for the
            current version.
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PipelineTemplate | Problem
    """

    return sync_detailed(
        template_id=template_id,
        client=client,
        version=version,
        tamarind_version=tamarind_version,
    ).parsed


async def asyncio_detailed(
    template_id: str,
    *,
    client: AuthenticatedClient | Client,
    version: None | str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Response[PipelineTemplate | Problem]:
    """Get a pipeline template

     Retrieve a template by id to view its nodes and required inputs.

    Args:
        template_id (str):
        version (None | str | Unset): A specific version to view (a `vN` handle); omit for the
            current version.
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PipelineTemplate | Problem]
    """

    kwargs = _get_kwargs(
        template_id=template_id,
        version=version,
        tamarind_version=tamarind_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    template_id: str,
    *,
    client: AuthenticatedClient | Client,
    version: None | str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> PipelineTemplate | Problem | None:
    """Get a pipeline template

     Retrieve a template by id to view its nodes and required inputs.

    Args:
        template_id (str):
        version (None | str | Unset): A specific version to view (a `vN` handle); omit for the
            current version.
        tamarind_version (str | Unset):

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
            version=version,
            tamarind_version=tamarind_version,
        )
    ).parsed
