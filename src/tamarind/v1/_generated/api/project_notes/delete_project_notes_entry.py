from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.problem import Problem
from ...types import UNSET, Response, Unset


def _get_kwargs(
    project_id: str,
    entry_id: str,
    *,
    version: int,
    tamarind_version: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(tamarind_version, Unset):
        headers["Tamarind-Version"] = tamarind_version

    params: dict[str, Any] = {}

    params["version"] = version

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": "/projects/{project_id}/notes/entries/{entry_id}".format(
            project_id=quote(str(project_id), safe=""),
            entry_id=quote(str(entry_id), safe=""),
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
    entry_id: str,
    *,
    client: AuthenticatedClient | Client,
    version: int,
    tamarind_version: str | Unset = UNSET,
) -> Response[Any | Problem]:
    """Delete entry

     Delete an entry for a project and all of its associated notes.
    A missing or non-integer `version` is 422. A stale `version` is 409 `version_conflict` with the
    `currentVersion` to retry with. A write that met another on the same records is 400
    `write_contended` with `retryable: true`: nothing was stored, so send it again.

    Args:
        project_id (str):
        entry_id (str):
        version (int):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | Problem]
    """

    kwargs = _get_kwargs(
        project_id=project_id,
        entry_id=entry_id,
        version=version,
        tamarind_version=tamarind_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    project_id: str,
    entry_id: str,
    *,
    client: AuthenticatedClient | Client,
    version: int,
    tamarind_version: str | Unset = UNSET,
) -> Any | Problem | None:
    """Delete entry

     Delete an entry for a project and all of its associated notes.
    A missing or non-integer `version` is 422. A stale `version` is 409 `version_conflict` with the
    `currentVersion` to retry with. A write that met another on the same records is 400
    `write_contended` with `retryable: true`: nothing was stored, so send it again.

    Args:
        project_id (str):
        entry_id (str):
        version (int):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | Problem
    """

    return sync_detailed(
        project_id=project_id,
        entry_id=entry_id,
        client=client,
        version=version,
        tamarind_version=tamarind_version,
    ).parsed


async def asyncio_detailed(
    project_id: str,
    entry_id: str,
    *,
    client: AuthenticatedClient | Client,
    version: int,
    tamarind_version: str | Unset = UNSET,
) -> Response[Any | Problem]:
    """Delete entry

     Delete an entry for a project and all of its associated notes.
    A missing or non-integer `version` is 422. A stale `version` is 409 `version_conflict` with the
    `currentVersion` to retry with. A write that met another on the same records is 400
    `write_contended` with `retryable: true`: nothing was stored, so send it again.

    Args:
        project_id (str):
        entry_id (str):
        version (int):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | Problem]
    """

    kwargs = _get_kwargs(
        project_id=project_id,
        entry_id=entry_id,
        version=version,
        tamarind_version=tamarind_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    project_id: str,
    entry_id: str,
    *,
    client: AuthenticatedClient | Client,
    version: int,
    tamarind_version: str | Unset = UNSET,
) -> Any | Problem | None:
    """Delete entry

     Delete an entry for a project and all of its associated notes.
    A missing or non-integer `version` is 422. A stale `version` is 409 `version_conflict` with the
    `currentVersion` to retry with. A write that met another on the same records is 400
    `write_contended` with `retryable: true`: nothing was stored, so send it again.

    Args:
        project_id (str):
        entry_id (str):
        version (int):
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
            entry_id=entry_id,
            client=client,
            version=version,
            tamarind_version=tamarind_version,
        )
    ).parsed
