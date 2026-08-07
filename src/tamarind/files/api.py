"""Workspace-file endpoints: one function per operation."""

from __future__ import annotations

from typing import Any

from ..errors import APIError
from ..http import HTTPClient

_TRUE = "true"


def upload_file_url(
    client: HTTPClient, *, filename: str, content_type: str = "application/octet-stream"
) -> dict:
    """POST /getPresignedUploadUrl — returns {uploadUrl, headUrl, key, bucket}.

    PUT the file bytes directly to ``uploadUrl`` with a matching ``Content-Type``
    header (the presigned signature covers the content type). This uploads
    straight to S3, bypassing the API's request-body size limit. Use
    :func:`tamarind.upload.put_presigned` for the transfer itself.
    """
    return client.post_json(
        "getPresignedUploadUrl", json={"filename": filename, "contentType": content_type}
    )


def delete_file(
    client: HTTPClient, *, file_path: str | None = None, folder: str | None = None
) -> Any:
    """Delete a file, or every file under a folder.

    The API expects DELETE (a GET returns 405 "Use DELETE or POST"); some older
    deployments may still want GET, so fall back on a 405.
    """
    params = {"filePath": file_path, "folder": folder}
    try:
        return client.delete_json("delete-file", params=params)
    except APIError as exc:
        if getattr(exc, "status_code", None) == 405:
            return client.get_json("delete-file", params=params)
        raise


def get_files(
    client: HTTPClient,
    *,
    limit: int | None = None,
    offset: int | None = None,
    types: str | None = None,
    search: str | None = None,
    folder: str | None = None,
    include_folders: bool = False,
    include_all: bool = False,
    include_metadata: bool = False,
) -> Any:
    """GET /files — list files in the workspace, with filtering/pagination."""
    params = {
        "limit": limit,
        "offset": offset,
        "types": types,
        "search": search,
        "folder": folder,
        "includeFolders": _TRUE if include_folders else None,
        "includeAll": _TRUE if include_all else None,
        "includeMetadata": _TRUE if include_metadata else None,
    }
    return client.get_json("files", params=params)


def get_folders(
    client: HTTPClient,
    *,
    limit: int | None = None,
    offset: int | None = None,
    load_all: bool = False,
) -> Any:
    """GET /getFolders — list folders in the workspace."""
    params = {
        "limit": limit,
        "offset": offset,
        "loadAll": _TRUE if load_all else None,
    }
    return client.get_json("getFolders", params=params)
