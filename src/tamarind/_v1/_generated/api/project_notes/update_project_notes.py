from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.problem import Problem
from ...models.update_notes_response import UpdateNotesResponse
from ...models.update_project_notes_body import UpdateProjectNotesBody
from ...types import UNSET, Response, Unset


def _get_kwargs(
    project_id: str,
    *,
    body: UpdateProjectNotesBody,
    tamarind_version: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(tamarind_version, Unset):
        headers["Tamarind-Version"] = tamarind_version

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": "/projects/{project_id}/notes".format(
            project_id=quote(str(project_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Problem | UpdateNotesResponse:
    if response.status_code == 200:
        response_200 = UpdateNotesResponse.from_dict(response.json())

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
) -> Response[Problem | UpdateNotesResponse]:
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
    body: UpdateProjectNotesBody,
    tamarind_version: str | Unset = UNSET,
) -> Response[Problem | UpdateNotesResponse]:
    """Update project notes

     Update the project's details, its lanes and its statuses.
    Updatable fields: tags, owner, startDate, dueDate, laneOrder
    `lanes` and `statuses` take operations, so removing one can say where its work goes. The project's
    description isn't one of them: it belongs to the project (`updateProject`), so sending it is 422.
    A value the notes store refuses inside `lanes` or `statuses` names the field in `detail` rather than
    with a pointer.
    A key the operation doesn't take is 422 `unknown_field`, refused before anything else. A value the
    notes store refuses is 400 `validation_failed`, pointing at the field. A stale `version` is 409
    `version_conflict` with the `currentVersion` to retry with. A write that met another on the same
    records is 400 `write_contended` with `retryable: true`: nothing was stored, so send it again.

    Args:
        project_id (str):
        tamarind_version (str | Unset):
        body (UpdateProjectNotesBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Problem | UpdateNotesResponse]
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
    body: UpdateProjectNotesBody,
    tamarind_version: str | Unset = UNSET,
) -> Problem | UpdateNotesResponse | None:
    """Update project notes

     Update the project's details, its lanes and its statuses.
    Updatable fields: tags, owner, startDate, dueDate, laneOrder
    `lanes` and `statuses` take operations, so removing one can say where its work goes. The project's
    description isn't one of them: it belongs to the project (`updateProject`), so sending it is 422.
    A value the notes store refuses inside `lanes` or `statuses` names the field in `detail` rather than
    with a pointer.
    A key the operation doesn't take is 422 `unknown_field`, refused before anything else. A value the
    notes store refuses is 400 `validation_failed`, pointing at the field. A stale `version` is 409
    `version_conflict` with the `currentVersion` to retry with. A write that met another on the same
    records is 400 `write_contended` with `retryable: true`: nothing was stored, so send it again.

    Args:
        project_id (str):
        tamarind_version (str | Unset):
        body (UpdateProjectNotesBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Problem | UpdateNotesResponse
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
    body: UpdateProjectNotesBody,
    tamarind_version: str | Unset = UNSET,
) -> Response[Problem | UpdateNotesResponse]:
    """Update project notes

     Update the project's details, its lanes and its statuses.
    Updatable fields: tags, owner, startDate, dueDate, laneOrder
    `lanes` and `statuses` take operations, so removing one can say where its work goes. The project's
    description isn't one of them: it belongs to the project (`updateProject`), so sending it is 422.
    A value the notes store refuses inside `lanes` or `statuses` names the field in `detail` rather than
    with a pointer.
    A key the operation doesn't take is 422 `unknown_field`, refused before anything else. A value the
    notes store refuses is 400 `validation_failed`, pointing at the field. A stale `version` is 409
    `version_conflict` with the `currentVersion` to retry with. A write that met another on the same
    records is 400 `write_contended` with `retryable: true`: nothing was stored, so send it again.

    Args:
        project_id (str):
        tamarind_version (str | Unset):
        body (UpdateProjectNotesBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Problem | UpdateNotesResponse]
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
    body: UpdateProjectNotesBody,
    tamarind_version: str | Unset = UNSET,
) -> Problem | UpdateNotesResponse | None:
    """Update project notes

     Update the project's details, its lanes and its statuses.
    Updatable fields: tags, owner, startDate, dueDate, laneOrder
    `lanes` and `statuses` take operations, so removing one can say where its work goes. The project's
    description isn't one of them: it belongs to the project (`updateProject`), so sending it is 422.
    A value the notes store refuses inside `lanes` or `statuses` names the field in `detail` rather than
    with a pointer.
    A key the operation doesn't take is 422 `unknown_field`, refused before anything else. A value the
    notes store refuses is 400 `validation_failed`, pointing at the field. A stale `version` is 409
    `version_conflict` with the `currentVersion` to retry with. A write that met another on the same
    records is 400 `write_contended` with `retryable: true`: nothing was stored, so send it again.

    Args:
        project_id (str):
        tamarind_version (str | Unset):
        body (UpdateProjectNotesBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Problem | UpdateNotesResponse
    """

    return (
        await asyncio_detailed(
            project_id=project_id,
            client=client,
            body=body,
            tamarind_version=tamarind_version,
        )
    ).parsed
