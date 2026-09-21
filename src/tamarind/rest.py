"""Typed wrappers over the Tamarind REST API (the job/file surface).

Every function here maps onto an operation in ``openapi-mcp.yaml`` — the same
server contract used by the Tamarind MCP surface. Keeping this mapping thin and
free of business logic reduces drift; contract tests and coordinated releases
remain necessary. Discovery/catalog calls live in :mod:`tamarind.catalog`.
"""

from __future__ import annotations

from typing import Any, NamedTuple

import httpx

from .errors import APIError
from .http import HTTPClient, map_error, parse_json, response_problem_code

# Query params that the API expects as the literal string "true" rather than a
# JSON boolean.
_TRUE = "true"

# Stamped onto every job the CLI creates so the backend can attribute usage by
# origin (the MCP server sends "MCP"). Validation calls are NOT tagged — they
# don't create a job.
_JOB_SOURCE = "CLI"


class _Reroute(NamedTuple):
    """One row of the finetune routing table."""

    alternate: str  # the sibling route to resend to
    rename_from: str  # the tool-name key this route uses
    rename_to: str  # the tool-name key the sibling route uses
    problem_code: str  # the 400 code that means "wrong route"
    on_404: bool  # whether an exact 404 also means "wrong route"


# Which tools are finetuning tools is knowable only SERVER-side, and /finetune
# did not exist before the route shipped. So a submission that lands on the wrong
# sibling route is resent ONCE to the right one, in both directions, from this
# one table. Both directions read the same rows, so they cannot drift apart.
#
# Exactly ONE resend, never a loop: a resent request that is refused again returns
# that second answer as-is. Only an explicit 400 problem code triggers a resend —
# plus, for the /finetune* rows, an exact 404, which is a deployment that predates
# the route and is the reason this is safe to ship before the server side lands.
#
# A 5xx, a timeout, and a network error NEVER trigger one: that request may
# already have created a job, and resending it would submit twice. Network errors
# raise out of ``HTTPClient.send`` before any branch here can see them.
_FINETUNE_ROUTING: dict[str, _Reroute] = {
    "submit-job": _Reroute("finetune", "type", "model", "use_finetune_endpoint", False),
    "submit-batch": _Reroute(
        "finetune-batch", "type", "model", "use_finetune_endpoint", False
    ),
    "finetune": _Reroute("submit-job", "model", "type", "not_a_finetune_tool", True),
    "finetune-batch": _Reroute(
        "submit-batch", "model", "type", "not_a_finetune_tool", True
    ),
}


def _should_reroute(resp: httpx.Response, route: _Reroute) -> bool:
    """Whether this refusal means "you sent it to the wrong route", and nothing else."""
    if resp.status_code == 404:
        return route.on_404
    if resp.status_code != 400:
        return False
    return response_problem_code(resp) == route.problem_code


def _rerouted_body(body: dict[str, Any], route: _Reroute) -> dict[str, Any]:
    """The same body with ONLY the tool-name key renamed; every other field is kept."""
    return {
        (route.rename_to if key == route.rename_from else key): value
        for key, value in body.items()
    }


def _post_submission(client: HTTPClient, path: str, body: dict[str, Any]) -> Any:
    """POST a submission, resending it ONCE to the sibling route if the server says so."""
    resp = client.send("POST", path, json=body)
    if resp.is_success:
        return parse_json(resp)
    # A route with no row simply never reroutes. Looking it up with [] instead would
    # raise KeyError over whatever the server actually said, turning a real API error
    # into a crash for the next caller that posts through here.
    route = _FINETUNE_ROUTING.get(path)
    if route is None or not _should_reroute(resp, route):
        raise map_error(resp, request_path=path)
    resent = client.send("POST", route.alternate, json=_rerouted_body(body, route))
    if resent.is_success:
        return parse_json(resent)
    raise map_error(resent, request_path=route.alternate)


