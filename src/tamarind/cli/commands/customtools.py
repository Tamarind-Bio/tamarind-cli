"""`tamarind ct` — authoring custom tools.

The lifecycle verbs people run constantly (`deploy`, `publish`) are registered at the
top level by :func:`register`; the occasional ones live under `ct`. That split is not
taste — `tamarind tools` already means "search the catalog", so the authoring surface
cannot take that name, and burying `deploy` three tokens deep would be worse.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from ... import customtools as ct
from ... import jobs as jobs_helpers
from ...customtools import archive as ct_archive
from ...customtools import flow as ct_flow
from ...customtools import project as ct_project
from ...errors import TamarindError, ValidationError
from .. import output

app = typer.Typer(no_args_is_help=True)


def _renderer(state) -> "callable":
    """Send progress to STDERR so stdout stays a clean result object.

    This is what makes `tamarind deploy --json | jq` work: build output and the result
    cannot share a stream. Suppressed entirely in quiet/JSON mode.
    """

    def handle(event: ct_flow.BuildEvent) -> None:
        if event.kind == "warning":
            output.info(f"warning: {event.message}", state.output)
        else:
            output.info(event.message, state.output)

    return handle


def _looks_like_already_exists(exc: TamarindError) -> bool:
    """Whether a 400 is the server saying the tool is already there.

    Message matching is unlovely, but the alternative is worse: the endpoint reports
    both "already exists" and "that name is invalid" as 400, and treating the whole
    class as a conflict swallowed real errors. Kept deliberately narrow — an unmatched
    message re-raises, so a new phrasing surfaces the error rather than hiding it.
    """
    text = str(getattr(exc, "message", exc)).lower()
    return "exist" in text or "already" in text or "duplicate" in text or "taken" in text


def _attach_logs(exc: TamarindError, build_id: str, collected: list) -> None:
    """Carry the drained log lines out on the exception.

    The CLI renders `detail` into the structured error, so this is what keeps the
    output someone asked for from being discarded exactly when the build failed.
    """
    detail = dict(exc.detail) if isinstance(exc.detail, dict) else {}
    if exc.detail is not None and not isinstance(exc.detail, dict):
        detail["upstreamDetail"] = exc.detail
    detail.update(buildId=build_id, logs=collected)
    exc.detail = detail


def _outcome_payload(outcome: ct.DeployOutcome, name: str) -> dict:
    return {
        "tool": name,
        "version": outcome.version_name,
        "path": outcome.path,
        "buildId": outcome.build_id,
        # The field a script branches on. Deliberately NOT re-derived from `path` by
        # the caller — that inference is made once, in plan.reconcile.
        "deployed": outcome.deployed,
        # Whether the deploy is known to have used YOUR source. A script that publishes
        # on its own should branch on this, not on `deployed`.
        "confirmed": outcome.confirmed,
        "reason": outcome.reason,
        "detail": outcome.explanation,
    }


# ------------------------------------------------------------- top-level verbs ----


def register(app_root: typer.Typer) -> None:
    """Attach the everyday verbs to the root command."""

    @app_root.command()
    def deploy(
        ctx: typer.Context,
        folder: Path = typer.Argument(
            Path("."), help="Tool folder. Defaults to the current directory."
        ),
        name: Optional[str] = typer.Option(
            None, "--name", help="Tool id. Defaults to .tamarind, then the folder name."
        ),
        create: bool = typer.Option(
            False, "--create", help="Create the tool first if it does not exist yet."
        ),
        wait: bool = typer.Option(
            True, "--wait/--no-wait", help="Watch the build until it finishes."
        ),
        publish_after: bool = typer.Option(
            False, "--publish", help="Publish the new version if the build succeeds."
        ),
        fail_on_noop: bool = typer.Option(
            False,
            "--fail-on-noop",
            help="Exit non-zero when there was nothing to deploy (for strict CI).",
        ),
        timeout: float = typer.Option(3600.0, "--timeout", help="Seconds to watch a build."),
    ) -> None:
        """Package a folder, upload it, and deploy it.

        Streams build output as it arrives. When nothing changed this still succeeds —
        `deployed: false` in the JSON says so, and `--fail-on-noop` makes it an error.
        """
        state = ctx.obj
        # Rejected here, before the upload, rather than failing after it. Publishing
        # requires a COMPLETE version and `--no-wait` returns while the build is still
        # running, so the combination cannot succeed for any build that actually builds
        # — accepting it would spend the upload and then refuse.
        if publish_after and not wait:
            raise ValidationError(
                "--publish needs the build to finish, so it cannot be combined with "
                "--no-wait. Drop --no-wait, or deploy now and run `tamarind publish` "
                "once the build completes."
            )
        # Same rule, same place: a bad --timeout must not be discovered AFTER the
        # upload and the build. `--timeout -1` expired only once a remote build was
        # already running, and `--timeout nan` produced a deadline no comparison ever
        # satisfies, so the bound silently did nothing. Reuses the jobs validator
        # rather than growing a second notion of a valid timeout.
        jobs_helpers.validate_wait_options(timeout=timeout)
        tool = ct_project.resolve_name(folder, name)
        with state.rest_client() as client:
            if create:
                # Idempotent by intent: --create means "make sure it exists", so an
                # already-created tool is not an error.
                try:
                    ct.create_tool(client, name=tool)
                except TamarindError as exc:
                    # A 409 is unambiguous. A 400 is the whole validation class — an
                    # invalid tool name arrives as one too — so suppressing every 400
                    # hid the real error, wrote a marker for a tool that was never
                    # created, and failed confusingly at the upload instead.
                    status = getattr(exc, "status_code", None)
                    already_exists = status == 409 or (
                        status == 400 and _looks_like_already_exists(exc)
                    )
                    if not already_exists:
                        raise
                # Written on BOTH paths. Skipping it on the already-exists branch left a
                # folder deploying to `--name other-tool` with no record of it, so the
                # next bare `deploy` fell back to the folder name — a different tool.
                ct_project.write(folder, name=tool)
            outcome = ct.build(
                client,
                name=tool,
                folder=folder,
                wait=wait,
                on_event=_renderer(state),
                timeout=timeout,
            )
            payload = _outcome_payload(outcome, tool)

            if publish_after and outcome.deployed and not outcome.publishable:
                # The build may have run against the previous source. Publishing is the
                # irreversible step, so it stops here rather than promoting a version
                # nobody asked to ship. The deploy itself still reports what it did.
                raise ValidationError(
                    f"Deployed, but the server never confirmed it unpacked this upload, "
                    f"so {outcome.version_name} may have been built from the previous "
                    f"source. Not publishing. Check `tamarind ct status {tool}`, then "
                    f"`tamarind publish {tool} <version>` when you are satisfied.",
                    detail=_outcome_payload(outcome, tool),
                )
            if publish_after and outcome.publishable and outcome.version_name:
                _, published = ct.publish(client, name=tool, version_name=outcome.version_name)
                payload["published"] = published

        human = (
            f"{tool} {outcome.version_name}: {outcome.explanation}"
            if outcome.deployed
            else f"{tool}: {outcome.explanation}"
        )
        output.emit(payload, state.output, human=human)
        if fail_on_noop and not outcome.deployed:
            raise typer.Exit(code=1)

    @app_root.command()
    def init(
        ctx: typer.Context,
        directory: Optional[Path] = typer.Argument(
            None, help="Folder to create. Defaults to ./<name>."
        ),
        name: Optional[str] = typer.Option(
            None, "--name", help="Tool id. Defaults to the folder name."
        ),
        display_name: Optional[str] = typer.Option(
            None, "--display-name", help="Human-readable name."
        ),
    ) -> None:
        """Create a tool and write its starting files.

        The scaffold comes from the server, not from templates carried here — it picks
        the Dockerfile's base image from the tool's packages, so local copies would
        drift the first time those images moved.
        """
        state = ctx.obj
        tool = name or (Path(directory).name if directory else None)
        if not tool:
            raise ValidationError("Give a folder or --name, e.g. `tamarind init my-esmfold`.")
        target = Path(directory) if directory else Path.cwd() / tool
        with state.rest_client() as client:
            folder, _ = ct.flow.init(
                client,
                name=tool,
                destination=target,
                display_name=display_name,
                on_event=_renderer(state),
            )
        output.emit(
            {"tool": tool, "path": str(folder)},
            state.output,
            human=f"created {tool} in {folder}\n\nnext: cd {folder} && tamarind deploy",
        )

    @app_root.command()
    def publish(
        ctx: typer.Context,
        name: Optional[str] = typer.Argument(None, help="Tool id. Defaults to the folder name."),
        version: Optional[str] = typer.Argument(
            None, help="Version. Defaults to the newest complete one."
        ),
    ) -> None:
        """Make a version live for the whole organization.

        Separate from `deploy` on purpose: publishing hands every member of your org the
        viewer role on the tool, so it should not happen as a side effect of building.
        """
        state = ctx.obj
        tool = ct_project.resolve_name(Path.cwd(), name)
        with state.rest_client() as client:
            _, published = ct.publish(client, name=tool, version_name=version)
        output.emit(
            {"tool": tool, "published": published},
            state.output,
            human=f"published {tool} {published}",
        )

    @app_root.command()
    def check(
        ctx: typer.Context,
        folder: Path = typer.Argument(
            Path("."), help="Tool folder. Defaults to the current directory."
        ),
    ) -> None:
        """Inspect a tool folder before spending a build on it.

        Local only and instant. These same checks run inside `deploy` — a pre-flight
        nobody remembers to run prevents nothing — so this exists for pre-commit hooks
        and CI, where running it alone is the point.
        """
        state = ctx.obj
        spec = ct_archive.plan_archive(folder)
        root = spec.root
        problems: list[str] = []
        warnings: list[str] = []
        facts: dict = {}

        # THE function `deploy` runs, not a second copy of it — that divergence is
        # what let a folder this command rejected still reach a remote build. `check`
        # collects rather than raises, though: being told about every problem at once
        # is the whole reason to run it separately.
        try:
            findings = ct.inspect_folder(root)
        except ValidationError as exc:
            problems.append(str(exc))
        else:
            problems += list(findings.errors)
            warnings += list(findings.warnings)
            facts = findings.facts

        advice = ct.packaging.env_var_advice(spec.secrets)
        if advice:
            warnings.append(advice)
        for weight in spec.weights:
            warnings.append(
                f"{weight} looks like model weights. The runtime container has no "
                f"network, so weights belong in the image via the Dockerfile."
            )
        if spec.links:
            warnings.append(
                f"Skipped {len(spec.links)} symlink(s) ({', '.join(sorted(spec.links)[:3])}"
                f"{' …' if len(spec.links) > 3 else ''}). Links are never followed — a "
                f"link's name says nothing about what it points at — so copy the real "
                f"file in if the build needs it."
            )

        payload = {
            "folder": str(root),
            "files": len(spec.included),
            "bytes": spec.total_bytes,
            "excludedSecrets": list(spec.secrets),
            "excludedLinks": list(spec.links),
            "excludedNoise": spec.noise_count,
            "problems": problems,
            "warnings": warnings,
            # What the manifest declares, echoed so a caller can confirm the tool it
            # is about to deploy is the one it meant (MSA on, batching on, N inputs).
            "config": facts,
            "ok": not problems,
        }
        for warning in warnings:
            output.info(f"warning: {warning}", state.output)
        human = (
            f"{len(spec.included)} files, {spec.total_bytes / 1024:.0f} KiB — looks deployable"
            if not problems
            else "\n".join(f"- {p}" for p in problems)
        )
        output.emit(payload, state.output, human=human)
        if problems:
            raise typer.Exit(code=5)


# ------------------------------------------------------------------- ct verbs ----


@app.command("list")
def list_tools(ctx: typer.Context) -> None:
    """Your organization's own custom tools (not the runnable catalog)."""
    state = ctx.obj
    with state.rest_client() as client:
        resp = ct.list_tools(client)
    tools = resp.get("tools", resp) if isinstance(resp, dict) else resp
    rows = tools if isinstance(tools, list) else []
    output.emit(
        resp,
        state.output,
        human=output.render_table(
            [
                {
                    "name": t.get("name"),
                    "status": t.get("status"),
                    "published": t.get("published"),
                }
                for t in rows
                if isinstance(t, dict)
            ],
            ["name", "status", "published"],
        ),
    )


