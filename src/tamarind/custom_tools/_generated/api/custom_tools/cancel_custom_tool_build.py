from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.public_problem import PublicProblem
from ...models.public_version import PublicVersion
from ...types import UNSET, Response, Unset


def _get_kwargs(
    name: str,
    *,
    version: None | str | Unset = UNSET,
    if_match: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(if_match, Unset):
        headers["If-Match"] = if_match

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
        "url": "/custom-tools/{name}/cancel-build".format(
            name=quote(str(name), safe=""),
        ),
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> PublicProblem | PublicVersion:
    if response.status_code == 200:
        response_200 = PublicVersion.from_dict(response.json())

        return response_200

    if response.status_code == 401:
        response_401 = PublicProblem.from_dict(response.json())

        return response_401

    if response.status_code == 404:
        response_404 = PublicProblem.from_dict(response.json())

        return response_404

    if response.status_code == 409:
        response_409 = PublicProblem.from_dict(response.json())

        return response_409

    if response.status_code == 412:
        response_412 = PublicProblem.from_dict(response.json())

        return response_412

    if response.status_code == 422:
        response_422 = PublicProblem.from_dict(response.json())

        return response_422

    response_default = PublicProblem.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[PublicProblem | PublicVersion]:
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
) -> Response[PublicProblem | PublicVersion]:
    """Cancel a custom tool build

     Request cancellation of an active build.

    When exactly one build is active, no version is needed. If multiple builds are active, pass a
    version such as `version=v2`. Cancellation is a request; continue polling for the outcome.

    Args:
        name (str): The custom tool name.
        version (None | str | Unset):
        if_match (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PublicProblem | PublicVersion]
    """

    kwargs = _get_kwargs(
        name=name,
        version=version,
        if_match=if_match,
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
) -> PublicProblem | PublicVersion | None:
    """Cancel a custom tool build

     Request cancellation of an active build.

    When exactly one build is active, no version is needed. If multiple builds are active, pass a
    version such as `version=v2`. Cancellation is a request; continue polling for the outcome.

    Args:
        name (str): The custom tool name.
        version (None | str | Unset):
        if_match (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PublicProblem | PublicVersion
    """

    return sync_detailed(
        name=name,
        client=client,
        version=version,
        if_match=if_match,
    ).parsed


async def asyncio_detailed(
    name: str,
    *,
    client: AuthenticatedClient | Client,
    version: None | str | Unset = UNSET,
    if_match: str | Unset = UNSET,
) -> Response[PublicProblem | PublicVersion]:
    """Cancel a custom tool build

     Request cancellation of an active build.

    When exactly one build is active, no version is needed. If multiple builds are active, pass a
    version such as `version=v2`. Cancellation is a request; continue polling for the outcome.

    Args:
        name (str): The custom tool name.
        version (None | str | Unset):
        if_match (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PublicProblem | PublicVersion]
    """

    kwargs = _get_kwargs(
        name=name,
        version=version,
        if_match=if_match,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    name: str,
    *,
    client: AuthenticatedClient | Client,
    version: None | str | Unset = UNSET,
    if_match: str | Unset = UNSET,
) -> PublicProblem | PublicVersion | None:
    """Cancel a custom tool build

     Request cancellation of an active build.

    When exactly one build is active, no version is needed. If multiple builds are active, pass a
    version such as `version=v2`. Cancellation is a request; continue polling for the outcome.

    Args:
        name (str): The custom tool name.
        version (None | str | Unset):
        if_match (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PublicProblem | PublicVersion
    """

    return (
        await asyncio_detailed(
            name=name,
            client=client,
            version=version,
            if_match=if_match,
        )
    ).parsed
