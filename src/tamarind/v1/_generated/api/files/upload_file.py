from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...models.file_upload import FileUpload
from ...models.problem import Problem
from ...models.upload_file_inline_request import UploadFileInlineRequest
from ...models.upload_file_multipart_request import UploadFileMultipartRequest
from ...models.upload_file_signed_request import UploadFileSignedRequest
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    body: UploadFileInlineRequest | UploadFileMultipartRequest | UploadFileSignedRequest,
    tamarind_version: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(tamarind_version, Unset):
        headers["Tamarind-Version"] = tamarind_version

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/files",
    }

    if isinstance(body, UploadFileInlineRequest):
        _kwargs["json"] = body.to_dict()
    elif isinstance(body, UploadFileSignedRequest):
        _kwargs["json"] = body.to_dict()
    else:
        _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> FileUpload | Problem:
    if response.status_code == 201:
        response_201 = FileUpload.from_dict(response.json())

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
) -> Response[FileUpload | Problem]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: UploadFileInlineRequest | UploadFileMultipartRequest | UploadFileSignedRequest,
    tamarind_version: str | Unset = UNSET,
) -> Response[FileUpload | Problem]:
    """Start a file upload, or upload a small file directly

     The only way to upload.

    - **Small files, or sandboxed clients:** send `contentBase64` (up to 3 MiB of content). The
      file is stored and `upload` is null.
    - **Everything else:** send `sizeBytes`, then PUT the bytes to `upload.url` with `upload.headers`.
    - **Over 5 GB, or for resumable transfers:** set `multipart: true`, PUT each part, then call
      `completeFileUpload`. Parts are at least 64 MiB and at most 5 GiB, and there are at most
      1,000 of them, so every part's URL comes in this one answer.

    Signed URLs expire in 1 hour. Uploading to an existing path replaces the file. The bytes
    never pass through this API except `contentBase64`. A `contentBase64` over the limit, or sent
    with `sizeBytes` or `multipart`, is 422 at `/contentBase64`; sending neither `contentBase64`
    nor `sizeBytes` is 422 at `/sizeBytes`; a path that leaves your workspace or names a private
    export is 422 at `/path`. Nothing is stored when the answer is an error.

    Args:
        tamarind_version (str | Unset):
        body (UploadFileInlineRequest | UploadFileMultipartRequest | UploadFileSignedRequest):
            Send `contentBase64` to store the file now, `sizeBytes` to get a signed URL, or
            `sizeBytes` with `multipart: true` for a multipart transfer.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[FileUpload | Problem]
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
    body: UploadFileInlineRequest | UploadFileMultipartRequest | UploadFileSignedRequest,
    tamarind_version: str | Unset = UNSET,
) -> FileUpload | Problem | None:
    """Start a file upload, or upload a small file directly

     The only way to upload.

    - **Small files, or sandboxed clients:** send `contentBase64` (up to 3 MiB of content). The
      file is stored and `upload` is null.
    - **Everything else:** send `sizeBytes`, then PUT the bytes to `upload.url` with `upload.headers`.
    - **Over 5 GB, or for resumable transfers:** set `multipart: true`, PUT each part, then call
      `completeFileUpload`. Parts are at least 64 MiB and at most 5 GiB, and there are at most
      1,000 of them, so every part's URL comes in this one answer.

    Signed URLs expire in 1 hour. Uploading to an existing path replaces the file. The bytes
    never pass through this API except `contentBase64`. A `contentBase64` over the limit, or sent
    with `sizeBytes` or `multipart`, is 422 at `/contentBase64`; sending neither `contentBase64`
    nor `sizeBytes` is 422 at `/sizeBytes`; a path that leaves your workspace or names a private
    export is 422 at `/path`. Nothing is stored when the answer is an error.

    Args:
        tamarind_version (str | Unset):
        body (UploadFileInlineRequest | UploadFileMultipartRequest | UploadFileSignedRequest):
            Send `contentBase64` to store the file now, `sizeBytes` to get a signed URL, or
            `sizeBytes` with `multipart: true` for a multipart transfer.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        FileUpload | Problem
    """

    return sync_detailed(
        client=client,
        body=body,
        tamarind_version=tamarind_version,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: UploadFileInlineRequest | UploadFileMultipartRequest | UploadFileSignedRequest,
    tamarind_version: str | Unset = UNSET,
) -> Response[FileUpload | Problem]:
    """Start a file upload, or upload a small file directly

     The only way to upload.

    - **Small files, or sandboxed clients:** send `contentBase64` (up to 3 MiB of content). The
      file is stored and `upload` is null.
    - **Everything else:** send `sizeBytes`, then PUT the bytes to `upload.url` with `upload.headers`.
    - **Over 5 GB, or for resumable transfers:** set `multipart: true`, PUT each part, then call
      `completeFileUpload`. Parts are at least 64 MiB and at most 5 GiB, and there are at most
      1,000 of them, so every part's URL comes in this one answer.

    Signed URLs expire in 1 hour. Uploading to an existing path replaces the file. The bytes
    never pass through this API except `contentBase64`. A `contentBase64` over the limit, or sent
    with `sizeBytes` or `multipart`, is 422 at `/contentBase64`; sending neither `contentBase64`
    nor `sizeBytes` is 422 at `/sizeBytes`; a path that leaves your workspace or names a private
    export is 422 at `/path`. Nothing is stored when the answer is an error.

    Args:
        tamarind_version (str | Unset):
        body (UploadFileInlineRequest | UploadFileMultipartRequest | UploadFileSignedRequest):
            Send `contentBase64` to store the file now, `sizeBytes` to get a signed URL, or
            `sizeBytes` with `multipart: true` for a multipart transfer.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[FileUpload | Problem]
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
    body: UploadFileInlineRequest | UploadFileMultipartRequest | UploadFileSignedRequest,
    tamarind_version: str | Unset = UNSET,
) -> FileUpload | Problem | None:
    """Start a file upload, or upload a small file directly

     The only way to upload.

    - **Small files, or sandboxed clients:** send `contentBase64` (up to 3 MiB of content). The
      file is stored and `upload` is null.
    - **Everything else:** send `sizeBytes`, then PUT the bytes to `upload.url` with `upload.headers`.
    - **Over 5 GB, or for resumable transfers:** set `multipart: true`, PUT each part, then call
      `completeFileUpload`. Parts are at least 64 MiB and at most 5 GiB, and there are at most
      1,000 of them, so every part's URL comes in this one answer.

    Signed URLs expire in 1 hour. Uploading to an existing path replaces the file. The bytes
    never pass through this API except `contentBase64`. A `contentBase64` over the limit, or sent
    with `sizeBytes` or `multipart`, is 422 at `/contentBase64`; sending neither `contentBase64`
    nor `sizeBytes` is 422 at `/sizeBytes`; a path that leaves your workspace or names a private
    export is 422 at `/path`. Nothing is stored when the answer is an error.

    Args:
        tamarind_version (str | Unset):
        body (UploadFileInlineRequest | UploadFileMultipartRequest | UploadFileSignedRequest):
            Send `contentBase64` to store the file now, `sizeBytes` to get a signed URL, or
            `sizeBytes` with `multipart: true` for a multipart transfer.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        FileUpload | Problem
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            tamarind_version=tamarind_version,
        )
    ).parsed