@app.command()
def status(ctx: typer.Context, name: str = typer.Argument(..., help="Tool id.")) -> None:
    """What state a tool is in, and whether it has changes that were never deployed."""
    state = ctx.obj
    with state.rest_client() as client:
        tool = ct.get_tool(client, name=name)
        versions = ct.get_versions(client, name=name)

    latest = versions[0] if versions else None
    # The genuinely useful line, and the only derived one: if the source has moved past
    # the newest version's ref, there is work sitting undeployed. NO version at all is
    # the strongest form of that — a source tree nobody has ever built — so it must not
    # fall through to False just because there is nothing to compare against.
    undeployed = bool(
        tool.current_source_ref and (latest is None or latest.ref != tool.current_source_ref)
    )
    payload = {
        "name": tool.name,
        "status": tool.status,
        "published": tool.published,
        "latestVersion": latest.name if latest else None,
        "latestVersionStatus": latest.status if latest else None,
        "latestBuildStatus": tool.latest_build_status,
        "sourceRef": tool.current_source_ref,
        "hasUndeployedChanges": undeployed,
        "publishPending": tool.publish_pending_version,
    }
    lines = [f"{tool.name}: {tool.status}" + (" (published)" if tool.published else "")]
    if latest:
        lines.append(f"latest version {latest.name} — {latest.status}")
    if undeployed:
        lines.append("source has changes that have not been deployed")
    output.emit(payload, state.output, human="\n".join(lines))


