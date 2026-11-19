from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.custom_tool_config_validation import CustomToolConfigValidation
from ...models.problem import Problem
from ...models.validate_custom_tool_config_request import ValidateCustomToolConfigRequest
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    body: ValidateCustomToolConfigRequest,
    tamarind_version: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(tamarind_version, Unset):
        headers["Tamarind-Version"] = tamarind_version

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/custom-tools/validate-config",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> CustomToolConfigValidation | Problem:
    if response.status_code == 200:
        response_200 = CustomToolConfigValidation.from_dict(response.json())

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
) -> Response[CustomToolConfigValidation | Problem]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: ValidateCustomToolConfigRequest,
    tamarind_version: str | Unset = UNSET,
) -> Response[CustomToolConfigValidation | Problem]:
    """Validate a tool config

     Check a `config.json` against the contract a build applies, before spending a build on it.

    Creates and changes nothing, and the tool need not exist. A config that fails is a successful check:
    the response is 200 with `valid: false` and the reason a build would give. It does not look at the
    rest of the source, so a build can still be refused for a missing `Dockerfile` or `run.sh`.

    Args:
        tamarind_version (str | Unset):
        body (ValidateCustomToolConfigRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CustomToolConfigValidation | Problem]
    """

    kwargs = _get_kwargs(
        body=body,
        tamarind_version=tamarind_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    body: ValidateCustomToolConfigRequest,
    tamarind_version: str | Unset = UNSET,
) -> CustomToolConfigValidation | Problem | None:
    """Validate a tool config

     Check a `config.json` against the contract a build applies, before spending a build on it.

    Creates and changes nothing, and the tool need not exist. A config that fails is a successful check:
    the response is 200 with `valid: false` and the reason a build would give. It does not look at the
    rest of the source, so a build can still be refused for a missing `Dockerfile` or `run.sh`.

    Args:
        tamarind_version (str | Unset):
        body (ValidateCustomToolConfigRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CustomToolConfigValidation | Problem
    """

    return sync_detailed(
        client=client,
        body=body,
        tamarind_version=tamarind_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: ValidateCustomToolConfigRequest,
    tamarind_version: str | Unset = UNSET,
) -> Response[CustomToolConfigValidation | Problem]:
    """Validate a tool config

     Check a `config.json` against the contract a build applies, before spending a build on it.

    Creates and changes nothing, and the tool need not exist. A config that fails is a successful check:
    the response is 200 with `valid: false` and the reason a build would give. It does not look at the
    rest of the source, so a build can still be refused for a missing `Dockerfile` or `run.sh`.

    Args:
        tamarind_version (str | Unset):
        body (ValidateCustomToolConfigRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CustomToolConfigValidation | Problem]
    """

    kwargs = _get_kwargs(
        body=body,
        tamarind_version=tamarind_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: ValidateCustomToolConfigRequest,
    tamarind_version: str | Unset = UNSET,
) -> CustomToolConfigValidation | Problem | None:
    """Validate a tool config

     Check a `config.json` against the contract a build applies, before spending a build on it.

    Creates and changes nothing, and the tool need not exist. A config that fails is a successful check:
    the response is 200 with `valid: false` and the reason a build would give. It does not look at the
    rest of the source, so a build can still be refused for a missing `Dockerfile` or `run.sh`.

    Args:
        tamarind_version (str | Unset):
        body (ValidateCustomToolConfigRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CustomToolConfigValidation | Problem
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            tamarind_version=tamarind_version,
        )
    ).parsed
