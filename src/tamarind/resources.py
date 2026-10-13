"""SDK resources that mirror the `tamarind` CLI command groups (jobs / tools / files).

Each method is a 1:1 wrapper over the same pure functions the CLI commands call
(:mod:`tamarind.rest`, :mod:`tamarind.catalog`, :mod:`tamarind.jobs`,
:mod:`tamarind.uploads`), so the SDK and CLI share one code path and one server contract.
Reached as ``client.jobs`` / ``client.tools`` / ``client.files`` on :class:`tamarind.Tamarind`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from . import catalog, rest, uploads
from .http import HTTPClient
from .jobs import fetch_job, wait_for_job


class Jobs:
    """Submit and manage jobs — mirrors ``tamarind submit/batch/validate/jobs/status/...``."""

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def submit(self, job_type: str, settings: dict[str, Any], *, name: str) -> Any:
        """Submit a single job (POST /submit-job). jobSource is stamped ``sdk``."""
        return rest.submit_job(self._http, job_name=name, job_type=job_type, settings=settings)

    def submit_batch(
        self, job_type: str, settings: list[dict[str, Any]], *, name: str,
        job_names: list[str] | None = None, max_runtime_seconds: int | None = None,
    ) -> Any:
        """Submit many jobs as one batch (POST /submit-batch)."""
        return rest.submit_batch(
            self._http, batch_name=name, job_type=job_type, settings=settings,
            job_names=job_names, max_runtime_seconds=max_runtime_seconds,
        )

    def validate(self, job_type: str, settings: dict[str, Any], *, name: str = "validation") -> dict:
        """Validate one settings dict without creating a job (POST /validate-job)."""
        return rest.validate_job(self._http, job_name=name, job_type=job_type, settings=settings)

    def validate_batch(
        self, job_type: str, settings: list[dict[str, Any]], *, job_names: list[str] | None = None,
    ) -> dict:
        """Validate many settings rows in ONE request (one verdict per row)."""
        return rest.validate_jobs(self._http, job_type=job_type, settings=settings, job_names=job_names)

    def list(self, **kwargs: Any) -> Any:
        """List jobs (GET /jobs). Accepts the same filters as :func:`tamarind.rest.get_jobs`."""
        return rest.get_jobs(self._http, **kwargs)

    def status(
        self, name: str, *, organization: bool = False, job_email: str | None = None,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        """Fetch one job by name (raises NotFoundError if absent)."""
        return fetch_job(
            self._http, name, organization=organization, job_email=job_email, timeout=timeout
        )

    def wait(
        self, name: str, *, poll_interval: float = 10.0, timeout: float | None = None,
        on_poll: Callable[[dict[str, Any]], None] | None = None,
        organization: bool = False, job_email: str | None = None,
    ) -> dict[str, Any]:
        """Block until ``name`` reaches a terminal status; returns the final job."""
        return wait_for_job(
            self._http, name, poll_interval=poll_interval, timeout=timeout, on_poll=on_poll,
            organization=organization, job_email=job_email,
        )

    def results(
        self, name: str, *, job_email: str | None = None, file_name: str | None = None,
        pdbs_only: bool | None = None,
    ) -> Any:
        """Get a presigned result URL (POST /result)."""
        return rest.get_result(
            self._http, job_name=name, job_email=job_email, file_name=file_name, pdbs_only=pdbs_only,
        )

    def cancel(self, *, name: str | None = None, job_id: str | None = None) -> dict:
        """Soft-stop a queued/running job (POST /cancelJob)."""
        return rest.cancel_job(self._http, job_name=name, job_id=job_id)

    def cancel_batch(self, batch_name: str) -> dict:
        """Soft-stop every job in a batch or pipeline (POST /cancelBatch)."""
        return rest.cancel_batch(self._http, batch_name=batch_name)

    def delete(self, name: str) -> Any:
        """Permanently remove a job and its subjobs (DELETE /delete-job)."""
        return rest.delete_job(self._http, job_name=name)


class Tools:
    """Discover the tool catalog and schemas — mirrors ``tamarind tools/modalities/schema/...``."""

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def list(
        self, *, modality: str | None = None, function: str | None = None,
        search: str | None = None, custom: bool | None = None,
    ) -> dict:
        """The filtered tool catalog (GET /catalog/tools)."""
        return catalog.list_tools(
            self._http, modality=modality, function=function, search=search, custom=custom,
        )

    def modalities(self) -> dict:
        """Available modalities (GET /catalog/modalities)."""
        return catalog.list_modalities(self._http)

    def functions(self) -> dict:
        """Available functions (GET /catalog/functions)."""
        return catalog.list_functions(self._http)

    def schema(self, job_type: str) -> dict:
        """The input schema for a tool (GET /tools/{name}/schema)."""
        return catalog.get_schema(self._http, job_type)

    def example(self, job_type: str) -> dict[str, Any]:
        """A runnable example settings dict derived from the tool's schema."""
        return catalog.example_settings(catalog.get_schema(self._http, job_type))


def _file_type_counts(files: list) -> dict:
    """Count workspace files by extension (top 20), mirroring the CLI/getFileStats."""
    counts: dict = {}
    for f in files:
        name = f if isinstance(f, str) else (f.get("name") or f.get("fileName") or "" if isinstance(f, dict) else "")
        ext = name.rsplit(".", 1)[1].lower() if "." in name else "no_extension"
        counts[ext] = counts.get(ext, 0) + 1
    ordered = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:20]
    return dict(ordered)


class Files:
    """Workspace file management — mirrors ``tamarind files list/stats/folders/upload/delete``."""

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def list(self, **kwargs: Any) -> Any:
        """List files (GET /files). Same filters as :func:`tamarind.rest.get_files`."""
        return rest.get_files(self._http, **kwargs)

    def stats(self) -> dict[str, Any]:
        """Summarize workspace files by type (counts), like the MCP getFileStats tool."""
        resp = rest.get_files(self._http)
        files = resp.get("files") if isinstance(resp, dict) else resp
        if not isinstance(files, list):
            files = []
        return {"totalFiles": len(files), "fileTypes": _file_type_counts(files)}

    def folders(self, **kwargs: Any) -> Any:
        """List folders (GET /getFolders)."""
        return rest.get_folders(self._http, **kwargs)

    def upload(
        self, path: str | Path, *, remote: str | None = None,
        content_type: str = "application/octet-stream",
    ) -> dict[str, Any]:
        """Upload a local file via the presigned two-step PUT. Returns {ok, filename, bytes}."""
        return uploads.upload_file(self._http, path, remote=remote, content_type=content_type)

    def delete(self, *, file_path: str | None = None, folder: str | None = None) -> Any:
        """Delete a file, or every file under a folder (DELETE /delete-file)."""
        return rest.delete_file(self._http, file_path=file_path, folder=folder)
