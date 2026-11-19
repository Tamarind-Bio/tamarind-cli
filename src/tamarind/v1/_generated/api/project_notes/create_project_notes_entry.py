from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.create_entry_response import CreateEntryResponse
from ...models.create_project_notes_entry_body import CreateProjectNotesEntryBody
from ...models.problem import Problem
from ...types import UNSET, Response, Unset


def _get_kwargs(
    project_id: str,
    *,
    body: CreateProjectNotesEntryBody,
    tamarind_version: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(tamarind_version, Unset):
        headers["Tamarind-Version"] = tamarind_version

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/projects/{project_id}/notes/entries".format(
            project_id=quote(str(project_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> CreateEntryResponse | Problem:
    if response.status_code == 201:
        response_201 = CreateEntryResponse.from_dict(response.json())

        return response_201

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
) -> Response[CreateEntryResponse | Problem]:
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
    body: CreateProjectNotesEntryBody,
    tamarind_version: str | Unset = UNSET,
) -> Response[CreateEntryResponse | Problem]:
    """Create entry

     Add an entry to the project.
    Resources that are included within `links` are added to the project. Unlinking a resource does not
    remove the resource from the project.
    A key the operation doesn't take is 422 `unknown_field`, refused before anything else. A value the
    notes store refuses is 400 `validation_failed`, pointing at the field. A stale `version` is 409
    `version_conflict` with the `currentVersion` to retry with. A write that met another on the same
    records is 400 `write_contended` with `retryable: true`: nothing was stored, so send it again.

    Args:
        project_id (str):
        tamarind_version (str | Unset):
        body (CreateProjectNotesEntryBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CreateEntryResponse | Problem]
    """

    kwargs = _get_kwargs(
        project_id=project_id,
        body=body,
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
    body: CreateProjectNotesEntryBody,
    tamarind_version: str | Unset = UNSET,
) -> CreateEntryResponse | Problem | None:
    """Create entry

     Add an entry to the project.
    Resources that are included within `links` are added to the project. Unlinking a resource does not
    remove the resource from the project.
    A key the operation doesn't take is 422 `unknown_field`, refused before anything else. A value the
    notes store refuses is 400 `validation_failed`, pointing at the field. A stale `version` is 409
    `version_conflict` with the `currentVersion` to retry with. A write that met another on the same
    records is 400 `write_contended` with `retryable: true`: nothing was stored, so send it again.

    Args:
        project_id (str):
        tamarind_version (str | Unset):
        body (CreateProjectNotesEntryBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CreateEntryResponse | Problem
    """

    return sync_detailed(
        project_id=project_id,
        client=client,
        body=body,
        tamarind_version=tamarind_version,
    ).parsed


async def asyncio_detailed(
    project_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: CreateProjectNotesEntryBody,
    tamarind_version: str | Unset = UNSET,
) -> Response[CreateEntryResponse | Problem]:
    """Create entry

     Add an entry to the project.
    Resources that are included within `links` are added to the project. Unlinking a resource does not
    remove the resource from the project.
    A key the operation doesn't take is 422 `unknown_field`, refused before anything else. A value the
    notes store refuses is 400 `validation_failed`, pointing at the field. A stale `version` is 409
    `version_conflict` with the `currentVersion` to retry with. A write that met another on the same
    records is 400 `write_contended` with `retryable: true`: nothing was stored, so send it again.

    Args:
        project_id (str):
        tamarind_version (str | Unset):
        body (CreateProjectNotesEntryBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CreateEntryResponse | Problem]
    """

    kwargs = _get_kwargs(
        project_id=project_id,
        body=body,
        tamarind_version=tamarind_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    project_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: CreateProjectNotesEntryBody,
    tamarind_version: str | Unset = UNSET,
) -> CreateEntryResponse | Problem | None:
    """Create entry

     Add an entry to the project.
    Resources that are included within `links` are added to the project. Unlinking a resource does not
    remove the resource from the project.
    A key the operation doesn't take is 422 `unknown_field`, refused before anything else. A value the
    notes store refuses is 400 `validation_failed`, pointing at the field. A stale `version` is 409
    `version_conflict` with the `currentVersion` to retry with. A write that met another on the same
    records is 400 `write_contended` with `retryable: true`: nothing was stored, so send it again.

    Args:
        project_id (str):
        tamarind_version (str | Unset):
        body (CreateProjectNotesEntryBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CreateEntryResponse | Problem
    """

    return (
        await asyncio_detailed(
            project_id=project_id,
            client=client,
            body=body,
            tamarind_version=tamarind_version,
        )
    ).parsed