def submit_job(
    client: HTTPClient, *, job_name: str, job_type: str, settings: dict[str, Any]
) -> Any:
    """POST /submit-job — submit a single job. Body: {jobName, type, settings, jobSource}."""
    return _post_submission(
        client,
        "submit-job",
        {
            "jobName": job_name,
            "type": job_type,
            "settings": settings,
            "jobSource": _JOB_SOURCE,
        },
    )


def submit_finetune(
    client: HTTPClient, *, job_name: str, model: str, settings: dict[str, Any]
) -> Any:
    """POST /finetune — submit one finetuning job. Body: {jobName, model, settings, jobSource}."""
    return _post_submission(
        client,
        "finetune",
        {
            "jobName": job_name,
            "model": model,
            "settings": settings,
            "jobSource": _JOB_SOURCE,
        },
    )


def validate_job(
    client: HTTPClient, *, job_name: str, job_type: str, settings: dict[str, Any]
) -> dict:
    """POST /validate-job — returns {valid, normalized?, error?} (HTTP 200 either way)."""
    return client.post_json(
        "validate-job",
        json={"jobName": job_name, "type": job_type, "settings": settings},
    )


# How many settings rows /validate-job accepts in ONE request, and how many bytes.
# Both bounds are the server's, and with large payloads the byte bound binds first:
# over ~4.5 MB the platform answers a bare 413 with no JSON body at all, ahead of the
# endpoint, so there is nothing to parse and nothing to explain. 3.5 MB leaves room
# for the envelope and the jobNames array alongside the rows.
VALIDATE_BATCH_MAX_ROWS = 1000
VALIDATE_BATCH_MAX_BYTES = 3_500_000


def validate_jobs(
    client: HTTPClient,
    *,
    job_type: str,
    settings: list[dict[str, Any]],
    job_names: list[str] | None = None,
) -> dict:
    """POST /validate-job with an ARRAY — one verdict per row, in ONE request.

    Every row is validated; nothing is sampled. What batching removes is the
    per-request cost, not the checking.

    Two response shapes, and they must be told apart by whether ``results`` is
    PRESENT, not by ``valid``:
      - ``{valid, count, valid_count, results: [{index, valid, ...}]}`` — the rows
        were judged and ``index`` is the row's position in ``settings``.
      - ``{valid: false, error}`` with NO ``results`` — the whole request was
        refused (out of quota, over the row cap, a bad ``jobNames``).
    """
    body: dict[str, Any] = {"type": job_type, "settings": settings}
    if job_names is not None:
        body["jobNames"] = job_names
    return client.post_json("validate-job", json=body)


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
        "jobSource": _JOB_SOURCE,
    }
    if job_names is not None:
        body["jobNames"] = job_names
    if max_runtime_seconds is not None:
        body["maxRuntimeSeconds"] = max_runtime_seconds
    return _post_submission(client, "submit-batch", body)


def submit_finetune_batch(
    client: HTTPClient,
    *,
    batch_name: str,
    model: str,
    settings: list[dict[str, Any]],
    job_names: list[str] | None = None,
    max_runtime_seconds: int | None = None,
) -> Any:
    """POST /finetune-batch — submit many finetuning jobs as one batch."""
    body: dict[str, Any] = {
        "batchName": batch_name,
        "model": model,
        "settings": settings,
        "jobSource": _JOB_SOURCE,
    }
    if job_names is not None:
        body["jobNames"] = job_names
    if max_runtime_seconds is not None:
        body["maxRuntimeSeconds"] = max_runtime_seconds
    return _post_submission(client, "finetune-batch", body)


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
    timeout: float | None = None,
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
    return client.get_json("jobs", params=params, timeout=timeout)


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


def upload_file_url(
    client: HTTPClient, *, filename: str, content_type: str = "application/octet-stream"
) -> dict:
    """POST /getPresignedUploadUrl — returns {uploadUrl, headUrl, key, bucket}.

    PUT the file bytes directly to ``uploadUrl`` with a matching ``Content-Type``
    header (the presigned signature covers the content type). This uploads
    straight to S3, bypassing the API's request-body size limit.
    """
    return client.post_json(
        "getPresignedUploadUrl", json={"filename": filename, "contentType": content_type}
    )


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
