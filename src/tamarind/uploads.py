"""Shared file-upload transport, used by BOTH the CLI (`tamarind files upload`) and the SDK
(`client.files.upload`) so the two go through one code path.

Small files take one presigned PUT. Files above ``MULTIPART_THRESHOLD_BYTES`` use the
multipart endpoint: the server creates the upload and signs one URL per part, the bytes go
straight to storage in parallel, and the server assembles the object on ``complete``.

A multipart upload is resumable. Its upload id and finished parts are saved under
``~/.tamarind/uploads/``; running the same upload again skips the parts already sent. The
saved upload is kept when the transfer is interrupted (Ctrl-C) or runs out of network
retries, because aborting it would throw away the parts a rerun can reuse. It is aborted,
and the saved state removed, when the server rejects the upload outright, when the local
file changed since the saved upload began, or when ``resume=False`` is passed.
"""

from __future__ import annotations

import concurrent.futures
import hashlib
import json
import os
import random
import threading
import time
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any, BinaryIO

import httpx

from . import rest
from .config import config_dir
from .errors import APIError, NotFoundError, RateLimitError, TamarindError
from .http import HTTPClient

_UPLOAD_CHUNK_SIZE = 1024 * 1024
_UPLOAD_TIMEOUT = 300.0

MIB = 1024 * 1024
GIB = 1024 * MIB

MULTIPART_THRESHOLD_BYTES = 100 * MIB
# The largest object one PUT may create; above this only multipart works.
SINGLE_PUT_MAX_BYTES = 5 * GIB
DEFAULT_CONCURRENCY = 4
MAX_CONCURRENCY = 16
MAX_PART_ATTEMPTS = 5
SIGN_BATCH_SIZE = 16
_BACKOFF_BASE_SECONDS = 0.5
_STATE_VERSION = 1

ProgressCallback = Callable[[int, int], None]


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


def _single_put(client: HTTPClient, path: Path, *, remote: str, content_type: str) -> int:
    signed = rest.upload_file_url(client, filename=remote, content_type=content_type)
    url = signed.get("uploadUrl") if isinstance(signed, dict) else None
    if not isinstance(url, str) or not url:
        # Never echo the response values: sibling fields (headUrl) can also be presigned URLs.
        detail: dict[str, Any] = {"responseType": type(signed).__name__}
        if isinstance(signed, dict):
            detail["fields"] = sorted(str(key) for key in signed)
        raise TamarindError("Upload did not return a presigned URL.", detail=detail)
    return put_presigned_upload(url, path, content_type=content_type, remote=remote)


def upload_file(
    client: HTTPClient,
    path: str | Path,
    *,
    remote: str | None = None,
    content_type: str = "application/octet-stream",
    concurrency: int = DEFAULT_CONCURRENCY,
    resume: bool = True,
    progress: ProgressCallback | None = None,
    state_dir: Path | None = None,
) -> dict[str, Any]:
    """Upload ``path`` to the workspace as ``remote`` (default: its basename).

    Returns ``{"ok": True, "filename": <remote>, "bytes": <size>}``, plus ``multipart``,
    ``parts`` and ``resumed`` for a multipart upload. ``progress(sent, total)`` is called
    as bytes go out.
    """
    path = Path(path)
    remote = remote or path.name
    try:
        size = path.stat().st_size
    except OSError as exc:
        raise TamarindError(f"Could not read '{path}': {exc}.") from exc

    if size > MULTIPART_THRESHOLD_BYTES:
        uploader = _MultipartUpload(
            client, path, remote=remote, size=size, content_type=content_type,
            concurrency=concurrency, progress=progress,
            state_dir=state_dir if state_dir is not None else config_dir() / "uploads",
        )
        try:
            return uploader.run(resume=resume)
        except _EndpointMissing:
            if size > SINGLE_PUT_MAX_BYTES:
                raise TamarindError(
                    f"'{path.name}' is {_format_bytes(size)}, and this server does not support "
                    f"multipart uploads, which files over {_format_bytes(SINGLE_PUT_MAX_BYTES)} "
                    "need. Upload it through the web app, or split it into smaller files."
                ) from None

    sent = _single_put(client, path, remote=remote, content_type=content_type)
    if progress:
        progress(sent, size)
    return {"ok": True, "filename": remote, "bytes": sent}


