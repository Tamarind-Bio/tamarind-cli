from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.list_pipeline_templates_scope_type_0 import ListPipelineTemplatesScopeType0
from ...models.pipeline_template_page import PipelineTemplatePage
from ...models.problem import Problem
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    published: bool | None | Unset = UNSET,
    scope: ListPipelineTemplatesScopeType0 | None | Unset = UNSET,
    search: None | str | Unset = UNSET,
    limit: int | Unset = 50,
    cursor: None | str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(tamarind_version, Unset):
        headers["Tamarind-Version"] = tamarind_version

    params: dict[str, Any] = {}

    json_published: bool | None | Unset
    if isinstance(published, Unset):
        json_published = UNSET
    else:
        json_published = published
    params["published"] = json_published

    json_scope: None | str | Unset
    if isinstance(scope, Unset):
        json_scope = UNSET
    elif isinstance(scope, ListPipelineTemplatesScopeType0):
        json_scope = scope.value
    else:
        json_scope = scope
    params["scope"] = json_scope

    json_search: None | str | Unset
    if isinstance(search, Unset):
        json_search = UNSET
    else:
        json_search = search
    params["search"] = json_search

    params["limit"] = limit

    json_cursor: None | str | Unset
    if isinstance(cursor, Unset):
        json_cursor = UNSET
    else:
        json_cursor = cursor
    params["cursor"] = json_cursor

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/pipelines/templates",
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> PipelineTemplatePage | Problem:
    if response.status_code == 200:
        response_200 = PipelineTemplatePage.from_dict(response.json())

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
) -> Response[PipelineTemplatePage | Problem]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    published: bool | None | Unset = UNSET,
    scope: ListPipelineTemplatesScopeType0 | None | Unset = UNSET,
    search: None | str | Unset = UNSET,
    limit: int | Unset = 50,
    cursor: None | str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Response[PipelineTemplatePage | Problem]:
    """List pipeline templates

     List your pipeline templates, or with `scope=org` your organization's. A `scope` it doesn't know is
    400 `validation_failed`. The cursor is bound to the caller and the filters.

    Args:
        published (bool | None | Unset): Filter to published (`true`) or unpublished (`false`)
            templates.
        scope (ListPipelineTemplatesScopeType0 | None | Unset): Whose templates to list: `mine`
            (the default) or `org` for your whole organization.
        search (None | str | Unset): Search pipelines by name.
        limit (int | Unset): Maximum number of templates to return in one page. Default: 50.
        cursor (None | str | Unset): Pagination token from the previous response's `nextCursor`.
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PipelineTemplatePage | Problem]
    """

    kwargs = _get_kwargs(
        published=published,
        scope=scope,
        search=search,
        limit=limit,
        cursor=cursor,
        tamarind_version=tamarind_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    published: bool | None | Unset = UNSET,
    scope: ListPipelineTemplatesScopeType0 | None | Unset = UNSET,
    search: None | str | Unset = UNSET,
    limit: int | Unset = 50,
    cursor: None | str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> PipelineTemplatePage | Problem | None:
    """List pipeline templates

     List your pipeline templates, or with `scope=org` your organization's. A `scope` it doesn't know is
    400 `validation_failed`. The cursor is bound to the caller and the filters.

    Args:
        published (bool | None | Unset): Filter to published (`true`) or unpublished (`false`)
            templates.
        scope (ListPipelineTemplatesScopeType0 | None | Unset): Whose templates to list: `mine`
            (the default) or `org` for your whole organization.
        search (None | str | Unset): Search pipelines by name.
        limit (int | Unset): Maximum number of templates to return in one page. Default: 50.
        cursor (None | str | Unset): Pagination token from the previous response's `nextCursor`.
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PipelineTemplatePage | Problem
    """

    return sync_detailed(
        client=client,
        published=published,
        scope=scope,
        search=search,
        limit=limit,
        cursor=cursor,
        tamarind_version=tamarind_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    published: bool | None | Unset = UNSET,
    scope: ListPipelineTemplatesScopeType0 | None | Unset = UNSET,
    search: None | str | Unset = UNSET,
    limit: int | Unset = 50,
    cursor: None | str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Response[PipelineTemplatePage | Problem]:
    """List pipeline templates

     List your pipeline templates, or with `scope=org` your organization's. A `scope` it doesn't know is
    400 `validation_failed`. The cursor is bound to the caller and the filters.

    Args:
        published (bool | None | Unset): Filter to published (`true`) or unpublished (`false`)
            templates.
        scope (ListPipelineTemplatesScopeType0 | None | Unset): Whose templates to list: `mine`
            (the default) or `org` for your whole organization.
        search (None | str | Unset): Search pipelines by name.
        limit (int | Unset): Maximum number of templates to return in one page. Default: 50.
        cursor (None | str | Unset): Pagination token from the previous response's `nextCursor`.
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PipelineTemplatePage | Problem]
    """

    kwargs = _get_kwargs(
        published=published,
        scope=scope,
        search=search,
        limit=limit,
        cursor=cursor,
        tamarind_version=tamarind_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    published: bool | None | Unset = UNSET,
    scope: ListPipelineTemplatesScopeType0 | None | Unset = UNSET,
    search: None | str | Unset = UNSET,
    limit: int | Unset = 50,
    cursor: None | str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> PipelineTemplatePage | Problem | None:
    """List pipeline templates

     List your pipeline templates, or with `scope=org` your organization's. A `scope` it doesn't know is
    400 `validation_failed`. The cursor is bound to the caller and the filters.

    Args:
        published (bool | None | Unset): Filter to published (`true`) or unpublished (`false`)
            templates.
        scope (ListPipelineTemplatesScopeType0 | None | Unset): Whose templates to list: `mine`
            (the default) or `org` for your whole organization.
        search (None | str | Unset): Search pipelines by name.
        limit (int | Unset): Maximum number of templates to return in one page. Default: 50.
        cursor (None | str | Unset): Pagination token from the previous response's `nextCursor`.
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PipelineTemplatePage | Problem
    """

    return (
        await asyncio_detailed(
            client=client,
            published=published,
            scope=scope,
            search=search,
            limit=limit,
            cursor=cursor,
            tamarind_version=tamarind_version,
        )
    ).parsed
