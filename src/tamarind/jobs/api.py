"""Job endpoints: one function per operation, client in, payload out.

Every function maps onto an operation in ``openapi-mcp.yaml`` — the same server
contract the Tamarind MCP surface is built from. Keeping this layer thin and free
of branching is what keeps the two from drifting; contract tests and coordinated
releases remain necessary.

Decisions belong in `plan`, multi-step orchestration in `flow`.
"""

from __future__ import annotations

from typing import Any

from ..http import HTTPClient

# Query params the API expects as the literal string "true" rather than a JSON boolean.
_TRUE = "true"

# Stamped onto every job the CLI creates so the backend can attribute usage by
# origin (the MCP server sends "MCP"). Validation calls are NOT tagged — they
# don't create a job.
JOB_SOURCE = "CLI"


def submit_job(
    client: HTTPClient, *, job_name: str, job_type: str, settings: dict[str, Any]
) -> Any:
    """POST /submit-job — submit a single job. Body: {jobName, type, settings, jobSource}."""
    return client.post_json(
        "submit-job",
        json={
            "jobName": job_name,
            "type": job_type,
            "settings": settings,
            "jobSource": JOB_SOURCE,
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
        "jobSource": JOB_SOURCE,
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


def submit_job_pinned(
    client: HTTPClient,
    *,
    job_name: str,
    job_type: str,
    settings: dict[str, Any],
    tool_ref: str,
) -> Any:
    """POST v2/jobs — submit against a SPECIFIC custom-tool version.

    A separate function because it is a different endpoint, and the split is not
    cosmetic. The legacy `/submit-job` route stamps `jobSource` but carries no
    `toolRef`, so it can only ever run whatever version is currently live; this route
    carries both, which is what makes "deploy, then test exactly what I just built"
    possible at all.

    Used only when a caller names a version. An unpinned submit stays on the legacy
    route, so the common path is unchanged.
    """
    return client.post_json(
        "v2/jobs",
        json={
            "jobName": job_name,
            "type": job_type,
            "settings": settings,
            "toolRef": tool_ref,
            "jobSource": JOB_SOURCE,
        },
    )


def submit_batch_pinned(
    client: HTTPClient,
    *,
    jobs: list[dict[str, Any]],
    tool_ref: str | None = None,
) -> Any:
    """POST v2/jobs/batch — submit up to 500 jobs, each against a named version.

    Distinct from `submit_batch` in more than the endpoint. Legacy `/submit-batch`
    creates a batch PARENT row with N children anchored to it; this route dispatches
    N INDEPENDENT jobs and carries no parent. Callers must not treat the two as
    interchangeable — `status <batchName>` finds nothing after this one, because
    there is no such row to find.

    ``batch`` is deliberately left unset on every item. The field anchors children to
    a parent by name and the worker's aggregator reads its gate off that parent, so
    labelling parentless jobs with it would point the aggregator at a row that does
    not exist.

    Per-item failures come back as ``ok: false`` inside a 200. Parse with
    `wire.parse_batch_submission` and reconcile with `plan.summarize_batch`; do not
    read success off the HTTP status.
    """
    payload = []
    for job in jobs:
        item = dict(job)
        item["jobSource"] = JOB_SOURCE
        if tool_ref is not None:
            item.setdefault("toolRef", tool_ref)
        payload.append(item)
    return client.post_json("v2/jobs/batch", json={"jobs": payload})
