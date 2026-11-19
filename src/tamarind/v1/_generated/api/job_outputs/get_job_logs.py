from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.job_log_chunk import JobLogChunk
from ...models.problem import Problem
from ...types import UNSET, Response, Unset


def _get_kwargs(
    job_id: str,
    *,
    max_bytes: int | Unset = 65536,
    cursor: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(tamarind_version, Unset):
        headers["Tamarind-Version"] = tamarind_version

    params: dict[str, Any] = {}

    params["maxBytes"] = max_bytes

    params["cursor"] = cursor

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/jobs/{job_id}/logs".format(
            job_id=quote(str(job_id), safe=""),
        ),
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> JobLogChunk | Problem:
    if response.status_code == 200:
        response_200 = JobLogChunk.from_dict(response.json())

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
) -> Response[JobLogChunk | Problem]:
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
    max_bytes: int | Unset = 65536,
    cursor: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Response[JobLogChunk | Problem]:
    """Read a job's logs

     Takes a `job_` id only; a `batch_` or `run_` id is 404. Returns the most recent output first,
    up to `maxBytes`, starting at a line (or else at a character). Follow `nextCursor` to page back
    through older output; the pages put back together are the log byte for byte. A window is at
    least 4 bytes, one whole UTF-8 character, so `maxBytes` of 1 to 3 reads 4. A job with no log
    yet answers 200 with empty `content`. A cursor is bound to the job's current attempt: once the
    job is re-dispatched, or its log is gone, the cursor is 400 `invalid_cursor`; start again
    without one.

    Another member's job or batch is 404 for now; once website#7795 merges, it follows today's
    `/result` rule for a key (decision 74, and Authentication in the introduction), and one that
    rule refuses is the same 404.

    Args:
        job_id (str):
        max_bytes (int | Unset):  Default: 65536.
        cursor (str | Unset):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[JobLogChunk | Problem]
    """

    kwargs = _get_kwargs(
        job_id=job_id,
        max_bytes=max_bytes,
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
    max_bytes: int | Unset = 65536,
    cursor: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> JobLogChunk | Problem | None:
    """Read a job's logs

     Takes a `job_` id only; a `batch_` or `run_` id is 404. Returns the most recent output first,
    up to `maxBytes`, starting at a line (or else at a character). Follow `nextCursor` to page back
    through older output; the pages put back together are the log byte for byte. A window is at
    least 4 bytes, one whole UTF-8 character, so `maxBytes` of 1 to 3 reads 4. A job with no log
    yet answers 200 with empty `content`. A cursor is bound to the job's current attempt: once the
    job is re-dispatched, or its log is gone, the cursor is 400 `invalid_cursor`; start again
    without one.

    Another member's job or batch is 404 for now; once website#7795 merges, it follows today's
    `/result` rule for a key (decision 74, and Authentication in the introduction), and one that
    rule refuses is the same 404.

    Args:
        job_id (str):
        max_bytes (int | Unset):  Default: 65536.
        cursor (str | Unset):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        JobLogChunk | Problem
    """

    return sync_detailed(
        job_id=job_id,
        client=client,
        max_bytes=max_bytes,
        cursor=cursor,
        tamarind_version=tamarind_version,
    ).parsed


async def asyncio_detailed(
    job_id: str,
    *,
    client: AuthenticatedClient | Client,
    max_bytes: int | Unset = 65536,
    cursor: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Response[JobLogChunk | Problem]:
    """Read a job's logs

     Takes a `job_` id only; a `batch_` or `run_` id is 404. Returns the most recent output first,
    up to `maxBytes`, starting at a line (or else at a character). Follow `nextCursor` to page back
    through older output; the pages put back together are the log byte for byte. A window is at
    least 4 bytes, one whole UTF-8 character, so `maxBytes` of 1 to 3 reads 4. A job with no log
    yet answers 200 with empty `content`. A cursor is bound to the job's current attempt: once the
    job is re-dispatched, or its log is gone, the cursor is 400 `invalid_cursor`; start again
    without one.

    Another member's job or batch is 404 for now; once website#7795 merges, it follows today's
    `/result` rule for a key (decision 74, and Authentication in the introduction), and one that
    rule refuses is the same 404.

    Args:
        job_id (str):
        max_bytes (int | Unset):  Default: 65536.
        cursor (str | Unset):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[JobLogChunk | Problem]
    """

    kwargs = _get_kwargs(
        job_id=job_id,
        max_bytes=max_bytes,
        cursor=cursor,
        tamarind_version=tamarind_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    job_id: str,
    *,
    client: AuthenticatedClient | Client,
    max_bytes: int | Unset = 65536,
    cursor: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> JobLogChunk | Problem | None:
    """Read a job's logs

     Takes a `job_` id only; a `batch_` or `run_` id is 404. Returns the most recent output first,
    up to `maxBytes`, starting at a line (or else at a character). Follow `nextCursor` to page back
    through older output; the pages put back together are the log byte for byte. A window is at
    least 4 bytes, one whole UTF-8 character, so `maxBytes` of 1 to 3 reads 4. A job with no log
    yet answers 200 with empty `content`. A cursor is bound to the job's current attempt: once the
    job is re-dispatched, or its log is gone, the cursor is 400 `invalid_cursor`; start again
    without one.

    Another member's job or batch is 404 for now; once website#7795 merges, it follows today's
    `/result` rule for a key (decision 74, and Authentication in the introduction), and one that
    rule refuses is the same 404.

    Args:
        job_id (str):
        max_bytes (int | Unset):  Default: 65536.
        cursor (str | Unset):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        JobLogChunk | Problem
    """

    return (
        await asyncio_detailed(
            job_id=job_id,
            client=client,
            max_bytes=max_bytes,
            cursor=cursor,
            tamarind_version=tamarind_version,
        )
    ).parsed
