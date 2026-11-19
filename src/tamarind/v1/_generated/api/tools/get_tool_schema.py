from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.problem import Problem
from ...models.tool_schema import ToolSchema
from ...types import UNSET, Response, Unset


def _get_kwargs(
    tool: str,
    *,
    version: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(tamarind_version, Unset):
        headers["Tamarind-Version"] = tamarind_version

    params: dict[str, Any] = {}

    params["version"] = version

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/tools/{tool}/schema".format(
            tool=quote(str(tool), safe=""),
        ),
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Problem | ToolSchema:
    if response.status_code == 200:
        response_200 = ToolSchema.from_dict(response.json())

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
) -> Response[Problem | ToolSchema]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    tool: str,
    *,
    client: AuthenticatedClient | Client,
    version: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Response[Problem | ToolSchema]:
    """Get a tool's settings schema and an example

     Built-in tools only for now: any other name, or a tool hidden from you, is 404
    `tool_not_found`. Settings behind a flag that's off for you are left out, and so are settings
    that depend on one left out; settings limited to some organizations or surfaces are kept and
    annotated.

    `example` is a `settings` object built from each setting's example or default, for one task
    branch, so clients don't have to strip conditional fields themselves. It isn't guaranteed to
    pass `validateJob`: file settings carry placeholder names (`target.pdb`) until you upload
    yours. `validateJob` also checks access,
    budget, quota and the queue.

    Args:
        tool (str):
        version (str | Unset):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Problem | ToolSchema]
    """

    kwargs = _get_kwargs(
        tool=tool,
        version=version,
        tamarind_version=tamarind_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    tool: str,
    *,
    client: AuthenticatedClient | Client,
    version: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Problem | ToolSchema | None:
    """Get a tool's settings schema and an example

     Built-in tools only for now: any other name, or a tool hidden from you, is 404
    `tool_not_found`. Settings behind a flag that's off for you are left out, and so are settings
    that depend on one left out; settings limited to some organizations or surfaces are kept and
    annotated.

    `example` is a `settings` object built from each setting's example or default, for one task
    branch, so clients don't have to strip conditional fields themselves. It isn't guaranteed to
    pass `validateJob`: file settings carry placeholder names (`target.pdb`) until you upload
    yours. `validateJob` also checks access,
    budget, quota and the queue.

    Args:
        tool (str):
        version (str | Unset):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Problem | ToolSchema
    """

    return sync_detailed(
        tool=tool,
        client=client,
        version=version,
        tamarind_version=tamarind_version,
    ).parsed


async def asyncio_detailed(
    tool: str,
    *,
    client: AuthenticatedClient | Client,
    version: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Response[Problem | ToolSchema]:
    """Get a tool's settings schema and an example

     Built-in tools only for now: any other name, or a tool hidden from you, is 404
    `tool_not_found`. Settings behind a flag that's off for you are left out, and so are settings
    that depend on one left out; settings limited to some organizations or surfaces are kept and
    annotated.

    `example` is a `settings` object built from each setting's example or default, for one task
    branch, so clients don't have to strip conditional fields themselves. It isn't guaranteed to
    pass `validateJob`: file settings carry placeholder names (`target.pdb`) until you upload
    yours. `validateJob` also checks access,
    budget, quota and the queue.

    Args:
        tool (str):
        version (str | Unset):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Problem | ToolSchema]
    """

    kwargs = _get_kwargs(
        tool=tool,
        version=version,
        tamarind_version=tamarind_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    tool: str,
    *,
    client: AuthenticatedClient | Client,
    version: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Problem | ToolSchema | None:
    """Get a tool's settings schema and an example

     Built-in tools only for now: any other name, or a tool hidden from you, is 404
    `tool_not_found`. Settings behind a flag that's off for you are left out, and so are settings
    that depend on one left out; settings limited to some organizations or surfaces are kept and
    annotated.

    `example` is a `settings` object built from each setting's example or default, for one task
    branch, so clients don't have to strip conditional fields themselves. It isn't guaranteed to
    pass `validateJob`: file settings carry placeholder names (`target.pdb`) until you upload
    yours. `validateJob` also checks access,
    budget, quota and the queue.

    Args:
        tool (str):
        version (str | Unset):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Problem | ToolSchema
    """

    return (
        await asyncio_detailed(
            tool=tool,
            client=client,
            version=version,
            tamarind_version=tamarind_version,
        )
    ).parsed