@app.command()
def versions(ctx: typer.Context, name: str = typer.Argument(..., help="Tool id.")) -> None:
    """Version history, newest first."""
    state = ctx.obj
    with state.rest_client() as client:
        found = ct.get_versions(client, name=name)
    output.emit(
        [v.raw for v in found],
        state.output,
        human=output.render_table(
            [
                {
                    "version": v.name,
                    "status": v.status,
                    "build": v.build_id,
                    "by": v.created_by,
                    "error": v.error_message,
                }
                for v in found
            ],
            ["version", "status", "build", "by", "error"],
        ),
    )


@app.command()
def logs(
    ctx: typer.Context,
    name: str = typer.Argument(..., help="Tool id."),
    build_id: Optional[str] = typer.Option(
        None, "--build-id", help="Defaults to the latest build."
    ),
    follow: bool = typer.Option(
        False, "--follow", "-f", help="Keep streaming until the build ends."
    ),
) -> None:
    """Build output, for reattaching after `--no-wait` or a dropped connection.

    Ctrl-C stops watching. It does NOT cancel the build — use `ct cancel` for that.
    """
    state = ctx.obj
    with state.rest_client() as client:
        target = build_id
        if target is None:
            tool = ct.get_tool(client, name=name)
            target = tool.latest_build_id
            if not target:
                raise ValidationError(f"'{name}' has no build to show logs for.")
        collected: list = []

        def collect(event: ct_flow.BuildEvent) -> None:
            if event.kind == "log":
                collected.append({"message": event.message, "timestamp": event.timestamp})
            render(event)

        render = _renderer(state)
        if follow:
            try:
                page = ct.wait_for_build(client, name=name, build_id=target, on_event=collect)
            except TamarindError as exc:
                # A FAILED build is the case someone runs this for, and the raise
                # skipped the payload entirely — so `--json ct logs --follow` returned
                # error metadata and none of the output it had just collected.
                _attach_logs(exc, target, collected)
                raise
        else:
            # One drain, shared with the follow path. Stopping at the first page showed
            # the OLDEST output and called it the log — the opposite of what someone
            # inspecting a failed build needs. Never blocks: it follows tokens already
            # issued and stops when the server stops issuing them.
            page, _, _ = ct_flow.drain_logs(client, name=name, build_id=target, on_event=collect)
    # The lines go in the PAYLOAD, not only through the renderer. `output.info` is
    # suppressed in JSON mode — which is the default whenever stdout is piped — so a
    # status-only payload meant `tamarind --json ct logs` returned no logs at all,
    # having just fetched every one of them.
    output.emit(
        {
            "buildId": target,
            "buildStatus": page.build_status,
            "error": page.error_message,
            "logs": collected,
        },
        state.output,
        human=f"build {target}: {page.build_status}",
    )


