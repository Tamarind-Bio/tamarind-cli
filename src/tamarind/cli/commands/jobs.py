"""Job lifecycle commands: submit/validate/batch/jobs/status/wait/results/logs/cancel/delete."""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Optional

import httpx
import typer

from ... import jobs as jobs_helpers
from ... import rest
from ...errors import NotFoundError, TamarindError, ValidationError
from .. import output
from ..inputs import resolve_job_input


def _gen_name(tool: str) -> str:
    return f"{tool}-{uuid.uuid4().hex[:8]}"


def _message(resp: object) -> str:
    """Best-effort human message from a response that may be a dict or a string."""
    if isinstance(resp, dict):
        return str(resp.get("message", resp))
    return str(resp)


def _download(url: str, dest: Path) -> int:
    """Stream a presigned URL to ``dest``. Returns bytes written."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    total = 0
    with httpx.stream("GET", url, follow_redirects=True, timeout=300.0) as resp:
        resp.raise_for_status()
        with dest.open("wb") as fh:
            for chunk in resp.iter_bytes():
                fh.write(chunk)
                total += len(chunk)
    return total


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
        job_name = name or job.job_name or _gen_name(tool)
        with state.rest_client() as client:
            result = rest.validate_job(
                client, job_name=job_name, job_type=job.job_type or tool, settings=job.settings
            )
        valid = bool(result.get("valid"))
        human = "valid ✓" if valid else f"invalid ✗  {result.get('error', '')}"
        output.emit(result, state.output, human=human)
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
        download: Optional[Path] = typer.Option(None, "--download", help="With --wait, download results to this directory."),
    ) -> None:
        """Submit a single job. Validates first unless --skip-validate."""
        state = ctx.obj
        job = resolve_job_input(input, set_)
        job_type = job.job_type or tool
        job_name = name or job.job_name or _gen_name(tool)

        with state.rest_client() as client:
            if not skip_validate:
                v = rest.validate_job(client, job_name=job_name, job_type=job_type, settings=job.settings)
                if not v.get("valid"):
                    raise ValidationError(f"Settings invalid: {v.get('error', 'unknown error')}", detail=v)
                # NB: submit the user's original settings, NOT validate-job's
                # `normalized` output — the normalizer injects backend-internal
                # fields (e.g. submit_method, msa) that submit-job rejects.

            output.info(f"Submitting {job_type} job '{job_name}'…", state.output)
            submit_resp = rest.submit_job(client, job_name=job_name, job_type=job_type, settings=job.settings)

            result = {"jobName": job_name, "type": job_type, "submit": submit_resp}

            if wait:
                output.info("Waiting for completion…", state.output)
                final = jobs_helpers.wait_for_job(
                    client,
                    job_name,
                    poll_interval=poll_interval,
                    on_poll=lambda j: output.info(f"  status: {jobs_helpers.job_status(j)}", state.output),
                )
                result["final"] = final
                status = jobs_helpers.job_status(final)
                if download and jobs_helpers.is_success(status):
                    url = rest.get_result(client, job_name=job_name)
                    dest = download / f"{job_name}.zip"
                    written = _download(url, dest)
                    result["download"] = {"path": str(dest), "bytes": written}
                    output.info(f"  downloaded {written} bytes → {dest}", state.output)

        human = f"submitted: {job_name}" + (
            f"  ({jobs_helpers.job_status(result['final'])})" if "final" in result else ""
        )
        output.emit(result, state.output, human=human)

    @app.command()
    def batch(
        ctx: typer.Context,
        tool: str = typer.Argument(..., help="Tool name applied to every job in the batch."),
        input: str = typer.Option(..., "--input", "-i", help="YAML/JSON list of per-job settings, or a {batchName,type,settings[],jobNames} object."),
        name: Optional[str] = typer.Option(None, "--name", "-n", help="Batch name (default: auto)."),
        max_runtime: Optional[int] = typer.Option(None, "--max-runtime", help="Max runtime seconds per job."),
    ) -> None:
        """Submit many jobs as one batch (preferred over looping submit)."""
        state = ctx.obj
        from ..inputs import _load_text, _parse_document  # internal reuse

        doc = _parse_document(_load_text(input))
        batch_name = name or _gen_name(tool)
        job_type = tool
        job_names = None
        if isinstance(doc, list):
            settings_list = doc
        elif isinstance(doc, dict) and isinstance(doc.get("settings"), list):
            settings_list = doc["settings"]
            batch_name = name or doc.get("batchName") or batch_name
            job_type = doc.get("type") or tool
            job_names = doc.get("jobNames")
        else:
            raise TamarindError("Batch --input must be a list of settings or a {settings:[...]} object.")

        with state.rest_client() as client:
            resp = rest.submit_batch(
                client,
                batch_name=batch_name,
                job_type=job_type,
                settings=settings_list,
                job_names=job_names,
                max_runtime_seconds=max_runtime,
            )
        result = {"batchName": batch_name, "type": job_type, "count": len(settings_list), "submit": resp}
        output.emit(result, state.output, human=f"submitted batch '{batch_name}' ({len(settings_list)} jobs)")

    @app.command()
    def jobs(
        ctx: typer.Context,
        status: Optional[str] = typer.Option(None, "--status", help="Filter by status (client-side)."),
        batch: Optional[str] = typer.Option(None, "--batch", help="Only jobs in this batch."),
        limit: int = typer.Option(50, "--limit", help="Max jobs to return."),
        organization: bool = typer.Option(False, "--organization", help="All jobs across your org."),
        include_subjobs: bool = typer.Option(False, "--include-subjobs", help="Include batch subjobs."),
        email: Optional[str] = typer.Option(None, "--email", help="Jobs for another org member."),
    ) -> None:
        """List your jobs."""
        state = ctx.obj
        with state.rest_client() as client:
            resp = rest.get_jobs(
                client,
                batch=batch,
                limit=limit,
                organization=organization,
                include_subjobs=include_subjobs,
                job_email=email,
            )
        job_list = resp.get("jobs", resp if isinstance(resp, list) else [])
        if status:
            job_list = [j for j in job_list if (jobs_helpers.job_status(j) or "").lower() == status.lower()]
        rows = [
            {
                "JobName": jobs_helpers.job_name(j),
                "Type": j.get("Type"),
                "JobStatus": jobs_helpers.job_status(j),
                "Created": j.get("Created"),
                "Score": j.get("Score"),
            }
            for j in job_list
        ]
        out = {"jobs": job_list, "count": len(job_list)}
        if isinstance(resp, dict) and resp.get("statuses"):
            out["statuses"] = resp["statuses"]
        output.emit(out, state.output, human=output.render_table(rows, ["JobName", "Type", "JobStatus", "Created", "Score"]))

    @app.command()
    def status(
        ctx: typer.Context,
        job_name: str = typer.Argument(..., help="Job name."),
    ) -> None:
        """Show one job's current status and metadata."""
        state = ctx.obj
        with state.rest_client() as client:
            job = jobs_helpers.fetch_job(client, job_name)
        output.emit(job, state.output, human=f"{job_name}: {jobs_helpers.job_status(job)}")

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
        output.emit(final, state.output, human=f"{job_name}: {jobs_helpers.job_status(final)}")

    @app.command()
    def results(
        ctx: typer.Context,
        job_name: str = typer.Argument(..., help="Job name."),
        download: Optional[Path] = typer.Option(None, "--download", help="Download the results bundle to this directory."),
        file: Optional[str] = typer.Option(None, "--file", help="A specific file within the results."),
        pdbs_only: bool = typer.Option(False, "--pdbs-only", help="Only PDB outputs."),
        wait: bool = typer.Option(False, "--wait", help="Wait for the job to finish first."),
        poll_interval: float = typer.Option(10.0, "--poll-interval", help="Seconds between polls when --wait."),
    ) -> None:
        """Get a presigned results URL, or download the results bundle."""
        state = ctx.obj
        with state.rest_client() as client:
            if wait:
                output.info("Waiting for completion…", state.output)
                jobs_helpers.wait_for_job(client, job_name, poll_interval=poll_interval)
            url = rest.get_result(
                client, job_name=job_name, file_name=file, pdbs_only=pdbs_only or None
            )
            if not isinstance(url, str):
                # Defensive: some deployments may wrap the URL in an object.
                url = url.get("url") if isinstance(url, dict) else str(url)
            result = {"jobName": job_name, "url": url}
            if download:
                suffix = file or f"{job_name}.zip"
                dest = download / Path(suffix).name
                written = _download(url, dest)
                result["download"] = {"path": str(dest), "bytes": written}
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
        output.emit(resp, state.output, human=_message(resp))

    @app.command()
    def delete(
        ctx: typer.Context,
        job_name: str = typer.Argument(..., help="Job name to permanently delete."),
        yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation."),
    ) -> None:
        """Permanently delete a job (and its subjobs, for batches)."""
        state = ctx.obj
        if not yes and not state.output.json:
            typer.confirm(f"Permanently delete job '{job_name}'?", abort=True)
        with state.rest_client() as client:
            resp = rest.delete_job(client, job_name=job_name)
        output.emit(resp, state.output, human=_message(resp))
