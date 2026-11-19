from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.molecule_caps_page import MoleculeCapsPage
from ...models.molecule_card_caps_page import MoleculeCardCapsPage
from ...models.molecule_card_page import MoleculeCardPage
from ...models.molecule_page import MoleculePage
from ...models.problem import Problem
from ...models.search_molecules_public_molecule_search_request import (
    SearchMoleculesPublicMoleculeSearchRequest,
)
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    body: SearchMoleculesPublicMoleculeSearchRequest,
    tamarind_version: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(tamarind_version, Unset):
        headers["Tamarind-Version"] = tamarind_version

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/molecules/search",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> MoleculeCapsPage | MoleculeCardCapsPage | MoleculeCardPage | MoleculePage | Problem:
    if response.status_code == 200:

        def _parse_response_200(
            data: object,
        ) -> MoleculeCapsPage | MoleculeCardCapsPage | MoleculeCardPage | MoleculePage:
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                response_200_type_0 = MoleculePage.from_dict(data)

                return response_200_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                response_200_type_1 = MoleculeCardPage.from_dict(data)

                return response_200_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                response_200_type_2 = MoleculeCapsPage.from_dict(data)

                return response_200_type_2
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            if not isinstance(data, dict):
                raise TypeError()
            response_200_type_3 = MoleculeCardCapsPage.from_dict(data)

            return response_200_type_3

        response_200 = _parse_response_200(response.json())

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

    if response.status_code == 413:
        response_413 = Problem.from_dict(response.json())

        return response_413

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
) -> Response[MoleculeCapsPage | MoleculeCardCapsPage | MoleculeCardPage | MoleculePage | Problem]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: SearchMoleculesPublicMoleculeSearchRequest,
    tamarind_version: str | Unset = UNSET,
) -> Response[MoleculeCapsPage | MoleculeCardCapsPage | MoleculeCardPage | MoleculePage | Problem]:
    """Search Molecules

     Search molecules using the same filters as `GET /molecules`, with the same names (`groupId`,
    `jobId`), plus `jobName`, which only this body takes. Send repeated filters as arrays. Maximum
    request body: 4 MB.

    Args:
        tamarind_version (str | Unset):
        body (SearchMoleculesPublicMoleculeSearchRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[MoleculeCapsPage | MoleculeCardCapsPage | MoleculeCardPage | MoleculePage | Problem]
    """

    kwargs = _get_kwargs(
        body=body,
        tamarind_version=tamarind_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    body: SearchMoleculesPublicMoleculeSearchRequest,
    tamarind_version: str | Unset = UNSET,
) -> MoleculeCapsPage | MoleculeCardCapsPage | MoleculeCardPage | MoleculePage | Problem | None:
    """Search Molecules

     Search molecules using the same filters as `GET /molecules`, with the same names (`groupId`,
    `jobId`), plus `jobName`, which only this body takes. Send repeated filters as arrays. Maximum
    request body: 4 MB.

    Args:
        tamarind_version (str | Unset):
        body (SearchMoleculesPublicMoleculeSearchRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        MoleculeCapsPage | MoleculeCardCapsPage | MoleculeCardPage | MoleculePage | Problem
    """

    return sync_detailed(
        client=client,
        body=body,
        tamarind_version=tamarind_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: SearchMoleculesPublicMoleculeSearchRequest,
    tamarind_version: str | Unset = UNSET,
) -> Response[MoleculeCapsPage | MoleculeCardCapsPage | MoleculeCardPage | MoleculePage | Problem]:
    """Search Molecules

     Search molecules using the same filters as `GET /molecules`, with the same names (`groupId`,
    `jobId`), plus `jobName`, which only this body takes. Send repeated filters as arrays. Maximum
    request body: 4 MB.

    Args:
        tamarind_version (str | Unset):
        body (SearchMoleculesPublicMoleculeSearchRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[MoleculeCapsPage | MoleculeCardCapsPage | MoleculeCardPage | MoleculePage | Problem]
    """

    kwargs = _get_kwargs(
        body=body,
        tamarind_version=tamarind_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: SearchMoleculesPublicMoleculeSearchRequest,
    tamarind_version: str | Unset = UNSET,
) -> MoleculeCapsPage | MoleculeCardCapsPage | MoleculeCardPage | MoleculePage | Problem | None:
    """Search Molecules

     Search molecules using the same filters as `GET /molecules`, with the same names (`groupId`,
    `jobId`), plus `jobName`, which only this body takes. Send repeated filters as arrays. Maximum
    request body: 4 MB.

    Args:
        tamarind_version (str | Unset):
        body (SearchMoleculesPublicMoleculeSearchRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        MoleculeCapsPage | MoleculeCardCapsPage | MoleculeCardPage | MoleculePage | Problem
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            tamarind_version=tamarind_version,
        )
    ).parsed