def _format_bytes(n: int) -> str:
    if n >= GIB:
        return f"{n / GIB:.1f} GB"
    return f"{n / MIB:.0f} MB"


class _EndpointMissing(Exception):
    """The server has no multipart endpoint (an older deployment)."""


class _UploadGone(Exception):
    """Storage no longer knows the upload id (aborted or expired)."""


class _PartFailed(Exception):
    def __init__(self, part_number: int, reason: str, *, retryable: bool) -> None:
        super().__init__(reason)
        self.part_number = part_number
        self.retryable = retryable


class _Cancelled(Exception):
    pass


def _is_transient(exc: TamarindError) -> bool:
    """Network failures, 5xx and 429 from the API are worth retrying; other errors are not."""
    if isinstance(exc, RateLimitError):
        return True
    if isinstance(exc, APIError):
        return exc.status_code >= 500
    # HTTPClient wraps transport failures (connection reset, timeout) in the base class.
    return isinstance(exc.__cause__, httpx.HTTPError)


class _State:
    """The on-disk record that makes an upload resumable.

    One JSON file per (server, account, local file, remote name). It holds the upload id,
    the file's size and mtime when the upload began, and the ETag of each finished part.
    It never holds credentials or presigned URLs.
    """

    def __init__(self, path: Path, data: dict[str, Any]) -> None:
        self.path = path
        self.data = data
        self._lock = threading.Lock()

    @staticmethod
    def file_for(state_dir: Path, client: HTTPClient, local: Path, remote: str) -> Path:
        account = hashlib.sha256((client.api_key or "").encode()).hexdigest()
        ident = "\n".join([client.base_url, account, str(local.resolve()), remote])
        return state_dir / f"{hashlib.sha256(ident.encode()).hexdigest()[:32]}.json"

    @classmethod
    def load(cls, path: Path) -> "_State | None":
        try:
            data = json.loads(path.read_text())
        except (OSError, ValueError):
            return None
        if not isinstance(data, dict) or data.get("version") != _STATE_VERSION:
            return None
        if not isinstance(data.get("uploadId"), str) or not isinstance(data.get("parts"), dict):
            return None
        return cls(path, data)

    @property
    def parts(self) -> dict[int, str]:
        return {int(k): v for k, v in self.data["parts"].items()}

    def matches(self, *, size: int, mtime_ns: int, remote: str) -> bool:
        d = self.data
        return d.get("size") == size and d.get("mtimeNs") == mtime_ns and d.get("remote") == remote

    def record_part(self, part_number: int, etag: str) -> None:
        with self._lock:
            self.data["parts"][str(part_number)] = etag
            self.save()

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_name(f"{self.path.name}.{os.getpid()}.{threading.get_ident()}.tmp")
        tmp.write_text(json.dumps(self.data, indent=1) + "\n")
        try:
            tmp.chmod(0o600)
        except OSError:
            pass
        os.replace(tmp, self.path)

    def delete(self) -> None:
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass


