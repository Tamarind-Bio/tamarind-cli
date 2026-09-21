"""Job lifecycle commands: submit/validate/batch/jobs/status/wait/results/logs/cancel/delete."""

from __future__ import annotations

import json
import re
import tempfile
import uuid
from pathlib import Path
from typing import NamedTuple, Optional
from urllib.parse import parse_qsl, urlsplit

import httpx
import typer

from ... import jobs as jobs_helpers
from ... import rest
from ...errors import ExitCode, NotFoundError, TamarindError, ValidationError
from .. import output
from ..guidance import rewrite_validation_guidance
from ..inputs import effective_job_name, effective_job_type, resolve_job_input


def _gen_name(tool: str) -> str:
    return f"{tool}-{uuid.uuid4().hex[:8]}"


def _message(resp: object) -> str:
    """Best-effort human message from a response that may be a dict or a string."""
    if isinstance(resp, dict):
        return str(resp.get("message", resp))
    return str(resp)


def _result_url(response: object) -> str:
    """Extract a presigned URL without echoing an invalid response body."""
    response_type = type(response).__name__
    if isinstance(response, str) and response:
        return response
    if isinstance(response, dict):
        for key in ("url", "downloadUrl", "presignedUrl"):
            value = response.get(key)
            if isinstance(value, str) and value:
                return value
    raise TamarindError(
        "Result API did not return a download URL.",
        detail={"responseType": response_type},
    )


def _download(url: str, dest: Path) -> int:
    """Stream a presigned URL atomically to ``dest``. Returns bytes written.

    Transfer failures become a clean :class:`TamarindError` and never include
    the presigned URL (which may contain credentials). An existing destination
    is left untouched unless the complete replacement download succeeds.
    """
    total = 0
    temp_path: Path | None = None
    replaced = False

    def discard_partial() -> None:
        if temp_path is not None:
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                pass

    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        with httpx.stream("GET", url, follow_redirects=True, timeout=300.0) as resp:
            resp.raise_for_status()
            with tempfile.NamedTemporaryFile(
                mode="wb",
                dir=dest.parent,
                prefix=f".{dest.name}.",
                suffix=".part",
                delete=False,
            ) as fh:
                temp_path = Path(fh.name)
                for chunk in resp.iter_bytes():
                    fh.write(chunk)
                    total += len(chunk)
        temp_path.replace(dest)
        replaced = True
    except httpx.HTTPStatusError as exc:
        raise TamarindError(
            f"Result download failed with HTTP {exc.response.status_code}.",
            detail={"type": type(exc).__name__, "statusCode": exc.response.status_code},
        ) from exc
    except (httpx.HTTPError, httpx.InvalidURL, httpx.StreamError) as exc:
        raise TamarindError(
            "Result download failed due to a network error.",
            detail={"type": type(exc).__name__},
        ) from exc
    except OSError as exc:
        raise TamarindError(
            f"Could not write downloaded results to '{dest}'.",
            detail={"type": type(exc).__name__, "errno": exc.errno},
        ) from exc
    finally:
        if not replaced:
            discard_partial()
    return total


def _failed_terminal(job: dict) -> bool:
    """Whether a returned terminal job represents an unsuccessful run."""
    status = jobs_helpers.job_status(job)
    return jobs_helpers.is_terminal(status) and not jobs_helpers.is_success(status)


def _outcome_is_ambiguous(exc: TamarindError) -> bool:
    """Whether a failed submission may still have created the job remotely.

    A bare ``TamarindError`` is the transport's network/timeout failure — the
    request may well have been received — and so is any 5xx. Anything the server
    classified (a 400, a 403) definitively created nothing.
    """
    status_code = getattr(exc, "status_code", None)
    return type(exc) is TamarindError or (
        isinstance(status_code, int) and status_code >= 500
    )


def _attach_error_context(exc: TamarindError, **context: object) -> TamarindError:
    """Add recovery metadata without changing the exception's stable exit code."""
    detail = dict(exc.detail) if isinstance(exc.detail, dict) else {}
    if exc.detail is not None and not isinstance(exc.detail, dict):
        detail["upstreamDetail"] = exc.detail
    detail.update(context)
    exc.detail = detail
    return exc


_SENSITIVE_JOB_URL_KEYS = {
    "resulturl",
    "downloadurl",
    "presignedurl",
    "uploadurl",
    "headurl",
}

_SENSITIVE_QUERY_NAMES = {
    "awsaccesskeyid",
    "googleaccessid",
    "policy",
    "sig",
    "signature",
    "token",
}


def _normalized_key(key: object) -> str:
    return re.sub(r"[^a-z0-9]", "", str(key).lower())


