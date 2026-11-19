from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.problem import Problem
from ...models.update_project_request import UpdateProjectRequest
from ...models.updated_project import UpdatedProject
from ...types import UNSET, Response, Unset


def _get_kwargs(
    project_id: str,
    *,
    body: UpdateProjectRequest,
    tamarind_version: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(tamarind_version, Unset):
        headers["Tamarind-Version"] = tamarind_version

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": "/projects/{project_id}".format(
            project_id=quote(str(project_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Problem | UpdatedProject:
    if response.status_code == 200:
        response_200 = UpdatedProject.from_dict(response.json())

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
) -> Response[Problem | UpdatedProject]:
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
    body: UpdateProjectRequest,
    tamarind_version: str | Unset = UNSET,
) -> Response[Problem | UpdatedProject]:
    """Update a project and its members

     Only the project's creator can do this. A project you can see but didn't create is 403; one you
    can't see is 404. Send only the fields to change. `null` clears `description`; for `name`,
    `color` and `isArchived` it is 422. `listProjectMembers` shows the result of `addMembers` and
    `removeMembers`. A member from outside who your sharing policy doesn't allow is 422 at
    `/addMembers/{i}` (diagnostic `not_in_org`), and 503 when that policy can't be read; nothing is
    written in either case. Adds that failed come back in `failedAdds`. A removal that fails
    answers 500 `members_not_removed`, because that person still has access, so retry it. Access
    saved in an older address format can't be removed here: 500 `member_key_outdated`, not
    retryable, and support removes it. Members changing while you save is 409 `members_changed`,
    and a name already in use is 409 `project_name_taken`. On those member errors the project's
    own fields are already saved, and `errors` names each address that didn't change.

    Args:
        project_id (str):
        tamarind_version (str | Unset):
        body (UpdateProjectRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Problem | UpdatedProject]
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
    body: UpdateProjectRequest,
    tamarind_version: str | Unset = UNSET,
) -> Problem | UpdatedProject | None:
    """Update a project and its members

     Only the project's creator can do this. A project you can see but didn't create is 403; one you
    can't see is 404. Send only the fields to change. `null` clears `description`; for `name`,
    `color` and `isArchived` it is 422. `listProjectMembers` shows the result of `addMembers` and
    `removeMembers`. A member from outside who your sharing policy doesn't allow is 422 at
    `/addMembers/{i}` (diagnostic `not_in_org`), and 503 when that policy can't be read; nothing is
    written in either case. Adds that failed come back in `failedAdds`. A removal that fails
    answers 500 `members_not_removed`, because that person still has access, so retry it. Access
    saved in an older address format can't be removed here: 500 `member_key_outdated`, not
    retryable, and support removes it. Members changing while you save is 409 `members_changed`,
    and a name already in use is 409 `project_name_taken`. On those member errors the project's
    own fields are already saved, and `errors` names each address that didn't change.

    Args:
        project_id (str):
        tamarind_version (str | Unset):
        body (UpdateProjectRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Problem | UpdatedProject
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
    body: UpdateProjectRequest,
    tamarind_version: str | Unset = UNSET,
) -> Response[Problem | UpdatedProject]:
    """Update a project and its members

     Only the project's creator can do this. A project you can see but didn't create is 403; one you
    can't see is 404. Send only the fields to change. `null` clears `description`; for `name`,
    `color` and `isArchived` it is 422. `listProjectMembers` shows the result of `addMembers` and
    `removeMembers`. A member from outside who your sharing policy doesn't allow is 422 at
    `/addMembers/{i}` (diagnostic `not_in_org`), and 503 when that policy can't be read; nothing is
    written in either case. Adds that failed come back in `failedAdds`. A removal that fails
    answers 500 `members_not_removed`, because that person still has access, so retry it. Access
    saved in an older address format can't be removed here: 500 `member_key_outdated`, not
    retryable, and support removes it. Members changing while you save is 409 `members_changed`,
    and a name already in use is 409 `project_name_taken`. On those member errors the project's
    own fields are already saved, and `errors` names each address that didn't change.

    Args:
        project_id (str):
        tamarind_version (str | Unset):
        body (UpdateProjectRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Problem | UpdatedProject]
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
    body: UpdateProjectRequest,
    tamarind_version: str | Unset = UNSET,
) -> Problem | UpdatedProject | None:
    """Update a project and its members

     Only the project's creator can do this. A project you can see but didn't create is 403; one you
    can't see is 404. Send only the fields to change. `null` clears `description`; for `name`,
    `color` and `isArchived` it is 422. `listProjectMembers` shows the result of `addMembers` and
    `removeMembers`. A member from outside who your sharing policy doesn't allow is 422 at
    `/addMembers/{i}` (diagnostic `not_in_org`), and 503 when that policy can't be read; nothing is
    written in either case. Adds that failed come back in `failedAdds`. A removal that fails
    answers 500 `members_not_removed`, because that person still has access, so retry it. Access
    saved in an older address format can't be removed here: 500 `member_key_outdated`, not
    retryable, and support removes it. Members changing while you save is 409 `members_changed`,
    and a name already in use is 409 `project_name_taken`. On those member errors the project's
    own fields are already saved, and `errors` names each address that didn't change.

    Args:
        project_id (str):
        tamarind_version (str | Unset):
        body (UpdateProjectRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Problem | UpdatedProject
    """

    return (
        await asyncio_detailed(
            project_id=project_id,
            client=client,
            body=body,
            tamarind_version=tamarind_version,
        )
    ).parsed
