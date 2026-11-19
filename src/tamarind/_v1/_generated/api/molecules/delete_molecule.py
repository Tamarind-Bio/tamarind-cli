from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote
from uuid import UUID

import httpx

from ...client import AuthenticatedClient, Client
from ...models.problem import Problem
from ...types import UNSET, Response, Unset


def _get_kwargs(
    molecule_id: UUID,
    *,
    tamarind_version: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(tamarind_version, Unset):
        headers["Tamarind-Version"] = tamarind_version

    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": "/molecules/{molecule_id}".format(
            molecule_id=quote(str(molecule_id), safe=""),
        ),
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
) -> Response[Any | Problem]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    molecule_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    tamarind_version: str | Unset = UNSET,
) -> Response[Any | Problem]:
    """Delete Molecule

     Permanently delete a molecule. Organization admin only, and a person's API key is never an
    organization admin, so only a service account's key can delete.

    Removes the molecule and all its group memberships, scores, and file links across the organization.
    To remove it from one group instead, use `POST /molecules/groups/{groupId}/molecules/remove`.

    A molecule is in reach only while one of your groups holds it, so once it has left its last group it
    can't be deleted here.

    Idempotent: an unknown id, or one you can't see or reach, also answers 204. So a 204 does not prove
    that a molecule was deleted. An id that isn't a UUID is 404.

    Args:
        molecule_id (UUID):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | Problem]
    """

    kwargs = _get_kwargs(
        molecule_id=molecule_id,
        tamarind_version=tamarind_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    molecule_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    tamarind_version: str | Unset = UNSET,
) -> Any | Problem | None:
    """Delete Molecule

     Permanently delete a molecule. Organization admin only, and a person's API key is never an
    organization admin, so only a service account's key can delete.

    Removes the molecule and all its group memberships, scores, and file links across the organization.
    To remove it from one group instead, use `POST /molecules/groups/{groupId}/molecules/remove`.

    A molecule is in reach only while one of your groups holds it, so once it has left its last group it
    can't be deleted here.

    Idempotent: an unknown id, or one you can't see or reach, also answers 204. So a 204 does not prove
    that a molecule was deleted. An id that isn't a UUID is 404.

    Args:
        molecule_id (UUID):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | Problem
    """

    return sync_detailed(
        molecule_id=molecule_id,
        client=client,
        tamarind_version=tamarind_version,
    ).parsed


async def asyncio_detailed(
    molecule_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    tamarind_version: str | Unset = UNSET,
) -> Response[Any | Problem]:
    """Delete Molecule

     Permanently delete a molecule. Organization admin only, and a person's API key is never an
    organization admin, so only a service account's key can delete.

    Removes the molecule and all its group memberships, scores, and file links across the organization.
    To remove it from one group instead, use `POST /molecules/groups/{groupId}/molecules/remove`.

    A molecule is in reach only while one of your groups holds it, so once it has left its last group it
    can't be deleted here.

    Idempotent: an unknown id, or one you can't see or reach, also answers 204. So a 204 does not prove
    that a molecule was deleted. An id that isn't a UUID is 404.

    Args:
        molecule_id (UUID):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | Problem]
    """

    kwargs = _get_kwargs(
        molecule_id=molecule_id,
        tamarind_version=tamarind_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    molecule_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    tamarind_version: str | Unset = UNSET,
) -> Any | Problem | None:
    """Delete Molecule

     Permanently delete a molecule. Organization admin only, and a person's API key is never an
    organization admin, so only a service account's key can delete.

    Removes the molecule and all its group memberships, scores, and file links across the organization.
    To remove it from one group instead, use `POST /molecules/groups/{groupId}/molecules/remove`.

    A molecule is in reach only while one of your groups holds it, so once it has left its last group it
    can't be deleted here.

    Idempotent: an unknown id, or one you can't see or reach, also answers 204. So a 204 does not prove
    that a molecule was deleted. An id that isn't a UUID is 404.

    Args:
        molecule_id (UUID):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | Problem
    """

    return (
        await asyncio_detailed(
            molecule_id=molecule_id,
            client=client,
            tamarind_version=tamarind_version,
        )
    ).parsed
