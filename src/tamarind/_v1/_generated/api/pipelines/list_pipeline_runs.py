from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.list_pipeline_runs_scope_type_0 import ListPipelineRunsScopeType0
from ...models.list_pipeline_runs_source_type_0 import ListPipelineRunsSourceType0
from ...models.pipeline_run_page import PipelineRunPage
from ...models.pipeline_run_status import PipelineRunStatus
from ...models.problem import Problem
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    status: None | PipelineRunStatus | Unset = UNSET,
    template_id: None | str | Unset = UNSET,
    scope: ListPipelineRunsScopeType0 | None | Unset = UNSET,
    source: ListPipelineRunsSourceType0 | None | Unset = UNSET,
    limit: int | Unset = 50,
    cursor: None | str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(tamarind_version, Unset):
        headers["Tamarind-Version"] = tamarind_version

    params: dict[str, Any] = {}

    json_status: None | str | Unset
    if isinstance(status, Unset):
        json_status = UNSET
    elif isinstance(status, PipelineRunStatus):
        json_status = status.value
    else:
        json_status = status
    params["status"] = json_status

    json_template_id: None | str | Unset
    if isinstance(template_id, Unset):
        json_template_id = UNSET
    else:
        json_template_id = template_id
    params["templateId"] = json_template_id

    json_scope: None | str | Unset
    if isinstance(scope, Unset):
        json_scope = UNSET
    elif isinstance(scope, ListPipelineRunsScopeType0):
        json_scope = scope.value
    else:
        json_scope = scope
    params["scope"] = json_scope

    json_source: None | str | Unset
    if isinstance(source, Unset):
        json_source = UNSET
    elif isinstance(source, ListPipelineRunsSourceType0):
        json_source = source.value
    else:
        json_source = source
    params["source"] = json_source

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
        "url": "/pipelines/runs",
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> PipelineRunPage | Problem:
    if response.status_code == 200:
        response_200 = PipelineRunPage.from_dict(response.json())

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
) -> Response[PipelineRunPage | Problem]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    status: None | PipelineRunStatus | Unset = UNSET,
    template_id: None | str | Unset = UNSET,
    scope: ListPipelineRunsScopeType0 | None | Unset = UNSET,
    source: ListPipelineRunsSourceType0 | None | Unset = UNSET,
    limit: int | Unset = 50,
    cursor: None | str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Response[PipelineRunPage | Problem]:
    """List pipeline runs

     List your pipeline runs, or with `scope=org` your organization's. A `status`, `scope` or `source` it
    doesn't know, or a `templateId` that isn't a template id, is 400 `validation_failed`, as on `GET
    /jobs`. The cursor is bound to the caller and the filters.

    Args:
        status (None | PipelineRunStatus | Unset): Filter by run status.
        template_id (None | str | Unset): Filter to runs of one pipeline (by template id). A value
            that isn't a template id is 400.
        scope (ListPipelineRunsScopeType0 | None | Unset): Whose runs to list: `mine` (the
            default) or `org` for your whole organization.
        source (ListPipelineRunsSourceType0 | None | Unset): Filter by run source: `test` or
            `production`.
        limit (int | Unset): Maximum number of runs to return in one page. Default: 50.
        cursor (None | str | Unset): Pagination token from the previous response's `nextCursor`.
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PipelineRunPage | Problem]
    """

    kwargs = _get_kwargs(
        status=status,
        template_id=template_id,
        scope=scope,
        source=source,
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
    status: None | PipelineRunStatus | Unset = UNSET,
    template_id: None | str | Unset = UNSET,
    scope: ListPipelineRunsScopeType0 | None | Unset = UNSET,
    source: ListPipelineRunsSourceType0 | None | Unset = UNSET,
    limit: int | Unset = 50,
    cursor: None | str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> PipelineRunPage | Problem | None:
    """List pipeline runs

     List your pipeline runs, or with `scope=org` your organization's. A `status`, `scope` or `source` it
    doesn't know, or a `templateId` that isn't a template id, is 400 `validation_failed`, as on `GET
    /jobs`. The cursor is bound to the caller and the filters.

    Args:
        status (None | PipelineRunStatus | Unset): Filter by run status.
        template_id (None | str | Unset): Filter to runs of one pipeline (by template id). A value
            that isn't a template id is 400.
        scope (ListPipelineRunsScopeType0 | None | Unset): Whose runs to list: `mine` (the
            default) or `org` for your whole organization.
        source (ListPipelineRunsSourceType0 | None | Unset): Filter by run source: `test` or
            `production`.
        limit (int | Unset): Maximum number of runs to return in one page. Default: 50.
        cursor (None | str | Unset): Pagination token from the previous response's `nextCursor`.
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PipelineRunPage | Problem
    """

    return sync_detailed(
        client=client,
        status=status,
        template_id=template_id,
        scope=scope,
        source=source,
        limit=limit,
        cursor=cursor,
        tamarind_version=tamarind_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    status: None | PipelineRunStatus | Unset = UNSET,
    template_id: None | str | Unset = UNSET,
    scope: ListPipelineRunsScopeType0 | None | Unset = UNSET,
    source: ListPipelineRunsSourceType0 | None | Unset = UNSET,
    limit: int | Unset = 50,
    cursor: None | str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Response[PipelineRunPage | Problem]:
    """List pipeline runs

     List your pipeline runs, or with `scope=org` your organization's. A `status`, `scope` or `source` it
    doesn't know, or a `templateId` that isn't a template id, is 400 `validation_failed`, as on `GET
    /jobs`. The cursor is bound to the caller and the filters.

    Args:
        status (None | PipelineRunStatus | Unset): Filter by run status.
        template_id (None | str | Unset): Filter to runs of one pipeline (by template id). A value
            that isn't a template id is 400.
        scope (ListPipelineRunsScopeType0 | None | Unset): Whose runs to list: `mine` (the
            default) or `org` for your whole organization.
        source (ListPipelineRunsSourceType0 | None | Unset): Filter by run source: `test` or
            `production`.
        limit (int | Unset): Maximum number of runs to return in one page. Default: 50.
        cursor (None | str | Unset): Pagination token from the previous response's `nextCursor`.
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PipelineRunPage | Problem]
    """

    kwargs = _get_kwargs(
        status=status,
        template_id=template_id,
        scope=scope,
        source=source,
        limit=limit,
        cursor=cursor,
        tamarind_version=tamarind_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    status: None | PipelineRunStatus | Unset = UNSET,
    template_id: None | str | Unset = UNSET,
    scope: ListPipelineRunsScopeType0 | None | Unset = UNSET,
    source: ListPipelineRunsSourceType0 | None | Unset = UNSET,
    limit: int | Unset = 50,
    cursor: None | str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> PipelineRunPage | Problem | None:
    """List pipeline runs

     List your pipeline runs, or with `scope=org` your organization's. A `status`, `scope` or `source` it
    doesn't know, or a `templateId` that isn't a template id, is 400 `validation_failed`, as on `GET
    /jobs`. The cursor is bound to the caller and the filters.

    Args:
        status (None | PipelineRunStatus | Unset): Filter by run status.
        template_id (None | str | Unset): Filter to runs of one pipeline (by template id). A value
            that isn't a template id is 400.
        scope (ListPipelineRunsScopeType0 | None | Unset): Whose runs to list: `mine` (the
            default) or `org` for your whole organization.
        source (ListPipelineRunsSourceType0 | None | Unset): Filter by run source: `test` or
            `production`.
        limit (int | Unset): Maximum number of runs to return in one page. Default: 50.
        cursor (None | str | Unset): Pagination token from the previous response's `nextCursor`.
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PipelineRunPage | Problem
    """

    return (
        await asyncio_detailed(
            client=client,
            status=status,
            template_id=template_id,
            scope=scope,
            source=source,
            limit=limit,
            cursor=cursor,
            tamarind_version=tamarind_version,
        )
    ).parsed
