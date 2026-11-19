from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.problem import Problem
from ...models.update_note_response import UpdateNoteResponse
from ...models.update_project_notes_note_body import UpdateProjectNotesNoteBody
from ...types import UNSET, Response, Unset


def _get_kwargs(
    project_id: str,
    entry_id: str,
    note_id: str,
    *,
    body: UpdateProjectNotesNoteBody,
    tamarind_version: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(tamarind_version, Unset):
        headers["Tamarind-Version"] = tamarind_version

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": "/projects/{project_id}/notes/entries/{entry_id}/notes/{note_id}".format(
            project_id=quote(str(project_id), safe=""),
            entry_id=quote(str(entry_id), safe=""),
            note_id=quote(str(note_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Problem | UpdateNoteResponse:
    if response.status_code == 200:
        response_200 = UpdateNoteResponse.from_dict(response.json())

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
) -> Response[Problem | UpdateNoteResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    project_id: str,
    entry_id: str,
    note_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateProjectNotesNoteBody,
    tamarind_version: str | Unset = UNSET,
) -> Response[Problem | UpdateNoteResponse]:
    """Update note

     Update a note. Editing sets `editedAt`; `createdAt` and the note's place in the log don't change.
    A key the operation doesn't take is 422 `unknown_field`, refused before anything else. A value the
    notes store refuses is 400 `validation_failed`, pointing at the field. A stale `version` is 409
    `version_conflict` with the `currentVersion` to retry with. A write that met another on the same
    records is 400 `write_contended` with `retryable: true`: nothing was stored, so send it again.

    Args:
        project_id (str):
        entry_id (str):
        note_id (str):
        tamarind_version (str | Unset):
        body (UpdateProjectNotesNoteBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Problem | UpdateNoteResponse]
    """

    kwargs = _get_kwargs(
        project_id=project_id,
        entry_id=entry_id,
        note_id=note_id,
        body=body,
        tamarind_version=tamarind_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    project_id: str,
    entry_id: str,
    note_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateProjectNotesNoteBody,
    tamarind_version: str | Unset = UNSET,
) -> Problem | UpdateNoteResponse | None:
    """Update note

     Update a note. Editing sets `editedAt`; `createdAt` and the note's place in the log don't change.
    A key the operation doesn't take is 422 `unknown_field`, refused before anything else. A value the
    notes store refuses is 400 `validation_failed`, pointing at the field. A stale `version` is 409
    `version_conflict` with the `currentVersion` to retry with. A write that met another on the same
    records is 400 `write_contended` with `retryable: true`: nothing was stored, so send it again.

    Args:
        project_id (str):
        entry_id (str):
        note_id (str):
        tamarind_version (str | Unset):
        body (UpdateProjectNotesNoteBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Problem | UpdateNoteResponse
    """

    return sync_detailed(
        project_id=project_id,
        entry_id=entry_id,
        note_id=note_id,
        client=client,
        body=body,
        tamarind_version=tamarind_version,
    ).parsed


async def asyncio_detailed(
    project_id: str,
    entry_id: str,
    note_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateProjectNotesNoteBody,
    tamarind_version: str | Unset = UNSET,
) -> Response[Problem | UpdateNoteResponse]:
    """Update note

     Update a note. Editing sets `editedAt`; `createdAt` and the note's place in the log don't change.
    A key the operation doesn't take is 422 `unknown_field`, refused before anything else. A value the
    notes store refuses is 400 `validation_failed`, pointing at the field. A stale `version` is 409
    `version_conflict` with the `currentVersion` to retry with. A write that met another on the same
    records is 400 `write_contended` with `retryable: true`: nothing was stored, so send it again.

    Args:
        project_id (str):
        entry_id (str):
        note_id (str):
        tamarind_version (str | Unset):
        body (UpdateProjectNotesNoteBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Problem | UpdateNoteResponse]
    """

    kwargs = _get_kwargs(
        project_id=project_id,
        entry_id=entry_id,
        note_id=note_id,
        body=body,
        tamarind_version=tamarind_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    project_id: str,
    entry_id: str,
    note_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateProjectNotesNoteBody,
    tamarind_version: str | Unset = UNSET,
) -> Problem | UpdateNoteResponse | None:
    """Update note

     Update a note. Editing sets `editedAt`; `createdAt` and the note's place in the log don't change.
    A key the operation doesn't take is 422 `unknown_field`, refused before anything else. A value the
    notes store refuses is 400 `validation_failed`, pointing at the field. A stale `version` is 409
    `version_conflict` with the `currentVersion` to retry with. A write that met another on the same
    records is 400 `write_contended` with `retryable: true`: nothing was stored, so send it again.

    Args:
        project_id (str):
        entry_id (str):
        note_id (str):
        tamarind_version (str | Unset):
        body (UpdateProjectNotesNoteBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Problem | UpdateNoteResponse
    """

    return (
        await asyncio_detailed(
            project_id=project_id,
            entry_id=entry_id,
            note_id=note_id,
            client=client,
            body=body,
            tamarind_version=tamarind_version,
        )
    ).parsed
