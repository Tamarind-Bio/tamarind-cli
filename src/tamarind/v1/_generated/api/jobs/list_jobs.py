import datetime
from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.job_page import JobPage
from ...models.job_status import JobStatus
from ...models.list_jobs_kind import ListJobsKind
from ...models.list_jobs_order import ListJobsOrder
from ...models.list_jobs_scope import ListJobsScope
from ...models.list_jobs_source import ListJobsSource
from ...models.problem import Problem
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    name: str | Unset = UNSET,
    kind: ListJobsKind | Unset = UNSET,
    status: list[JobStatus] | Unset = UNSET,
    tool: str | Unset = UNSET,
    batch_id: str | Unset = UNSET,
    pipeline_run_id: str | Unset = UNSET,
    search: str | Unset = UNSET,
    source: ListJobsSource | Unset = UNSET,
    order: ListJobsOrder | Unset = ListJobsOrder.DESC,
    project_id: str | Unset = UNSET,
    api_key_id: str | Unset = UNSET,
    scope: ListJobsScope | Unset = ListJobsScope.MINE,
    created_by: str | Unset = UNSET,
    created_after: datetime.datetime | Unset = UNSET,
    created_before: datetime.datetime | Unset = UNSET,
    limit: int | Unset = 50,
    cursor: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(tamarind_version, Unset):
        headers["Tamarind-Version"] = tamarind_version

    params: dict[str, Any] = {}

    params["name"] = name

    json_kind: str | Unset = UNSET
    if not isinstance(kind, Unset):
        json_kind = kind.value

    params["kind"] = json_kind

    json_status: list[str] | Unset = UNSET
    if not isinstance(status, Unset):
        json_status = []
        for status_item_data in status:
            status_item = status_item_data.value
            json_status.append(status_item)

    params["status"] = json_status

    params["tool"] = tool

    params["batchId"] = batch_id

    params["pipelineRunId"] = pipeline_run_id

    params["search"] = search

    json_source: str | Unset = UNSET
    if not isinstance(source, Unset):
        json_source = source.value

    params["source"] = json_source

    json_order: str | Unset = UNSET
    if not isinstance(order, Unset):
        json_order = order.value

    params["order"] = json_order

    params["projectId"] = project_id

    params["apiKeyId"] = api_key_id

    json_scope: str | Unset = UNSET
    if not isinstance(scope, Unset):
        json_scope = scope.value

    params["scope"] = json_scope

    params["createdBy"] = created_by

    json_created_after: str | Unset = UNSET
    if not isinstance(created_after, Unset):
        json_created_after = created_after.isoformat()
    params["createdAfter"] = json_created_after

    json_created_before: str | Unset = UNSET
    if not isinstance(created_before, Unset):
        json_created_before = created_before.isoformat()
    params["createdBefore"] = json_created_before

    params["limit"] = limit

    params["cursor"] = cursor

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/jobs",
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> JobPage | Problem:
    if response.status_code == 200:
        response_200 = JobPage.from_dict(response.json())

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
) -> Response[JobPage | Problem]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    name: str | Unset = UNSET,
    kind: ListJobsKind | Unset = UNSET,
    status: list[JobStatus] | Unset = UNSET,
    tool: str | Unset = UNSET,
    batch_id: str | Unset = UNSET,
    pipeline_run_id: str | Unset = UNSET,
    search: str | Unset = UNSET,
    source: ListJobsSource | Unset = UNSET,
    order: ListJobsOrder | Unset = ListJobsOrder.DESC,
    project_id: str | Unset = UNSET,
    api_key_id: str | Unset = UNSET,
    scope: ListJobsScope | Unset = ListJobsScope.MINE,
    created_by: str | Unset = UNSET,
    created_after: datetime.datetime | Unset = UNSET,
    created_before: datetime.datetime | Unset = UNSET,
    limit: int | Unset = 50,
    cursor: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Response[JobPage | Problem]:
    """List your jobs, batches and pipeline runs, newest first

     Returns summaries without `settings`. Each item has a `kind`: `job`, `batch` or `pipeline`.
    The default list is what you started: single jobs, batches and pipeline runs, but not the
    jobs inside a batch or a run. `batchId=` lists a batch's jobs and `pipelineRunId=` a run's.
    Pipeline runs are listed only for a caller in an organization, and benchmark runs never.

    Jobs and batches are listed by their display time, pipeline runs by their start (when they
    were submitted), merged newest first under one cursor; `order=asc` reads oldest first. A
    single-tool run is listed as its job, not as a run, as the app shows it.

    `kind`, `status`, `tool`, `search` and `source` filter each page, so a page can hold fewer
    than `limit` items while `nextCursor` still says there's more; stop when `nextCursor` is
    null. A page also stops early when counting its batches has read a lot of rows. With
    `search` or `source`, a page reads at most 1,000 rows across jobs and runs, then ends short
    with a `nextCursor` to continue. `tool` matches jobs and batches only, since a run has no
    single tool. `source` matches a run only if the run recorded its channel.

    A value `kind`, `status`, `source`, `order` or `scope` doesn't take is 400
    `validation_failed`, and so are these, not built yet, rather than a silently wider list:
    `projectId`, `apiKeyId`, `createdAfter`, `createdBefore`, `scope=org`, and `createdBy`
    naming anyone but you. Past its 15-second deadline a read is 503
    `jobs_dependency_unavailable`.

    Args:
        name (str | Unset):
        kind (ListJobsKind | Unset):
        status (list[JobStatus] | Unset):
        tool (str | Unset):
        batch_id (str | Unset):
        pipeline_run_id (str | Unset):
        search (str | Unset):
        source (ListJobsSource | Unset):
        order (ListJobsOrder | Unset):  Default: ListJobsOrder.DESC.
        project_id (str | Unset):
        api_key_id (str | Unset):
        scope (ListJobsScope | Unset):  Default: ListJobsScope.MINE.
        created_by (str | Unset):
        created_after (datetime.datetime | Unset):
        created_before (datetime.datetime | Unset):
        limit (int | Unset):  Default: 50.
        cursor (str | Unset):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[JobPage | Problem]
    """

    kwargs = _get_kwargs(
        name=name,
        kind=kind,
        status=status,
        tool=tool,
        batch_id=batch_id,
        pipeline_run_id=pipeline_run_id,
        search=search,
        source=source,
        order=order,
        project_id=project_id,
        api_key_id=api_key_id,
        scope=scope,
        created_by=created_by,
        created_after=created_after,
        created_before=created_before,
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
    name: str | Unset = UNSET,
    kind: ListJobsKind | Unset = UNSET,
    status: list[JobStatus] | Unset = UNSET,
    tool: str | Unset = UNSET,
    batch_id: str | Unset = UNSET,
    pipeline_run_id: str | Unset = UNSET,
    search: str | Unset = UNSET,
    source: ListJobsSource | Unset = UNSET,
    order: ListJobsOrder | Unset = ListJobsOrder.DESC,
    project_id: str | Unset = UNSET,
    api_key_id: str | Unset = UNSET,
    scope: ListJobsScope | Unset = ListJobsScope.MINE,
    created_by: str | Unset = UNSET,
    created_after: datetime.datetime | Unset = UNSET,
    created_before: datetime.datetime | Unset = UNSET,
    limit: int | Unset = 50,
    cursor: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> JobPage | Problem | None:
    """List your jobs, batches and pipeline runs, newest first

     Returns summaries without `settings`. Each item has a `kind`: `job`, `batch` or `pipeline`.
    The default list is what you started: single jobs, batches and pipeline runs, but not the
    jobs inside a batch or a run. `batchId=` lists a batch's jobs and `pipelineRunId=` a run's.
    Pipeline runs are listed only for a caller in an organization, and benchmark runs never.

    Jobs and batches are listed by their display time, pipeline runs by their start (when they
    were submitted), merged newest first under one cursor; `order=asc` reads oldest first. A
    single-tool run is listed as its job, not as a run, as the app shows it.

    `kind`, `status`, `tool`, `search` and `source` filter each page, so a page can hold fewer
    than `limit` items while `nextCursor` still says there's more; stop when `nextCursor` is
    null. A page also stops early when counting its batches has read a lot of rows. With
    `search` or `source`, a page reads at most 1,000 rows across jobs and runs, then ends short
    with a `nextCursor` to continue. `tool` matches jobs and batches only, since a run has no
    single tool. `source` matches a run only if the run recorded its channel.

    A value `kind`, `status`, `source`, `order` or `scope` doesn't take is 400
    `validation_failed`, and so are these, not built yet, rather than a silently wider list:
    `projectId`, `apiKeyId`, `createdAfter`, `createdBefore`, `scope=org`, and `createdBy`
    naming anyone but you. Past its 15-second deadline a read is 503
    `jobs_dependency_unavailable`.

    Args:
        name (str | Unset):
        kind (ListJobsKind | Unset):
        status (list[JobStatus] | Unset):
        tool (str | Unset):
        batch_id (str | Unset):
        pipeline_run_id (str | Unset):
        search (str | Unset):
        source (ListJobsSource | Unset):
        order (ListJobsOrder | Unset):  Default: ListJobsOrder.DESC.
        project_id (str | Unset):
        api_key_id (str | Unset):
        scope (ListJobsScope | Unset):  Default: ListJobsScope.MINE.
        created_by (str | Unset):
        created_after (datetime.datetime | Unset):
        created_before (datetime.datetime | Unset):
        limit (int | Unset):  Default: 50.
        cursor (str | Unset):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        JobPage | Problem
    """

    return sync_detailed(
        client=client,
        name=name,
        kind=kind,
        status=status,
        tool=tool,
        batch_id=batch_id,
        pipeline_run_id=pipeline_run_id,
        search=search,
        source=source,
        order=order,
        project_id=project_id,
        api_key_id=api_key_id,
        scope=scope,
        created_by=created_by,
        created_after=created_after,
        created_before=created_before,
        limit=limit,
        cursor=cursor,
        tamarind_version=tamarind_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    name: str | Unset = UNSET,
    kind: ListJobsKind | Unset = UNSET,
    status: list[JobStatus] | Unset = UNSET,
    tool: str | Unset = UNSET,
    batch_id: str | Unset = UNSET,
    pipeline_run_id: str | Unset = UNSET,
    search: str | Unset = UNSET,
    source: ListJobsSource | Unset = UNSET,
    order: ListJobsOrder | Unset = ListJobsOrder.DESC,
    project_id: str | Unset = UNSET,
    api_key_id: str | Unset = UNSET,
    scope: ListJobsScope | Unset = ListJobsScope.MINE,
    created_by: str | Unset = UNSET,
    created_after: datetime.datetime | Unset = UNSET,
    created_before: datetime.datetime | Unset = UNSET,
    limit: int | Unset = 50,
    cursor: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Response[JobPage | Problem]:
    """List your jobs, batches and pipeline runs, newest first

     Returns summaries without `settings`. Each item has a `kind`: `job`, `batch` or `pipeline`.
    The default list is what you started: single jobs, batches and pipeline runs, but not the
    jobs inside a batch or a run. `batchId=` lists a batch's jobs and `pipelineRunId=` a run's.
    Pipeline runs are listed only for a caller in an organization, and benchmark runs never.

    Jobs and batches are listed by their display time, pipeline runs by their start (when they
    were submitted), merged newest first under one cursor; `order=asc` reads oldest first. A
    single-tool run is listed as its job, not as a run, as the app shows it.

    `kind`, `status`, `tool`, `search` and `source` filter each page, so a page can hold fewer
    than `limit` items while `nextCursor` still says there's more; stop when `nextCursor` is
    null. A page also stops early when counting its batches has read a lot of rows. With
    `search` or `source`, a page reads at most 1,000 rows across jobs and runs, then ends short
    with a `nextCursor` to continue. `tool` matches jobs and batches only, since a run has no
    single tool. `source` matches a run only if the run recorded its channel.

    A value `kind`, `status`, `source`, `order` or `scope` doesn't take is 400
    `validation_failed`, and so are these, not built yet, rather than a silently wider list:
    `projectId`, `apiKeyId`, `createdAfter`, `createdBefore`, `scope=org`, and `createdBy`
    naming anyone but you. Past its 15-second deadline a read is 503
    `jobs_dependency_unavailable`.

    Args:
        name (str | Unset):
        kind (ListJobsKind | Unset):
        status (list[JobStatus] | Unset):
        tool (str | Unset):
        batch_id (str | Unset):
        pipeline_run_id (str | Unset):
        search (str | Unset):
        source (ListJobsSource | Unset):
        order (ListJobsOrder | Unset):  Default: ListJobsOrder.DESC.
        project_id (str | Unset):
        api_key_id (str | Unset):
        scope (ListJobsScope | Unset):  Default: ListJobsScope.MINE.
        created_by (str | Unset):
        created_after (datetime.datetime | Unset):
        created_before (datetime.datetime | Unset):
        limit (int | Unset):  Default: 50.
        cursor (str | Unset):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[JobPage | Problem]
    """

    kwargs = _get_kwargs(
        name=name,
        kind=kind,
        status=status,
        tool=tool,
        batch_id=batch_id,
        pipeline_run_id=pipeline_run_id,
        search=search,
        source=source,
        order=order,
        project_id=project_id,
        api_key_id=api_key_id,
        scope=scope,
        created_by=created_by,
        created_after=created_after,
        created_before=created_before,
        limit=limit,
        cursor=cursor,
        tamarind_version=tamarind_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    name: str | Unset = UNSET,
    kind: ListJobsKind | Unset = UNSET,
    status: list[JobStatus] | Unset = UNSET,
    tool: str | Unset = UNSET,
    batch_id: str | Unset = UNSET,
    pipeline_run_id: str | Unset = UNSET,
    search: str | Unset = UNSET,
    source: ListJobsSource | Unset = UNSET,
    order: ListJobsOrder | Unset = ListJobsOrder.DESC,
    project_id: str | Unset = UNSET,
    api_key_id: str | Unset = UNSET,
    scope: ListJobsScope | Unset = ListJobsScope.MINE,
    created_by: str | Unset = UNSET,
    created_after: datetime.datetime | Unset = UNSET,
    created_before: datetime.datetime | Unset = UNSET,
    limit: int | Unset = 50,
    cursor: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> JobPage | Problem | None:
    """List your jobs, batches and pipeline runs, newest first

     Returns summaries without `settings`. Each item has a `kind`: `job`, `batch` or `pipeline`.
    The default list is what you started: single jobs, batches and pipeline runs, but not the
    jobs inside a batch or a run. `batchId=` lists a batch's jobs and `pipelineRunId=` a run's.
    Pipeline runs are listed only for a caller in an organization, and benchmark runs never.

    Jobs and batches are listed by their display time, pipeline runs by their start (when they
    were submitted), merged newest first under one cursor; `order=asc` reads oldest first. A
    single-tool run is listed as its job, not as a run, as the app shows it.

    `kind`, `status`, `tool`, `search` and `source` filter each page, so a page can hold fewer
    than `limit` items while `nextCursor` still says there's more; stop when `nextCursor` is
    null. A page also stops early when counting its batches has read a lot of rows. With
    `search` or `source`, a page reads at most 1,000 rows across jobs and runs, then ends short
    with a `nextCursor` to continue. `tool` matches jobs and batches only, since a run has no
    single tool. `source` matches a run only if the run recorded its channel.

    A value `kind`, `status`, `source`, `order` or `scope` doesn't take is 400
    `validation_failed`, and so are these, not built yet, rather than a silently wider list:
    `projectId`, `apiKeyId`, `createdAfter`, `createdBefore`, `scope=org`, and `createdBy`
    naming anyone but you. Past its 15-second deadline a read is 503
    `jobs_dependency_unavailable`.

    Args:
        name (str | Unset):
        kind (ListJobsKind | Unset):
        status (list[JobStatus] | Unset):
        tool (str | Unset):
        batch_id (str | Unset):
        pipeline_run_id (str | Unset):
        search (str | Unset):
        source (ListJobsSource | Unset):
        order (ListJobsOrder | Unset):  Default: ListJobsOrder.DESC.
        project_id (str | Unset):
        api_key_id (str | Unset):
        scope (ListJobsScope | Unset):  Default: ListJobsScope.MINE.
        created_by (str | Unset):
        created_after (datetime.datetime | Unset):
        created_before (datetime.datetime | Unset):
        limit (int | Unset):  Default: 50.
        cursor (str | Unset):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        JobPage | Problem
    """

    return (
        await asyncio_detailed(
            client=client,
            name=name,
            kind=kind,
            status=status,
            tool=tool,
            batch_id=batch_id,
            pipeline_run_id=pipeline_run_id,
            search=search,
            source=source,
            order=order,
            project_id=project_id,
            api_key_id=api_key_id,
            scope=scope,
            created_by=created_by,
            created_after=created_after,
            created_before=created_before,
            limit=limit,
            cursor=cursor,
            tamarind_version=tamarind_version,
        )
    ).parsed
