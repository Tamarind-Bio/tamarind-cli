"""Shared file-upload transport, used by BOTH the CLI (`tamarind files upload`) and the SDK
(`client.files.upload`) so the two go through one code path (the presigned two-step PUT)."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any, BinaryIO

import httpx

from . import rest
from .errors import TamarindError
from .http import HTTPClient

_UPLOAD_CHUNK_SIZE = 1024 * 1024
_UPLOAD_TIMEOUT = 300.0


def _iter_file_chunks(fh: BinaryIO) -> Iterator[bytes]:
    """Read an upload incrementally instead of buffering the whole file."""
    while chunk := fh.read(_UPLOAD_CHUNK_SIZE):
        yield chunk


def put_presigned_upload(url: str, path: Path, *, content_type: str, remote: str) -> int:
    """Stream ``path`` to a presigned URL and translate transport failures.

    Presigned URLs contain temporary credentials, so error messages deliberately omit the
    URL rather than echoing ``httpx``'s exception text. Returns the uploaded byte count.
    """
    try:
        size = path.stat().st_size
        headers = {
            "Content-Type": content_type,
            # Supplying the size avoids chunked transfer encoding, which is not
            # accepted by every S3-compatible presigned PUT endpoint.
            "Content-Length": str(size),
        }
        with path.open("rb") as fh:
            put = httpx.put(url, content=_iter_file_chunks(fh), headers=headers, timeout=_UPLOAD_TIMEOUT)
        put.raise_for_status()
    except httpx.TimeoutException as exc:
        raise TamarindError(f"Upload of '{remote}' timed out after {_UPLOAD_TIMEOUT:g} seconds.") from exc
    except httpx.HTTPStatusError as exc:
        raise TamarindError(f"Upload of '{remote}' failed with HTTP {exc.response.status_code}.") from exc
    except (httpx.RequestError, httpx.InvalidURL, httpx.StreamError) as exc:
        raise TamarindError(f"Upload transfer failed for '{remote}' ({type(exc).__name__}).") from exc
    except OSError as exc:
        raise TamarindError(f"Could not read '{path}' during upload: {exc}.") from exc
    return size


def upload_file(
    client: HTTPClient, path: str | Path, *, remote: str | None = None,
    content_type: str = "application/octet-stream",
) -> dict[str, Any]:
    """End-to-end upload: presign (POST /getPresignedUploadUrl) then PUT the bytes.

    Returns ``{"ok": True, "filename": <remote>, "bytes": <size>}``.
    """
    path = Path(path)
    remote = remote or path.name
    signed = rest.upload_file_url(client, filename=remote, content_type=content_type)
    url = signed.get("uploadUrl") if isinstance(signed, dict) else None
    if not isinstance(url, str) or not url:
        # Never echo the response values: sibling fields (headUrl) can also be presigned URLs.
        detail: dict[str, Any] = {"responseType": type(signed).__name__}
        if isinstance(signed, dict):
            detail["fields"] = sorted(str(key) for key in signed)
        raise TamarindError("Upload did not return a presigned URL.", detail=detail)
    size = put_presigned_upload(url, path, content_type=content_type, remote=remote)
    return {"ok": True, "filename": remote, "bytes": size}
