from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...models.archive_preparing import ArchivePreparing
from ...models.archive_ready import ArchiveReady
from ...models.archive_request import ArchiveRequest
from ...models.problem import Problem
from ...types import UNSET, Response, Unset


def _get_kwargs(
    job_id: str,
    *,
    body: ArchiveRequest | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(tamarind_version, Unset):
        headers["Tamarind-Version"] = tamarind_version

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/jobs/{job_id}/archive".format(
            job_id=quote(str(job_id), safe=""),
        ),
    }

    if not isinstance(body, Unset):
        _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ArchivePreparing | ArchiveReady | Problem:
    if response.status_code == 200:
        response_200 = ArchiveReady.from_dict(response.json())

        return response_200

    if response.status_code == 202:
        response_202 = ArchivePreparing.from_dict(response.json())

        return response_202

    if response.status_code == 400:
        response_400 = Problem.from_dict(response.json())

        return response_400

    if response.status_code == 401:
        response_401 = Problem.from_dict(response.json())

        return response_401

    if response.status_code == 403:
        response_403 = Problem.from_dict(response.json())

        return response_403

    if response.status_code == 404:
        response_404 = Problem.from_dict(response.json())

        return response_404

    if response.status_code == 409:
        response_409 = Problem.from_dict(response.json())

        return response_409

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
) -> Response[ArchivePreparing | ArchiveReady | Problem]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    job_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: ArchiveRequest | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Response[ArchivePreparing | ArchiveReady | Problem]:
    r"""Get a zip of a job's or a batch's outputs

     Takes a `job_` or `batch_` id; a `run_` id is 404 (use `archivePipelineRun`). Serves the
    stored archive the job's worker wrote, the one today's `POST /result` serves. 200 means ready,
    with a link that expires in 1 hour, its expiry, the size and the real `fileCount`, read from
    the zip itself. `truncated` is false, since a stored archive is never cut short. 202 means
    still preparing: the job or batch is still running, by the status `getJob` shows (a batch's is
    its jobs'; a single-tool pipeline run's job is its run's), or a `Complete` batch's archive is
    being rebuilt. Call again after
    `retryAfterSeconds`, which `Retry-After` also carries. 409 `archive_failed` when it ended
    `Stopped` or `Failed` (only `Complete` work has an archive), when a single job has no stored
    archive (list its files with `listJobFiles` instead), when a rebuild ended without one, or
    when the stored zip is damaged. If storage fails while the zip is read, the answer is 503
    `jobs_dependency_unavailable`; retry.

    `paths` or `glob` (one of them) chooses files: the answer
    is a zip of just those files of that archive, copied from it as they are. `paths` are paths
    inside the archive: a job's are the paths `listJobFiles` shows, and a batch's archive holds
    each of its jobs' files under the job's name, plus its combined files. `glob` matches the
    whole path (`*` spans `/`, case-sensitive). The zip is kept beside the archive, and asking
    again answers the same one. A path the archive has no file at is 422 `file_not_found` at
    `/paths/<i>` (each one), and a `glob` that matches nothing is 422 `file_not_found` at
    `/glob`. More than 10,000 files, or a zip of more than 1 GiB, is 422 `out_of_range` at the
    field: nothing is cut short, so `truncated` stays false. Sending both is 422 `conditional_not_met`
    at `/glob`. A selection of every file answers the whole archive.

    `bestStructures: true` answers one best structure per job, as the app's \"PDBs only\" download
    does (see `ArchiveRequest`). A job or a design batch (`numDesigns`) without a stored structures
    zip is 422 `not_supported`. When a batch submitted as a batch has none, one is built: past an
    8-minute deadline the answer is 503 `jobs_dependency_unavailable` (retryable), a second build
    from your account while one runs is 429 `rate_limited`, and a server already running two is
    503 `service_unavailable`.

    When a batch's archive would be rebuilt, an organization that has lost read access gets 403
    `organization_export_disabled`. In practice v1 refuses such an organization at authentication
    first, with 403 `organization_read_disabled`.

    Another member's job or batch follows today's `/result` rule for a key (decision 74, and
    Authentication in the introduction), a batch only when that rule admits every job in it, and
    one that rule refuses is the same 404.

    Args:
        job_id (str):
        tamarind_version (str | Unset):
        body (ArchiveRequest | Unset): Send at most one of `paths`, `glob` and `bestStructures`;
            send none for the whole archive.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ArchivePreparing | ArchiveReady | Problem]
    """

    kwargs = _get_kwargs(
        job_id=job_id,
        body=body,
        tamarind_version=tamarind_version,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    job_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: ArchiveRequest | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> ArchivePreparing | ArchiveReady | Problem | None:
    r"""Get a zip of a job's or a batch's outputs

     Takes a `job_` or `batch_` id; a `run_` id is 404 (use `archivePipelineRun`). Serves the
    stored archive the job's worker wrote, the one today's `POST /result` serves. 200 means ready,
    with a link that expires in 1 hour, its expiry, the size and the real `fileCount`, read from
    the zip itself. `truncated` is false, since a stored archive is never cut short. 202 means
    still preparing: the job or batch is still running, by the status `getJob` shows (a batch's is
    its jobs'; a single-tool pipeline run's job is its run's), or a `Complete` batch's archive is
    being rebuilt. Call again after
    `retryAfterSeconds`, which `Retry-After` also carries. 409 `archive_failed` when it ended
    `Stopped` or `Failed` (only `Complete` work has an archive), when a single job has no stored
    archive (list its files with `listJobFiles` instead), when a rebuild ended without one, or
    when the stored zip is damaged. If storage fails while the zip is read, the answer is 503
    `jobs_dependency_unavailable`; retry.

    `paths` or `glob` (one of them) chooses files: the answer
    is a zip of just those files of that archive, copied from it as they are. `paths` are paths
    inside the archive: a job's are the paths `listJobFiles` shows, and a batch's archive holds
    each of its jobs' files under the job's name, plus its combined files. `glob` matches the
    whole path (`*` spans `/`, case-sensitive). The zip is kept beside the archive, and asking
    again answers the same one. A path the archive has no file at is 422 `file_not_found` at
    `/paths/<i>` (each one), and a `glob` that matches nothing is 422 `file_not_found` at
    `/glob`. More than 10,000 files, or a zip of more than 1 GiB, is 422 `out_of_range` at the
    field: nothing is cut short, so `truncated` stays false. Sending both is 422 `conditional_not_met`
    at `/glob`. A selection of every file answers the whole archive.

    `bestStructures: true` answers one best structure per job, as the app's \"PDBs only\" download
    does (see `ArchiveRequest`). A job or a design batch (`numDesigns`) without a stored structures
    zip is 422 `not_supported`. When a batch submitted as a batch has none, one is built: past an
    8-minute deadline the answer is 503 `jobs_dependency_unavailable` (retryable), a second build
    from your account while one runs is 429 `rate_limited`, and a server already running two is
    503 `service_unavailable`.

    When a batch's archive would be rebuilt, an organization that has lost read access gets 403
    `organization_export_disabled`. In practice v1 refuses such an organization at authentication
    first, with 403 `organization_read_disabled`.

    Another member's job or batch follows today's `/result` rule for a key (decision 74, and
    Authentication in the introduction), a batch only when that rule admits every job in it, and
    one that rule refuses is the same 404.

    Args:
        job_id (str):
        tamarind_version (str | Unset):
        body (ArchiveRequest | Unset): Send at most one of `paths`, `glob` and `bestStructures`;
            send none for the whole archive.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ArchivePreparing | ArchiveReady | Problem
    """

    return sync_detailed(
        job_id=job_id,
        client=client,
        body=body,
        tamarind_version=tamarind_version,
    ).parsed


async def asyncio_detailed(
    job_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: ArchiveRequest | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> Response[ArchivePreparing | ArchiveReady | Problem]:
    r"""Get a zip of a job's or a batch's outputs

     Takes a `job_` or `batch_` id; a `run_` id is 404 (use `archivePipelineRun`). Serves the
    stored archive the job's worker wrote, the one today's `POST /result` serves. 200 means ready,
    with a link that expires in 1 hour, its expiry, the size and the real `fileCount`, read from
    the zip itself. `truncated` is false, since a stored archive is never cut short. 202 means
    still preparing: the job or batch is still running, by the status `getJob` shows (a batch's is
    its jobs'; a single-tool pipeline run's job is its run's), or a `Complete` batch's archive is
    being rebuilt. Call again after
    `retryAfterSeconds`, which `Retry-After` also carries. 409 `archive_failed` when it ended
    `Stopped` or `Failed` (only `Complete` work has an archive), when a single job has no stored
    archive (list its files with `listJobFiles` instead), when a rebuild ended without one, or
    when the stored zip is damaged. If storage fails while the zip is read, the answer is 503
    `jobs_dependency_unavailable`; retry.

    `paths` or `glob` (one of them) chooses files: the answer
    is a zip of just those files of that archive, copied from it as they are. `paths` are paths
    inside the archive: a job's are the paths `listJobFiles` shows, and a batch's archive holds
    each of its jobs' files under the job's name, plus its combined files. `glob` matches the
    whole path (`*` spans `/`, case-sensitive). The zip is kept beside the archive, and asking
    again answers the same one. A path the archive has no file at is 422 `file_not_found` at
    `/paths/<i>` (each one), and a `glob` that matches nothing is 422 `file_not_found` at
    `/glob`. More than 10,000 files, or a zip of more than 1 GiB, is 422 `out_of_range` at the
    field: nothing is cut short, so `truncated` stays false. Sending both is 422 `conditional_not_met`
    at `/glob`. A selection of every file answers the whole archive.

    `bestStructures: true` answers one best structure per job, as the app's \"PDBs only\" download
    does (see `ArchiveRequest`). A job or a design batch (`numDesigns`) without a stored structures
    zip is 422 `not_supported`. When a batch submitted as a batch has none, one is built: past an
    8-minute deadline the answer is 503 `jobs_dependency_unavailable` (retryable), a second build
    from your account while one runs is 429 `rate_limited`, and a server already running two is
    503 `service_unavailable`.

    When a batch's archive would be rebuilt, an organization that has lost read access gets 403
    `organization_export_disabled`. In practice v1 refuses such an organization at authentication
    first, with 403 `organization_read_disabled`.

    Another member's job or batch follows today's `/result` rule for a key (decision 74, and
    Authentication in the introduction), a batch only when that rule admits every job in it, and
    one that rule refuses is the same 404.

    Args:
        job_id (str):
        tamarind_version (str | Unset):
        body (ArchiveRequest | Unset): Send at most one of `paths`, `glob` and `bestStructures`;
            send none for the whole archive.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ArchivePreparing | ArchiveReady | Problem]
    """

    kwargs = _get_kwargs(
        job_id=job_id,
        body=body,
        tamarind_version=tamarind_version,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    job_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: ArchiveRequest | Unset = UNSET,
    tamarind_version: str | Unset = UNSET,
) -> ArchivePreparing | ArchiveReady | Problem | None:
    r"""Get a zip of a job's or a batch's outputs

     Takes a `job_` or `batch_` id; a `run_` id is 404 (use `archivePipelineRun`). Serves the
    stored archive the job's worker wrote, the one today's `POST /result` serves. 200 means ready,
    with a link that expires in 1 hour, its expiry, the size and the real `fileCount`, read from
    the zip itself. `truncated` is false, since a stored archive is never cut short. 202 means
    still preparing: the job or batch is still running, by the status `getJob` shows (a batch's is
    its jobs'; a single-tool pipeline run's job is its run's), or a `Complete` batch's archive is
    being rebuilt. Call again after
    `retryAfterSeconds`, which `Retry-After` also carries. 409 `archive_failed` when it ended
    `Stopped` or `Failed` (only `Complete` work has an archive), when a single job has no stored
    archive (list its files with `listJobFiles` instead), when a rebuild ended without one, or
    when the stored zip is damaged. If storage fails while the zip is read, the answer is 503
    `jobs_dependency_unavailable`; retry.

    `paths` or `glob` (one of them) chooses files: the answer
    is a zip of just those files of that archive, copied from it as they are. `paths` are paths
    inside the archive: a job's are the paths `listJobFiles` shows, and a batch's archive holds
    each of its jobs' files under the job's name, plus its combined files. `glob` matches the
    whole path (`*` spans `/`, case-sensitive). The zip is kept beside the archive, and asking
    again answers the same one. A path the archive has no file at is 422 `file_not_found` at
    `/paths/<i>` (each one), and a `glob` that matches nothing is 422 `file_not_found` at
    `/glob`. More than 10,000 files, or a zip of more than 1 GiB, is 422 `out_of_range` at the
    field: nothing is cut short, so `truncated` stays false. Sending both is 422 `conditional_not_met`
    at `/glob`. A selection of every file answers the whole archive.

    `bestStructures: true` answers one best structure per job, as the app's \"PDBs only\" download
    does (see `ArchiveRequest`). A job or a design batch (`numDesigns`) without a stored structures
    zip is 422 `not_supported`. When a batch submitted as a batch has none, one is built: past an
    8-minute deadline the answer is 503 `jobs_dependency_unavailable` (retryable), a second build
    from your account while one runs is 429 `rate_limited`, and a server already running two is
    503 `service_unavailable`.

    When a batch's archive would be rebuilt, an organization that has lost read access gets 403
    `organization_export_disabled`. In practice v1 refuses such an organization at authentication
    first, with 403 `organization_read_disabled`.

    Another member's job or batch follows today's `/result` rule for a key (decision 74, and
    Authentication in the introduction), a batch only when that rule admits every job in it, and
    one that rule refuses is the same 404.

    Args:
        job_id (str):
        tamarind_version (str | Unset):
        body (ArchiveRequest | Unset): Send at most one of `paths`, `glob` and `bestStructures`;
            send none for the whole archive.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ArchivePreparing | ArchiveReady | Problem
    """

    return (
        await asyncio_detailed(
            job_id=job_id,
            client=client,
            body=body,
            tamarind_version=tamarind_version,
        )
    ).parsed
