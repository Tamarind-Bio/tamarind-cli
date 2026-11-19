import datetime
from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.get_usage_group_by_item import GetUsageGroupByItem
from ...models.get_usage_metric import GetUsageMetric
from ...models.get_usage_scope import GetUsageScope
from ...models.problem import Problem
from ...models.usage_page import UsagePage
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    metric: GetUsageMetric | Unset = GetUsageMetric.WEIGHTEDHOURS,
    group_by: list[GetUsageGroupByItem] | Unset = UNSET,
    from_: datetime.datetime | Unset = UNSET,
    to: datetime.datetime | Unset = UNSET,
    scope: GetUsageScope | Unset = GetUsageScope.MINE,
    organization_slug: str | Unset = UNSET,
    api_key_id: str | Unset = UNSET,
    limit: int | Unset = 50,
    cursor: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(tamarind_version, Unset):
        headers["Tamarind-Version"] = tamarind_version

    params: dict[str, Any] = {}

    json_metric: str | Unset = UNSET
    if not isinstance(metric, Unset):
        json_metric = metric.value

    params["metric"] = json_metric

    json_group_by: list[str] | Unset = UNSET
    if not isinstance(group_by, Unset):
        json_group_by = []
        for group_by_item_data in group_by:
            group_by_item = group_by_item_data.value
            json_group_by.append(group_by_item)

    params["groupBy"] = json_group_by

    json_from_: str | Unset = UNSET
    if not isinstance(from_, Unset):
        json_from_ = from_.isoformat()
    params["from"] = json_from_

    json_to: str | Unset = UNSET
    if not isinstance(to, Unset):
        json_to = to.isoformat()
    params["to"] = json_to

    json_scope: str | Unset = UNSET
    if not isinstance(scope, Unset):
        json_scope = scope.value

    params["scope"] = json_scope

    params["organizationSlug"] = organization_slug

    params["apiKeyId"] = api_key_id

    params["limit"] = limit

    params["cursor"] = cursor

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/usage",
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Problem | UsagePage:
    if response.status_code == 200:
        response_200 = UsagePage.from_dict(response.json())

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
) -> Response[Problem | UsagePage]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    metric: GetUsageMetric | Unset = GetUsageMetric.WEIGHTEDHOURS,
    group_by: list[GetUsageGroupByItem] | Unset = UNSET,
    from_: datetime.datetime | Unset = UNSET,
    to: datetime.datetime | Unset = UNSET,
    scope: GetUsageScope | Unset = GetUsageScope.MINE,
    organization_slug: str | Unset = UNSET,
    api_key_id: str | Unset = UNSET,
    limit: int | Unset = 50,
    cursor: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Response[Problem | UsagePage]:
    """Query compute and agent usage

     One query over the stored monthly usage the web usage portal reads. Choose a `metric`, a range
    of Pacific months and up to three `groupBy` dimensions. Send `Accept: text/csv` for CSV. A CSV
    is one page, like the JSON form, and its next cursor is in the `X-Next-Cursor` header (also set
    on JSON pages). Items are in the order of their dimension values, months oldest first.

    Nothing is recomputed: a figure the stored rows don't hold exactly is refused, not estimated.
    Rows from before a breakdown was stored (every row before 2026 has no weighted hours, and the
    source, custom-tool and pipeline breakdowns came later) make a query that needs that breakdown
    422 `not_supported`, naming the months.

    `total` counts each job once. With `team`, a member in several teams appears under each and one
    in none under none. `project` groups cover tagged usage only. Groups whose value is zero are
    left out. `asOf` is the OLDEST refresh time of the rows read, so it never claims fresher
    figures than the stalest row holds; with no rows, it's the time of the request. Use
    `refreshUsage` to request newer figures. A failed read is 503, never a quietly smaller total.

    `scope=org` is every current member's usage, including months from before they joined, as the
    portal shows it. Only a caller who sees shared budgets on `GET /me` may ask for it (the
    organization's service account, or any member when the organization shares its budget with
    members); anyone else, a personal account included, is 403 `forbidden`, not their own usage
    instead. While your membership of the organization isn't confirmed yet, it's 503
    `service_unavailable` with `Retry-After`, as on `/organization`. A second `scope=org` query from the
    same account while one is still running is 429.

    Args:
        metric (GetUsageMetric | Unset):  Default: GetUsageMetric.WEIGHTEDHOURS.
        group_by (list[GetUsageGroupByItem] | Unset):
        from_ (datetime.datetime | Unset):
        to (datetime.datetime | Unset):
        scope (GetUsageScope | Unset):  Default: GetUsageScope.MINE.
        organization_slug (str | Unset):
        api_key_id (str | Unset):
        limit (int | Unset):  Default: 50.
        cursor (str | Unset):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Problem | UsagePage]
    """

    kwargs = _get_kwargs(
        metric=metric,
        group_by=group_by,
        from_=from_,
        to=to,
        scope=scope,
        organization_slug=organization_slug,
        api_key_id=api_key_id,
        limit=limit,
        cursor=cursor,
        tamarind_version=tamarind_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    metric: GetUsageMetric | Unset = GetUsageMetric.WEIGHTEDHOURS,
    group_by: list[GetUsageGroupByItem] | Unset = UNSET,
    from_: datetime.datetime | Unset = UNSET,
    to: datetime.datetime | Unset = UNSET,
    scope: GetUsageScope | Unset = GetUsageScope.MINE,
    organization_slug: str | Unset = UNSET,
    api_key_id: str | Unset = UNSET,
    limit: int | Unset = 50,
    cursor: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Problem | UsagePage | None:
    """Query compute and agent usage

     One query over the stored monthly usage the web usage portal reads. Choose a `metric`, a range
    of Pacific months and up to three `groupBy` dimensions. Send `Accept: text/csv` for CSV. A CSV
    is one page, like the JSON form, and its next cursor is in the `X-Next-Cursor` header (also set
    on JSON pages). Items are in the order of their dimension values, months oldest first.

    Nothing is recomputed: a figure the stored rows don't hold exactly is refused, not estimated.
    Rows from before a breakdown was stored (every row before 2026 has no weighted hours, and the
    source, custom-tool and pipeline breakdowns came later) make a query that needs that breakdown
    422 `not_supported`, naming the months.

    `total` counts each job once. With `team`, a member in several teams appears under each and one
    in none under none. `project` groups cover tagged usage only. Groups whose value is zero are
    left out. `asOf` is the OLDEST refresh time of the rows read, so it never claims fresher
    figures than the stalest row holds; with no rows, it's the time of the request. Use
    `refreshUsage` to request newer figures. A failed read is 503, never a quietly smaller total.

    `scope=org` is every current member's usage, including months from before they joined, as the
    portal shows it. Only a caller who sees shared budgets on `GET /me` may ask for it (the
    organization's service account, or any member when the organization shares its budget with
    members); anyone else, a personal account included, is 403 `forbidden`, not their own usage
    instead. While your membership of the organization isn't confirmed yet, it's 503
    `service_unavailable` with `Retry-After`, as on `/organization`. A second `scope=org` query from the
    same account while one is still running is 429.

    Args:
        metric (GetUsageMetric | Unset):  Default: GetUsageMetric.WEIGHTEDHOURS.
        group_by (list[GetUsageGroupByItem] | Unset):
        from_ (datetime.datetime | Unset):
        to (datetime.datetime | Unset):
        scope (GetUsageScope | Unset):  Default: GetUsageScope.MINE.
        organization_slug (str | Unset):
        api_key_id (str | Unset):
        limit (int | Unset):  Default: 50.
        cursor (str | Unset):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Problem | UsagePage
    """

    return sync_detailed(
        client=client,
        metric=metric,
        group_by=group_by,
        from_=from_,
        to=to,
        scope=scope,
        organization_slug=organization_slug,
        api_key_id=api_key_id,
        limit=limit,
        cursor=cursor,
        tamarind_version=tamarind_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    metric: GetUsageMetric | Unset = GetUsageMetric.WEIGHTEDHOURS,
    group_by: list[GetUsageGroupByItem] | Unset = UNSET,
    from_: datetime.datetime | Unset = UNSET,
    to: datetime.datetime | Unset = UNSET,
    scope: GetUsageScope | Unset = GetUsageScope.MINE,
    organization_slug: str | Unset = UNSET,
    api_key_id: str | Unset = UNSET,
    limit: int | Unset = 50,
    cursor: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Response[Problem | UsagePage]:
    """Query compute and agent usage

     One query over the stored monthly usage the web usage portal reads. Choose a `metric`, a range
    of Pacific months and up to three `groupBy` dimensions. Send `Accept: text/csv` for CSV. A CSV
    is one page, like the JSON form, and its next cursor is in the `X-Next-Cursor` header (also set
    on JSON pages). Items are in the order of their dimension values, months oldest first.

    Nothing is recomputed: a figure the stored rows don't hold exactly is refused, not estimated.
    Rows from before a breakdown was stored (every row before 2026 has no weighted hours, and the
    source, custom-tool and pipeline breakdowns came later) make a query that needs that breakdown
    422 `not_supported`, naming the months.

    `total` counts each job once. With `team`, a member in several teams appears under each and one
    in none under none. `project` groups cover tagged usage only. Groups whose value is zero are
    left out. `asOf` is the OLDEST refresh time of the rows read, so it never claims fresher
    figures than the stalest row holds; with no rows, it's the time of the request. Use
    `refreshUsage` to request newer figures. A failed read is 503, never a quietly smaller total.

    `scope=org` is every current member's usage, including months from before they joined, as the
    portal shows it. Only a caller who sees shared budgets on `GET /me` may ask for it (the
    organization's service account, or any member when the organization shares its budget with
    members); anyone else, a personal account included, is 403 `forbidden`, not their own usage
    instead. While your membership of the organization isn't confirmed yet, it's 503
    `service_unavailable` with `Retry-After`, as on `/organization`. A second `scope=org` query from the
    same account while one is still running is 429.

    Args:
        metric (GetUsageMetric | Unset):  Default: GetUsageMetric.WEIGHTEDHOURS.
        group_by (list[GetUsageGroupByItem] | Unset):
        from_ (datetime.datetime | Unset):
        to (datetime.datetime | Unset):
        scope (GetUsageScope | Unset):  Default: GetUsageScope.MINE.
        organization_slug (str | Unset):
        api_key_id (str | Unset):
        limit (int | Unset):  Default: 50.
        cursor (str | Unset):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Problem | UsagePage]
    """

    kwargs = _get_kwargs(
        metric=metric,
        group_by=group_by,
        from_=from_,
        to=to,
        scope=scope,
        organization_slug=organization_slug,
        api_key_id=api_key_id,
        limit=limit,
        cursor=cursor,
        tamarind_version=tamarind_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    metric: GetUsageMetric | Unset = GetUsageMetric.WEIGHTEDHOURS,
    group_by: list[GetUsageGroupByItem] | Unset = UNSET,
    from_: datetime.datetime | Unset = UNSET,
    to: datetime.datetime | Unset = UNSET,
    scope: GetUsageScope | Unset = GetUsageScope.MINE,
    organization_slug: str | Unset = UNSET,
    api_key_id: str | Unset = UNSET,
    limit: int | Unset = 50,
    cursor: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Problem | UsagePage | None:
    """Query compute and agent usage

     One query over the stored monthly usage the web usage portal reads. Choose a `metric`, a range
    of Pacific months and up to three `groupBy` dimensions. Send `Accept: text/csv` for CSV. A CSV
    is one page, like the JSON form, and its next cursor is in the `X-Next-Cursor` header (also set
    on JSON pages). Items are in the order of their dimension values, months oldest first.

    Nothing is recomputed: a figure the stored rows don't hold exactly is refused, not estimated.
    Rows from before a breakdown was stored (every row before 2026 has no weighted hours, and the
    source, custom-tool and pipeline breakdowns came later) make a query that needs that breakdown
    422 `not_supported`, naming the months.

    `total` counts each job once. With `team`, a member in several teams appears under each and one
    in none under none. `project` groups cover tagged usage only. Groups whose value is zero are
    left out. `asOf` is the OLDEST refresh time of the rows read, so it never claims fresher
    figures than the stalest row holds; with no rows, it's the time of the request. Use
    `refreshUsage` to request newer figures. A failed read is 503, never a quietly smaller total.

    `scope=org` is every current member's usage, including months from before they joined, as the
    portal shows it. Only a caller who sees shared budgets on `GET /me` may ask for it (the
    organization's service account, or any member when the organization shares its budget with
    members); anyone else, a personal account included, is 403 `forbidden`, not their own usage
    instead. While your membership of the organization isn't confirmed yet, it's 503
    `service_unavailable` with `Retry-After`, as on `/organization`. A second `scope=org` query from the
    same account while one is still running is 429.

    Args:
        metric (GetUsageMetric | Unset):  Default: GetUsageMetric.WEIGHTEDHOURS.
        group_by (list[GetUsageGroupByItem] | Unset):
        from_ (datetime.datetime | Unset):
        to (datetime.datetime | Unset):
        scope (GetUsageScope | Unset):  Default: GetUsageScope.MINE.
        organization_slug (str | Unset):
        api_key_id (str | Unset):
        limit (int | Unset):  Default: 50.
        cursor (str | Unset):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Problem | UsagePage
    """

    return (
        await asyncio_detailed(
            client=client,
            metric=metric,
            group_by=group_by,
            from_=from_,
            to=to,
            scope=scope,
            organization_slug=organization_slug,
            api_key_id=api_key_id,
            limit=limit,
            cursor=cursor,
            tamarind_version=tamarind_version,
        )
    ).parsed
