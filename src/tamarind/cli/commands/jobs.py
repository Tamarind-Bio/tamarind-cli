"""Job lifecycle commands: submit/finetune/validate/batch/jobs/status/wait/results/logs/cancel/delete."""

from __future__ import annotations

import json
import re
import tempfile
import uuid
from pathlib import Path
from typing import Optional
from urllib.parse import parse_qsl, urlsplit

import httpx
import typer

from ... import jobs as jobs_helpers
from ... import rest
from ...errors import ExitCode, NotFoundError, TamarindError, ValidationError
from .. import output
from ..guidance import rewrite_validation_guidance
from ..inputs import effective_job_name, effective_job_tool, effective_job_type, resolve_job_input


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


_SUBMIT_JOB_ENDPOINT = "/submit-job"
_SUBMIT_BATCH_ENDPOINT = "/submit-batch"
_FINETUNE_ENDPOINT = "/finetune"
_FINETUNE_BATCH_ENDPOINT = "/finetune-batch"


def _refusal_code(exc: TamarindError) -> str | None:
    """The JSON ``code`` of an HTTP 400 refusal, or None for anything else."""
    if exc.http_status != 400:
        return None
    detail = exc.detail
    code = detail.get("code") if isinstance(detail, dict) else None
    return code if isinstance(code, str) else None


def _wrong_endpoint_for_ordinary_endpoint(exc: TamarindError) -> bool:
    """/submit-job and /submit-batch: only the exact finetune refusal moves a job."""
    return _refusal_code(exc) == rest.USE_FINETUNE_ENDPOINT


def _wrong_endpoint_for_finetune_endpoint(exc: TamarindError) -> bool:
    """/finetune and /finetune-batch: the exact ordinary-tool refusal, or a 404 —
    a server that has not shipped the route yet, where the old route still takes
    finetune tools. The error came from the exact route that was posted."""
    return exc.http_status == 404 or _refusal_code(exc) == rest.NOT_A_FINETUNE_TOOL


# endpoint -> (where a refused request is resent, the refusal test for it)
_ENDPOINT_REROUTES = {
    _SUBMIT_JOB_ENDPOINT: (_FINETUNE_ENDPOINT, _wrong_endpoint_for_ordinary_endpoint),
    _SUBMIT_BATCH_ENDPOINT: (_FINETUNE_BATCH_ENDPOINT, _wrong_endpoint_for_ordinary_endpoint),
    _FINETUNE_ENDPOINT: (_SUBMIT_JOB_ENDPOINT, _wrong_endpoint_for_finetune_endpoint),
    _FINETUNE_BATCH_ENDPOINT: (_SUBMIT_BATCH_ENDPOINT, _wrong_endpoint_for_finetune_endpoint),
}


def _post_routed(state, *, endpoint: str, tool: str, post):
    """``post(endpoint)`` and return ``(response, endpoint_used)``.

    Finetune tools submit through POST /finetune and /finetune-batch (tool field
    ``model``); every other tool through POST /submit-job and /submit-batch
    (``type``). The CLI does not classify tools itself — the server's answer is the
    authority — so a request refused with the matching ``code`` (or, from a
    finetune route, a 404) is resent to the paired endpoint exactly ONCE. Those
    answers come before a job exists, so the resend cannot duplicate one; any other
    error, or a second refusal, propagates unchanged.
    """
    other, should_resend = _ENDPOINT_REROUTES[endpoint]
    try:
        return post(endpoint), endpoint
    except TamarindError as exc:
        if not should_resend(exc):
            raise
        reason = "does not exist on this server" if exc.http_status == 404 else "was refused"
    output.info(f"  {tool} on {endpoint} {reason}; sending it to {other}…", state.output)
    return post(other), other


def _submit_single(client, state, *, endpoint: str, job_name: str, tool: str, settings: dict):
    """One job to /submit-job or /finetune, following the server's routing once."""

    def post(target: str):
        if target == _FINETUNE_ENDPOINT:
            return rest.finetune_job(client, job_name=job_name, model=tool, settings=settings)
        return rest.submit_job(client, job_name=job_name, job_type=tool, settings=settings)

    return _post_routed(state, endpoint=endpoint, tool=tool, post=post)


def _submit_batch(
    client, state, *, endpoint: str, batch_name: str, tool: str, settings_list: list,
    job_names: list | None, max_runtime: int | None,
):
    """One batch request to /submit-batch or /finetune-batch, following the server's
    routing once. The batch is always ONE request — never split into jobs."""

    def post(target: str):
        if target == _FINETUNE_BATCH_ENDPOINT:
            return rest.finetune_batch(
                client, batch_name=batch_name, model=tool, settings=settings_list,
                job_names=job_names, max_runtime_seconds=max_runtime,
            )
        return rest.submit_batch(
            client, batch_name=batch_name, job_type=tool, settings=settings_list,
            job_names=job_names, max_runtime_seconds=max_runtime,
        )

    return _post_routed(state, endpoint=endpoint, tool=tool, post=post)


