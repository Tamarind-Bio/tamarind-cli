from http import HTTPStatus
from typing import Any
from urllib.parse import quote
from uuid import UUID

import httpx

from ...client import AuthenticatedClient, Client
from ...models.molecule import Molecule
from ...models.problem import Problem
from ...models.update_metadata_request import UpdateMetadataRequest
from ...types import UNSET, Response, Unset


def _get_kwargs(
    molecule_id: UUID,
    *,
    body: UpdateMetadataRequest,
    tamarind_version: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(tamarind_version, Unset):
        headers["Tamarind-Version"] = tamarind_version

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": "/molecules/{molecule_id}/metadata".format(
            molecule_id=quote(str(molecule_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Molecule | Problem:
    if response.status_code == 200:
        response_200 = Molecule.from_dict(response.json())

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
) -> Response[Molecule | Problem]:
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
    body: UpdateMetadataRequest,
    tamarind_version: str | Unset = UNSET,
) -> Response[Molecule | Problem]:
    """Update Molecule Metadata

     Update a molecule. All fields are optional and applied together. Leave one out to leave it
    unchanged, and send `null` to clear `source` or `fileId`.

    Merge your own annotations with `properties` (tool scores aren't editable here). Set the derived-
    from molecule with `source`, this group's primary structure file with `fileId`, and the per-group
    display name with `name`.

    A `name` already used in the group returns `409`.

    Args:
        molecule_id (UUID):
        tamarind_version (str | Unset):
        body (UpdateMetadataRequest): The spec's `UpdateMoleculeRequest` — a PARTIAL patch across
            the MOLECULE and
            MEMBERSHIP tenancy grains, applied ATOMICALLY (all-or-nothing, one transaction: if any
            field's write fails, none of them persist).

            Every field is OPTIONAL and independent: an ABSENT field is left untouched, which
            is DISTINCT from a field sent as `null` (which CLEARS it, where the grain allows).
            The fields and the grain each writes:

              * `properties` (MOLECULE grain) — merge scalar annotations into the molecule's
                metadata. Only the keys you send change; a key set to `null` REMOVES that key
                (an absent key and a null key mean different things, so the raw dict carries
                intent). Tool score-run entries are written by tools and are not editable here;
                when the molecule's group is schema-bound the MERGED result must still satisfy
                it. This is the properties-only PATCH's behaviour, unchanged.
              * `source` (MOLECULE grain) — the id of the PARENT molecule this one was derived
                from; `null` clears it. The parent must be visible in YOUR scope, or the write
                is refused (404) — you cannot point a molecule at a parent you cannot see.
              * `fileId` (MOLECULE + MEMBERSHIP grain) — a structure file to associate as this
                membership's primary; `null` clears it. The file must already be attached to
                this molecule in your tenant.
              * `name` (MEMBERSHIP grain) — rename this molecule's per-group display name. A
                name already used by another molecule in the same group is a 409 conflict (the
                `UNIQUE (group_id, name)` constraint), never a 500.

            The membership-grained writes (`name`, `fileId`) target the molecule's MOST RECENT
            in-scope group membership, matching how the group-less by-id read resolves labels.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Molecule | Problem]
    """

    kwargs = _get_kwargs(
        molecule_id=molecule_id,
        body=body,
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
    body: UpdateMetadataRequest,
    tamarind_version: str | Unset = UNSET,
) -> Molecule | Problem | None:
    """Update Molecule Metadata

     Update a molecule. All fields are optional and applied together. Leave one out to leave it
    unchanged, and send `null` to clear `source` or `fileId`.

    Merge your own annotations with `properties` (tool scores aren't editable here). Set the derived-
    from molecule with `source`, this group's primary structure file with `fileId`, and the per-group
    display name with `name`.

    A `name` already used in the group returns `409`.

    Args:
        molecule_id (UUID):
        tamarind_version (str | Unset):
        body (UpdateMetadataRequest): The spec's `UpdateMoleculeRequest` — a PARTIAL patch across
            the MOLECULE and
            MEMBERSHIP tenancy grains, applied ATOMICALLY (all-or-nothing, one transaction: if any
            field's write fails, none of them persist).

            Every field is OPTIONAL and independent: an ABSENT field is left untouched, which
            is DISTINCT from a field sent as `null` (which CLEARS it, where the grain allows).
            The fields and the grain each writes:

              * `properties` (MOLECULE grain) — merge scalar annotations into the molecule's
                metadata. Only the keys you send change; a key set to `null` REMOVES that key
                (an absent key and a null key mean different things, so the raw dict carries
                intent). Tool score-run entries are written by tools and are not editable here;
                when the molecule's group is schema-bound the MERGED result must still satisfy
                it. This is the properties-only PATCH's behaviour, unchanged.
              * `source` (MOLECULE grain) — the id of the PARENT molecule this one was derived
                from; `null` clears it. The parent must be visible in YOUR scope, or the write
                is refused (404) — you cannot point a molecule at a parent you cannot see.
              * `fileId` (MOLECULE + MEMBERSHIP grain) — a structure file to associate as this
                membership's primary; `null` clears it. The file must already be attached to
                this molecule in your tenant.
              * `name` (MEMBERSHIP grain) — rename this molecule's per-group display name. A
                name already used by another molecule in the same group is a 409 conflict (the
                `UNIQUE (group_id, name)` constraint), never a 500.

            The membership-grained writes (`name`, `fileId`) target the molecule's MOST RECENT
            in-scope group membership, matching how the group-less by-id read resolves labels.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Molecule | Problem
    """

    return sync_detailed(
        molecule_id=molecule_id,
        client=client,
        body=body,
        tamarind_version=tamarind_version,
    ).parsed


async def asyncio_detailed(
    molecule_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateMetadataRequest,
    tamarind_version: str | Unset = UNSET,
) -> Response[Molecule | Problem]:
    """Update Molecule Metadata

     Update a molecule. All fields are optional and applied together. Leave one out to leave it
    unchanged, and send `null` to clear `source` or `fileId`.

    Merge your own annotations with `properties` (tool scores aren't editable here). Set the derived-
    from molecule with `source`, this group's primary structure file with `fileId`, and the per-group
    display name with `name`.

    A `name` already used in the group returns `409`.

    Args:
        molecule_id (UUID):
        tamarind_version (str | Unset):
        body (UpdateMetadataRequest): The spec's `UpdateMoleculeRequest` — a PARTIAL patch across
            the MOLECULE and
            MEMBERSHIP tenancy grains, applied ATOMICALLY (all-or-nothing, one transaction: if any
            field's write fails, none of them persist).

            Every field is OPTIONAL and independent: an ABSENT field is left untouched, which
            is DISTINCT from a field sent as `null` (which CLEARS it, where the grain allows).
            The fields and the grain each writes:

              * `properties` (MOLECULE grain) — merge scalar annotations into the molecule's
                metadata. Only the keys you send change; a key set to `null` REMOVES that key
                (an absent key and a null key mean different things, so the raw dict carries
                intent). Tool score-run entries are written by tools and are not editable here;
                when the molecule's group is schema-bound the MERGED result must still satisfy
                it. This is the properties-only PATCH's behaviour, unchanged.
              * `source` (MOLECULE grain) — the id of the PARENT molecule this one was derived
                from; `null` clears it. The parent must be visible in YOUR scope, or the write
                is refused (404) — you cannot point a molecule at a parent you cannot see.
              * `fileId` (MOLECULE + MEMBERSHIP grain) — a structure file to associate as this
                membership's primary; `null` clears it. The file must already be attached to
                this molecule in your tenant.
              * `name` (MEMBERSHIP grain) — rename this molecule's per-group display name. A
                name already used by another molecule in the same group is a 409 conflict (the
                `UNIQUE (group_id, name)` constraint), never a 500.

            The membership-grained writes (`name`, `fileId`) target the molecule's MOST RECENT
            in-scope group membership, matching how the group-less by-id read resolves labels.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Molecule | Problem]
    """

    kwargs = _get_kwargs(
        molecule_id=molecule_id,
        body=body,
        tamarind_version=tamarind_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    molecule_id: UUID,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateMetadataRequest,
    tamarind_version: str | Unset = UNSET,
) -> Molecule | Problem | None:
    """Update Molecule Metadata

     Update a molecule. All fields are optional and applied together. Leave one out to leave it
    unchanged, and send `null` to clear `source` or `fileId`.

    Merge your own annotations with `properties` (tool scores aren't editable here). Set the derived-
    from molecule with `source`, this group's primary structure file with `fileId`, and the per-group
    display name with `name`.

    A `name` already used in the group returns `409`.

    Args:
        molecule_id (UUID):
        tamarind_version (str | Unset):
        body (UpdateMetadataRequest): The spec's `UpdateMoleculeRequest` — a PARTIAL patch across
            the MOLECULE and
            MEMBERSHIP tenancy grains, applied ATOMICALLY (all-or-nothing, one transaction: if any
            field's write fails, none of them persist).

            Every field is OPTIONAL and independent: an ABSENT field is left untouched, which
            is DISTINCT from a field sent as `null` (which CLEARS it, where the grain allows).
            The fields and the grain each writes:

              * `properties` (MOLECULE grain) — merge scalar annotations into the molecule's
                metadata. Only the keys you send change; a key set to `null` REMOVES that key
                (an absent key and a null key mean different things, so the raw dict carries
                intent). Tool score-run entries are written by tools and are not editable here;
                when the molecule's group is schema-bound the MERGED result must still satisfy
                it. This is the properties-only PATCH's behaviour, unchanged.
              * `source` (MOLECULE grain) — the id of the PARENT molecule this one was derived
                from; `null` clears it. The parent must be visible in YOUR scope, or the write
                is refused (404) — you cannot point a molecule at a parent you cannot see.
              * `fileId` (MOLECULE + MEMBERSHIP grain) — a structure file to associate as this
                membership's primary; `null` clears it. The file must already be attached to
                this molecule in your tenant.
              * `name` (MEMBERSHIP grain) — rename this molecule's per-group display name. A
                name already used by another molecule in the same group is a 409 conflict (the
                `UNIQUE (group_id, name)` constraint), never a 500.

            The membership-grained writes (`name`, `fileId`) target the molecule's MOST RECENT
            in-scope group membership, matching how the group-less by-id read resolves labels.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Molecule | Problem
    """

    return (
        await asyncio_detailed(
            molecule_id=molecule_id,
            client=client,
            body=body,
            tamarind_version=tamarind_version,
        )
    ).parsed
