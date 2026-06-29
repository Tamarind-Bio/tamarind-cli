"""Typed wrappers over the Tamarind REST API (the job/file surface).

Every function here maps 1:1 onto an operation in ``openapi-mcp.yaml`` — the
same spec the Tamarind MCP server is built from. Keeping this a thin, literal
mapping (no business logic) is what keeps the CLI and the MCP from drifting on
the REST surface. Discovery/catalog calls live in :mod:`tamarind.catalog`.
"""

from __future__ import annotations

from typing import Any

from .errors import APIError
from .http import HTTPClient

# Query params that the API expects as the literal string "true" rather than a
# JSON boolean.
_TRUE = "true"


def submit_job(
    client: HTTPClient, *, job_name: str, job_type: str, settings: dict[str, Any]
) -> Any:
    """POST /submit-job — submit a single job. Body: {jobName, type, settings}."""
    return client.post_json(
        "submit-job",
        json={"jobName": job_name, "type": job_type, "settings": settings},
    )


def validate_job(
    client: HTTPClient, *, job_name: str, job_type: str, settings: dict[str, Any]
) -> dict:
    """POST /validate-job — returns {valid, normalized?, error?} (HTTP 200 either way)."""
    return client.post_json(
        "validate-job",
        json={"jobName": job_name, "type": job_type, "settings": settings},
    )


def submit_batch(
    client: HTTPClient,
    *,
    batch_name: str,
    job_type: str,
    settings: list[dict[str, Any]],
    job_names: list[str] | None = None,
    max_runtime_seconds: int | None = None,
) -> Any:
    """POST /submit-batch — submit many jobs as one batch."""
    body: dict[str, Any] = {
        "batchName": batch_name,
        "type": job_type,
        "settings": settings,
    }
    if job_names is not None:
        body["jobNames"] = job_names
    if max_runtime_seconds is not None:
        body["maxRuntimeSeconds"] = max_runtime_seconds
    return client.post_json("submit-batch", json=body)


def get_jobs(
    client: HTTPClient,
    *,
    job_name: str | None = None,
    batch: str | None = None,
    start_key: str | None = None,
    limit: int | None = None,
    organization: bool = False,
    include_subjobs: bool = False,
    job_email: str | None = None,
) -> Any:
    """GET /jobs — list jobs, or fetch one when ``job_name`` is given."""
    params = {
        "jobName": job_name,
        "batch": batch,
        "startKey": start_key,
        "limit": limit,
        "organization": _TRUE if organization else None,
        "includeSubjobs": _TRUE if include_subjobs else None,
        "jobEmail": job_email,
    }
    return client.get_json("jobs", params=params)


def get_result(
    client: HTTPClient,
    *,
    job_name: str,
    job_email: str | None = None,
    file_name: str | None = None,
    pdbs_only: bool | None = None,
) -> Any:
    """POST /result — returns an S3 presigned URL (string) for the result bundle."""
    body: dict[str, Any] = {"jobName": job_name}
    if job_email is not None:
        body["jobEmail"] = job_email
    if file_name is not None:
        body["fileName"] = file_name
    if pdbs_only is not None:
        body["pdbsOnly"] = pdbs_only
    return client.post_json("result", json=body)


def upload_file_url(client: HTTPClient, *, filename: str) -> dict:
    """POST /uploadFile — returns {signedUrl, filename}; PUT the bytes to signedUrl."""
    return client.post_json("uploadFile", json={"filename": filename})


def cancel_job(
    client: HTTPClient, *, job_name: str | None = None, job_id: str | None = None
) -> dict:
    """POST /cancelJob — soft-stop a queued/running job (preserves the row)."""
    body: dict[str, Any] = {}
    if job_name is not None:
        body["jobName"] = job_name
    if job_id is not None:
        body["jobId"] = job_id
    return client.post_json("cancelJob", json=body)


def cancel_batch(client: HTTPClient, *, batch_name: str) -> dict:
    """POST /cancelBatch — soft-stop every job in a batch or pipeline."""
    return client.post_json("cancelBatch", json={"batchName": batch_name})


def delete_job(client: HTTPClient, *, job_name: str) -> Any:
    """DELETE /delete-job — permanently remove a job (and subjobs, for batches).

    The endpoint may return a bare string (not JSON), so parse defensively.
    """
    return client.delete_json("delete-job", json={"jobName": job_name})


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
