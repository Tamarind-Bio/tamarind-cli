from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.problem import Problem
from ...models.recommend_tools_view import RecommendToolsView
from ...models.tool_recommendation import ToolRecommendation
from ...models.tool_recommendation_request import ToolRecommendationRequest
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    body: ToolRecommendationRequest,
    view: RecommendToolsView | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(tamarind_version, Unset):
        headers["Tamarind-Version"] = tamarind_version

    params: dict[str, Any] = {}

    json_view: str | Unset = UNSET
    if not isinstance(view, Unset):
        json_view = view.value

    params["view"] = json_view

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/tools/recommend",
        "params": params,
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Problem | ToolRecommendation:
    if response.status_code == 200:
        response_200 = ToolRecommendation.from_dict(response.json())

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
) -> Response[Problem | ToolRecommendation]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: ToolRecommendationRequest,
    view: RecommendToolsView | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Response[Problem | ToolRecommendation]:
    """Recommend tools for a task described in words

     Ranks tools for a structure-prediction or co-folding task from benchmark evidence, narrowed to
    the tools `listTools` shows you in the same `view`: others are left out and never named, and when
    that leaves
    none the answer abstains with `abstainReason` `not_available_to_your_account`. An abstention
    says why in `abstainReason`, and `retryable` says whether asking again may help. A synchronous call,
    bounded to finish inside the gateway's 30
    seconds: a request that takes more than 25 seconds is 503 and retryable (most take 12 to 18
    seconds). Behind the `model-router` flag, and refused for an unclaimed agent account: both are
    403 `forbidden`. At most two requests per account run at once on each server; more is 429. A
    deployment without the recommendation service answers 503, not retryable.

    Args:
        view (RecommendToolsView | Unset):
        tamarind_version (str | Unset):
        body (ToolRecommendationRequest): Ask which tool to run for a stated task.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Problem | ToolRecommendation]
    """

    kwargs = _get_kwargs(
        body=body,
        view=view,
        tamarind_version=tamarind_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    body: ToolRecommendationRequest,
    view: RecommendToolsView | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Problem | ToolRecommendation | None:
    """Recommend tools for a task described in words

     Ranks tools for a structure-prediction or co-folding task from benchmark evidence, narrowed to
    the tools `listTools` shows you in the same `view`: others are left out and never named, and when
    that leaves
    none the answer abstains with `abstainReason` `not_available_to_your_account`. An abstention
    says why in `abstainReason`, and `retryable` says whether asking again may help. A synchronous call,
    bounded to finish inside the gateway's 30
    seconds: a request that takes more than 25 seconds is 503 and retryable (most take 12 to 18
    seconds). Behind the `model-router` flag, and refused for an unclaimed agent account: both are
    403 `forbidden`. At most two requests per account run at once on each server; more is 429. A
    deployment without the recommendation service answers 503, not retryable.

    Args:
        view (RecommendToolsView | Unset):
        tamarind_version (str | Unset):
        body (ToolRecommendationRequest): Ask which tool to run for a stated task.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Problem | ToolRecommendation
    """

    return sync_detailed(
        client=client,
        body=body,
        view=view,
        tamarind_version=tamarind_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: ToolRecommendationRequest,
    view: RecommendToolsView | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Response[Problem | ToolRecommendation]:
    """Recommend tools for a task described in words

     Ranks tools for a structure-prediction or co-folding task from benchmark evidence, narrowed to
    the tools `listTools` shows you in the same `view`: others are left out and never named, and when
    that leaves
    none the answer abstains with `abstainReason` `not_available_to_your_account`. An abstention
    says why in `abstainReason`, and `retryable` says whether asking again may help. A synchronous call,
    bounded to finish inside the gateway's 30
    seconds: a request that takes more than 25 seconds is 503 and retryable (most take 12 to 18
    seconds). Behind the `model-router` flag, and refused for an unclaimed agent account: both are
    403 `forbidden`. At most two requests per account run at once on each server; more is 429. A
    deployment without the recommendation service answers 503, not retryable.

    Args:
        view (RecommendToolsView | Unset):
        tamarind_version (str | Unset):
        body (ToolRecommendationRequest): Ask which tool to run for a stated task.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Problem | ToolRecommendation]
    """

    kwargs = _get_kwargs(
        body=body,
        view=view,
        tamarind_version=tamarind_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: ToolRecommendationRequest,
    view: RecommendToolsView | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Problem | ToolRecommendation | None:
    """Recommend tools for a task described in words

     Ranks tools for a structure-prediction or co-folding task from benchmark evidence, narrowed to
    the tools `listTools` shows you in the same `view`: others are left out and never named, and when
    that leaves
    none the answer abstains with `abstainReason` `not_available_to_your_account`. An abstention
    says why in `abstainReason`, and `retryable` says whether asking again may help. A synchronous call,
    bounded to finish inside the gateway's 30
    seconds: a request that takes more than 25 seconds is 503 and retryable (most take 12 to 18
    seconds). Behind the `model-router` flag, and refused for an unclaimed agent account: both are
    403 `forbidden`. At most two requests per account run at once on each server; more is 429. A
    deployment without the recommendation service answers 503, not retryable.

    Args:
        view (RecommendToolsView | Unset):
        tamarind_version (str | Unset):
        body (ToolRecommendationRequest): Ask which tool to run for a stated task.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Problem | ToolRecommendation
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            view=view,
            tamarind_version=tamarind_version,
        )
    ).parsed
