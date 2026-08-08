"""Custom tools: create, deploy, publish.

The fourth resource, in the package's standard shape — `wire` (the boundary), `api`
(endpoints), `plan` (pure decisions), `flow` (orchestration that owns the clock), plus
`packaging`/`archive` for deciding and writing the source upload.

The public surface is re-exported here, so a script can drive the whole lifecycle:

    from tamarind import customtools
    from tamarind.config import load_config
    from tamarind.http import HTTPClient

    cfg = load_config()
    client = HTTPClient(cfg.api_base, cfg.api_key)
    outcome = customtools.build(client, name="my-tool", folder="./my-tool")
    if outcome.deployed:
        customtools.publish(client, name="my-tool", version_name=outcome.version_name)

`build` is the one to read first — the sequence in `flow` is load-bearing, and the
comment there explains which step exists because of which race.
"""

from __future__ import annotations

from . import api, archive, flow, packaging, plan, project, wire
from .api import (
    cancel_build,
    create_tool,
    delete_tool,
    download_archive,
    get_logs,
    get_tool,
    get_versions,
    list_tools,
    publish_version,
    save_config,
    update_tool,
)
from .archive import MAX_SOURCE_BYTES, ArchivePlan, plan_archive
from .flow import (
    BuildEvent,
    apply_config,
    build,
    init,
    publish,
    unpack_source,
    wait_for_build,
    wait_for_source,
)
from .packaging import Disposition, classify
from .plan import DeployOutcome, is_terminal_build, select_publishable
from .wire import DeployResult, LogPage, Tool, UploadTicket, Version

__all__ = [
    "unpack_source",
    "init",
    "apply_config",
    "project",
    "MAX_SOURCE_BYTES",
    "ArchivePlan",
    "BuildEvent",
    "DeployOutcome",
    "DeployResult",
    "Disposition",
    "LogPage",
    "Tool",
    "UploadTicket",
    "Version",
    "api",
    "archive",
    "build",
    "cancel_build",
    "classify",
    "create_tool",
    "delete_tool",
    "download_archive",
    "flow",
    "get_logs",
    "get_tool",
    "get_versions",
    "is_terminal_build",
    "list_tools",
    "packaging",
    "plan",
    "plan_archive",
    "publish",
    "publish_version",
    "save_config",
    "select_publishable",
    "update_tool",
    "wait_for_build",
    "wait_for_source",
    "wire",
]
