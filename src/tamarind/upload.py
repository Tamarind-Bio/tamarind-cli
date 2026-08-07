"""Streaming uploads to presigned URLs.

Promoted out of `cli/commands/files.py`. Transport is not a command-layer concern,
and the custom-tools work needs the same streaming PUT for source archives — so it
lives where both can reach it rather than being copied.

The error handling here is the valuable part and the reason not to reimplement it:
presigned URLs carry temporary credentials in their query string, so every failure
path deliberately reports the *remote name* and never echoes httpx's exception text,
which would put the signed URL in a log.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import BinaryIO

import httpx

from .errors import TamarindError

UPLOAD_CHUNK_SIZE = 1024 * 1024
UPLOAD_TIMEOUT = 300.0


def iter_file_chunks(fh: BinaryIO, chunk_size: int = UPLOAD_CHUNK_SIZE) -> Iterator[bytes]:
    """Read an upload incrementally instead of buffering the whole file."""
    while chunk := fh.read(chunk_size):
        yield chunk


def put_presigned(
    url: str,
    path: Path,
    *,
    content_type: str,
    remote: str,
    timeout: float = UPLOAD_TIMEOUT,
) -> int:
    """Stream ``path`` to a presigned URL. Returns the byte count sent.

    Raises :class:`TamarindError` on any transport failure, with a message that
    names ``remote`` — never the signed URL.
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
            put = httpx.put(url, content=iter_file_chunks(fh), headers=headers, timeout=timeout)
        put.raise_for_status()
    except httpx.TimeoutException as exc:
        raise TamarindError(f"Upload of '{remote}' timed out after {timeout:g} seconds.") from exc
    except httpx.HTTPStatusError as exc:
        raise TamarindError(
            f"Upload of '{remote}' failed with HTTP {exc.response.status_code}."
        ) from exc
    except (httpx.RequestError, httpx.InvalidURL, httpx.StreamError) as exc:
        raise TamarindError(
            f"Upload transfer failed for '{remote}' ({type(exc).__name__})."
        ) from exc
    except OSError as exc:
        raise TamarindError(f"Could not read '{path}' during upload: {exc}.") from exc
    return size
