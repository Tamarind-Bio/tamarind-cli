from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.build_custom_tool_request import BuildCustomToolRequest
from ...models.custom_tool_build_result import CustomToolBuildResult
from ...models.problem import Problem
from ...types import UNSET, Response, Unset


def _get_kwargs(
    name: str,
    *,
    body: BuildCustomToolRequest,
    idempotency_key: str | Unset = UNSET,
    if_match: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(idempotency_key, Unset):
        headers["Idempotency-Key"] = idempotency_key

    if not isinstance(if_match, Unset):
        headers["If-Match"] = if_match

    if not isinstance(tamarind_version, Unset):
        headers["Tamarind-Version"] = tamarind_version

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/custom-tools/{name}/build".format(
            name=quote(str(name), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> CustomToolBuildResult | Problem:
    if response.status_code == 202:
        response_202 = CustomToolBuildResult.from_dict(response.json())

        return response_202

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

    if response.status_code == 412:
        response_412 = Problem.from_dict(response.json())

        return response_412

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
) -> Response[CustomToolBuildResult | Problem]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    name: str,
    *,
    client: AuthenticatedClient | Client,
    body: BuildCustomToolRequest,
    idempotency_key: str | Unset = UNSET,
    if_match: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Response[CustomToolBuildResult | Problem]:
    """Build a custom tool

     Build a version from an uploaded source archive.

    The archive also updates the tool's editable source and configuration. Optionally send the Tool
    `etag` field from the Get tool JSON body to reject concurrent edits. Without it, the current tool is
    updated.
    Returns immediately with the new or reused version and its current status.

    `Idempotency-Key` keeps the carried Custom Tools behaviour, not the API-wide one: a retry with the
    same key
    and the same uploaded bytes answers 202 with the version it admitted and `action: unchanged`, with
    no
    `Idempotent-Replayed` header, and the same key for a different build (another upload, or other
    runtime
    settings) is 409 `custom_tool_idempotency_key_conflict`, not 422 `idempotency_key_reused`.

    Args:
        name (str): The custom tool name.
        idempotency_key (str | Unset):
        if_match (str | Unset):
        tamarind_version (str | Unset):
        body (BuildCustomToolRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CustomToolBuildResult | Problem]
    """

    kwargs = _get_kwargs(
        name=name,
        body=body,
        idempotency_key=idempotency_key,
        if_match=if_match,
        tamarind_version=tamarind_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    name: str,
    *,
    client: AuthenticatedClient | Client,
    body: BuildCustomToolRequest,
    idempotency_key: str | Unset = UNSET,
    if_match: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> CustomToolBuildResult | Problem | None:
    """Build a custom tool

     Build a version from an uploaded source archive.

    The archive also updates the tool's editable source and configuration. Optionally send the Tool
    `etag` field from the Get tool JSON body to reject concurrent edits. Without it, the current tool is
    updated.
    Returns immediately with the new or reused version and its current status.

    `Idempotency-Key` keeps the carried Custom Tools behaviour, not the API-wide one: a retry with the
    same key
    and the same uploaded bytes answers 202 with the version it admitted and `action: unchanged`, with
    no
    `Idempotent-Replayed` header, and the same key for a different build (another upload, or other
    runtime
    settings) is 409 `custom_tool_idempotency_key_conflict`, not 422 `idempotency_key_reused`.

    Args:
        name (str): The custom tool name.
        idempotency_key (str | Unset):
        if_match (str | Unset):
        tamarind_version (str | Unset):
        body (BuildCustomToolRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CustomToolBuildResult | Problem
    """

    return sync_detailed(
        name=name,
        client=client,
        body=body,
        idempotency_key=idempotency_key,
        if_match=if_match,
        tamarind_version=tamarind_version,
    ).parsed


async def asyncio_detailed(
    name: str,
    *,
    client: AuthenticatedClient | Client,
    body: BuildCustomToolRequest,
    idempotency_key: str | Unset = UNSET,
    if_match: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Response[CustomToolBuildResult | Problem]:
    """Build a custom tool

     Build a version from an uploaded source archive.

    The archive also updates the tool's editable source and configuration. Optionally send the Tool
    `etag` field from the Get tool JSON body to reject concurrent edits. Without it, the current tool is
    updated.
    Returns immediately with the new or reused version and its current status.

    `Idempotency-Key` keeps the carried Custom Tools behaviour, not the API-wide one: a retry with the
    same key
    and the same uploaded bytes answers 202 with the version it admitted and `action: unchanged`, with
    no
    `Idempotent-Replayed` header, and the same key for a different build (another upload, or other
    runtime
    settings) is 409 `custom_tool_idempotency_key_conflict`, not 422 `idempotency_key_reused`.

    Args:
        name (str): The custom tool name.
        idempotency_key (str | Unset):
        if_match (str | Unset):
        tamarind_version (str | Unset):
        body (BuildCustomToolRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CustomToolBuildResult | Problem]
    """

    kwargs = _get_kwargs(
        name=name,
        body=body,
        idempotency_key=idempotency_key,
        if_match=if_match,
        tamarind_version=tamarind_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    name: str,
    *,
    client: AuthenticatedClient | Client,
    body: BuildCustomToolRequest,
    idempotency_key: str | Unset = UNSET,
    if_match: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> CustomToolBuildResult | Problem | None:
    """Build a custom tool

     Build a version from an uploaded source archive.

    The archive also updates the tool's editable source and configuration. Optionally send the Tool
    `etag` field from the Get tool JSON body to reject concurrent edits. Without it, the current tool is
    updated.
    Returns immediately with the new or reused version and its current status.

    `Idempotency-Key` keeps the carried Custom Tools behaviour, not the API-wide one: a retry with the
    same key
    and the same uploaded bytes answers 202 with the version it admitted and `action: unchanged`, with
    no
    `Idempotent-Replayed` header, and the same key for a different build (another upload, or other
    runtime
    settings) is 409 `custom_tool_idempotency_key_conflict`, not 422 `idempotency_key_reused`.

    Args:
        name (str): The custom tool name.
        idempotency_key (str | Unset):
        if_match (str | Unset):
        tamarind_version (str | Unset):
        body (BuildCustomToolRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CustomToolBuildResult | Problem
    """

    return (
        await asyncio_detailed(
            name=name,
            client=client,
            body=body,
            idempotency_key=idempotency_key,
            if_match=if_match,
            tamarind_version=tamarind_version,
        )
    ).parsed
