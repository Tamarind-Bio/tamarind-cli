from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.api_key import ApiKey
from ...models.api_key_with_secret import ApiKeyWithSecret
from ...models.create_api_key_request import CreateApiKeyRequest
from ...models.problem import Problem
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    body: CreateApiKeyRequest,
    idempotency_key: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(idempotency_key, Unset):
        headers["Idempotency-Key"] = idempotency_key

    if not isinstance(tamarind_version, Unset):
        headers["Tamarind-Version"] = tamarind_version

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api-keys",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ApiKey | ApiKeyWithSecret | Problem:
    if response.status_code == 200:
        response_200 = ApiKey.from_dict(response.json())

        return response_200

    if response.status_code == 201:
        response_201 = ApiKeyWithSecret.from_dict(response.json())

        return response_201

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

    if response.status_code == 500:
        response_500 = Problem.from_dict(response.json())

        return response_500

    if response.status_code == 503:
        response_503 = Problem.from_dict(response.json())

        return response_503

    response_default = Problem.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ApiKey | ApiKeyWithSecret | Problem]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateApiKeyRequest,
    idempotency_key: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Response[ApiKey | ApiKeyWithSecret | Problem]:
    """Create a service account's API key

     Makes a key for one of your organization's service accounts, named by `serviceAccountId`.
    Only an organization admin's own key can (the rule `listApiKeys` describes). An id that isn't
    one of your organization's service accounts is 404.

    A key never makes a key for its own owner. Without `serviceAccountId` (absent or null), or
    with a body that isn't a JSON object, this is 403 `session_required` before anything else in
    the body is checked: create your own keys on the website's keys page, which only a signed-in
    session can use, so a leaked key can't make a backup that outlives revoking it. A body that
    isn't valid JSON is 422.

    The response is the ONLY time the secret is returned. The secret is a UUID, as the keys page
    makes them, and only its SHA-256 hash is stored. Keys have no budget or expiry yet: a
    non-null `budget` or `expiresAt` is 422 `not_supported` at that field. An account holds at
    most 20 live created keys; past that it's 409 `api_key_limit`.

    Args:
        idempotency_key (str | Unset):
        tamarind_version (str | Unset):
        body (CreateApiKeyRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiKey | ApiKeyWithSecret | Problem]
    """

    kwargs = _get_kwargs(
        body=body,
        idempotency_key=idempotency_key,
        tamarind_version=tamarind_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    body: CreateApiKeyRequest,
    idempotency_key: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> ApiKey | ApiKeyWithSecret | Problem | None:
    """Create a service account's API key

     Makes a key for one of your organization's service accounts, named by `serviceAccountId`.
    Only an organization admin's own key can (the rule `listApiKeys` describes). An id that isn't
    one of your organization's service accounts is 404.

    A key never makes a key for its own owner. Without `serviceAccountId` (absent or null), or
    with a body that isn't a JSON object, this is 403 `session_required` before anything else in
    the body is checked: create your own keys on the website's keys page, which only a signed-in
    session can use, so a leaked key can't make a backup that outlives revoking it. A body that
    isn't valid JSON is 422.

    The response is the ONLY time the secret is returned. The secret is a UUID, as the keys page
    makes them, and only its SHA-256 hash is stored. Keys have no budget or expiry yet: a
    non-null `budget` or `expiresAt` is 422 `not_supported` at that field. An account holds at
    most 20 live created keys; past that it's 409 `api_key_limit`.

    Args:
        idempotency_key (str | Unset):
        tamarind_version (str | Unset):
        body (CreateApiKeyRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiKey | ApiKeyWithSecret | Problem
    """

    return sync_detailed(
        client=client,
        body=body,
        idempotency_key=idempotency_key,
        tamarind_version=tamarind_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateApiKeyRequest,
    idempotency_key: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Response[ApiKey | ApiKeyWithSecret | Problem]:
    """Create a service account's API key

     Makes a key for one of your organization's service accounts, named by `serviceAccountId`.
    Only an organization admin's own key can (the rule `listApiKeys` describes). An id that isn't
    one of your organization's service accounts is 404.

    A key never makes a key for its own owner. Without `serviceAccountId` (absent or null), or
    with a body that isn't a JSON object, this is 403 `session_required` before anything else in
    the body is checked: create your own keys on the website's keys page, which only a signed-in
    session can use, so a leaked key can't make a backup that outlives revoking it. A body that
    isn't valid JSON is 422.

    The response is the ONLY time the secret is returned. The secret is a UUID, as the keys page
    makes them, and only its SHA-256 hash is stored. Keys have no budget or expiry yet: a
    non-null `budget` or `expiresAt` is 422 `not_supported` at that field. An account holds at
    most 20 live created keys; past that it's 409 `api_key_limit`.

    Args:
        idempotency_key (str | Unset):
        tamarind_version (str | Unset):
        body (CreateApiKeyRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiKey | ApiKeyWithSecret | Problem]
    """

    kwargs = _get_kwargs(
        body=body,
        idempotency_key=idempotency_key,
        tamarind_version=tamarind_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: CreateApiKeyRequest,
    idempotency_key: str | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> ApiKey | ApiKeyWithSecret | Problem | None:
    """Create a service account's API key

     Makes a key for one of your organization's service accounts, named by `serviceAccountId`.
    Only an organization admin's own key can (the rule `listApiKeys` describes). An id that isn't
    one of your organization's service accounts is 404.

    A key never makes a key for its own owner. Without `serviceAccountId` (absent or null), or
    with a body that isn't a JSON object, this is 403 `session_required` before anything else in
    the body is checked: create your own keys on the website's keys page, which only a signed-in
    session can use, so a leaked key can't make a backup that outlives revoking it. A body that
    isn't valid JSON is 422.

    The response is the ONLY time the secret is returned. The secret is a UUID, as the keys page
    makes them, and only its SHA-256 hash is stored. Keys have no budget or expiry yet: a
    non-null `budget` or `expiresAt` is 422 `not_supported` at that field. An account holds at
    most 20 live created keys; past that it's 409 `api_key_limit`.

    Args:
        idempotency_key (str | Unset):
        tamarind_version (str | Unset):
        body (CreateApiKeyRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiKey | ApiKeyWithSecret | Problem
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            idempotency_key=idempotency_key,
            tamarind_version=tamarind_version,
        )
    ).parsed
