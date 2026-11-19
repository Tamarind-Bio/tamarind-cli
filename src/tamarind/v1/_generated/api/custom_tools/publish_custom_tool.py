from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.custom_tool import CustomTool
from ...models.problem import Problem
from ...types import UNSET, Response, Unset


def _get_kwargs(
    name: str,
    *,
    version: None | str | Unset = UNSET,
    if_match: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(if_match, Unset):
        headers["If-Match"] = if_match

    if not isinstance(tamarind_version, Unset):
        headers["Tamarind-Version"] = tamarind_version

    params: dict[str, Any] = {}

    json_version: None | str | Unset
    if isinstance(version, Unset):
        json_version = UNSET
    else:
        json_version = version
    params["version"] = json_version

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/custom-tools/{name}/publish".format(
            name=quote(str(name), safe=""),
        ),
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> CustomTool | Problem:
    if response.status_code == 200:
        response_200 = CustomTool.from_dict(response.json())

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
) -> Response[CustomTool | Problem]:
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
    version: None | str | Unset = UNSET,
    if_match: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Response[CustomTool | Problem]:
    """Publish a custom tool version

     Publish a completed version.

    By default this publishes the latest completed version. Pass `version=v2` to publish or roll back
    to a specific completed version.

    Args:
        name (str): The custom tool name.
        version (None | str | Unset):
        if_match (str | Unset):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CustomTool | Problem]
    """

    kwargs = _get_kwargs(
        name=name,
        version=version,
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
    version: None | str | Unset = UNSET,
    if_match: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> CustomTool | Problem | None:
    """Publish a custom tool version

     Publish a completed version.

    By default this publishes the latest completed version. Pass `version=v2` to publish or roll back
    to a specific completed version.

    Args:
        name (str): The custom tool name.
        version (None | str | Unset):
        if_match (str | Unset):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CustomTool | Problem
    """

    return sync_detailed(
        name=name,
        client=client,
        version=version,
        if_match=if_match,
        tamarind_version=tamarind_version,
    ).parsed


async def asyncio_detailed(
    name: str,
    *,
    client: AuthenticatedClient | Client,
    version: None | str | Unset = UNSET,
    if_match: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Response[CustomTool | Problem]:
    """Publish a custom tool version

     Publish a completed version.

    By default this publishes the latest completed version. Pass `version=v2` to publish or roll back
    to a specific completed version.

    Args:
        name (str): The custom tool name.
        version (None | str | Unset):
        if_match (str | Unset):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CustomTool | Problem]
    """

    kwargs = _get_kwargs(
        name=name,
        version=version,
        if_match=if_match,
        tamarind_version=tamarind_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    name: str,
    *,
    client: AuthenticatedClient | Client,
    version: None | str | Unset = UNSET,
    if_match: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> CustomTool | Problem | None:
    """Publish a custom tool version

     Publish a completed version.

    By default this publishes the latest completed version. Pass `version=v2` to publish or roll back
    to a specific completed version.

    Args:
        name (str): The custom tool name.
        version (None | str | Unset):
        if_match (str | Unset):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CustomTool | Problem
    """

    return (
        await asyncio_detailed(
            name=name,
            client=client,
            version=version,
            if_match=if_match,
            tamarind_version=tamarind_version,
        )
    ).parsed
