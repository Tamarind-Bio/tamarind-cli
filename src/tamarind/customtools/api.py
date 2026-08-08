"""Custom-tool endpoints: one function per operation, client in, wire types out.

All of these live under the `v2/` prefix, which the website rewrites onto the backend's
`/api/v1/*`. There is no second base URL and no separate credential — the same
`HTTPClient` the job surface uses reaches these with the same API key.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any

from ..http import HTTPClient
from . import wire

_PREFIX = "v2/custom-tools"


# ------------------------------------------------------------------- lifecycle ----


def create_tool(
    client: HTTPClient,
    *,
    name: str,
    display_name: str | None = None,
    description: str | None = None,
    template: str | None = None,
) -> wire.Tool:
    """POST v2/custom-tools — create a tool. ``name`` is permanent.

    ``template="scratch"`` asks the server to seed the repo with a working Dockerfile,
    run.sh, requirements.txt, main.py and config.json — which is why `init` does not
    ship its own copies of those files.
    """
    body: dict[str, Any] = {"name": name}
    if display_name is not None:
        body["displayName"] = display_name
    if description is not None:
        body["description"] = description
    if template is not None:
        body["template"] = template
    return wire.parse_tool(client.post_json(_PREFIX, json=body))


def list_tools(
    client: HTTPClient, *, status: str | None = None, published: bool | None = None
) -> Any:
    """GET v2/custom-tools — the org's own custom tools."""
    params: dict[str, Any] = {"status": status}
    if published is not None:
        params["published"] = "true" if published else "false"
    return client.get_json(_PREFIX, params=params)


def get_tool(client: HTTPClient, *, name: str) -> wire.Tool:
    """GET v2/custom-tools/{name} — detail, latest build, and currentSourceRef."""
    return wire.parse_tool(client.get_json(f"{_PREFIX}/{name}"))


def update_tool(client: HTTPClient, *, name: str, **fields: Any) -> wire.Tool:
    """PUT v2/custom-tools/{name} — tool-level metadata and resources.

    Never builds and never mints a version. Inputs and outputs are deliberately NOT
    accepted here: config.json in the repo is canonical for those, and one funnel owns
    writing the file and mirroring it, so changing an input means editing the file and
    deploying.
    """
    body = {k: v for k, v in fields.items() if v is not None}
    return wire.parse_tool(client.put_json(f"{_PREFIX}/{name}", json=body))


def save_config(
    client: HTTPClient, *, name: str, config_json: str, target_version: str | None = None
) -> Any:
    """PUT v2/custom-tools/{name}/config — apply config.json in place.

    No new version, no rebuild. ``target_version`` amends that version's snapshotted
    inputs, which is the only way to correct a schema on a version that already built.
    """
    body: dict[str, Any] = {"configJsonBytes": config_json}
    if target_version is not None:
        body["targetVersion"] = target_version
    return client.put_json(f"{_PREFIX}/{name}/config", json=body)


def delete_tool(client: HTTPClient, *, name: str) -> Any:
    """DELETE v2/custom-tools/{name} — hard-deletes the tool and its repo."""
    return client.delete_json(f"{_PREFIX}/{name}")


# ---------------------------------------------------------------------- source ----


def init_upload(client: HTTPClient, *, name: str) -> wire.UploadTicket:
    """POST .../uploads/init — a presigned destination for the source archive."""
    return wire.parse_upload_ticket(client.post_json(f"{_PREFIX}/{name}/uploads/init"))


def finalize_upload(client: HTTPClient, *, name: str, upload_id: str) -> Any:
    """POST .../uploads/{id}/finalize — hand the staged archive to the extractor.

    Returns immediately with ``sourceHash="pending"``: extraction runs in a background
    task AFTER the response is sent. Nothing in this response indicates the source has
    landed, which is why `flow.wait_for_source` exists at all.
    """
    return client.post_json(f"{_PREFIX}/{name}/uploads/{upload_id}/finalize")


def download_archive(
    client: HTTPClient, *, name: str, ref: str | None = None, destination: Path | None = None
) -> Path:
    """GET .../archive — the tool's source as a zip, written to ``destination``.

    Streamed to disk rather than returned as bytes. Sources are allowed up to 5 GiB, and
    buffering the whole body to hand back a `bytes` made a large-but-valid tool an
    out-of-memory crash on the client; it also ran the download under the ordinary
    request timeout, which a multi-gigabyte body will not finish inside.

    LFS-tracked files arrive as pointer files rather than content, matching how GitHub
    and GitLab serve archives, so a clone of a tool with large assets is not
    immediately redeployable.
    """
    params = {"ref": ref} if ref else None
    if destination is not None:
        target = Path(destination)
    else:
        # mkstemp hands back an OPEN descriptor. Dropping it leaks one per download,
        # and a long-lived process cloning repeatedly runs out — so it is closed here
        # rather than relying on the second `open` below to somehow account for it.
        handle_fd, temp_name = tempfile.mkstemp(suffix=".zip")
        os.close(handle_fd)
        target = Path(temp_name)
    with client.stream("GET", f"{_PREFIX}/{name}/archive", params=params) as response:
        with target.open("wb") as handle:
            for chunk in response.iter_bytes():
                handle.write(chunk)
    return target


# ---------------------------------------------------------------------- deploy ----


def deploy(
    client: HTTPClient, *, name: str, carry_forward_from_version: str | None = None
) -> wire.DeployResult:
    """POST .../deploy — build at the repository's CURRENT head.

    The response's ``path`` discriminates noop / saved / building. Note what this does
    NOT do: it does not upload anything and it does not wait for one. It builds
    whatever is committed at the moment it runs.
    """
    body: dict[str, Any] = {}
    if carry_forward_from_version is not None:
        body["carryForwardFromVersion"] = carry_forward_from_version
    return wire.parse_deploy_result(client.post_json(f"{_PREFIX}/{name}/deploy", json=body))


def cancel_build(client: HTTPClient, *, name: str, build_id: str) -> Any:
    """POST .../cancel — stop an in-progress build."""
    return client.post_json(f"{_PREFIX}/{name}/cancel", params={"buildId": build_id})


def get_logs(
    client: HTTPClient, *, name: str, build_id: str, next_token: str | None = None
) -> wire.LogPage:
    """GET .../logs — one page of build output plus the build's status.

    Not a pure read: polling this also reconciles build state, so it is one of the
    paths that advances the queue when a completion event is missed.
    """
    params: dict[str, Any] = {"buildId": build_id}
    if next_token:
        params["nextToken"] = next_token
    return wire.parse_log_page(client.get_json(f"{_PREFIX}/{name}/logs", params=params))


# -------------------------------------------------------------------- versions ----


def get_versions(client: HTTPClient, *, name: str) -> tuple[wire.Version, ...]:
    """GET .../versions — newest first; legacy unnamed rows are filtered server-side."""
    return wire.parse_versions(client.get_json(f"{_PREFIX}/{name}/versions"))


def publish_version(client: HTTPClient, *, name: str, version_name: str) -> wire.Tool:
    """POST .../publish/{version} — activate a version AND publish it org-wide.

    Two effects in one call: it swaps the image pointer and sets published. Publishing
    hands every org member the viewer role — read and run, but not the source.
    """
    return wire.parse_tool(client.post_json(f"{_PREFIX}/{name}/publish/{version_name}"))
