from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.problem import Problem
from ...types import UNSET, Response, Unset


def _get_kwargs(
    project_id: str,
    *,
    move_to_project_id: str | Unset = UNSET,
    confirm_job_removal: bool | Unset = False,
    tamarind_version: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(tamarind_version, Unset):
        headers["Tamarind-Version"] = tamarind_version

    params: dict[str, Any] = {}

    params["moveToProjectId"] = move_to_project_id

    params["confirmJobRemoval"] = confirm_job_removal

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": "/projects/{project_id}".format(
            project_id=quote(str(project_id), safe=""),
        ),
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Any | Problem:
    if response.status_code == 204:
        response_204 = cast(Any, None)
        return response_204

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
) -> Response[Any | Problem]:
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
    move_to_project_id: str | Unset = UNSET,
    confirm_job_removal: bool | Unset = False,
    tamarind_version: str | Unset = UNSET,
) -> Response[Any | Problem]:
    """Delete a project. Its jobs are kept

     Only the project's creator can do this. A project with jobs needs one of two choices:
    `moveToProjectId`
    moves them to another project, and `confirmJobRemoval=true` leaves them in no project. With neither,
    the
    answer is 409 `project_not_empty`. If your organization requires a project on every job, leaving
    them in
    none is not allowed, so `moveToProjectId` is the only choice and anything else is 409
    `project_move_required`.
    Only jobs the app lists count here: a project holding only deleted jobs needs no choice, and those
    are
    unfiled, or moved with the rest. `moveToProjectId` is checked only when the project has jobs.
    A `moveToProjectId` that is this project, is archived, doesn't resolve for you, or breaks your
    organization's project policy (projects turned off, or an organization project required) is 422 at
    `/moveToProjectId`. Jobs move in bulk only to an organization project, or between your own personal
    projects, and any other target is 403. A key only moves or unfiles jobs its owner owns, so a project
    holding anyone else's is 403 too, before anything is written.

    Moving the jobs runs inside the request. If it stops partway, the project is kept and the answer is
    500
    `project_partially_emptied`, which is retryable: repeating the call finishes the move. A very large
    project can need a few calls. The project's notes go with it, and a personal project's members and
    shares are removed with it.

    Args:
        project_id (str):
        move_to_project_id (str | Unset):
        confirm_job_removal (bool | Unset):  Default: False.
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | Problem]
    """

    kwargs = _get_kwargs(
        project_id=project_id,
        move_to_project_id=move_to_project_id,
        confirm_job_removal=confirm_job_removal,
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
    move_to_project_id: str | Unset = UNSET,
    confirm_job_removal: bool | Unset = False,
    tamarind_version: str | Unset = UNSET,
) -> Any | Problem | None:
    """Delete a project. Its jobs are kept

     Only the project's creator can do this. A project with jobs needs one of two choices:
    `moveToProjectId`
    moves them to another project, and `confirmJobRemoval=true` leaves them in no project. With neither,
    the
    answer is 409 `project_not_empty`. If your organization requires a project on every job, leaving
    them in
    none is not allowed, so `moveToProjectId` is the only choice and anything else is 409
    `project_move_required`.
    Only jobs the app lists count here: a project holding only deleted jobs needs no choice, and those
    are
    unfiled, or moved with the rest. `moveToProjectId` is checked only when the project has jobs.
    A `moveToProjectId` that is this project, is archived, doesn't resolve for you, or breaks your
    organization's project policy (projects turned off, or an organization project required) is 422 at
    `/moveToProjectId`. Jobs move in bulk only to an organization project, or between your own personal
    projects, and any other target is 403. A key only moves or unfiles jobs its owner owns, so a project
    holding anyone else's is 403 too, before anything is written.

    Moving the jobs runs inside the request. If it stops partway, the project is kept and the answer is
    500
    `project_partially_emptied`, which is retryable: repeating the call finishes the move. A very large
    project can need a few calls. The project's notes go with it, and a personal project's members and
    shares are removed with it.

    Args:
        project_id (str):
        move_to_project_id (str | Unset):
        confirm_job_removal (bool | Unset):  Default: False.
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | Problem
    """

    return sync_detailed(
        project_id=project_id,
        client=client,
        move_to_project_id=move_to_project_id,
        confirm_job_removal=confirm_job_removal,
        tamarind_version=tamarind_version,
    ).parsed


