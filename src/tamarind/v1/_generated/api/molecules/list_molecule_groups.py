from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.molecule_group_page import MoleculeGroupPage
from ...models.problem import Problem
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    search: None | str | Unset = UNSET,
    filter_: list[str] | None | Unset = UNSET,
    scope: str | Unset = "mine",
    sort_by: str | Unset = "recent",
    dir_: str | Unset = "desc",
    limit: int | Unset = 50,
    cursor: None | str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(tamarind_version, Unset):
        headers["Tamarind-Version"] = tamarind_version

    params: dict[str, Any] = {}

    json_search: None | str | Unset
    if isinstance(search, Unset):
        json_search = UNSET
    else:
        json_search = search
    params["search"] = json_search

    json_filter_: list[str] | None | Unset
    if isinstance(filter_, Unset):
        json_filter_ = UNSET
    elif isinstance(filter_, list):
        json_filter_ = filter_

    else:
        json_filter_ = filter_
    params["filter"] = json_filter_

    params["scope"] = scope

    params["sortBy"] = sort_by

    params["dir"] = dir_

    params["limit"] = limit

    json_cursor: None | str | Unset
    if isinstance(cursor, Unset):
        json_cursor = UNSET
    else:
        json_cursor = cursor
    params["cursor"] = json_cursor

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/molecules/groups",
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> MoleculeGroupPage | Problem:
    if response.status_code == 200:
        response_200 = MoleculeGroupPage.from_dict(response.json())

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
) -> Response[MoleculeGroupPage | Problem]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    search: None | str | Unset = UNSET,
    filter_: list[str] | None | Unset = UNSET,
    scope: str | Unset = "mine",
    sort_by: str | Unset = "recent",
    dir_: str | Unset = "desc",
    limit: int | Unset = 50,
    cursor: None | str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Response[MoleculeGroupPage | Problem]:
    """List Groups

     List your molecule groups.

    A group is a named collection of molecules. Pass `scope=org` to include your whole organization.

    Today's spelling `sort` is 400 `validation_failed` naming `sortBy`, rather than being ignored.

    Paginated — follow `nextCursor` until it is null.

    Args:
        search (None | str | Unset): Case-insensitive substring match on the group's name.
        filter_ (list[str] | None | Unset): One condition on the group's own metadata, written
            `field:operator:value`. Repeat it and a group must pass every condition. Operators: `gt`,
            `gte`, `lt`, `lte`, `eq`, `neq`, `iequals`, `includes`, `in`, and `exists`, written
            `field:exists` with no value. `in` takes a set of values separated by `|` and matches a
            value equal to any of them (`stage:in:lead|backup`): each member matches the stored text
            ignoring case, and a member that is a number also matches that number stored as a number
            or as text (`2` finds a stored `2.0`). A member's text is compared as written, spaces
            included. Blank members are dropped, a set with no member left is refused, and a set holds
            at most 64 members. A dotted field names a metadata key here, never a tool score, for
            every operator (`stage.phase` reads the key `stage.phase`, so `stage.phase:in:1|2` does
            too): groups carry no scores, so nothing on this endpoint reads one. At most 32
            conditions.
        scope (str | Unset): `mine` (the default) shows groups you created; `org` shows every
            group in your organization. Default: 'mine'.
        sort_by (str | Unset): Sort by `recent` (the default, by creation date), `name`, or `size`
            (how many molecules the group holds). Pair with `dir`. Default: 'recent'.
        dir_ (str | Unset): Sort direction, `asc` or `desc`. Default: 'desc'.
        limit (int | Unset): Maximum number of items to return in one page. Default: 50.
        cursor (None | str | Unset): Pagination token from the previous response's `nextCursor`.
            Omit for the first page; follow `nextCursor` until null (an empty `items` page while
            `nextCursor` is set is normal).
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[MoleculeGroupPage | Problem]
    """

    kwargs = _get_kwargs(
        search=search,
        filter_=filter_,
        scope=scope,
        sort_by=sort_by,
        dir_=dir_,
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
    search: None | str | Unset = UNSET,
    filter_: list[str] | None | Unset = UNSET,
    scope: str | Unset = "mine",
    sort_by: str | Unset = "recent",
    dir_: str | Unset = "desc",
    limit: int | Unset = 50,
    cursor: None | str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> MoleculeGroupPage | Problem | None:
    """List Groups

     List your molecule groups.

    A group is a named collection of molecules. Pass `scope=org` to include your whole organization.

    Today's spelling `sort` is 400 `validation_failed` naming `sortBy`, rather than being ignored.

    Paginated — follow `nextCursor` until it is null.

    Args:
        search (None | str | Unset): Case-insensitive substring match on the group's name.
        filter_ (list[str] | None | Unset): One condition on the group's own metadata, written
            `field:operator:value`. Repeat it and a group must pass every condition. Operators: `gt`,
            `gte`, `lt`, `lte`, `eq`, `neq`, `iequals`, `includes`, `in`, and `exists`, written
            `field:exists` with no value. `in` takes a set of values separated by `|` and matches a
            value equal to any of them (`stage:in:lead|backup`): each member matches the stored text
            ignoring case, and a member that is a number also matches that number stored as a number
            or as text (`2` finds a stored `2.0`). A member's text is compared as written, spaces
            included. Blank members are dropped, a set with no member left is refused, and a set holds
            at most 64 members. A dotted field names a metadata key here, never a tool score, for
            every operator (`stage.phase` reads the key `stage.phase`, so `stage.phase:in:1|2` does
            too): groups carry no scores, so nothing on this endpoint reads one. At most 32
            conditions.
        scope (str | Unset): `mine` (the default) shows groups you created; `org` shows every
            group in your organization. Default: 'mine'.
        sort_by (str | Unset): Sort by `recent` (the default, by creation date), `name`, or `size`
            (how many molecules the group holds). Pair with `dir`. Default: 'recent'.
        dir_ (str | Unset): Sort direction, `asc` or `desc`. Default: 'desc'.
        limit (int | Unset): Maximum number of items to return in one page. Default: 50.
        cursor (None | str | Unset): Pagination token from the previous response's `nextCursor`.
            Omit for the first page; follow `nextCursor` until null (an empty `items` page while
            `nextCursor` is set is normal).
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        MoleculeGroupPage | Problem
    """

    return sync_detailed(
        client=client,
        search=search,
        filter_=filter_,
        scope=scope,
        sort_by=sort_by,
        dir_=dir_,
        limit=limit,
        cursor=cursor,
        tamarind_version=tamarind_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    search: None | str | Unset = UNSET,
    filter_: list[str] | None | Unset = UNSET,
    scope: str | Unset = "mine",
    sort_by: str | Unset = "recent",
    dir_: str | Unset = "desc",
    limit: int | Unset = 50,
    cursor: None | str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Response[MoleculeGroupPage | Problem]:
    """List Groups

     List your molecule groups.

    A group is a named collection of molecules. Pass `scope=org` to include your whole organization.

    Today's spelling `sort` is 400 `validation_failed` naming `sortBy`, rather than being ignored.

    Paginated — follow `nextCursor` until it is null.

    Args:
        search (None | str | Unset): Case-insensitive substring match on the group's name.
        filter_ (list[str] | None | Unset): One condition on the group's own metadata, written
            `field:operator:value`. Repeat it and a group must pass every condition. Operators: `gt`,
            `gte`, `lt`, `lte`, `eq`, `neq`, `iequals`, `includes`, `in`, and `exists`, written
            `field:exists` with no value. `in` takes a set of values separated by `|` and matches a
            value equal to any of them (`stage:in:lead|backup`): each member matches the stored text
            ignoring case, and a member that is a number also matches that number stored as a number
            or as text (`2` finds a stored `2.0`). A member's text is compared as written, spaces
            included. Blank members are dropped, a set with no member left is refused, and a set holds
            at most 64 members. A dotted field names a metadata key here, never a tool score, for
            every operator (`stage.phase` reads the key `stage.phase`, so `stage.phase:in:1|2` does
            too): groups carry no scores, so nothing on this endpoint reads one. At most 32
            conditions.
        scope (str | Unset): `mine` (the default) shows groups you created; `org` shows every
            group in your organization. Default: 'mine'.
        sort_by (str | Unset): Sort by `recent` (the default, by creation date), `name`, or `size`
            (how many molecules the group holds). Pair with `dir`. Default: 'recent'.
        dir_ (str | Unset): Sort direction, `asc` or `desc`. Default: 'desc'.
        limit (int | Unset): Maximum number of items to return in one page. Default: 50.
        cursor (None | str | Unset): Pagination token from the previous response's `nextCursor`.
            Omit for the first page; follow `nextCursor` until null (an empty `items` page while
            `nextCursor` is set is normal).
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[MoleculeGroupPage | Problem]
    """

    kwargs = _get_kwargs(
        search=search,
        filter_=filter_,
        scope=scope,
        sort_by=sort_by,
        dir_=dir_,
        limit=limit,
        cursor=cursor,
        tamarind_version=tamarind_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    search: None | str | Unset = UNSET,
    filter_: list[str] | None | Unset = UNSET,
    scope: str | Unset = "mine",
    sort_by: str | Unset = "recent",
    dir_: str | Unset = "desc",
    limit: int | Unset = 50,
    cursor: None | str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> MoleculeGroupPage | Problem | None:
    """List Groups

     List your molecule groups.

    A group is a named collection of molecules. Pass `scope=org` to include your whole organization.

    Today's spelling `sort` is 400 `validation_failed` naming `sortBy`, rather than being ignored.

    Paginated — follow `nextCursor` until it is null.

    Args:
        search (None | str | Unset): Case-insensitive substring match on the group's name.
        filter_ (list[str] | None | Unset): One condition on the group's own metadata, written
            `field:operator:value`. Repeat it and a group must pass every condition. Operators: `gt`,
            `gte`, `lt`, `lte`, `eq`, `neq`, `iequals`, `includes`, `in`, and `exists`, written
            `field:exists` with no value. `in` takes a set of values separated by `|` and matches a
            value equal to any of them (`stage:in:lead|backup`): each member matches the stored text
            ignoring case, and a member that is a number also matches that number stored as a number
            or as text (`2` finds a stored `2.0`). A member's text is compared as written, spaces
            included. Blank members are dropped, a set with no member left is refused, and a set holds
            at most 64 members. A dotted field names a metadata key here, never a tool score, for
            every operator (`stage.phase` reads the key `stage.phase`, so `stage.phase:in:1|2` does
            too): groups carry no scores, so nothing on this endpoint reads one. At most 32
            conditions.
        scope (str | Unset): `mine` (the default) shows groups you created; `org` shows every
            group in your organization. Default: 'mine'.
        sort_by (str | Unset): Sort by `recent` (the default, by creation date), `name`, or `size`
            (how many molecules the group holds). Pair with `dir`. Default: 'recent'.
        dir_ (str | Unset): Sort direction, `asc` or `desc`. Default: 'desc'.
        limit (int | Unset): Maximum number of items to return in one page. Default: 50.
        cursor (None | str | Unset): Pagination token from the previous response's `nextCursor`.
            Omit for the first page; follow `nextCursor` until null (an empty `items` page while
            `nextCursor` is set is normal).
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        MoleculeGroupPage | Problem
    """

    return (
        await asyncio_detailed(
            client=client,
            search=search,
            filter_=filter_,
            scope=scope,
            sort_by=sort_by,
            dir_=dir_,
            limit=limit,
            cursor=cursor,
            tamarind_version=tamarind_version,
        )
    ).parsed