def _is_credential_url(value: object) -> bool:
    """Return whether a string is an HTTP(S) URL carrying auth query data."""
    if not isinstance(value, str):
        return False
    try:
        parsed = urlsplit(value.strip())
    except ValueError:
        return False
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc:
        return False
    names = {name.lower() for name, _ in parse_qsl(parsed.query, keep_blank_values=True)}
    return any(
        name in _SENSITIVE_QUERY_NAMES
        or name.startswith(("x-amz-", "x-goog-", "x-ms-"))
        or name.endswith(("signature", "credential", "security-token"))
        for name in names
    )


def _with_redactions(cleaned: dict, removed: list[str]) -> dict:
    if not removed:
        return cleaned
    existing = cleaned.get("redactedFields")
    if existing is None or (
        isinstance(existing, list) and all(isinstance(item, str) for item in existing)
    ):
        cleaned["redactedFields"] = sorted(set((existing or []) + removed))
    else:
        # Never overwrite an upstream field that happens to use our metadata
        # name. Keep our redaction audit under a collision-safe key.
        cleaned["tamarindRedactedFields"] = sorted(set(removed))
    return cleaned


def _sanitize_job_output(value: object) -> object:
    """Remove credential-bearing transfer URLs from ordinary job output."""
    if isinstance(value, list):
        return [_sanitize_job_output(item) for item in value]
    if _is_credential_url(value):
        return "<redacted credential URL>"
    if not isinstance(value, dict):
        return value
    sanitized = {}
    removed = []
    for key, item in value.items():
        normalized = _normalized_key(key)
        if normalized in _SENSITIVE_JOB_URL_KEYS or (
            _is_credential_url(item)
            and (normalized.endswith(("url", "uri", "link", "location"))
                 or "signed" in normalized)
        ):
            removed.append(str(key))
            continue
        sanitized[key] = _sanitize_job_output(item)
    return _with_redactions(sanitized, removed)


def _rewrite_validation_guidance(value: object) -> object:
    """Rewrite only server-authored validation errors, not user settings text."""
    if not isinstance(value, dict) or not isinstance(value.get("error"), str):
        return value
    rewritten = dict(value)
    rewritten["error"] = rewrite_validation_guidance(rewritten["error"])
    return rewritten


def _chunk_for_validate(
    settings_list: list, *, job_type: str = "", names: "list | None" = None
) -> "list[tuple[int, list]]":
    """Split rows into calls bounded by BOTH the row cap and the body-size cap.

    The row cap alone is not enough: a batch of large payloads crosses the ~4.5 MB
    request limit well before 1000 rows, and that failure arrives as a bare 413 from
    the platform with no JSON body to report.

    Measures the WHOLE body ``validate_jobs`` will send — `type` and one `jobNames`
    entry per row ride along with the rows, and a budget that ignores them is not the
    budget the edge applies.
    """
    def fits(offset: int, count: int) -> bool:
        body: dict = {"type": job_type, "settings": settings_list[offset : offset + count]}
        if names is not None:
            body["jobNames"] = names[offset : offset + count]
        return len(json.dumps(body).encode()) <= rest.VALIDATE_BATCH_MAX_BYTES

    chunks: list[tuple[int, list]] = []
    offset, total = 0, len(settings_list)
    while offset < total:
        hi = min(rest.VALIDATE_BATCH_MAX_ROWS, total - offset)
        if fits(offset, hi):
            count = hi
        else:
            # The largest prefix that fits. Halving would overshoot — if 600 rows fit it
            # settles for 500 — and every extra request is one the caller did not need.
            # `lo` starts at 1, so a single row too large to split is still sent and the
            # server gets to answer for it.
            lo = 1
            while lo < hi:
                mid = (lo + hi + 1) // 2
                if fits(offset, mid):
                    lo = mid
                else:
                    hi = mid - 1
            count = lo
        chunks.append((offset, settings_list[offset : offset + count]))
        offset += count
    return chunks


