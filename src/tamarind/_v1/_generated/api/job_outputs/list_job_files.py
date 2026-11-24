from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.job_file_page import JobFilePage
from ...models.problem import Problem
from ...types import UNSET, Response, Unset


def _get_kwargs(
    job_id: str,
    *,
    prefix: str | Unset = UNSET,
    glob: str | Unset = UNSET,
    include_download_urls: bool | Unset = False,
    limit: int | Unset = 50,
    cursor: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(tamarind_version, Unset):
        headers["Tamarind-Version"] = tamarind_version

    params: dict[str, Any] = {}

    params["prefix"] = prefix

    params["glob"] = glob

    params["includeDownloadUrls"] = include_download_urls

    params["limit"] = limit

    params["cursor"] = cursor

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/jobs/{job_id}/files".format(
            job_id=quote(str(job_id), safe=""),
        ),
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> JobFilePage | Problem:
    if response.status_code == 200:
        response_200 = JobFilePage.from_dict(response.json())

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
) -> Response[JobFilePage | Problem]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    job_id: str,
    *,
    client: AuthenticatedClient | Client,
    prefix: str | Unset = UNSET,
    glob: str | Unset = UNSET,
    include_download_urls: bool | Unset = False,
    limit: int | Unset = 50,
    cursor: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Response[JobFilePage | Problem]:
    """List the files a job or a batch produced

     Takes a `job_` or `batch_` id; a `run_` id is 404. Available while the job runs, in path order,
    every file type included. A batch's own folder holds its combined results; each job's files
    are under that job's id. With `includeDownloadUrls=true`, one call gives every link on the
    page, so there is no need for one call per file. Links expire in 1 hour. A page reads at most
    5,000 stored files, so with a `glob` that matches few of them a page can be short while
    `nextCursor` says there's more.

    Another member's job or batch is listed for exactly the callers who may download its
    zip, under today's `/result` rule for a key (decision 74; today's API has no key route
    that lists a member's files), a batch only when that rule admits every job in it, and one
    that rule refuses is the same 404.

    Args:
        job_id (str):
        prefix (str | Unset):
        glob (str | Unset):
        include_download_urls (bool | Unset):  Default: False.
        limit (int | Unset):  Default: 50.
        cursor (str | Unset):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[JobFilePage | Problem]
    """

    kwargs = _get_kwargs(
        job_id=job_id,
        prefix=prefix,
        glob=glob,
        include_download_urls=include_download_urls,
        limit=limit,
        cursor=cursor,
        tamarind_version=tamarind_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    job_id: str,
    *,
    client: AuthenticatedClient | Client,
    prefix: str | Unset = UNSET,
    glob: str | Unset = UNSET,
    include_download_urls: bool | Unset = False,
    limit: int | Unset = 50,
    cursor: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> JobFilePage | Problem | None:
    """List the files a job or a batch produced

     Takes a `job_` or `batch_` id; a `run_` id is 404. Available while the job runs, in path order,
    every file type included. A batch's own folder holds its combined results; each job's files
    are under that job's id. With `includeDownloadUrls=true`, one call gives every link on the
    page, so there is no need for one call per file. Links expire in 1 hour. A page reads at most
    5,000 stored files, so with a `glob` that matches few of them a page can be short while
    `nextCursor` says there's more.

    Another member's job or batch is listed for exactly the callers who may download its
    zip, under today's `/result` rule for a key (decision 74; today's API has no key route
    that lists a member's files), a batch only when that rule admits every job in it, and one
    that rule refuses is the same 404.

    Args:
        job_id (str):
        prefix (str | Unset):
        glob (str | Unset):
        include_download_urls (bool | Unset):  Default: False.
        limit (int | Unset):  Default: 50.
        cursor (str | Unset):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        JobFilePage | Problem
    """

    return sync_detailed(
        job_id=job_id,
        client=client,
        prefix=prefix,
        glob=glob,
        include_download_urls=include_download_urls,
        limit=limit,
        cursor=cursor,
        tamarind_version=tamarind_version,
    ).parsed


async def asyncio_detailed(
    job_id: str,
    *,
    client: AuthenticatedClient | Client,
    prefix: str | Unset = UNSET,
    glob: str | Unset = UNSET,
    include_download_urls: bool | Unset = False,
    limit: int | Unset = 50,
    cursor: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Response[JobFilePage | Problem]:
    """List the files a job or a batch produced

     Takes a `job_` or `batch_` id; a `run_` id is 404. Available while the job runs, in path order,
    every file type included. A batch's own folder holds its combined results; each job's files
    are under that job's id. With `includeDownloadUrls=true`, one call gives every link on the
    page, so there is no need for one call per file. Links expire in 1 hour. A page reads at most
    5,000 stored files, so with a `glob` that matches few of them a page can be short while
    `nextCursor` says there's more.

    Another member's job or batch is listed for exactly the callers who may download its
    zip, under today's `/result` rule for a key (decision 74; today's API has no key route
    that lists a member's files), a batch only when that rule admits every job in it, and one
    that rule refuses is the same 404.

    Args:
        job_id (str):
        prefix (str | Unset):
        glob (str | Unset):
        include_download_urls (bool | Unset):  Default: False.
        limit (int | Unset):  Default: 50.
        cursor (str | Unset):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[JobFilePage | Problem]
    """

    kwargs = _get_kwargs(
        job_id=job_id,
        prefix=prefix,
        glob=glob,
        include_download_urls=include_download_urls,
        limit=limit,
        cursor=cursor,
        tamarind_version=tamarind_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    job_id: str,
    *,
    client: AuthenticatedClient | Client,
    prefix: str | Unset = UNSET,
    glob: str | Unset = UNSET,
    include_download_urls: bool | Unset = False,
    limit: int | Unset = 50,
    cursor: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> JobFilePage | Problem | None:
    """List the files a job or a batch produced

     Takes a `job_` or `batch_` id; a `run_` id is 404. Available while the job runs, in path order,
    every file type included. A batch's own folder holds its combined results; each job's files
    are under that job's id. With `includeDownloadUrls=true`, one call gives every link on the
    page, so there is no need for one call per file. Links expire in 1 hour. A page reads at most
    5,000 stored files, so with a `glob` that matches few of them a page can be short while
    `nextCursor` says there's more.

    Another member's job or batch is listed for exactly the callers who may download its
    zip, under today's `/result` rule for a key (decision 74; today's API has no key route
    that lists a member's files), a batch only when that rule admits every job in it, and one
    that rule refuses is the same 404.

    Args:
        job_id (str):
        prefix (str | Unset):
        glob (str | Unset):
        include_download_urls (bool | Unset):  Default: False.
        limit (int | Unset):  Default: 50.
        cursor (str | Unset):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        JobFilePage | Problem
    """

    return (
        await asyncio_detailed(
            job_id=job_id,
            client=client,
            prefix=prefix,
            glob=glob,
            include_download_urls=include_download_urls,
            limit=limit,
            cursor=cursor,
            tamarind_version=tamarind_version,
        )
    ).parsed