class _MultipartUpload:
    def __init__(
        self,
        client: HTTPClient,
        path: Path,
        *,
        remote: str,
        size: int,
        content_type: str,
        concurrency: int,
        progress: ProgressCallback | None,
        state_dir: Path,
        max_attempts: int = MAX_PART_ATTEMPTS,
    ) -> None:
        self.client = client
        self.path = path
        self.remote = remote
        self.size = size
        self.content_type = content_type
        self.concurrency = max(1, min(int(concurrency), MAX_CONCURRENCY))
        self.progress = progress
        self.state_file = _State.file_for(state_dir, client, path, remote)
        self.max_attempts = max_attempts
        self._api_lock = threading.Lock()
        self._url_lock = threading.Lock()
        self._progress_lock = threading.Lock()
        self._sent = 0
        self._cancel = threading.Event()
        self._urls: dict[int, str] = {}

    # -- API ---------------------------------------------------------------
    def _call(self, action: str, **body: Any) -> Any:
        with self._api_lock:
            return rest.multipart_upload(self.client, action=action, filename=self.remote, **body)

    def _abort(self, upload_id: str) -> None:
        try:
            self._call("abort", uploadId=upload_id)
        except TamarindError:
            pass

    # -- driver --------------------------------------------------------------
    def run(self, *, resume: bool) -> dict[str, Any]:
        mtime_ns = self.path.stat().st_mtime_ns
        state = _State.load(self.state_file)
        resumed = False
        if state is not None:
            if resume and state.matches(size=self.size, mtime_ns=mtime_ns, remote=self.remote):
                resumed = True
            else:
                self._abort(state.data["uploadId"])
                state.delete()
                state = None
        if state is None:
            state = self._create(mtime_ns)

        try:
            return self._upload(state, resumed=resumed)
        except _UploadGone:
            if not resumed:
                state.delete()
                raise TamarindError(
                    f"Upload of '{self.remote}' was cancelled on the server before it finished."
                ) from None
        # The saved upload expired or was aborted elsewhere: start once from scratch.
        state.delete()
        self._sent = 0
        self._urls.clear()
        self._cancel.clear()
        state = self._create(mtime_ns)
        try:
            return self._upload(state, resumed=False)
        except _UploadGone:
            state.delete()
            raise TamarindError(
                f"Upload of '{self.remote}' was cancelled on the server before it finished."
            ) from None

    def _create(self, mtime_ns: int) -> _State:
        try:
            created = self._call("create", size=self.size, contentType=self.content_type)
        except NotFoundError:
            raise _EndpointMissing() from None
        if not isinstance(created, dict) or not isinstance(created.get("uploadId"), str):
            raise TamarindError("Multipart upload did not return an upload id.")
        part_size = created.get("partSize")
        part_count = created.get("partCount")
        if not isinstance(part_size, int) or part_size <= 0 or part_count != _part_count(self.size, part_size):
            self._abort(created["uploadId"])
            raise TamarindError("Server and client disagree on the multipart part layout.")
        state = _State(self.state_file, {
            "version": _STATE_VERSION,
            "remote": self.remote,
            "path": str(self.path.resolve()),
            "size": self.size,
            "mtimeNs": mtime_ns,
            "uploadId": created["uploadId"],
            # Names this upload on the stored object, so a lost complete is confirmed
            # against this upload and not an older file of the same size.
            "uploadToken": created.get("uploadToken") if isinstance(created.get("uploadToken"), str) else None,
            "partSize": part_size,
            "partCount": part_count,
            "parts": {},
            "createdAt": int(time.time()),
        })
        state.save()
        return state

    def _upload(self, state: _State, *, resumed: bool) -> dict[str, Any]:
        upload_id: str = state.data["uploadId"]
        part_size: int = state.data["partSize"]
        part_count: int = state.data["partCount"]
        done = state.parts
        todo = [n for n in range(1, part_count + 1) if n not in done]
        self._add_progress(sum(_part_range(n, part_size, self.size)[1] for n in done))

        try:
            if todo:
                self._upload_parts(state, upload_id, part_size, todo)
            parts = state.parts
            if len(parts) != part_count:
                raise _PartFailed(
                    min(set(range(1, part_count + 1)) - set(parts)),
                    "the part was not uploaded", retryable=True,
                )
            now = self.path.stat()
            if now.st_size != self.size or now.st_mtime_ns != state.data["mtimeNs"]:
                raise _PartFailed(part_count, "the file changed while it was uploading", retryable=False)
            self._complete(upload_id, state.data.get("uploadToken"), parts)
        except (_UploadGone, KeyboardInterrupt):
            raise
        except _PartFailed as exc:
            if exc.retryable:
                raise TamarindError(
                    f"Upload of '{self.remote}' stopped at part {exc.part_number} of {part_count}: "
                    f"{exc}. Finished parts are saved; rerun the same command to resume."
                ) from None
            self._abort(upload_id)
            state.delete()
            raise TamarindError(f"Upload of '{self.remote}' failed: {exc}.") from None
        except TamarindError as exc:
            if _is_transient(exc):
                exc.message = (
                    f"{exc.message} Finished parts are saved; rerun the same command to resume."
                )
                raise
            self._abort(upload_id)
            state.delete()
            raise

        state.delete()
        return {
            "ok": True,
            "filename": self.remote,
            "bytes": self.size,
            "multipart": True,
            "parts": part_count,
            "resumed": resumed,
        }

    def _complete(self, upload_id: str, upload_token: str | None, parts: dict[int, str]) -> None:
        body = [{"partNumber": n, "etag": parts[n]} for n in sorted(parts)]
        try:
            completed = self._call("complete", uploadId=upload_id, uploadToken=upload_token, size=self.size, parts=body)
        except TamarindError as exc:
            # The object may have been assembled even though the response was lost.
            lost = _is_transient(exc) or isinstance(exc, NotFoundError)
            if not lost or not self._confirmed(upload_token):
                raise
            return
        # The server checks the assembled size before answering; trust its answer.
        if not isinstance(completed, dict) or completed.get("size") != self.size:
            raise TamarindError(
                f"Upload of '{self.remote}' completed, but the stored size does not match "
                f"the local file ({self.size} bytes)."
            )

    def _confirmed(self, upload_token: str | None) -> bool:
        """True only if the stored object was written by this upload, at the expected size."""
        if not upload_token:
            return False
        try:
            status = self._call("status", size=self.size, uploadToken=upload_token)
        except TamarindError:
            return False
        return (
            isinstance(status, dict)
            and status.get("exists") is True
            and status.get("size") == self.size
            and status.get("matchesUpload") is True
        )

    # -- parts ---------------------------------------------------------------
    def _upload_parts(self, state: _State, upload_id: str, part_size: int, todo: list[int]) -> None:
        pending = iter(todo)
        pending_lock = threading.Lock()
        failure: list[BaseException] = []

        def next_part() -> int | None:
            with pending_lock:
                return next(pending, None)

        def worker(http: httpx.Client) -> None:
            while not self._cancel.is_set():
                n = next_part()
                if n is None:
                    return
                try:
                    etag = self._upload_part(http, upload_id, n, part_size, todo)
                except _Cancelled:
                    return
                except BaseException as exc:
                    failure.append(exc)
                    self._cancel.set()
                    return
                state.record_part(n, etag)

        timeout = httpx.Timeout(_UPLOAD_TIMEOUT, connect=30.0)
        limits = httpx.Limits(max_connections=self.concurrency, max_keepalive_connections=self.concurrency)
        with httpx.Client(timeout=timeout, limits=limits) as http:
            pool = concurrent.futures.ThreadPoolExecutor(max_workers=self.concurrency)
            futures = [pool.submit(worker, http) for _ in range(min(self.concurrency, len(todo)))]
            try:
                # Wait in short slices so Ctrl-C reaches the main thread promptly.
                while not all(f.done() for f in futures):
                    concurrent.futures.wait(futures, timeout=0.25)
            except KeyboardInterrupt:
                self._cancel.set()
                pool.shutdown(wait=True)
                raise
            pool.shutdown(wait=True)
        if failure:
            raise failure[0]

    def _url_for(self, upload_id: str, n: int, todo: list[int], *, fresh: bool) -> str:
        with self._url_lock:
            return self._url_for_locked(upload_id, n, todo, fresh=fresh)

    def _url_for_locked(self, upload_id: str, n: int, todo: list[int], *, fresh: bool) -> str:
        if fresh:
            self._urls.pop(n, None)
        if n not in self._urls:
            batch = [n] if fresh else [m for m in todo if m >= n and m not in self._urls][:SIGN_BATCH_SIZE]
            signed = self._call("sign", uploadId=upload_id, size=self.size, partNumbers=batch)
            for entry in (signed or {}).get("parts", []) if isinstance(signed, dict) else []:
                if isinstance(entry, dict) and isinstance(entry.get("url"), str):
                    self._urls[int(entry["partNumber"])] = entry["url"]
        url = self._urls.get(n)
        if not url:
            raise TamarindError(f"No upload URL was returned for part {n}.")
        return url

    def _upload_part(self, http: httpx.Client, upload_id: str, n: int, part_size: int, todo: list[int]) -> str:
        start, length = _part_range(n, part_size, self.size)
        reason = "unknown error"
        retryable = True
        for attempt in range(1, self.max_attempts + 1):
            if self._cancel.is_set():
                raise _Cancelled()
            sent = [0]
            ok = False
            try:
                # A retry may come long after the batch was signed: always re-sign it.
                url = self._url_for(upload_id, n, todo, fresh=attempt > 1)
                resp = http.put(
                    url,
                    content=self._read_range(start, length, sent),
                    headers={"Content-Length": str(length)},
                )
                if resp.status_code == 404:
                    raise _UploadGone()
                resp.raise_for_status()
                etag = resp.headers.get("etag")
                if not etag:
                    raise _PartFailed(n, "storage did not return an ETag for the part", retryable=False)
                ok = True
                return etag
            except (_Cancelled, _UploadGone, _PartFailed):
                raise
            except TamarindError as exc:
                if not _is_transient(exc):
                    raise
                reason = exc.message
            except httpx.HTTPStatusError as exc:
                code = exc.response.status_code
                reason = f"HTTP {code}"
                # Storage rejected the request itself; resending it cannot help. A 403 can be
                # an expired URL, which the re-signed retry fixes, so it is retried first.
                if 400 <= code < 500 and code not in (403, 408, 429):
                    raise _PartFailed(n, f"storage rejected the part ({reason})", retryable=False) from None
                retryable = code != 403
            except (httpx.RequestError, httpx.StreamError) as exc:
                reason = type(exc).__name__
                retryable = True
            except OSError as exc:
                raise _PartFailed(n, f"could not read '{self.path}': {exc}", retryable=False) from None
            finally:
                if not ok:
                    self._add_progress(-sent[0])
            if attempt < self.max_attempts:
                self._backoff(attempt)
        raise _PartFailed(n, f"{reason} after {self.max_attempts} attempts", retryable=retryable)

    def _backoff(self, attempt: int) -> None:
        delay = min(30.0, _BACKOFF_BASE_SECONDS * (2 ** (attempt - 1))) * (0.5 + random.random() / 2)
        if self._cancel.wait(delay):
            raise _Cancelled()

    def _read_range(self, start: int, length: int, sent: list[int]) -> Iterator[bytes]:
        with self.path.open("rb") as fh:
            fh.seek(start)
            remaining = length
            while remaining > 0:
                if self._cancel.is_set():
                    raise _Cancelled()
                chunk = fh.read(min(_UPLOAD_CHUNK_SIZE, remaining))
                if not chunk:
                    raise OSError("file is shorter than when the upload started")
                remaining -= len(chunk)
                sent[0] += len(chunk)
                self._add_progress(len(chunk))
                yield chunk

    def _add_progress(self, delta: int) -> None:
        if not delta:
            return
        with self._progress_lock:
            self._sent = max(0, min(self.size, self._sent + delta))
            sent = self._sent
        if self.progress:
            self.progress(sent, self.size)


def _part_count(size: int, part_size: int) -> int:
    return -(-size // part_size)


def _part_range(n: int, part_size: int, size: int) -> tuple[int, int]:
    start = (n - 1) * part_size
    return start, min(part_size, size - start)
