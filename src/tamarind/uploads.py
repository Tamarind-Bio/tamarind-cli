"""Shared file-upload transport, used by BOTH the CLI (`tamarind files upload`) and the SDK
(`client.files.upload`) so the two go through one code path (the presigned two-step PUT).

The Agent API's chat files (`tamarind chat files upload`, `client.agent.files.upload`) are a
different API with a different contract: a presigned form POST, in :func:`post_presigned_form`."""

from __future__ import annotations

import re
from collections.abc import Iterator, Mapping
from pathlib import Path
from typing import Any, BinaryIO

import httpx

from . import rest
from ._logging import redact_signed_urls
from .errors import TamarindError
from .http import HTTPClient

_UPLOAD_CHUNK_SIZE = 1024 * 1024
_UPLOAD_TIMEOUT = 300.0
# The one thing an S3-style error body is quoted for: its error code, which is a short
# identifier (``EntityTooLarge``). The rest of the body can echo the signed policy.
_ERROR_CODE = re.compile(r"<Code>([A-Za-z0-9]{1,64})</Code>")


def _iter_file_chunks(fh: BinaryIO) -> Iterator[bytes]:
    """Read an upload incrementally instead of buffering the whole file."""
    while chunk := fh.read(_UPLOAD_CHUNK_SIZE):
        yield chunk


def put_presigned_upload(url: str, path: Path, *, content_type: str, remote: str) -> int:
    """Stream ``path`` to a presigned URL and translate transport failures.

    Presigned URLs contain temporary credentials, so error messages deliberately omit the
    URL rather than echoing ``httpx``'s exception text, and the httpx error is not chained
    (``from None``): its message carries the full signed URL into any traceback. Returns the uploaded byte count.
    """
    redact_signed_urls()  # httpx logs the URL at INFO, and the URL is the credential
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
    except httpx.TimeoutException:
        raise TamarindError(f"Upload of '{remote}' timed out after {_UPLOAD_TIMEOUT:g} seconds.") from None
    except httpx.HTTPStatusError as exc:
        raise TamarindError(f"Upload of '{remote}' failed with HTTP {exc.response.status_code}.") from None
    except (httpx.RequestError, httpx.InvalidURL, httpx.StreamError) as exc:
        raise TamarindError(f"Upload transfer failed for '{remote}' ({type(exc).__name__}).") from None
    except OSError as exc:
        raise TamarindError(f"Could not read '{path}' during upload: {exc}.") from exc
    return size


def post_presigned_form(url: str, fields: Mapping[str, str], path: Path, *, remote: str) -> int:
    """Send ``path`` to a presigned upload form (``POST`` multipart) and translate failures.

    The Agent API's upload contract: every entry of ``fields`` as a form field, exactly as
    given and in the given order, then the file itself as the last field, named ``file``. The
    fields carry what storage requires (key, signed policy, the file's type), so nothing is
    added to them, and nothing but the form is sent: no API key, no API headers. A success
    answers 204 with no body.

    Both the URL and the fields are credentials: error messages omit them and the httpx error
    is not chained (``from None``). The one thing taken from a refusal's body is its error
    code (``EntityTooLarge`` for a file over the limit or an empty one). Returns the byte count.
    """
    redact_signed_urls()  # httpx logs the URL at INFO, and a URL can carry a signature
    # The part's own type repeats the form's `Content-Type` field when it has one, rather than
    # a guess from the file name that depends on the operating system's tables.
    part_type = next((v for k, v in fields.items() if k.lower() == "content-type"),
                     "application/octet-stream")
    try:
        size = path.stat().st_size
        with path.open("rb") as fh:
            sent = httpx.post(url, data=dict(fields), files={"file": (remote, fh, part_type)},
                              timeout=_UPLOAD_TIMEOUT)
        sent.raise_for_status()
    except httpx.TimeoutException:
        raise TamarindError(f"Upload of '{remote}' timed out after {_UPLOAD_TIMEOUT:g} seconds.") from None
    except httpx.HTTPStatusError as exc:
        found = _ERROR_CODE.search(exc.response.text[:8192])
        code = f" ({found.group(1)})" if found else ""
        raise TamarindError(f"Upload of '{remote}' failed with HTTP {exc.response.status_code}{code}.") from None
    except (httpx.RequestError, httpx.InvalidURL, httpx.StreamError) as exc:
        raise TamarindError(f"Upload transfer failed for '{remote}' ({type(exc).__name__}).") from None
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
