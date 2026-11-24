from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.list_tools_view import ListToolsView
from ...models.problem import Problem
from ...models.tool_page import ToolPage
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    search: str | Unset = UNSET,
    modality: str | Unset = UNSET,
    function: str | Unset = UNSET,
    custom: bool | Unset = UNSET,
    finetune: bool | Unset = UNSET,
    pipeline_tools: bool | Unset = False,
    limit: int | Unset = 50,
    cursor: str | Unset = UNSET,
    view: ListToolsView | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(tamarind_version, Unset):
        headers["Tamarind-Version"] = tamarind_version

    params: dict[str, Any] = {}

    params["search"] = search

    params["modality"] = modality

    params["function"] = function

    params["custom"] = custom

    params["finetune"] = finetune

    params["pipelineTools"] = pipeline_tools

    params["limit"] = limit

    params["cursor"] = cursor

    json_view: str | Unset = UNSET
    if not isinstance(view, Unset):
        json_view = view.value

    params["view"] = json_view

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/tools",
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Problem | ToolPage:
    if response.status_code == 200:
        response_200 = ToolPage.from_dict(response.json())

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
) -> Response[Problem | ToolPage]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    search: str | Unset = UNSET,
    modality: str | Unset = UNSET,
    function: str | Unset = UNSET,
    custom: bool | Unset = UNSET,
    finetune: bool | Unset = UNSET,
    pipeline_tools: bool | Unset = False,
    limit: int | Unset = 50,
    cursor: str | Unset = UNSET,
    view: ListToolsView | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Response[Problem | ToolPage]:
    """Find tools

     The built-in tools your account may run, in the catalog's display order rather than newest
    first. Visibility rules live in this endpoint, not in clients: a tool a flag, a block or
    licensing hides from you isn't listed, and neither is one your submit would be refused (your
    organization's or team's policy, a licence such as Rosetta's, a GPL tool for a pharma
    organization, or a domain restriction). As today's `GET /api/tools` does, the list also leaves
    out a tool with no display name of its own or one hidden from the app's tool pages, though it
    still answers by name on `getTool`, `getToolSchema` and a submit. `view=agent` lists the
    catalog as the Tamarind MCP and agents see it instead (see the parameter).

    `custom=true` lists your organization's custom tools instead, as the MCP lists them: each one
    whose current version is deployed and published, by name, in name order, with the same
    filters; `view` doesn't change it. A tool whose current version is private or a draft isn't
    listed, even when an earlier version was published. With no organization, or only a personal
    one, the list is empty. A custom tool's `finetune` is true only when it trains models and your
    organization has custom finetuning. To manage custom tools, see `listCustomTools`.

    At launch this answers without a key too, like today's public `/tools.json`: without a key you
    get the public catalog, the tools a signed-out reader of the docs may see; with one, the tools
    its owner may run. Requests without a key share one overall rate limit. Until launch it needs a
    key like every v1 operation, because the `api-v1` flag decides by the caller. Without a key,
    `custom` and `view` are 400.

    Args:
        search (str | Unset):
        modality (str | Unset):
        function (str | Unset):
        custom (bool | Unset):
        finetune (bool | Unset):
        pipeline_tools (bool | Unset):  Default: False.
        limit (int | Unset):  Default: 50.
        cursor (str | Unset):
        view (ListToolsView | Unset):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Problem | ToolPage]
    """

    kwargs = _get_kwargs(
        search=search,
        modality=modality,
        function=function,
        custom=custom,
        finetune=finetune,
        pipeline_tools=pipeline_tools,
        limit=limit,
        cursor=cursor,
        view=view,
        tamarind_version=tamarind_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    search: str | Unset = UNSET,
    modality: str | Unset = UNSET,
    function: str | Unset = UNSET,
    custom: bool | Unset = UNSET,
    finetune: bool | Unset = UNSET,
    pipeline_tools: bool | Unset = False,
    limit: int | Unset = 50,
    cursor: str | Unset = UNSET,
    view: ListToolsView | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Problem | ToolPage | None:
    """Find tools

     The built-in tools your account may run, in the catalog's display order rather than newest
    first. Visibility rules live in this endpoint, not in clients: a tool a flag, a block or
    licensing hides from you isn't listed, and neither is one your submit would be refused (your
    organization's or team's policy, a licence such as Rosetta's, a GPL tool for a pharma
    organization, or a domain restriction). As today's `GET /api/tools` does, the list also leaves
    out a tool with no display name of its own or one hidden from the app's tool pages, though it
    still answers by name on `getTool`, `getToolSchema` and a submit. `view=agent` lists the
    catalog as the Tamarind MCP and agents see it instead (see the parameter).

    `custom=true` lists your organization's custom tools instead, as the MCP lists them: each one
    whose current version is deployed and published, by name, in name order, with the same
    filters; `view` doesn't change it. A tool whose current version is private or a draft isn't
    listed, even when an earlier version was published. With no organization, or only a personal
    one, the list is empty. A custom tool's `finetune` is true only when it trains models and your
    organization has custom finetuning. To manage custom tools, see `listCustomTools`.

    At launch this answers without a key too, like today's public `/tools.json`: without a key you
    get the public catalog, the tools a signed-out reader of the docs may see; with one, the tools
    its owner may run. Requests without a key share one overall rate limit. Until launch it needs a
    key like every v1 operation, because the `api-v1` flag decides by the caller. Without a key,
    `custom` and `view` are 400.

    Args:
        search (str | Unset):
        modality (str | Unset):
        function (str | Unset):
        custom (bool | Unset):
        finetune (bool | Unset):
        pipeline_tools (bool | Unset):  Default: False.
        limit (int | Unset):  Default: 50.
        cursor (str | Unset):
        view (ListToolsView | Unset):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Problem | ToolPage
    """

    return sync_detailed(
        client=client,
        search=search,
        modality=modality,
        function=function,
        custom=custom,
        finetune=finetune,
        pipeline_tools=pipeline_tools,
        limit=limit,
        cursor=cursor,
        view=view,
        tamarind_version=tamarind_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    search: str | Unset = UNSET,
    modality: str | Unset = UNSET,
    function: str | Unset = UNSET,
    custom: bool | Unset = UNSET,
    finetune: bool | Unset = UNSET,
    pipeline_tools: bool | Unset = False,
    limit: int | Unset = 50,
    cursor: str | Unset = UNSET,
    view: ListToolsView | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Response[Problem | ToolPage]:
    """Find tools

     The built-in tools your account may run, in the catalog's display order rather than newest
    first. Visibility rules live in this endpoint, not in clients: a tool a flag, a block or
    licensing hides from you isn't listed, and neither is one your submit would be refused (your
    organization's or team's policy, a licence such as Rosetta's, a GPL tool for a pharma
    organization, or a domain restriction). As today's `GET /api/tools` does, the list also leaves
    out a tool with no display name of its own or one hidden from the app's tool pages, though it
    still answers by name on `getTool`, `getToolSchema` and a submit. `view=agent` lists the
    catalog as the Tamarind MCP and agents see it instead (see the parameter).

    `custom=true` lists your organization's custom tools instead, as the MCP lists them: each one
    whose current version is deployed and published, by name, in name order, with the same
    filters; `view` doesn't change it. A tool whose current version is private or a draft isn't
    listed, even when an earlier version was published. With no organization, or only a personal
    one, the list is empty. A custom tool's `finetune` is true only when it trains models and your
    organization has custom finetuning. To manage custom tools, see `listCustomTools`.

    At launch this answers without a key too, like today's public `/tools.json`: without a key you
    get the public catalog, the tools a signed-out reader of the docs may see; with one, the tools
    its owner may run. Requests without a key share one overall rate limit. Until launch it needs a
    key like every v1 operation, because the `api-v1` flag decides by the caller. Without a key,
    `custom` and `view` are 400.

    Args:
        search (str | Unset):
        modality (str | Unset):
        function (str | Unset):
        custom (bool | Unset):
        finetune (bool | Unset):
        pipeline_tools (bool | Unset):  Default: False.
        limit (int | Unset):  Default: 50.
        cursor (str | Unset):
        view (ListToolsView | Unset):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Problem | ToolPage]
    """

    kwargs = _get_kwargs(
        search=search,
        modality=modality,
        function=function,
        custom=custom,
        finetune=finetune,
        pipeline_tools=pipeline_tools,
        limit=limit,
        cursor=cursor,
        view=view,
        tamarind_version=tamarind_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    search: str | Unset = UNSET,
    modality: str | Unset = UNSET,
    function: str | Unset = UNSET,
    custom: bool | Unset = UNSET,
    finetune: bool | Unset = UNSET,
    pipeline_tools: bool | Unset = False,
    limit: int | Unset = 50,
    cursor: str | Unset = UNSET,
    view: ListToolsView | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Problem | ToolPage | None:
    """Find tools

     The built-in tools your account may run, in the catalog's display order rather than newest
    first. Visibility rules live in this endpoint, not in clients: a tool a flag, a block or
    licensing hides from you isn't listed, and neither is one your submit would be refused (your
    organization's or team's policy, a licence such as Rosetta's, a GPL tool for a pharma
    organization, or a domain restriction). As today's `GET /api/tools` does, the list also leaves
    out a tool with no display name of its own or one hidden from the app's tool pages, though it
    still answers by name on `getTool`, `getToolSchema` and a submit. `view=agent` lists the
    catalog as the Tamarind MCP and agents see it instead (see the parameter).

    `custom=true` lists your organization's custom tools instead, as the MCP lists them: each one
    whose current version is deployed and published, by name, in name order, with the same
    filters; `view` doesn't change it. A tool whose current version is private or a draft isn't
    listed, even when an earlier version was published. With no organization, or only a personal
    one, the list is empty. A custom tool's `finetune` is true only when it trains models and your
    organization has custom finetuning. To manage custom tools, see `listCustomTools`.

    At launch this answers without a key too, like today's public `/tools.json`: without a key you
    get the public catalog, the tools a signed-out reader of the docs may see; with one, the tools
    its owner may run. Requests without a key share one overall rate limit. Until launch it needs a
    key like every v1 operation, because the `api-v1` flag decides by the caller. Without a key,
    `custom` and `view` are 400.

    Args:
        search (str | Unset):
        modality (str | Unset):
        function (str | Unset):
        custom (bool | Unset):
        finetune (bool | Unset):
        pipeline_tools (bool | Unset):  Default: False.
        limit (int | Unset):  Default: 50.
        cursor (str | Unset):
        view (ListToolsView | Unset):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Problem | ToolPage
    """

    return (
        await asyncio_detailed(
            client=client,
            search=search,
            modality=modality,
            function=function,
            custom=custom,
            finetune=finetune,
            pipeline_tools=pipeline_tools,
            limit=limit,
            cursor=cursor,
            view=view,
            tamarind_version=tamarind_version,
        )
    ).parsed
