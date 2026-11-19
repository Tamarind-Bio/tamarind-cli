from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.problem import Problem
from ...models.read_notes_response import ReadNotesResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    project_id: str,
    *,
    tamarind_version: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(tamarind_version, Unset):
        headers["Tamarind-Version"] = tamarind_version

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/projects/{project_id}/notes".format(
            project_id=quote(str(project_id), safe=""),
        ),
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Problem | ReadNotesResponse:
    if response.status_code == 200:
        response_200 = ReadNotesResponse.from_dict(response.json())

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

    if response.status_code == 429:
        response_429 = Problem.from_dict(response.json())

        return response_429

    if response.status_code == 500:
        response_500 = Problem.from_dict(response.json())

        return response_500

    if response.status_code == 503:
        response_503 = Problem.from_dict(response.json())

        return response_503

    response_default = Problem.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[Problem | ReadNotesResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    project_id: str,
    *,
    client: AuthenticatedClient | Client,
    tamarind_version: str | Unset = UNSET,
) -> Response[Problem | ReadNotesResponse]:
    """Get project notes

     Fetch the project notes. This includes project metadata and entry data. Log notes are not included
    and can be fetched one entry at a time from `GET /projects/{projectId}/notes/entries/{entryId}`.
    The first read of a project sets its notes up, so it can be 400 `write_contended`
    (`retryable: true`) when another request does the same at that moment; send it again. A read-only
    member gets the notes as they would open, without anything being set up.

    On every notes operation: a project that doesn't exist or that you can't see is 404, as on the
    project operations, so a project's existence isn't disclosed. With project notes turned off for
    you, every project is 404. A read-only member's
    writes are 403. A request whose `x-tamarind-actor` header is `agent` also needs the user's agent
    opt-in (403 without it), and its writes count against a per-minute budget (429).

    Args:
        project_id (str):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Problem | ReadNotesResponse]
    """

    kwargs = _get_kwargs(
        project_id=project_id,
        tamarind_version=tamarind_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    project_id: str,
    *,
    client: AuthenticatedClient | Client,
    tamarind_version: str | Unset = UNSET,
) -> Problem | ReadNotesResponse | None:
    """Get project notes

     Fetch the project notes. This includes project metadata and entry data. Log notes are not included
    and can be fetched one entry at a time from `GET /projects/{projectId}/notes/entries/{entryId}`.
    The first read of a project sets its notes up, so it can be 400 `write_contended`
    (`retryable: true`) when another request does the same at that moment; send it again. A read-only
    member gets the notes as they would open, without anything being set up.

    On every notes operation: a project that doesn't exist or that you can't see is 404, as on the
    project operations, so a project's existence isn't disclosed. With project notes turned off for
    you, every project is 404. A read-only member's
    writes are 403. A request whose `x-tamarind-actor` header is `agent` also needs the user's agent
    opt-in (403 without it), and its writes count against a per-minute budget (429).

    Args:
        project_id (str):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Problem | ReadNotesResponse
    """

    return sync_detailed(
        project_id=project_id,
        client=client,
        tamarind_version=tamarind_version,
    ).parsed


async def asyncio_detailed(
    project_id: str,
    *,
    client: AuthenticatedClient | Client,
    tamarind_version: str | Unset = UNSET,
) -> Response[Problem | ReadNotesResponse]:
    """Get project notes

     Fetch the project notes. This includes project metadata and entry data. Log notes are not included
    and can be fetched one entry at a time from `GET /projects/{projectId}/notes/entries/{entryId}`.
    The first read of a project sets its notes up, so it can be 400 `write_contended`
    (`retryable: true`) when another request does the same at that moment; send it again. A read-only
    member gets the notes as they would open, without anything being set up.

    On every notes operation: a project that doesn't exist or that you can't see is 404, as on the
    project operations, so a project's existence isn't disclosed. With project notes turned off for
    you, every project is 404. A read-only member's
    writes are 403. A request whose `x-tamarind-actor` header is `agent` also needs the user's agent
    opt-in (403 without it), and its writes count against a per-minute budget (429).

    Args:
        project_id (str):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Problem | ReadNotesResponse]
    """

    kwargs = _get_kwargs(
        project_id=project_id,
        tamarind_version=tamarind_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    project_id: str,
    *,
    client: AuthenticatedClient | Client,
    tamarind_version: str | Unset = UNSET,
) -> Problem | ReadNotesResponse | None:
    """Get project notes

     Fetch the project notes. This includes project metadata and entry data. Log notes are not included
    and can be fetched one entry at a time from `GET /projects/{projectId}/notes/entries/{entryId}`.
    The first read of a project sets its notes up, so it can be 400 `write_contended`
    (`retryable: true`) when another request does the same at that moment; send it again. A read-only
    member gets the notes as they would open, without anything being set up.

    On every notes operation: a project that doesn't exist or that you can't see is 404, as on the
    project operations, so a project's existence isn't disclosed. With project notes turned off for
    you, every project is 404. A read-only member's
    writes are 403. A request whose `x-tamarind-actor` header is `agent` also needs the user's agent
    opt-in (403 without it), and its writes count against a per-minute budget (429).

    Args:
        project_id (str):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Problem | ReadNotesResponse
    """

    return (
        await asyncio_detailed(
            project_id=project_id,
            client=client,
            tamarind_version=tamarind_version,
        )
    ).parsed