def _submit_command(
    ctx: typer.Context,
    *,
    endpoint: str,
    tool: str,
    input: Optional[str],
    set_: list[str],
    name: Optional[str],
    skip_validate: bool,
    wait: bool,
    poll_interval: float,
    timeout: Optional[float],
    download: Optional[Path],
) -> None:
    """Shared body of ``submit`` (POST /submit-job) and ``finetune`` (POST /finetune)."""
    state = ctx.obj
    job = resolve_job_input(input, set_)
    job_type = effective_job_tool(tool, job)
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

        noun = "finetune" if endpoint == _FINETUNE_ENDPOINT else job_type
        output.info(f"Submitting {noun} job '{job_name}'…", state.output)
        try:
            submit_resp, endpoint_used = _submit_single(
                client,
                state,
                endpoint=endpoint,
                job_name=job_name,
                tool=job_type,
                settings=job.settings,
            )
        except TamarindError as exc:
            status_code = getattr(exc, "status_code", None)
            ambiguous = type(exc) is TamarindError or (
                isinstance(status_code, int) and status_code >= 500
            )
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

        result = {
            "jobName": job_name,
            "type": job_type,
            "endpoint": endpoint_used,
            "submit": submit_resp,
        }

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
        job_type = effective_job_tool(tool, job)
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
        """Submit a single job. Validates first unless --skip-validate.

        Prefer `tamarind finetune MODEL` (POST /finetune) to train a model. A finetune
        tool submitted here still goes through: if the server answers that it belongs
        on /finetune, it is resent there once.
        """
        _submit_command(
            ctx,
            endpoint=_SUBMIT_JOB_ENDPOINT,
            tool=tool,
            input=input,
            set_=set_,
            name=name,
            skip_validate=skip_validate,
            wait=wait,
            poll_interval=poll_interval,
            timeout=timeout,
            download=download,
        )

    @app.command()
    def finetune(
        ctx: typer.Context,
        model: str = typer.Argument(..., help="Finetune tool to train with (e.g. 'chemprop-finetune'). See `tamarind tools --function finetuning`."),
        input: Optional[str] = typer.Option(None, "--input", "-i", help="Settings file (YAML/JSON), '-' for stdin, or @yaml://path."),
        set_: list[str] = typer.Option([], "--set", help="Override a setting: key=value (repeatable)."),
        name: Optional[str] = typer.Option(None, "--name", "-n", help="Job name (default: auto-generated)."),
        skip_validate: bool = typer.Option(False, "--skip-validate", help="Skip the pre-submit validate-job check."),
        wait: bool = typer.Option(False, "--wait", help="Block until the job reaches a terminal state."),
        poll_interval: float = typer.Option(10.0, "--poll-interval", help="Seconds between polls when --wait."),
        timeout: Optional[float] = typer.Option(None, "--timeout", help="With --wait, give up after N seconds."),
        download: Optional[Path] = typer.Option(None, "--download", help="With --wait, download results to this directory."),
    ) -> None:
        """Train (finetune) a model: submit one finetuning job to POST /finetune.

        Same inputs as `submit`. To train several models in one request, use `batch`
        with the finetune tool. If MODEL is not a finetune tool, or the server has no
        /finetune yet, the job is resent to /submit-job once.
        """
        _submit_command(
            ctx,
            endpoint=_FINETUNE_ENDPOINT,
            tool=model,
            input=input,
            set_=set_,
            name=name,
            skip_validate=skip_validate,
            wait=wait,
            poll_interval=poll_interval,
            timeout=timeout,
            download=download,
        )

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
            help="Validate every item before submitting (one API request per item).",
        ),
    ) -> None:
        """Submit many jobs as one batch (preferred over looping submit).

        A finetune tool batch goes to POST /finetune-batch: if the server answers that
        the batch belongs there, the same batch is resent there once.
        """
        state = ctx.obj
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
            job_type = effective_job_type(tool, doc.get("type"))
            effective_job_type(tool, doc.get("model"), field="model")
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

        with state.rest_client() as client:
            if prevalidate:
                for index, settings in enumerate(settings_list):
                    validation_name = (
                        job_names[index]
                        if isinstance(job_names, list)
                        and index < len(job_names)
                        and job_names[index]
                        else f"{batch_name}-{index + 1}"
                    )
                    validation = _rewrite_validation_guidance(
                        rest.validate_job(
                            client,
                            job_name=str(validation_name),
                            job_type=job_type,
                            settings=settings,
                        )
                    )
                    if not isinstance(validation, dict) or not validation.get("valid"):
                        validation_error = (
                            validation.get("error", "unknown error")
                            if isinstance(validation, dict)
                            else "unexpected validation response"
                        )
                        raise ValidationError(
                            f"Batch item {index + 1} settings invalid: "
                            f"{validation_error}",
                            detail={"index": index, "jobName": validation_name, "validation": validation},
                        )
            try:
                resp, endpoint_used = _submit_batch(
                    client,
                    state,
                    endpoint=_SUBMIT_BATCH_ENDPOINT,
                    batch_name=batch_name,
                    tool=job_type,
                    settings_list=settings_list,
                    job_names=job_names,
                    max_runtime=max_runtime,
                )
            except TamarindError as exc:
                status_code = getattr(exc, "status_code", None)
                ambiguous = type(exc) is TamarindError or (
                    isinstance(status_code, int) and status_code >= 500
                )
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
        result = {
            "batchName": batch_name,
            "type": job_type,
            "count": len(settings_list),
            "endpoint": endpoint_used,
            "submit": resp,
        }
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
