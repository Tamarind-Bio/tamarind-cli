"""The custom-tools boundary: raw payloads in, frozen types out.

Everything the package knows about the shape of a custom-tool response lives here.

One distinction is load-bearing enough to be types rather than strings: a **version**
and a **build** report different vocabularies, and they overlap on the word "Stopped".
A version is Queued/Claimed/Running/Complete/Stopped; a build is CodeBuild's
SUCCEEDED/FAILED/STOPPED/FAULT/TIMED_OUT/CLIENT_ERROR/IN_PROGRESS. Conflating them
produced a real bug in the platform's own backend — a terminal set missing FAULT and
CLIENT_ERROR would leave a poll loop running forever on either.

Tolerant in, strict out, as elsewhere: an unrecognized payload yields a value with
null fields and the original mapping on ``raw`` rather than raising.

Pure: no network, no clock, no filesystem.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

# A BUILD's terminal states, in CodeBuild's vocabulary. All six: a poll loop that
# watches only SUCCEEDED/FAILED runs forever when a build FAULTs or is rejected as a
# CLIENT_ERROR, which is a hang rather than an error — the worse failure.
TERMINAL_BUILD_STATUSES = frozenset(
    {"SUCCEEDED", "FAILED", "STOPPED", "FAULT", "TIMED_OUT", "CLIENT_ERROR"}
)
SUCCESSFUL_BUILD_STATUS = "SUCCEEDED"

# A VERSION's states. Note "Stopped" appears here AND in the build vocabulary above
# meaning something different, which is exactly why these are not interchangeable.
# A failed build leaves its version Stopped — there is no version state called FAILED.
COMPLETE_VERSION_STATUS = "Complete"
IN_FLIGHT_VERSION_STATUSES = frozenset({"Queued", "Claimed", "Running"})

# What `deploy` did. Discriminates the three outcomes the endpoint can produce.
DEPLOY_PATHS = frozenset({"noop", "saved", "building"})


@dataclass(frozen=True)
class Tool:
    """A custom tool's detail. ``raw`` keeps the server's full answer for rendering."""

    name: str | None = None
    status: str | None = None
    published: bool = False
    # Gitea main HEAD. Null when the repo is empty, the tool has no source, or Gitea is
    # unreachable, so a null reads as "not yet" rather than "never".
    #
    # NOT the signal that an upload landed, though it looks like one: an identical
    # re-upload produces no commit, so this never moves for the single most common
    # deploy in CI. It answers "did the content change", which is a different question.
    current_source_ref: str | None = None
    # Stamped by the extractor on EVERY successful extraction, including one whose tree
    # matched and produced no commit. That is what makes it the completion signal the
    # ref cannot be: it distinguishes "identical, and done" from "not finished yet".
    last_updated_at: str | None = None
    # Set when extraction FAILED (bad zip, LFS pointers, Gitea unreachable). Non-null
    # turns a wait into an immediate, specific error instead of a silent timeout.
    connection_error: str | None = None
    latest_build_id: str | None = None
    latest_build_status: str | None = None
    # Non-null while a publish has been accepted but the default-version pointer has
    # not propagated yet.
    publish_pending_version: str | None = None
    has_source: bool = False
    can_deploy: bool = False
    raw: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Version:
    """One version of a tool. ``status`` is a VERSION status, not a build status."""

    name: str | None = None
    status: str | None = None
    build_id: str | None = None
    ref: str | None = None
    error_message: str | None = None
    created_by: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict)

    @property
    def is_complete(self) -> bool:
        return self.status == COMPLETE_VERSION_STATUS

    @property
    def is_in_flight(self) -> bool:
        return self.status in IN_FLIGHT_VERSION_STATUSES


@dataclass(frozen=True)
class DeployResult:
    """What the deploy endpoint reported. ``path`` is noop | saved | building."""

    version_name: str | None = None
    path: str | None = None
    build_id: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class UploadTicket:
    """A presigned destination for the source archive."""

    upload_id: str | None = None
    upload_url: str | None = None
    expires_in: int | None = None
    raw: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class LogLine:
    message: str
    timestamp: int | None = None


@dataclass(frozen=True)
class LogPage:
    """One page of build output. ``build_status`` is a BUILD status."""

    build_status: str | None = None
    lines: tuple[LogLine, ...] = ()
    next_token: str | None = None
    error_message: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict)


def _str_or_none(value: Any) -> str | None:
    return str(value) if value not in (None, "") else None


def parse_tool(payload: Any) -> Tool:
    """Normalize a tool-detail payload. Never raises.

    The endpoint nests the tool under ``latest`` and hangs build/publish/source fields
    off the envelope, so both levels are read here rather than at each call site.
    """
    if not isinstance(payload, Mapping):
        return Tool()
    nested = payload.get("latest")
    inner: Mapping[str, Any] = nested if isinstance(nested, Mapping) else payload
    return Tool(
        name=_str_or_none(inner.get("name")),
        status=_str_or_none(inner.get("status")),
        published=bool(inner.get("published")),
        current_source_ref=_str_or_none(payload.get("currentSourceRef")),
        last_updated_at=_str_or_none(inner.get("lastUpdatedAt")),
        connection_error=_str_or_none(inner.get("connectionError")),
        latest_build_id=_str_or_none(payload.get("latestBuildId")),
        latest_build_status=_str_or_none(payload.get("latestBuildStatus")),
        publish_pending_version=_str_or_none(payload.get("publishPendingVersion")),
        has_source=bool(inner.get("hasSource")),
        can_deploy=bool(inner.get("canDeploy")),
        raw=payload,
    )


def parse_version(payload: Any) -> Version:
    """Normalize one version row. Never raises."""
    if not isinstance(payload, Mapping):
        return Version()
    return Version(
        name=_str_or_none(payload.get("versionName")),
        status=_str_or_none(payload.get("status")),
        build_id=_str_or_none(payload.get("buildId")),
        ref=_str_or_none(payload.get("ref")),
        error_message=_str_or_none(payload.get("errorMessage")),
        created_by=_str_or_none(payload.get("createdBy")),
        raw=payload,
    )


def parse_versions(payload: Any) -> tuple[Version, ...]:
    """Normalize a version list, newest first as the endpoint returns it.

    Non-mapping entries are dropped rather than parsed to blanks: a blank Version has
    no name, and a nameless version in a list is indistinguishable from a real one that
    failed to parse — which is how a selection function ends up choosing nothing.
    """
    if not isinstance(payload, (list, tuple)):
        return ()
    return tuple(parse_version(v) for v in payload if isinstance(v, Mapping))


def parse_deploy_result(payload: Any) -> DeployResult:
    """Normalize the deploy response. Never raises.

    An unrecognized ``path`` is left as-is rather than coerced: the caller decides what
    to do with a value the server invented, and silently mapping it onto a known path
    would be worse than reporting it.
    """
    if not isinstance(payload, Mapping):
        return DeployResult()
    return DeployResult(
        version_name=_str_or_none(payload.get("versionName")),
        path=_str_or_none(payload.get("path")),
        build_id=_str_or_none(payload.get("buildId")),
        raw=payload,
    )


def parse_upload_ticket(payload: Any) -> UploadTicket:
    """Normalize the upload-init response. Never raises."""
    if not isinstance(payload, Mapping):
        return UploadTicket()
    expires = payload.get("expiresIn")
    return UploadTicket(
        upload_id=_str_or_none(payload.get("uploadId")),
        upload_url=_str_or_none(payload.get("uploadUrl")),
        expires_in=expires if isinstance(expires, int) else None,
        raw=payload,
    )


def parse_log_page(payload: Any) -> LogPage:
    """Normalize a page of build output. Never raises."""
    if not isinstance(payload, Mapping):
        return LogPage()
    raw_lines = payload.get("logs")
    lines: tuple[LogLine, ...] = ()
    if isinstance(raw_lines, (list, tuple)):
        lines = tuple(
            LogLine(
                message=str(entry.get("message", "")),
                timestamp=entry.get("timestamp")
                if isinstance(entry.get("timestamp"), int)
                else None,
            )
            for entry in raw_lines
            if isinstance(entry, Mapping)
        )
    return LogPage(
        build_status=_str_or_none(payload.get("buildStatus")),
        lines=lines,
        next_token=_str_or_none(payload.get("nextToken")),
        error_message=_str_or_none(payload.get("errorMessage")),
        raw=payload,
    )
