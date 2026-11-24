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
from ...models.problem import Problem
from ...models.submission_channel import SubmissionChannel
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
    source: SubmissionChannel | Unset = UNSET,
    order: ListJobsOrder | Unset = ListJobsOrder.DESC,
    project_id: str | Unset = UNSET,
    api_key_id: str | Unset = UNSET,
    scope: ListJobsScope | Unset = ListJobsScope.MINE,
    created_by: str | Unset = UNSET,
    include_subjobs: bool | Unset = False,
    batch_name: str | Unset = UNSET,
    all_matches: bool | Unset = False,
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

    params["includeSubjobs"] = include_subjobs

    params["batchName"] = batch_name

    params["allMatches"] = all_matches

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
    source: SubmissionChannel | Unset = UNSET,
    order: ListJobsOrder | Unset = ListJobsOrder.DESC,
    project_id: str | Unset = UNSET,
    api_key_id: str | Unset = UNSET,
    scope: ListJobsScope | Unset = ListJobsScope.MINE,
    created_by: str | Unset = UNSET,
    include_subjobs: bool | Unset = False,
    batch_name: str | Unset = UNSET,
    all_matches: bool | Unset = False,
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
    `projectId`, `apiKeyId`, `createdAfter` and `createdBefore`. Past its 15-second deadline a
    read is 503 `jobs_dependency_unavailable`.

    Organization scope (decision 74). With
    `scope=org` the list is the organization's jobs and batches, not pipeline runs (those list
    under `listPipelineRuns?scope=org`), as today's API shows them: every member's when the
    organization shares within itself or you're its admin or its service account, otherwise
    only yours. `createdBy` is another member's email and needs `scope=org` (400 without it); a
    member whose jobs you can't see is 403 `forbidden`. Pages walk the members in turn (you
    first, then the others by email), each page newest first. `name=` works with both.
    `batchId`, `pipelineRunId`, `search`, `source`, `order=asc` and `kind=pipeline` can't be
    combined with `scope=org` yet (400). `batchId=` of another member's batch needs no
    `scope=org`: it lists the batch's jobs as today's batch read does, each admitted on its own.

    Today's list options. Each one is answered by the same reader today's `GET /jobs` uses, so it
    lists what today's API lists.

    - `includeSubjobs=true`: your list, or a member's with `createdBy`, holds every batch's own
      jobs as well, each with its `batchId`. With `scope=org` alone the list is unchanged, because
      today's organization list never had a batch's jobs. Pipeline runs aren't in it.
    - `batchName=`: the jobs of every batch with that exact name in the scope you ask for, which
      is yours, one member's (`scope=org&createdBy=`) or the organization's (`scope=org`). A name
      with nothing you can see answers an empty page. Today's organization batch read keeps only
      rows the organization's own list would show, and a batch's jobs almost never are, so with
      `scope=org` alone it is mostly empty, as it is today.
    - `allMatches=true`, with `name` and `scope=org` and no `createdBy`: every member's match,
      newest first, rather than only the newest. It is still one page with no `nextCursor`.

    With `includeSubjobs` or `batchName`, `kind`, `status` and `tool` filter each page. `name`,
    `batchId`, `pipelineRunId`, `search`, `source`, `order=asc` and `kind=pipeline` can't be
    combined with them (400). `allMatches` anywhere else is 400.

    Args:
        name (str | Unset):
        kind (ListJobsKind | Unset):
        status (list[JobStatus] | Unset):
        tool (str | Unset):
        batch_id (str | Unset):
        pipeline_run_id (str | Unset):
        search (str | Unset):
        source (SubmissionChannel | Unset): The channel a job, batch or pipeline run was submitted
            through. Tamarind's SDK, CLI, MCP and agents declare theirs with `X-Tamarind-Client-
            Channel` (see Attribution in the introduction); any other API-key submit is `api`, and the
            app's is `web`.
        order (ListJobsOrder | Unset):  Default: ListJobsOrder.DESC.
        project_id (str | Unset):
        api_key_id (str | Unset):
        scope (ListJobsScope | Unset):  Default: ListJobsScope.MINE.
        created_by (str | Unset):
        include_subjobs (bool | Unset):  Default: False.
        batch_name (str | Unset):
        all_matches (bool | Unset):  Default: False.
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
        include_subjobs=include_subjobs,
        batch_name=batch_name,
        all_matches=all_matches,
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
    source: SubmissionChannel | Unset = UNSET,
    order: ListJobsOrder | Unset = ListJobsOrder.DESC,
    project_id: str | Unset = UNSET,
    api_key_id: str | Unset = UNSET,
    scope: ListJobsScope | Unset = ListJobsScope.MINE,
    created_by: str | Unset = UNSET,
    include_subjobs: bool | Unset = False,
    batch_name: str | Unset = UNSET,
    all_matches: bool | Unset = False,
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
    `projectId`, `apiKeyId`, `createdAfter` and `createdBefore`. Past its 15-second deadline a
    read is 503 `jobs_dependency_unavailable`.

    Organization scope (decision 74). With
    `scope=org` the list is the organization's jobs and batches, not pipeline runs (those list
    under `listPipelineRuns?scope=org`), as today's API shows them: every member's when the
    organization shares within itself or you're its admin or its service account, otherwise
    only yours. `createdBy` is another member's email and needs `scope=org` (400 without it); a
    member whose jobs you can't see is 403 `forbidden`. Pages walk the members in turn (you
    first, then the others by email), each page newest first. `name=` works with both.
    `batchId`, `pipelineRunId`, `search`, `source`, `order=asc` and `kind=pipeline` can't be
    combined with `scope=org` yet (400). `batchId=` of another member's batch needs no
    `scope=org`: it lists the batch's jobs as today's batch read does, each admitted on its own.

    Today's list options. Each one is answered by the same reader today's `GET /jobs` uses, so it
    lists what today's API lists.

    - `includeSubjobs=true`: your list, or a member's with `createdBy`, holds every batch's own
      jobs as well, each with its `batchId`. With `scope=org` alone the list is unchanged, because
      today's organization list never had a batch's jobs. Pipeline runs aren't in it.
    - `batchName=`: the jobs of every batch with that exact name in the scope you ask for, which
      is yours, one member's (`scope=org&createdBy=`) or the organization's (`scope=org`). A name
      with nothing you can see answers an empty page. Today's organization batch read keeps only
      rows the organization's own list would show, and a batch's jobs almost never are, so with
      `scope=org` alone it is mostly empty, as it is today.
    - `allMatches=true`, with `name` and `scope=org` and no `createdBy`: every member's match,
      newest first, rather than only the newest. It is still one page with no `nextCursor`.

    With `includeSubjobs` or `batchName`, `kind`, `status` and `tool` filter each page. `name`,
    `batchId`, `pipelineRunId`, `search`, `source`, `order=asc` and `kind=pipeline` can't be
    combined with them (400). `allMatches` anywhere else is 400.

    Args:
        name (str | Unset):
        kind (ListJobsKind | Unset):
        status (list[JobStatus] | Unset):
        tool (str | Unset):
        batch_id (str | Unset):
        pipeline_run_id (str | Unset):
        search (str | Unset):
        source (SubmissionChannel | Unset): The channel a job, batch or pipeline run was submitted
            through. Tamarind's SDK, CLI, MCP and agents declare theirs with `X-Tamarind-Client-
            Channel` (see Attribution in the introduction); any other API-key submit is `api`, and the
            app's is `web`.
        order (ListJobsOrder | Unset):  Default: ListJobsOrder.DESC.
        project_id (str | Unset):
        api_key_id (str | Unset):
        scope (ListJobsScope | Unset):  Default: ListJobsScope.MINE.
        created_by (str | Unset):
        include_subjobs (bool | Unset):  Default: False.
        batch_name (str | Unset):
        all_matches (bool | Unset):  Default: False.
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
        include_subjobs=include_subjobs,
        batch_name=batch_name,
        all_matches=all_matches,
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
    source: SubmissionChannel | Unset = UNSET,
    order: ListJobsOrder | Unset = ListJobsOrder.DESC,
    project_id: str | Unset = UNSET,
    api_key_id: str | Unset = UNSET,
    scope: ListJobsScope | Unset = ListJobsScope.MINE,
    created_by: str | Unset = UNSET,
    include_subjobs: bool | Unset = False,
    batch_name: str | Unset = UNSET,
    all_matches: bool | Unset = False,
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
    `projectId`, `apiKeyId`, `createdAfter` and `createdBefore`. Past its 15-second deadline a
    read is 503 `jobs_dependency_unavailable`.

    Organization scope (decision 74). With
    `scope=org` the list is the organization's jobs and batches, not pipeline runs (those list
    under `listPipelineRuns?scope=org`), as today's API shows them: every member's when the
    organization shares within itself or you're its admin or its service account, otherwise
    only yours. `createdBy` is another member's email and needs `scope=org` (400 without it); a
    member whose jobs you can't see is 403 `forbidden`. Pages walk the members in turn (you
    first, then the others by email), each page newest first. `name=` works with both.
    `batchId`, `pipelineRunId`, `search`, `source`, `order=asc` and `kind=pipeline` can't be
    combined with `scope=org` yet (400). `batchId=` of another member's batch needs no
    `scope=org`: it lists the batch's jobs as today's batch read does, each admitted on its own.

    Today's list options. Each one is answered by the same reader today's `GET /jobs` uses, so it
    lists what today's API lists.

    - `includeSubjobs=true`: your list, or a member's with `createdBy`, holds every batch's own
      jobs as well, each with its `batchId`. With `scope=org` alone the list is unchanged, because
      today's organization list never had a batch's jobs. Pipeline runs aren't in it.
    - `batchName=`: the jobs of every batch with that exact name in the scope you ask for, which
      is yours, one member's (`scope=org&createdBy=`) or the organization's (`scope=org`). A name
      with nothing you can see answers an empty page. Today's organization batch read keeps only
      rows the organization's own list would show, and a batch's jobs almost never are, so with
      `scope=org` alone it is mostly empty, as it is today.
    - `allMatches=true`, with `name` and `scope=org` and no `createdBy`: every member's match,
      newest first, rather than only the newest. It is still one page with no `nextCursor`.

    With `includeSubjobs` or `batchName`, `kind`, `status` and `tool` filter each page. `name`,
    `batchId`, `pipelineRunId`, `search`, `source`, `order=asc` and `kind=pipeline` can't be
    combined with them (400). `allMatches` anywhere else is 400.

    Args:
        name (str | Unset):
        kind (ListJobsKind | Unset):
        status (list[JobStatus] | Unset):
        tool (str | Unset):
        batch_id (str | Unset):
        pipeline_run_id (str | Unset):
        search (str | Unset):
        source (SubmissionChannel | Unset): The channel a job, batch or pipeline run was submitted
            through. Tamarind's SDK, CLI, MCP and agents declare theirs with `X-Tamarind-Client-
            Channel` (see Attribution in the introduction); any other API-key submit is `api`, and the
            app's is `web`.
        order (ListJobsOrder | Unset):  Default: ListJobsOrder.DESC.
        project_id (str | Unset):
        api_key_id (str | Unset):
        scope (ListJobsScope | Unset):  Default: ListJobsScope.MINE.
        created_by (str | Unset):
        include_subjobs (bool | Unset):  Default: False.
        batch_name (str | Unset):
        all_matches (bool | Unset):  Default: False.
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
        include_subjobs=include_subjobs,
        batch_name=batch_name,
        all_matches=all_matches,
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
    source: SubmissionChannel | Unset = UNSET,
    order: ListJobsOrder | Unset = ListJobsOrder.DESC,
    project_id: str | Unset = UNSET,
    api_key_id: str | Unset = UNSET,
    scope: ListJobsScope | Unset = ListJobsScope.MINE,
    created_by: str | Unset = UNSET,
    include_subjobs: bool | Unset = False,
    batch_name: str | Unset = UNSET,
    all_matches: bool | Unset = False,
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
    `projectId`, `apiKeyId`, `createdAfter` and `createdBefore`. Past its 15-second deadline a
    read is 503 `jobs_dependency_unavailable`.

    Organization scope (decision 74). With
    `scope=org` the list is the organization's jobs and batches, not pipeline runs (those list
    under `listPipelineRuns?scope=org`), as today's API shows them: every member's when the
    organization shares within itself or you're its admin or its service account, otherwise
    only yours. `createdBy` is another member's email and needs `scope=org` (400 without it); a
    member whose jobs you can't see is 403 `forbidden`. Pages walk the members in turn (you
    first, then the others by email), each page newest first. `name=` works with both.
    `batchId`, `pipelineRunId`, `search`, `source`, `order=asc` and `kind=pipeline` can't be
    combined with `scope=org` yet (400). `batchId=` of another member's batch needs no
    `scope=org`: it lists the batch's jobs as today's batch read does, each admitted on its own.

    Today's list options. Each one is answered by the same reader today's `GET /jobs` uses, so it
    lists what today's API lists.

    - `includeSubjobs=true`: your list, or a member's with `createdBy`, holds every batch's own
      jobs as well, each with its `batchId`. With `scope=org` alone the list is unchanged, because
      today's organization list never had a batch's jobs. Pipeline runs aren't in it.
    - `batchName=`: the jobs of every batch with that exact name in the scope you ask for, which
      is yours, one member's (`scope=org&createdBy=`) or the organization's (`scope=org`). A name
      with nothing you can see answers an empty page. Today's organization batch read keeps only
      rows the organization's own list would show, and a batch's jobs almost never are, so with
      `scope=org` alone it is mostly empty, as it is today.
    - `allMatches=true`, with `name` and `scope=org` and no `createdBy`: every member's match,
      newest first, rather than only the newest. It is still one page with no `nextCursor`.

    With `includeSubjobs` or `batchName`, `kind`, `status` and `tool` filter each page. `name`,
    `batchId`, `pipelineRunId`, `search`, `source`, `order=asc` and `kind=pipeline` can't be
    combined with them (400). `allMatches` anywhere else is 400.

    Args:
        name (str | Unset):
        kind (ListJobsKind | Unset):
        status (list[JobStatus] | Unset):
        tool (str | Unset):
        batch_id (str | Unset):
        pipeline_run_id (str | Unset):
        search (str | Unset):
        source (SubmissionChannel | Unset): The channel a job, batch or pipeline run was submitted
            through. Tamarind's SDK, CLI, MCP and agents declare theirs with `X-Tamarind-Client-
            Channel` (see Attribution in the introduction); any other API-key submit is `api`, and the
            app's is `web`.
        order (ListJobsOrder | Unset):  Default: ListJobsOrder.DESC.
        project_id (str | Unset):
        api_key_id (str | Unset):
        scope (ListJobsScope | Unset):  Default: ListJobsScope.MINE.
        created_by (str | Unset):
        include_subjobs (bool | Unset):  Default: False.
        batch_name (str | Unset):
        all_matches (bool | Unset):  Default: False.
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
            include_subjobs=include_subjobs,
            batch_name=batch_name,
            all_matches=all_matches,
            created_after=created_after,
            created_before=created_before,
            limit=limit,
            cursor=cursor,
            tamarind_version=tamarind_version,
        )
    ).parsed
