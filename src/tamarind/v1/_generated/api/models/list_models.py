from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.model_page import ModelPage
from ...models.problem import Problem
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    tool: str | Unset = UNSET,
    limit: int | Unset = 50,
    cursor: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(tamarind_version, Unset):
        headers["Tamarind-Version"] = tamarind_version

    params: dict[str, Any] = {}

    params["tool"] = tool

    params["limit"] = limit

    params["cursor"] = cursor

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/models",
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ModelPage | Problem:
    if response.status_code == 200:
        response_200 = ModelPage.from_dict(response.json())

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
) -> Response[ModelPage | Problem]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    tool: str | Unset = UNSET,
    limit: int | Unset = 50,
    cursor: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Response[ModelPage | Problem]:
    """List finetuned models you can run

     Your models and your teammates', newest first; `owner` says whose it is. Teammates' models are
    included when your organization shares within itself or you are its service account;
    otherwise only yours. A person's key never gets an organization admin's wider view. A model
    id held by several stored rows is listed once, as its newest row. Deleted models and models of
    trainers hidden from you aren't listed.

    When there are more models than one request reads (2,500 rows, or about 4.3 MB), the answer is
    503, not retryable, so a list never quietly leaves models out. A second list from the same
    account while one is still running is 429.

    Args:
        tool (str | Unset):
        limit (int | Unset):  Default: 50.
        cursor (str | Unset):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ModelPage | Problem]
    """

    kwargs = _get_kwargs(
        tool=tool,
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
    tool: str | Unset = UNSET,
    limit: int | Unset = 50,
    cursor: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> ModelPage | Problem | None:
    """List finetuned models you can run

     Your models and your teammates', newest first; `owner` says whose it is. Teammates' models are
    included when your organization shares within itself or you are its service account;
    otherwise only yours. A person's key never gets an organization admin's wider view. A model
    id held by several stored rows is listed once, as its newest row. Deleted models and models of
    trainers hidden from you aren't listed.

    When there are more models than one request reads (2,500 rows, or about 4.3 MB), the answer is
    503, not retryable, so a list never quietly leaves models out. A second list from the same
    account while one is still running is 429.

    Args:
        tool (str | Unset):
        limit (int | Unset):  Default: 50.
        cursor (str | Unset):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ModelPage | Problem
    """

    return sync_detailed(
        client=client,
        tool=tool,
        limit=limit,
        cursor=cursor,
        tamarind_version=tamarind_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    tool: str | Unset = UNSET,
    limit: int | Unset = 50,
    cursor: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Response[ModelPage | Problem]:
    """List finetuned models you can run

     Your models and your teammates', newest first; `owner` says whose it is. Teammates' models are
    included when your organization shares within itself or you are its service account;
    otherwise only yours. A person's key never gets an organization admin's wider view. A model
    id held by several stored rows is listed once, as its newest row. Deleted models and models of
    trainers hidden from you aren't listed.

    When there are more models than one request reads (2,500 rows, or about 4.3 MB), the answer is
    503, not retryable, so a list never quietly leaves models out. A second list from the same
    account while one is still running is 429.

    Args:
        tool (str | Unset):
        limit (int | Unset):  Default: 50.
        cursor (str | Unset):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ModelPage | Problem]
    """

    kwargs = _get_kwargs(
        tool=tool,
        limit=limit,
        cursor=cursor,
        tamarind_version=tamarind_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    tool: str | Unset = UNSET,
    limit: int | Unset = 50,
    cursor: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> ModelPage | Problem | None:
    """List finetuned models you can run

     Your models and your teammates', newest first; `owner` says whose it is. Teammates' models are
    included when your organization shares within itself or you are its service account;
    otherwise only yours. A person's key never gets an organization admin's wider view. A model
    id held by several stored rows is listed once, as its newest row. Deleted models and models of
    trainers hidden from you aren't listed.

    When there are more models than one request reads (2,500 rows, or about 4.3 MB), the answer is
    503, not retryable, so a list never quietly leaves models out. A second list from the same
    account while one is still running is 429.

    Args:
        tool (str | Unset):
        limit (int | Unset):  Default: 50.
        cursor (str | Unset):
        tamarind_version (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ModelPage | Problem
    """

    return (
        await asyncio_detailed(
            client=client,
            tool=tool,
            limit=limit,
            cursor=cursor,
            tamarind_version=tamarind_version,
        )
    ).parsed