def _prevalidate_batch(
    client, *, batch_name: str, job_type: str, settings_list: list, job_names
) -> None:
    """Pre-flight every row of a batch, in as FEW requests as possible.

    This was one request per job. At campaign scale that SHAPE is the failure: a
    10,000-job batch meant 10,000 POSTs from one address, which edge rate limiting
    refuses — 429s first, then an address-wide block answering 403 on every endpoint
    until it expires — long before it is a load problem for the server. /validate-job
    takes the whole array and still checks every row, so nothing is sampled and only
    the per-request cost is gone.

    Raises ValidationError on the first invalid row, identified by its index in the
    ORIGINAL list — chunking must not renumber it.
    """
    names = [
        str(
            job_names[index]
            if isinstance(job_names, list) and index < len(job_names) and job_names[index]
            else f"{batch_name}-{index + 1}"
        )
        for index in range(len(settings_list))
    ]

    def _row_index(row: dict) -> int:
        value = row.get("index")
        return value if isinstance(value, int) and not isinstance(value, bool) else 0

    for offset, rows in _chunk_for_validate(settings_list, job_type=job_type, names=names):
        response = rest.validate_jobs(
            client,
            job_type=job_type,
            settings=rows,
            job_names=names[offset : offset + len(rows)],
        )
        results = response.get("results") if isinstance(response, dict) else None
        if not isinstance(results, list):
            # No per-row verdicts means the request was refused AS A WHOLE — out of
            # quota, over a cap, a bad jobNames. Pinning that on row 0 would send the
            # caller off to fix a payload that is fine.
            reason = (
                response.get("error", "unknown error")
                if isinstance(response, dict)
                else "unexpected validation response"
            )
            raise ValidationError(
                f"Batch validation was refused: {rewrite_validation_guidance(str(reason))}",
                detail={"batchName": batch_name, "validation": response},
            )
        # One verdict per row is the contract. Fewer, or entries with no usable index,
        # means rows went unjudged — and "no invalid rows" would then be a false pass on
        # the ones never checked. That is the one direction a pre-flight must not fail
        # in, because the caller acts on it by spending compute.
        judged = {
            r["index"]
            for r in results
            if isinstance(r, dict)
            and isinstance(r.get("index"), int)
            and not isinstance(r["index"], bool)
        }
        if judged != set(range(len(rows))):
            raise ValidationError(
                f"Batch validation answered for {len(judged)} of {len(rows)} rows; "
                f"refusing to submit jobs it did not check.",
                detail={"batchName": batch_name, "offset": offset, "validation": response},
            )
        invalid = [r for r in results if isinstance(r, dict) and not r.get("valid")]
        if invalid:
            # The FIRST bad row in input order, which is what the per-job loop reported.
            row = min(invalid, key=_row_index)
            index = offset + _row_index(row)
            validation = _rewrite_validation_guidance(row)
            error = (
                validation.get("error", "unknown error")
                if isinstance(validation, dict)
                else "unexpected validation response"
            )
            raise ValidationError(
                f"Batch item {index + 1} settings invalid: {error}",
                detail={
                    "index": index,
                    "jobName": names[index] if index < len(names) else None,
                    "validation": validation,
                },
            )


# Safety bound on `jobs --all` so a runaway cursor can't loop forever.
_MAX_AUTO_PAGES = 100


def _fetch_all_jobs(client, **kwargs):
    """Follow the ``startKey`` cursor, accumulating every job (bounded by a page cap).

    Returns ``(jobs, statuses, next_key, pages)``. ``next_key`` is non-None only if
    the page cap was hit before the cursor ran out — surface it so the caller can
    resume with ``--start-key``. ``statuses`` is recomputed from the full set (the
    server's per-response ``statuses`` only counts that page).
    """
    all_jobs: list = []
    key = kwargs.pop("start_key", None)
    pages = 0
    while True:
        resp = rest.get_jobs(client, start_key=key, **kwargs)
        all_jobs.extend(resp.get("jobs", resp if isinstance(resp, list) else []))
        key = resp.get("startKey") if isinstance(resp, dict) else None
        pages += 1
        if not key or pages >= _MAX_AUTO_PAGES:
            break
    statuses: dict = {}
    for j in all_jobs:
        statuses[jobs_helpers.job_status(j) or "Unknown"] = (
            statuses.get(jobs_helpers.job_status(j) or "Unknown", 0) + 1
        )
    return all_jobs, statuses, key, pages


class _BatchInput(NamedTuple):
    batch_name: str
    tool: str
    settings_list: list
    job_names: object


def _resolve_batch_document(
    input: str,
    *,
    tool: str,
    name: Optional[str],
    max_runtime: Optional[int],
    tool_key: str = "type",
) -> _BatchInput:
    """Parse and fully validate a batch ``--input`` document before any remote call.

    ``tool_key`` is the document field that may override the tool on the command
    line — ``type`` for an ordinary batch, ``model`` for a finetuning batch — so
    both commands enforce one set of rules instead of two that can drift.
    """
    from ..inputs import _load_text, _parse_document  # internal reuse

    doc = _parse_document(_load_text(input))
    batch_name = effective_job_name(name, None) or _gen_name(tool)
    job_type = tool
    job_names = None
    if isinstance(doc, list):
        settings_list = doc
    elif isinstance(doc, dict) and isinstance(doc.get("settings"), list):
        settings_list = doc["settings"]
        batch_name = effective_job_name(name, doc.get("batchName")) or batch_name
        job_type = effective_job_type(tool, doc.get(tool_key), tool_key=tool_key)
        job_names = doc.get("jobNames")
    else:
        raise TamarindError("Batch --input must be a list of settings or a {settings:[...]} object.")
    if not isinstance(batch_name, str) or not batch_name.strip():
        raise ValidationError("Batch name must be a non-empty string.")
    if batch_name != batch_name.strip():
        raise ValidationError("Batch name may not have leading or trailing whitespace.")
    if max_runtime is not None and max_runtime <= 0:
        raise ValidationError("Batch max runtime must be greater than zero.")
    if not settings_list:
        raise ValidationError("Batch settings list may not be empty.")
    for index, settings in enumerate(settings_list):
        if not isinstance(settings, dict):
            raise ValidationError(
                f"Batch settings item {index + 1} must be an object, "
                f"not {type(settings).__name__}."
            )
    if job_names is not None and (
        not isinstance(job_names, list) or len(job_names) != len(settings_list)
    ):
        raise ValidationError("Batch jobNames must be a list with one name per settings item.")
    if isinstance(job_names, list):
        if any(not isinstance(job_name, str) or not job_name.strip() for job_name in job_names):
            raise ValidationError("Every batch jobName must be a non-empty string.")
        if any(job_name != job_name.strip() for job_name in job_names):
            raise ValidationError(
                "Batch jobNames may not have leading or trailing whitespace."
            )
        normalized_names = [job_name.strip() for job_name in job_names]
        if len(set(normalized_names)) != len(normalized_names):
            raise ValidationError("Batch jobNames must be unique.")
    return _BatchInput(batch_name, job_type, settings_list, job_names)


