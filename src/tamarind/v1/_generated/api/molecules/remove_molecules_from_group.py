from http import HTTPStatus
from typing import Any
from urllib.parse import quote
from uuid import UUID

import httpx

from ...client import AuthenticatedClient, Client
from ...models.problem import Problem
from ...models.remove_molecules_request import RemoveMoleculesRequest
from ...models.remove_molecules_response import RemoveMoleculesResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    group_id: UUID,
    *,
    body: RemoveMoleculesRequest,
    tamarind_version: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(tamarind_version, Unset):
        headers["Tamarind-Version"] = tamarind_version

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/molecules/groups/{group_id}/molecules/remove".format(
            group_id=quote(str(group_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Problem | RemoveMoleculesResponse:
    if response.status_code == 200:
        response_200 = RemoveMoleculesResponse.from_dict(response.json())

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

    if response.status_code == 503:
        response_503 = Problem.from_dict(response.json())

        return response_503

    response_default = Problem.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[Problem | RemoveMoleculesResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    group_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    body: RemoveMoleculesRequest,
    tamarind_version: str | Unset = UNSET,
) -> Response[Problem | RemoveMoleculesResponse]:
    """Remove Molecules

     Remove molecules from a group.

    This detaches group membership; it does not delete the molecule, which stays in any other groups
    with its scores and files intact. To delete a molecule everywhere, use `DELETE
    /molecules/{moleculeId}`.

    Idempotent — ids not in the group are ignored, and `removedIds` lists what was detached.

    Args:
        group_id (UUID):
        tamarind_version (str | Unset):
        body (RemoveMoleculesRequest): Body for `POST
            /molecules/groups/{groupId}/molecules/remove`: the molecules to detach from the group in
            the path. Same `moleculeIds` cap (maxItems, a real statement bound — every id is a bound
            `uuid[]` parameter, never inlined).

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Problem | RemoveMoleculesResponse]
    """

    kwargs = _get_kwargs(
        group_id=group_id,
        body=body,
        tamarind_version=tamarind_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    group_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    body: RemoveMoleculesRequest,
    tamarind_version: str | Unset = UNSET,
) -> Problem | RemoveMoleculesResponse | None:
    """Remove Molecules

     Remove molecules from a group.

    This detaches group membership; it does not delete the molecule, which stays in any other groups
    with its scores and files intact. To delete a molecule everywhere, use `DELETE
    /molecules/{moleculeId}`.

    Idempotent — ids not in the group are ignored, and `removedIds` lists what was detached.

    Args:
        group_id (UUID):
        tamarind_version (str | Unset):
        body (RemoveMoleculesRequest): Body for `POST
            /molecules/groups/{groupId}/molecules/remove`: the molecules to detach from the group in
            the path. Same `moleculeIds` cap (maxItems, a real statement bound — every id is a bound
            `uuid[]` parameter, never inlined).

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Problem | RemoveMoleculesResponse
    """

    return sync_detailed(
        group_id=group_id,
        client=client,
        body=body,
        tamarind_version=tamarind_version,
    ).parsed


async def asyncio_detailed(
    group_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    body: RemoveMoleculesRequest,
    tamarind_version: str | Unset = UNSET,
) -> Response[Problem | RemoveMoleculesResponse]:
    """Remove Molecules

     Remove molecules from a group.

    This detaches group membership; it does not delete the molecule, which stays in any other groups
    with its scores and files intact. To delete a molecule everywhere, use `DELETE
    /molecules/{moleculeId}`.

    Idempotent — ids not in the group are ignored, and `removedIds` lists what was detached.

    Args:
        group_id (UUID):
        tamarind_version (str | Unset):
        body (RemoveMoleculesRequest): Body for `POST
            /molecules/groups/{groupId}/molecules/remove`: the molecules to detach from the group in
            the path. Same `moleculeIds` cap (maxItems, a real statement bound — every id is a bound
            `uuid[]` parameter, never inlined).

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Problem | RemoveMoleculesResponse]
    """

    kwargs = _get_kwargs(
        group_id=group_id,
        body=body,
        tamarind_version=tamarind_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    group_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    body: RemoveMoleculesRequest,
    tamarind_version: str | Unset = UNSET,
) -> Problem | RemoveMoleculesResponse | None:
    """Remove Molecules

     Remove molecules from a group.

    This detaches group membership; it does not delete the molecule, which stays in any other groups
    with its scores and files intact. To delete a molecule everywhere, use `DELETE
    /molecules/{moleculeId}`.

    Idempotent — ids not in the group are ignored, and `removedIds` lists what was detached.

    Args:
        group_id (UUID):
        tamarind_version (str | Unset):
        body (RemoveMoleculesRequest): Body for `POST
            /molecules/groups/{groupId}/molecules/remove`: the molecules to detach from the group in
            the path. Same `moleculeIds` cap (maxItems, a real statement bound — every id is a bound
            `uuid[]` parameter, never inlined).

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Problem | RemoveMoleculesResponse
    """

    return (
        await asyncio_detailed(
            group_id=group_id,
            client=client,
            body=body,
            tamarind_version=tamarind_version,
        )
    ).parsed