@app.command()
def cancel(
    ctx: typer.Context,
    name: str = typer.Argument(..., help="Tool id."),
    build_id: Optional[str] = typer.Option(
        None, "--build-id", help="Defaults to the in-flight build."
    ),
) -> None:
    """Stop a build that is still running."""
    state = ctx.obj
    with state.rest_client() as client:
        target = build_id
        if target is None:
            target = ct.plan.cancellable_build_id(ct.get_versions(client, name=name))
            if not target:
                # Deliberately an error rather than a silent no-op: "cancelled" on a
                # finished build reads as success and hides that nothing happened.
                raise ValidationError(f"'{name}' has no build in progress to cancel.")
        resp = ct.cancel_build(client, name=name, build_id=target)
    output.emit(resp, state.output, human=f"cancelled build {target}")


@app.command()
def config(
    ctx: typer.Context,
    name: Optional[str] = typer.Argument(None, help="Tool id. Defaults to .tamarind."),
    apply: Optional[Path] = typer.Option(
        None,
        "--apply",
        help="Push this folder's config.json in place — no build, no new version.",
    ),
    version: Optional[str] = typer.Option(
        None, "--version", help="With --apply: amend this built version's inputs."
    ),
    gpu_type: Optional[str] = typer.Option(None, "--gpu-type", help="None|T4|L4|L40S|A10|A100."),
    memory: Optional[str] = typer.Option(None, "--memory", help="e.g. 8Gi, 32Gi, 180Gi."),
    cpu: Optional[int] = typer.Option(None, "--cpu", help="1-8."),
    home_disk_gi: Optional[int] = typer.Option(None, "--home-disk-gi", help="1-50."),
    display_name: Optional[str] = typer.Option(None, "--display-name"),
    description: Optional[str] = typer.Option(None, "--description"),
    env: Optional[list[str]] = typer.Option(
        None,
        "--env",
        "-e",
        metavar="KEY=VALUE",
        help="Set a run-time environment variable. Repeatable. Merges with existing.",
    ),
) -> None:
    """Read or change a tool's resources, metadata, and environment.

    Never builds and never creates a version — changes apply to the next run. Inputs
    are NOT settable here: config.json in the repo is canonical for those, so changing
    one means editing that file and deploying.

    `--env` is the answer to "where do I put my API key", since a credential file in
    the source archive would be baked into a readable image layer. Values are sent to
    the server and stored on the tool, so they are not secrets FROM Tamarind — they
    are secrets from anyone who can read your tool's source.
    """
    state = ctx.obj
    tool = ct_project.resolve_name(apply or Path.cwd(), name)
    if apply is not None:
        # --apply pushes config.json and nothing else. Accepting the other flags
        # alongside it and reporting success discarded them silently — worst with
        # --env, where the command would claim to have stored a credential it never
        # sent. Refused rather than half-applied.
        ignored = [
            flag
            for flag, value in (
                ("--env", env),
                ("--gpu-type", gpu_type),
                ("--memory", memory),
                ("--cpu", cpu),
                ("--home-disk-gi", home_disk_gi),
                ("--display-name", display_name),
                ("--description", description),
            )
            # `is not None`, not truthiness: `--cpu 0` is a supplied flag with a falsey
            # value, so the truthy filter dropped it and applied config.json alone while
            # reporting success — the exact silent discard this check was added to stop.
            if value is not None
        ]
        if ignored:
            raise ValidationError(
                f"--apply only pushes config.json, so {', '.join(ignored)} would be "
                f"ignored. Run them as a separate `tamarind ct config` call."
            )
        with state.rest_client() as client:
            ct.flow.apply_config(client, name=tool, folder=apply, target_version=version)
        output.emit(
            {"tool": tool, "applied": str(Path(apply) / "config.json"), "version": version},
            state.output,
            human=(
                f"applied {tool}'s config.json"
                + (f" to {version}" if version else "")
                + " — no build, no new version"
            ),
        )
        return
    name = tool
    changes = {
        "gpuType": gpu_type,
        "memory": memory,
        "cpu": cpu,
        "homeDiskGi": home_disk_gi,
        "displayName": display_name,
        "description": description,
    }
    changes = {k: v for k, v in changes.items() if v is not None}
    with state.rest_client() as client:
        if env:
            # Read-modify-write, because the server replaces the whole map: sending
            # only the new pair would silently delete every variable already set.
            current = ct.get_tool(client, name=name)
            merged = dict(current.raw.get("latest", current.raw).get("envVars") or {})
            merged.update(ct.parse_env_assignments(env))
            changes["envVars"] = merged
        tool = (
            ct.update_tool(client, name=name, **changes)
            if changes
            else ct.get_tool(client, name=name)
        )
    latest = tool.raw.get("latest", tool.raw)
    shown = {
        k: latest.get(k)
        for k in ("gpuType", "memory", "cpu", "homeDiskGi", "displayName", "description")
    }
    # NAMES only. These are the values someone just stored with `--env`, i.e. exactly
    # the API keys this command exists to keep out of the source archive — and JSON is
    # the default the moment stdout is piped, so printing them puts credentials into CI
    # logs. The names are what a caller actually needs to confirm the write landed.
    env_vars = latest.get("envVars")
    shown["envVarNames"] = sorted(env_vars) if isinstance(env_vars, dict) else []
    output.emit(
        shown,
        state.output,
        human="\n".join(f"{k}: {v}" for k, v in shown.items() if v not in (None, [])),
    )