def register(app: typer.Typer) -> None:
    @app.command()
    def validate(
        ctx: typer.Context,
        tool: str = typer.Argument(..., help="Tool name (e.g. 'boltz')."),
        input: Optional[str] = typer.Option(None, "--input", "-i", help="Settings file (YAML/JSON), '-' for stdin, or @yaml://path."),
        set_: list[str] = typer.Option([], "--set", help="Override a setting: key=value (repeatable)."),
        name: Optional[str] = typer.Option(None, "--name", "-n", help="Job name (default: auto)."),
    ) -> None:
        """Validate a job's settings without submitting (catches errors early)."""
        state = ctx.obj
        job = resolve_job_input(input, set_)
        job_type = effective_job_type(tool, job.job_type)
        job_name = effective_job_name(name, job.job_name) or _gen_name(tool)
        with state.rest_client() as client:
            result = _rewrite_validation_guidance(
                rest.validate_job(
                    client,
                    job_name=job_name,
                    job_type=job_type,
                    settings=job.settings,
                )
            )
        valid = bool(result.get("valid"))
        human = "valid ✓" if valid else f"invalid ✗ {result.get('error', '')}"
        output.emit(_sanitize_job_output(result), state.output, human=human)
        if not valid:
            raise typer.Exit(ValidationError.exit_code)

    @app.command()
    def submit(
        ctx: typer.Context,
        tool: str = typer.Argument(..., help="Tool name (e.g. 'boltz'). See `tamarind tools`."),
        input: Optional[str] = typer.Option(None, "--input", "-i", help="Settings file (YAML/JSON), '-' for stdin, or @yaml://path."),
        set_: list[str] = typer.Option([], "--set", help="Override a setting: key=value (repeatable)."),
        name: Optional[str] = typer.Option(None, "--name", "-n", help="Job name (default: auto-generated)."),
        skip_validate: bool = typer.Option(False, "--skip-validate", help="Skip the pre-submit validate-job check."),
        wait: bool = typer.Option(False, "--wait", help="Block until the job reaches a terminal state."),
        poll_interval: float = typer.Option(10.0, "--poll-interval", help="Seconds between polls when --wait."),
        timeout: Optional[float] = typer.Option(None, "--timeout", help="With --wait, give up after N seconds."),
        download: Optional[Path] = typer.Option(None, "--download", help="With --wait, download results to this directory."),
    ) -> None:
        """Submit a single job. Validates first unless --skip-validate."""
        state = ctx.obj
        job = resolve_job_input(input, set_)
        job_type = effective_job_type(tool, job.job_type)
        job_name = effective_job_name(name, job.job_name) or _gen_name(tool)
        if wait:
            # A local wait-option error must never occur after creating a
            # remote, potentially billable job.
            jobs_helpers.validate_wait_options(
                poll_interval=poll_interval, timeout=timeout
            )

        with state.rest_client() as client:
            if not skip_validate:
                v = _rewrite_validation_guidance(
                    rest.validate_job(
                        client,
                        job_name=job_name,
                        job_type=job_type,
                        settings=job.settings,
                    )
                )
                if not v.get("valid"):
                    raise ValidationError(f"Settings invalid: {v.get('error', 'unknown error')}", detail=v)
                # NB: submit the user's original settings, NOT validate-job's
                # `normalized` output — the normalizer injects backend-internal
                # fields (e.g. submit_method, msa) that submit-job rejects.

            output.info(f"Submitting {job_type} job '{job_name}'…", state.output)
            try:
                submit_resp = rest.submit_job(
                    client, job_name=job_name, job_type=job_type, settings=job.settings
                )
            except TamarindError as exc:
                ambiguous = _outcome_is_ambiguous(exc)
                if ambiguous:
                    exc.message = (
                        f"{exc.message} Submission outcome may be ambiguous; "
                        f"query job '{job_name}' before retrying."
                    )
                raise _attach_error_context(
                    exc,
                    jobName=job_name,
                    phase="submit",
                    submitted=None if ambiguous else False,
                    outcomeMayBeAmbiguous=ambiguous,
                    recoveryCommand=f"tamarind --json status {job_name}",
                )

            result = {"jobName": job_name, "type": job_type, "submit": submit_resp}

            if wait:
                try:
                    output.info("Waiting for completion…", state.output)
                    final = jobs_helpers.wait_for_job(
                        client,
                        job_name,
                        poll_interval=poll_interval,
                        timeout=timeout,
                        on_poll=lambda j: output.info(
                            f"  status: {jobs_helpers.job_status(j)}", state.output
                        ),
                    )
                    result["final"] = final
                    status = jobs_helpers.job_status(final)
                    if download and jobs_helpers.is_success(status):
                        url = _result_url(rest.get_result(client, job_name=job_name))
                        dest = download / Path(f"{job_name}.zip").name
                        written = _download(url, dest)
                        result["download"] = {"path": str(dest), "bytes": written}
                        output.info(f"  downloaded {written} bytes → {dest}", state.output)
                except TamarindError as exc:
                    raise _attach_error_context(
                        exc,
                        jobName=job_name,
                        phase="post-submit",
                        submitted=True,
                        outcomeMayBeAmbiguous=False,
                        recoveryCommand=f"tamarind --json status {job_name}",
                    )

        human = f"submitted: {job_name}" + (
            f"  ({jobs_helpers.job_status(result['final'])})" if "final" in result else ""
        )
        output.emit(_sanitize_job_output(result), state.output, human=human)
        if "final" in result and _failed_terminal(result["final"]):
            raise typer.Exit(ExitCode.JOB_FAILED)

    @app.command()
    def finetune(
        ctx: typer.Context,
        model: str = typer.Argument(..., help="Base model to finetune (e.g. 'esm2'). See `tamarind tools`."),
        input: Optional[str] = typer.Option(None, "--input", "-i", help="Settings file (YAML/JSON), '-' for stdin, or @yaml://path."),
        set_: list[str] = typer.Option([], "--set", help="Override a setting: key=value (repeatable)."),
        name: Optional[str] = typer.Option(None, "--name", "-n", help="Job name (default: auto-generated)."),
        skip_validate: bool = typer.Option(False, "--skip-validate", help="Skip the pre-submit validate-job check."),
        wait: bool = typer.Option(False, "--wait", help="Block until the job reaches a terminal state."),
        poll_interval: float = typer.Option(10.0, "--poll-interval", help="Seconds between polls when --wait."),
        timeout: Optional[float] = typer.Option(None, "--timeout", help="With --wait, give up after N seconds."),
        download: Optional[Path] = typer.Option(None, "--download", help="With --wait, download results to this directory."),
    ) -> None:
        """Finetune a model on your own data. Validates first unless --skip-validate."""
        state = ctx.obj
        job = resolve_job_input(input, set_, tool_key="model")
        model_name = effective_job_type(model, job.job_type, tool_key="model")
        job_name = effective_job_name(name, job.job_name) or _gen_name(model)
        if wait:
            # A local wait-option error must never occur after creating a
            # remote, potentially billable job.
            jobs_helpers.validate_wait_options(
                poll_interval=poll_interval, timeout=timeout
            )

        with state.rest_client() as client:
            if not skip_validate:
                v = _rewrite_validation_guidance(
                    rest.validate_job(
                        client,
                        job_name=job_name,
                        job_type=model_name,
                        settings=job.settings,
                    )
                )
                if not v.get("valid"):
                    raise ValidationError(f"Settings invalid: {v.get('error', 'unknown error')}", detail=v)

            output.info(f"Submitting {model_name} finetuning job '{job_name}'…", state.output)
            try:
                submit_resp = rest.submit_finetune(
                    client, job_name=job_name, model=model_name, settings=job.settings
                )
            except TamarindError as exc:
                ambiguous = _outcome_is_ambiguous(exc)
                if ambiguous:
                    exc.message = (
                        f"{exc.message} Submission outcome may be ambiguous; "
                        f"query job '{job_name}' before retrying."
                    )
                raise _attach_error_context(
                    exc,
                    jobName=job_name,
                    phase="finetune",
                    submitted=None if ambiguous else False,
                    outcomeMayBeAmbiguous=ambiguous,
                    recoveryCommand=f"tamarind --json status {job_name}",
                )

            result = {"jobName": job_name, "model": model_name, "submit": submit_resp}

            if wait:
                try:
                    output.info("Waiting for completion…", state.output)
                    final = jobs_helpers.wait_for_job(
                        client,
                        job_name,
                        poll_interval=poll_interval,
                        timeout=timeout,
                        on_poll=lambda j: output.info(
                            f"  status: {jobs_helpers.job_status(j)}", state.output
                        ),
                    )
                    result["final"] = final
                    status = jobs_helpers.job_status(final)
                    if download and jobs_helpers.is_success(status):
                        url = _result_url(rest.get_result(client, job_name=job_name))
                        dest = download / Path(f"{job_name}.zip").name
                        written = _download(url, dest)
                        result["download"] = {"path": str(dest), "bytes": written}
                        output.info(f"  downloaded {written} bytes → {dest}", state.output)
                except TamarindError as exc:
                    raise _attach_error_context(
                        exc,
                        jobName=job_name,
                        phase="post-submit",
                        submitted=True,
                        outcomeMayBeAmbiguous=False,
                        recoveryCommand=f"tamarind --json status {job_name}",
                    )

        human = f"submitted: {job_name}" + (
            f"  ({jobs_helpers.job_status(result['final'])})" if "final" in result else ""
        )
        output.emit(_sanitize_job_output(result), state.output, human=human)
        if "final" in result and _failed_terminal(result["final"]):
            raise typer.Exit(ExitCode.JOB_FAILED)

    @app.command()
    def batch(
        ctx: typer.Context,
        tool: str = typer.Argument(..., help="Tool name applied to every job in the batch."),
        input: str = typer.Option(..., "--input", "-i", help="YAML/JSON list of per-job settings, or a {batchName,type,settings[],jobNames} object."),
        name: Optional[str] = typer.Option(None, "--name", "-n", help="Batch name (default: auto)."),
        max_runtime: Optional[int] = typer.Option(None, "--max-runtime", help="Max runtime seconds per job."),
        prevalidate: bool = typer.Option(
            False,
            "--prevalidate",
            help="Validate every item before submitting.",
        ),
    ) -> None:
        """Submit many jobs as one batch (preferred over looping submit)."""
        state = ctx.obj
        batch_name, job_type, settings_list, job_names = _resolve_batch_document(
            input, tool=tool, name=name, max_runtime=max_runtime
        )

        with state.rest_client() as client:
            if prevalidate:
                _prevalidate_batch(
                    client,
                    batch_name=batch_name,
                    job_type=job_type,
                    settings_list=settings_list,
                    job_names=job_names,
                )
            try:
                resp = rest.submit_batch(
                    client,
                    batch_name=batch_name,
                    job_type=job_type,
                    settings=settings_list,
                    job_names=job_names,
                    max_runtime_seconds=max_runtime,
                )
            except TamarindError as exc:
                ambiguous = _outcome_is_ambiguous(exc)
                if ambiguous:
                    exc.message = (
                        f"{exc.message} Batch submission outcome may be ambiguous; "
                        f"query batch '{batch_name}' before retrying."
                    )
                raise _attach_error_context(
                    exc,
                    batchName=batch_name,
                    phase="submit-batch",
                    submitted=None if ambiguous else False,
                    outcomeMayBeAmbiguous=ambiguous,
                    recoveryCommand=f"tamarind --json status {batch_name}",
                )
        result = {"batchName": batch_name, "type": job_type, "count": len(settings_list), "submit": resp}
        output.emit(
            _sanitize_job_output(result),
            state.output,
            human=f"submitted batch '{batch_name}' ({len(settings_list)} jobs)",
        )

    @app.command("finetune-batch")
    def finetune_batch(
        ctx: typer.Context,
        model: str = typer.Argument(..., help="Base model applied to every job in the batch."),
        input: str = typer.Option(..., "--input", "-i", help="YAML/JSON list of per-job settings, or a {batchName,model,settings[],jobNames} object."),
        name: Optional[str] = typer.Option(None, "--name", "-n", help="Batch name (default: auto)."),
        max_runtime: Optional[int] = typer.Option(None, "--max-runtime", help="Max runtime seconds per job."),
        prevalidate: bool = typer.Option(
            False,
            "--prevalidate",
            help="Validate every item before submitting.",
        ),
    ) -> None:
        """Submit many finetuning jobs as one batch (preferred over looping finetune)."""
        state = ctx.obj
        batch_name, model_name, settings_list, job_names = _resolve_batch_document(
            input, tool=model, name=name, max_runtime=max_runtime, tool_key="model"
        )

        with state.rest_client() as client:
            if prevalidate:
                _prevalidate_batch(
                    client,
                    batch_name=batch_name,
                    job_type=model_name,
                    settings_list=settings_list,
                    job_names=job_names,
                )
            try:
                resp = rest.submit_finetune_batch(
                    client,
                    batch_name=batch_name,
                    model=model_name,
                    settings=settings_list,
                    job_names=job_names,
                    max_runtime_seconds=max_runtime,
                )
            except TamarindError as exc:
                ambiguous = _outcome_is_ambiguous(exc)
                if ambiguous:
                    exc.message = (
                        f"{exc.message} Batch submission outcome may be ambiguous; "
                        f"query batch '{batch_name}' before retrying."
                    )
                raise _attach_error_context(
                    exc,
                    batchName=batch_name,
                    phase="finetune-batch",
                    submitted=None if ambiguous else False,
                    outcomeMayBeAmbiguous=ambiguous,
                    recoveryCommand=f"tamarind --json status {batch_name}",
                )
        result = {"batchName": batch_name, "model": model_name, "count": len(settings_list), "submit": resp}
        output.emit(
            _sanitize_job_output(result),
            state.output,
            human=f"submitted batch '{batch_name}' ({len(settings_list)} jobs)",
        )

    @app.command()
    def jobs(
        ctx: typer.Context,
        status: Optional[str] = typer.Option(None, "--status", help="Filter by status (client-side)."),
        batch: Optional[str] = typer.Option(None, "--batch", help="Only jobs in this batch."),
        limit: int = typer.Option(50, "--limit", help="Max jobs to return (page size when --all)."),
        start_key: Optional[str] = typer.Option(
            None, "--start-key", help="Pagination cursor: the 'startKey' from a previous listing."
        ),
        all_jobs: bool = typer.Option(
            False, "--all", help="Auto-paginate: follow startKey until every job is fetched."
        ),
        organization: bool = typer.Option(False, "--organization", help="All jobs across your org."),
        include_subjobs: bool = typer.Option(False, "--include-subjobs", help="Include batch subjobs."),
        email: Optional[str] = typer.Option(None, "--email", help="Jobs for another org member."),
    ) -> None:
        """List your jobs. When more remain, a 'startKey' is returned; pass it to --start-key (or use --all)."""
        state = ctx.obj
        with state.rest_client() as client:
            if all_jobs:
                job_list, statuses, next_key, _pages = _fetch_all_jobs(
                    client,
                    batch=batch,
                    start_key=start_key,
                    limit=limit,
                    organization=organization,
                    include_subjobs=include_subjobs,
                    job_email=email,
                )
            else:
                resp = rest.get_jobs(
                    client,
                    batch=batch,
                    start_key=start_key,
                    limit=limit,
                    organization=organization,
                    include_subjobs=include_subjobs,
                    job_email=email,
                )
                job_list = resp.get("jobs", resp if isinstance(resp, list) else [])
                statuses = resp.get("statuses") if isinstance(resp, dict) else None
                next_key = resp.get("startKey") if isinstance(resp, dict) else None
        if status:
            job_list = [j for j in job_list if (jobs_helpers.job_status(j) or "").lower() == status.lower()]
        # The raw Score is a large per-tool JSON blob — keep it out of the human
        # table (it's noise there) but retain it in the --json payload / `status`.
        rows = [
            {
                "JobName": jobs_helpers.job_name(j),
                "Type": j.get("Type"),
                "JobStatus": jobs_helpers.job_status(j),
                "Created": j.get("Created"),
            }
            for j in job_list
        ]
        out = {"jobs": _sanitize_job_output(job_list), "count": len(job_list)}
        if statuses:
            out["statuses"] = statuses
        human = output.render_table(rows, ["JobName", "Type", "JobStatus", "Created"])
        if next_key:
            # Keep the raw cursor out of the human footer (it's a 36-char UUID that
            # blows past narrow terminals) — it's always available in --json output.
            out["startKey"] = next_key
            human += "\n\n" + (
                f"More results — hit the {_MAX_AUTO_PAGES}-page cap; the startKey to continue is in --json."
                if all_jobs
                else "More results — re-run with --all to fetch them all (startKey is in --json)."
            )
        output.emit(out, state.output, human=human)

    @app.command()
    def status(
        ctx: typer.Context,
        job_name: str = typer.Argument(..., help="Job name."),
    ) -> None:
        """Show one job's current status and metadata."""
        state = ctx.obj
        with state.rest_client() as client:
            job = jobs_helpers.fetch_job(client, job_name)
        output.emit(
            _sanitize_job_output(job),
            state.output,
            human=f"{job_name}: {jobs_helpers.job_status(job)}",
        )

    @app.command()
    def wait(
        ctx: typer.Context,
        job_name: str = typer.Argument(..., help="Job name."),
        poll_interval: float = typer.Option(10.0, "--poll-interval", help="Seconds between polls."),
        timeout: Optional[float] = typer.Option(None, "--timeout", help="Give up after N seconds."),
    ) -> None:
        """Block until a job reaches a terminal state."""
        state = ctx.obj
        with state.rest_client() as client:
            final = jobs_helpers.wait_for_job(
                client,
                job_name,
                poll_interval=poll_interval,
                timeout=timeout,
                on_poll=lambda j: output.info(f"  status: {jobs_helpers.job_status(j)}", state.output),
            )
        output.emit(
            _sanitize_job_output(final),
            state.output,
            human=f"{job_name}: {jobs_helpers.job_status(final)}",
        )
        if _failed_terminal(final):
            raise typer.Exit(ExitCode.JOB_FAILED)

    @app.command()
    def results(
        ctx: typer.Context,
        job_name: str = typer.Argument(..., help="Job name."),
        download: Optional[Path] = typer.Option(None, "--download", help="Download the results bundle to this directory."),
        file: Optional[str] = typer.Option(None, "--file", help="A specific file within the results."),
        pdbs_only: bool = typer.Option(False, "--pdbs-only", help="Only PDB outputs."),
        show_url: bool = typer.Option(
            False,
            "--show-url",
            help="Print the credential-bearing presigned URL instead of downloading it.",
        ),
        wait: bool = typer.Option(False, "--wait", help="Wait for the job to finish first."),
        poll_interval: float = typer.Option(10.0, "--poll-interval", help="Seconds between polls when --wait."),
        timeout: Optional[float] = typer.Option(None, "--timeout", help="With --wait, give up after N seconds."),
    ) -> None:
        """Download results, or explicitly request a credential-bearing URL."""
        state = ctx.obj
        if download is None and not show_url:
            raise typer.BadParameter(
                "Results require --download DIR. Use --show-url only when an "
                "explicit presigned URL is needed outside agent logs."
            )
        if download is not None and show_url:
            raise typer.BadParameter("--download and --show-url are mutually exclusive.")
        with state.rest_client() as client:
            final = None
            if wait:
                output.info("Waiting for completion…", state.output)
                final = jobs_helpers.wait_for_job(
                    client,
                    job_name,
                    poll_interval=poll_interval,
                    timeout=timeout,
                    on_poll=lambda j: output.info(
                        f"  status: {jobs_helpers.job_status(j)}", state.output
                    ),
                )
                if _failed_terminal(final):
                    result = {
                        "jobName": job_name,
                        "final": _sanitize_job_output(final),
                    }
                    output.emit(
                        result,
                        state.output,
                        human=f"{job_name}: {jobs_helpers.job_status(final)}",
                    )
                    raise typer.Exit(ExitCode.JOB_FAILED)
            url = _result_url(
                rest.get_result(
                    client, job_name=job_name, file_name=file, pdbs_only=pdbs_only or None
                )
            )
            result = {"jobName": job_name}
            if final is not None:
                result["final"] = _sanitize_job_output(final)
            if download:
                suffix = file or f"{job_name}.zip"
                dest = download / Path(suffix).name
                written = _download(url, dest)
                result["download"] = {"path": str(dest), "bytes": written}
            elif show_url:
                result["url"] = url
        human = result.get("download", {}).get("path") if download else url
        output.emit(result, state.output, human=str(human))

    @app.command()
    def logs(
        ctx: typer.Context,
        job_name: str = typer.Argument(..., help="Job name."),
        max_lines: int = typer.Option(500, "--max-lines", help="Tail at most this many lines."),
    ) -> None:
        """Fetch a job's run logs (served by the catalog/gateway service)."""
        state = ctx.obj
        with state.catalog_client() as client:
            resp = client.get_json(f"catalog/jobs/{job_name}/logs", params={"maxLines": max_lines})
        if isinstance(resp, dict):
            # getJobLogs returns {"log": "..."} on success, {"error": "..."} otherwise.
            if resp.get("error"):
                msg = str(resp["error"])
                ml = msg.lower()
                if "not found" in ml or "no such" in ml or "does not exist" in ml:
                    raise NotFoundError(msg)
                raise TamarindError(msg)
            text = resp.get("log") or resp.get("hint") or json.dumps(resp, indent=2)
        else:
            text = resp
        output.emit(resp, state.output, human=str(text))

    @app.command()
    def cancel(
        ctx: typer.Context,
        job_name: Optional[str] = typer.Argument(None, help="Job name to cancel."),
        batch: Optional[str] = typer.Option(None, "--batch", help="Cancel an entire batch/pipeline instead."),
    ) -> None:
        """Cancel a running/queued job, or an entire batch."""
        state = ctx.obj
        if not job_name and not batch:
            raise TamarindError("Provide a job name or --batch <name>.")
        with state.rest_client() as client:
            if batch:
                resp = rest.cancel_batch(client, batch_name=batch)
            else:
                resp = rest.cancel_job(client, job_name=job_name)
        safe_resp = _sanitize_job_output(resp)
        output.emit(safe_resp, state.output, human=_message(safe_resp))

    @app.command()
    def delete(
        ctx: typer.Context,
        job_name: str = typer.Argument(..., help="Job name to permanently delete."),
        yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation."),
    ) -> None:
        """Permanently delete a job (and its subjobs, for batches)."""
        state = ctx.obj
        output.confirm_destructive(
            f"permanently delete job '{job_name}'", yes=yes, mode=state.output
        )
        with state.rest_client() as client:
            resp = rest.delete_job(client, job_name=job_name)
        safe_resp = _sanitize_job_output(resp)
        output.emit(safe_resp, state.output, human=_message(safe_resp))