async def asyncio_detailed(
    project_id: str,
    *,
    client: AuthenticatedClient | Client,
    move_to_project_id: str | Unset = UNSET,
    confirm_job_removal: bool | Unset = False,
    tamarind_version: str | Unset = UNSET,
) -> Response[Any | Problem]:
    """Delete a project. Its jobs are kept

     Only the project's creator can do this. A project with jobs needs one of two choices:
    `moveToProjectId`
    moves them to another project, and `confirmJobRemoval=true` leaves them in no project. With neither,
    the
    answer is 409 `project_not_empty`. If your organization requires a project on every job, leaving
    them in
    none is not allowed, so `moveToProjectId` is the only choice and anything else is 409
    `project_move_required`.
    Only jobs the app lists count here: a project holding only deleted jobs needs no choice, and those
    are
    unfiled, or moved with the rest. `moveToProjectId` is checked only when the project has jobs.
    A `moveToProjectId` that is this project, is archived, doesn't resolve for you, or breaks your
    organization's project policy (projects turned off, or an organization project required) is 422 at
    `/moveToProjectId`. Jobs move in bulk only to an organization project, or between your own personal
    projects, and any other target is 403. A key only moves or unfiles jobs its owner owns, so a project
    holding anyone else's is 403 too, before anything is written.

    Moving the jobs runs inside the request. If it stops partway, the project is kept and the answer is
    500
    `project_partially_emptied`, which is retryable: repeating the call finishes the move. A very large
    project can need a few calls. The project's notes go with it, and a personal project's members and
    shares are removed with it.

    Args:
        project_id (str):
        move_to_project_id (str | Unset):
        confirm_job_removal (bool | Unset):  Default: False.
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | Problem]
    """

    kwargs = _get_kwargs(
        project_id=project_id,
        move_to_project_id=move_to_project_id,
        confirm_job_removal=confirm_job_removal,
        tamarind_version=tamarind_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    project_id: str,
    *,
    client: AuthenticatedClient | Client,
    move_to_project_id: str | Unset = UNSET,
    confirm_job_removal: bool | Unset = False,
    tamarind_version: str | Unset = UNSET,
) -> Any | Problem | None:
    """Delete a project. Its jobs are kept

     Only the project's creator can do this. A project with jobs needs one of two choices:
    `moveToProjectId`
    moves them to another project, and `confirmJobRemoval=true` leaves them in no project. With neither,
    the
    answer is 409 `project_not_empty`. If your organization requires a project on every job, leaving
    them in
    none is not allowed, so `moveToProjectId` is the only choice and anything else is 409
    `project_move_required`.
    Only jobs the app lists count here: a project holding only deleted jobs needs no choice, and those
    are
    unfiled, or moved with the rest. `moveToProjectId` is checked only when the project has jobs.
    A `moveToProjectId` that is this project, is archived, doesn't resolve for you, or breaks your
    organization's project policy (projects turned off, or an organization project required) is 422 at
    `/moveToProjectId`. Jobs move in bulk only to an organization project, or between your own personal
    projects, and any other target is 403. A key only moves or unfiles jobs its owner owns, so a project
    holding anyone else's is 403 too, before anything is written.

    Moving the jobs runs inside the request. If it stops partway, the project is kept and the answer is
    500
    `project_partially_emptied`, which is retryable: repeating the call finishes the move. A very large
    project can need a few calls. The project's notes go with it, and a personal project's members and
    shares are removed with it.

    Args:
        project_id (str):
        move_to_project_id (str | Unset):
        confirm_job_removal (bool | Unset):  Default: False.
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | Problem
    """

    return (
        await asyncio_detailed(
            project_id=project_id,
            client=client,
            move_to_project_id=move_to_project_id,
            confirm_job_removal=confirm_job_removal,
            tamarind_version=tamarind_version,
        )
    ).parsed