@app.command()
def clone(
    ctx: typer.Context,
    name: str = typer.Argument(..., help="Tool id."),
    dest: Optional[Path] = typer.Argument(None, help="Destination. Defaults to ./<name>."),
    version: Optional[str] = typer.Option(None, "--version", help="Version to fetch."),
    force: bool = typer.Option(
        False, "--force", help="Extract into a non-empty destination, overwriting files."
    ),
) -> None:
    """Download a tool's source, so you can edit it and deploy it back.

    Refuses a destination that already has files in it. Extraction overwrites without
    asking, so re-running `clone` in a folder you have been editing would silently
    destroy that work — and `clone name .` is an easy way to ask for exactly that.
    """
    state = ctx.obj
    # The same guard `init` uses. Two copies of it drifted once already: both crashed
    # with a raw NotADirectoryError when the destination was an existing FILE.
    target = ct_flow.ensure_usable_destination(
        Path(dest) if dest else Path.cwd() / name, allow_nonempty=force
    )

    with state.rest_client() as client:
        ref = None
        if version:
            found = ct.plan.find_version(ct.get_versions(client, name=name), version)
            if found is None:
                raise ValidationError(f"'{name}' has no version {version}.")
            if not found.ref:
                # A null ref would fall through to "no ref parameter", which fetches the
                # tool's CURRENT source — a different tree, reported as the version the
                # user asked for. The pinned-submit path already refuses this.
                raise ValidationError(
                    f"Version {version} of '{name}' records no source ref, so its exact "
                    f"tree cannot be fetched. `tamarind ct clone {name}` gets the current "
                    f"source instead."
                )
            ref = found.ref
        _, pointer_paths = ct.flow.fetch_source(client, name=name, destination=target, ref=ref)

    # THIRD write site for the marker, and the one that was missing. A clone into a
    # differently-named folder left no record, so the next bare `deploy` fell back to
    # the folder name and targeted another tool — and with --force a stale marker from
    # the directory's previous occupant would have survived and pointed somewhere else
    # entirely. Written after extraction succeeds, so a failed clone leaves no claim.
    ct_project.write(target, name=name)

    pointers = [Path(p).name for p in pointer_paths]
    if pointers:
        output.info(
            f"warning: {len(pointers)} file(s) came down as Git-LFS pointers, not "
            f"content ({', '.join(sorted(pointers)[:3])}…). Deploying this folder as-is "
            f"would upload the pointers.",
            state.output,
        )
    output.emit(
        {"tool": name, "path": str(target), "lfsPointers": pointers},
        state.output,
        human=f"cloned {name} to {target}",
    )


def _is_lfs_pointer(path: Path) -> bool:
    """Whether a file is a Git-LFS pointer rather than its content.

    Archives serve LFS-tracked files as pointers, matching GitHub and GitLab, so a
    clone of a tool with large assets is not immediately redeployable — worth saying
    rather than letting the next build fail confusingly.
    """
    try:
        with path.open("rb") as fh:
            return fh.read(45).startswith(b"version https://git-lfs.github.com/spec")
    except OSError:
        return False


@app.command()
def delete(
    ctx: typer.Context,
    name: str = typer.Argument(..., help="Tool id."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip the confirmation."),
) -> None:
    """Permanently delete a tool and its source. There is no recycle bin."""
    state = ctx.obj
    output.confirm_destructive(
        f"delete custom tool '{name}' and all its source", yes=yes, mode=state.output
    )
    with state.rest_client() as client:
        ct.delete_tool(client, name=name)
    output.emit({"tool": name, "deleted": True}, state.output, human=f"deleted {name}")
