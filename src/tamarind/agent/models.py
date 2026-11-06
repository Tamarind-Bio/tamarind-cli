"""Typed views of the Agent API's JSON objects.

Each model reads the fields the spec names (camelCase on the wire, snake_case here) and
keeps the whole object as ``raw``. The contract says clients MUST ignore unknown fields
and that new fields and enum values arrive without a version bump, so parsing never
rejects an extra field or an enum value it does not know: enum-valued fields are plain
strings. A required field that is missing, or a field of the wrong JSON type, is a
contract break and raises :class:`~tamarind.errors.TamarindError`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Generic, Mapping, TypeVar

from tamarind.errors import TamarindError

from ._contract import FINAL_MESSAGE_STATUSES

T = TypeVar("T")
_MISSING = object()


class ContractError(TamarindError):
    """An Agent API response did not have the shape the pinned contract describes."""


def _get(wire: Mapping[str, Any], key: str, kinds: tuple[type, ...], *, required: bool,
         nullable: bool = True) -> Any:
    value = wire.get(key, _MISSING)
    if value is _MISSING:
        if required:
            raise ContractError(f"Agent API response is missing '{key}'.")
        return None
    if value is None:
        if nullable:
            return None
        raise ContractError(f"Agent API response has a null '{key}'.")
    # bool is an int subclass: a JSON true is never a number here.
    if isinstance(value, bool) and bool not in kinds:
        raise ContractError(f"Agent API response field '{key}' has the wrong type.")
    if not isinstance(value, kinds):
        raise ContractError(f"Agent API response field '{key}' has the wrong type.")
    return value


def _str(wire: Mapping[str, Any], key: str, *, required: bool = False) -> Any:
    return _get(wire, key, (str,), required=required, nullable=not required)


def _num(wire: Mapping[str, Any], key: str, *, required: bool = False) -> Any:
    value = _get(wire, key, (int, float), required=required, nullable=True)
    return float(value) if value is not None else None


def _int(wire: Mapping[str, Any], key: str) -> Any:
    return _get(wire, key, (int,), required=False)


def _bool(wire: Mapping[str, Any], key: str) -> Any:
    return _get(wire, key, (bool,), required=False)


def _obj(wire: Mapping[str, Any], key: str) -> Any:
    return _get(wire, key, (dict,), required=False)


def _list(wire: Mapping[str, Any], key: str, *, required: bool = False) -> list[Any]:
    value = _get(wire, key, (list,), required=required)
    return value if value is not None else []


def _objects(wire: Mapping[str, Any], key: str, parse: Callable[[Any], T], *,
             required: bool = False) -> tuple[T, ...]:
    items = _list(wire, key, required=required)
    return tuple(parse(_as_object(item)) for item in items)


def _as_object(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ContractError("Agent API response item is not an object.")
    return value


def _strings(wire: Mapping[str, Any], key: str) -> tuple[str, ...]:
    items = _list(wire, key)
    if any(not isinstance(item, str) for item in items):
        raise ContractError(f"Agent API response field '{key}' is not a list of strings.")
    return tuple(items)


@dataclass(frozen=True)
class Page(Generic[T]):
    """One page of a list. Pass ``next_cursor`` as ``cursor`` for the next; None is the last."""

    items: tuple[T, ...]
    next_cursor: str | None = None


def page_of(wire: Any, parse: Callable[[dict[str, Any]], T], *, cursor: bool = True) -> Page[T]:
    body = _as_object(wire)
    items = _objects(body, "data", parse, required=True)
    return Page(items=items, next_cursor=_str(body, "nextCursor") if cursor else None)


# ── usage ──

@dataclass(frozen=True)
class TokenCounts:
    input: int
    output: int
    cache_read: int
    cache_write: int

    @classmethod
    def from_wire(cls, wire: dict[str, Any]) -> "TokenCounts":
        def need(key: str) -> int:
            value = _get(wire, key, (int,), required=True, nullable=False)
            return int(value)
        return cls(need("input"), need("output"), need("cacheRead"), need("cacheWrite"))


@dataclass(frozen=True)
class ModelUsage:
    model: str
    usd: float
    hours: float | None
    tokens: TokenCounts

    @classmethod
    def from_wire(cls, wire: dict[str, Any]) -> "ModelUsage":
        tokens = _get(wire, "tokens", (dict,), required=True, nullable=False)
        return cls(
            model=_str(wire, "model", required=True),
            usd=_num(wire, "usd", required=True),
            hours=_num(wire, "hours"),
            tokens=TokenCounts.from_wire(tokens),
        )


@dataclass(frozen=True)
class Usage:
    """What the agent cost. ``month``/``remaining_hours`` are set by ``usage.month`` only."""

    agent_hours: float
    jobs_hours: float
    total_hours: float
    agent_usd: float | None = None
    cap_hours: float | None = None
    tokens: TokenCounts | None = None
    by_model: tuple[ModelUsage, ...] = ()
    month: str | None = None
    remaining_hours: float | None = None
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_wire(cls, wire: dict[str, Any]) -> "Usage":
        tokens = _obj(wire, "tokens")
        return cls(
            agent_hours=_num(wire, "agentHours", required=True),
            jobs_hours=_num(wire, "jobsHours", required=True),
            total_hours=_num(wire, "totalHours", required=True),
            agent_usd=_num(wire, "agentUsd"),
            cap_hours=_num(wire, "capHours"),
            tokens=TokenCounts.from_wire(tokens) if tokens is not None else None,
            by_model=_objects(wire, "byModel", ModelUsage.from_wire),
            month=_str(wire, "month"),
            remaining_hours=_num(wire, "remainingHours"),
            raw=wire,
        )


# ── chats ──

@dataclass(frozen=True)
class Budget:
    cap_hours: float | None
    used_hours: float | None
    per_job_hours: float | None

    @classmethod
    def from_wire(cls, wire: dict[str, Any]) -> "Budget":
        return cls(_num(wire, "capHours"), _num(wire, "usedHours"), _num(wire, "perJobHours"))


@dataclass(frozen=True)
class Campaign:
    """A chat's campaign, read on :attr:`Chat.campaign`; change it with ``chats.update``."""

    id: str
    engine: str
    workflow: str
    status: str
    plan: Mapping[str, Any] | None
    candidate_count: int | None
    paused_workflows: tuple[Mapping[str, Any], ...]
    started_at: str | None
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_wire(cls, wire: dict[str, Any]) -> "Campaign":
        return cls(
            id=_str(wire, "id", required=True),
            engine=_str(wire, "engine", required=True),
            workflow=_str(wire, "workflow", required=True),
            status=_str(wire, "status", required=True),
            plan=_obj(wire, "plan"),
            candidate_count=_int(wire, "candidateCount"),
            paused_workflows=_objects(wire, "pausedWorkflows", lambda item: item),
            started_at=_str(wire, "startedAt"),
            raw=wire,
        )


@dataclass(frozen=True)
class Chat:
    id: str
    title: str
    status: str
    source: str
    created_at: str
    updated_at: str
    # Not in ``chats.list`` items (the list says only whether the chat is working).
    active_message_ids: tuple[str, ...] = ()
    effort: str | None = None
    agent_id: str | None = None
    budget: Budget | None = None
    auto_approve: bool | None = None
    mode: str | None = None
    workflow: str | None = None
    campaign: Campaign | None = None
    usage: Usage | None = None
    web_url: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_wire(cls, wire: dict[str, Any]) -> "Chat":
        budget = _obj(wire, "budget")
        campaign = _obj(wire, "campaign")
        usage = _obj(wire, "usage")
        return cls(
            id=_str(wire, "id", required=True),
            title=_str(wire, "title", required=True),
            status=_str(wire, "status", required=True),
            source=_str(wire, "source", required=True),
            created_at=_str(wire, "createdAt", required=True),
            updated_at=_str(wire, "updatedAt", required=True),
            active_message_ids=_strings(wire, "activeMessageIds"),
            effort=_str(wire, "effort"),
            agent_id=_str(wire, "agentId"),
            budget=Budget.from_wire(budget) if budget is not None else None,
            auto_approve=_bool(wire, "autoApprove"),
            mode=_str(wire, "mode"),
            workflow=_str(wire, "workflow"),
            campaign=Campaign.from_wire(campaign) if campaign is not None else None,
            usage=Usage.from_wire(usage) if usage is not None else None,
            web_url=_str(wire, "webUrl"),
            raw=wire,
        )


@dataclass(frozen=True)
class ArchivedChat:
    id: str
    status: str
    campaigns_stopping: tuple[str, ...]

    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_wire(cls, wire: dict[str, Any]) -> "ArchivedChat":
        return cls(
            id=_str(wire, "id", required=True),
            status=_str(wire, "status", required=True),
            campaigns_stopping=_strings(wire, "campaignsStopping"),
            raw=wire,
        )


# ── messages ──

@dataclass(frozen=True)
class Step:
    id: str
    kind: str
    title: str
    status: str
    subagent_id: str | None = None

    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_wire(cls, wire: dict[str, Any]) -> "Step":
        return cls(
            id=_str(wire, "id", required=True),
            kind=_str(wire, "kind", required=True),
            title=_str(wire, "title", required=True),
            status=_str(wire, "status", required=True),
            subagent_id=_str(wire, "subagentId"),
            raw=wire,
        )


@dataclass(frozen=True)
class Approval:
    """A paused action. ``detail`` is what the web app's card shows, as written."""

    id: str
    status: str
    kind: str
    summary: str
    created_at: str
    message_id: str | None = None
    detail: Mapping[str, Any] = field(default_factory=dict)
    estimate: Mapping[str, Any] | None = None
    expires_at: str | None = None
    resolved_at: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_wire(cls, wire: dict[str, Any]) -> "Approval":
        return cls(
            id=_str(wire, "id", required=True),
            status=_str(wire, "status", required=True),
            kind=_str(wire, "kind", required=True),
            summary=_str(wire, "summary", required=True),
            created_at=_str(wire, "createdAt", required=True),
            message_id=_str(wire, "messageId"),
            detail=_obj(wire, "detail") or {},
            estimate=_obj(wire, "estimate"),
            expires_at=_str(wire, "expiresAt"),
            resolved_at=_str(wire, "resolvedAt"),
            raw=wire,
        )


@dataclass(frozen=True)
class Question:
    """The agent asking you to choose. Answer with ``questions.answer``."""

    id: str
    status: str
    questions: tuple[Mapping[str, Any], ...]
    created_at: str
    message_id: str | None = None
    answers: Mapping[str, str] | None = None
    expires_at: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_wire(cls, wire: dict[str, Any]) -> "Question":
        return cls(
            id=_str(wire, "id", required=True),
            status=_str(wire, "status", required=True),
            questions=_objects(wire, "questions", lambda item: item, required=True),
            created_at=_str(wire, "createdAt", required=True),
            message_id=_str(wire, "messageId"),
            answers=_obj(wire, "answers"),
            expires_at=_str(wire, "expiresAt"),
            raw=wire,
        )


@dataclass(frozen=True)
class Message:
    """Yours (``role == "user"``) or one agent reply (``role == "assistant"``).

    ``content`` keeps each part as the wire object (``{"type": "text"|"file"|"step", ...}``):
    new part types may appear, and a script should skip ones it does not know.
    """

    id: str
    chat_id: str
    role: str
    content: tuple[Mapping[str, Any], ...]
    created_at: str
    status: str | None = None
    started_by: str | None = None
    in_reply_to: str | None = None
    continued_by: str | None = None
    incomplete_reason: str | None = None
    error: Mapping[str, Any] | None = None
    model: str | None = None
    pending_approvals: tuple[Approval, ...] = ()
    pending_questions: tuple[Question, ...] = ()
    usage: Usage | None = None
    completed_at: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_wire(cls, wire: dict[str, Any]) -> "Message":
        usage = _obj(wire, "usage")
        return cls(
            id=_str(wire, "id", required=True),
            chat_id=_str(wire, "chatId", required=True),
            role=_str(wire, "role", required=True),
            content=_objects(wire, "content", lambda item: item, required=True),
            created_at=_str(wire, "createdAt", required=True),
            status=_str(wire, "status"),
            started_by=_str(wire, "startedBy"),
            in_reply_to=_str(wire, "inReplyTo"),
            continued_by=_str(wire, "continuedBy"),
            incomplete_reason=_str(wire, "incompleteReason"),
            error=_obj(wire, "error"),
            model=_str(wire, "model"),
            # A `message.requires_action` event carries the cards as `approvals` too; take
            # them when `pendingApprovals` is empty, so the reply names its own cards.
            pending_approvals=(_objects(wire, "pendingApprovals", Approval.from_wire)
                               or _objects(wire, "approvals", Approval.from_wire)),
            pending_questions=_objects(wire, "pendingQuestions", Question.from_wire),
            usage=Usage.from_wire(usage) if usage is not None else None,
            completed_at=_str(wire, "completedAt"),
            raw=wire,
        )

    @property
    def text(self) -> str:
        """The reply's text parts, joined by blank lines."""
        return "\n\n".join(
            str(part.get("text") or "") for part in self.content if part.get("type") == "text"
        )

    @property
    def is_final(self) -> bool:
        return self.status in FINAL_MESSAGE_STATUSES


# ── files ──

@dataclass(frozen=True)
class File:
    id: str
    filename: str
    status: str
    path: str | None = None
    content_type: str | None = None
    size: int | None = None
    origin: str | None = None
    created_at: str | None = None

    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_wire(cls, wire: dict[str, Any]) -> "File":
        return cls(
            id=_str(wire, "id", required=True),
            filename=_str(wire, "filename", required=True),
            status=_str(wire, "status", required=True),
            path=_str(wire, "path"),
            content_type=_str(wire, "contentType"),
            size=_int(wire, "size"),
            origin=_str(wire, "origin"),
            created_at=_str(wire, "createdAt"),
            raw=wire,
        )


@dataclass(frozen=True)
class FileUpload:
    """An upload slot. ``upload_url`` is presigned: it is a credential, so do not log it."""

    file_id: str
    upload_url: str = field(repr=False)
    expires_at: str

    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_wire(cls, wire: dict[str, Any]) -> "FileUpload":
        return cls(
            file_id=_str(wire, "fileId", required=True),
            upload_url=_str(wire, "uploadUrl", required=True),
            expires_at=_str(wire, "expiresAt", required=True),
            raw=wire,
        )


# ── subagents ──

@dataclass(frozen=True)
class Subagent:
    id: str
    chat_id: str
    message_id: str
    name: str
    title: str
    status: str
    created_at: str
    instructions: str | None = None
    background: bool | None = None
    # Only on ``subagents.get``.
    steps: tuple[Step, ...] = ()
    result: str | None = None
    completed_at: str | None = None

    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_wire(cls, wire: dict[str, Any]) -> "Subagent":
        return cls(
            id=_str(wire, "id", required=True),
            chat_id=_str(wire, "chatId", required=True),
            message_id=_str(wire, "messageId", required=True),
            name=_str(wire, "name", required=True),
            title=_str(wire, "title", required=True),
            status=_str(wire, "status", required=True),
            created_at=_str(wire, "createdAt", required=True),
            instructions=_str(wire, "instructions"),
            background=_bool(wire, "background"),
            steps=_objects(wire, "steps", Step.from_wire),
            result=_str(wire, "result"),
            completed_at=_str(wire, "completedAt"),
            raw=wire,
        )


# ── campaign mode ──

@dataclass(frozen=True)
class Workflow:
    id: str
    engine: str
    label: str
    description: str | None = None
    supports: tuple[str, ...] = ()

    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_wire(cls, wire: dict[str, Any]) -> "Workflow":
        return cls(
            id=_str(wire, "id", required=True),
            engine=_str(wire, "engine", required=True),
            label=_str(wire, "label", required=True),
            description=_str(wire, "description"),
            supports=_strings(wire, "supports"),
            raw=wire,
        )


@dataclass(frozen=True)
class Candidate:
    id: str
    sequence: str
    name: str | None = None
    rank: int | None = None
    metrics: Mapping[str, float] = field(default_factory=dict)
    structure_file_id: str | None = None
    job_name: str | None = None

    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_wire(cls, wire: dict[str, Any]) -> "Candidate":
        return cls(
            id=_str(wire, "id", required=True),
            sequence=_str(wire, "sequence", required=True),
            name=_str(wire, "name"),
            rank=_int(wire, "rank"),
            metrics=_obj(wire, "metrics") or {},
            structure_file_id=_str(wire, "structureFileId"),
            job_name=_str(wire, "jobName"),
            raw=wire,
        )


@dataclass(frozen=True)
class JobRef:
    """A platform job; ``job_name`` works directly with the jobs API (``client.jobs``)."""

    job_name: str
    tool: str
    status: str
    submitted_at: str | None = None
    compute_hours: float | None = None
    campaign_id: str | None = None

    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_wire(cls, wire: dict[str, Any]) -> "JobRef":
        return cls(
            job_name=_str(wire, "jobName", required=True),
            tool=_str(wire, "tool", required=True),
            status=_str(wire, "status", required=True),
            submitted_at=_str(wire, "submittedAt"),
            compute_hours=_num(wire, "computeHours"),
            campaign_id=_str(wire, "campaignId"),
            raw=wire,
        )


@dataclass(frozen=True)
class TaskReport:
    id: str
    title: str
    status: str
    report: str | None = None
    trace: tuple[Step, ...] = ()

    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_wire(cls, wire: dict[str, Any]) -> "TaskReport":
        return cls(
            id=_str(wire, "id", required=True),
            title=_str(wire, "title", required=True),
            status=_str(wire, "status", required=True),
            report=_str(wire, "report"),
            trace=_objects(wire, "trace", Step.from_wire),
            raw=wire,
        )


@dataclass(frozen=True)
class Export:
    id: str
    status: str
    format: str | None = None
    download_url: str | None = field(default=None, repr=False)
    expires_at: str | None = None

    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_wire(cls, wire: dict[str, Any]) -> "Export":
        return cls(
            id=_str(wire, "id", required=True),
            status=_str(wire, "status", required=True),
            format=_str(wire, "format"),
            download_url=_str(wire, "downloadUrl"),
            expires_at=_str(wire, "expiresAt"),
            raw=wire,
        )


# ── events ──

@dataclass(frozen=True)
class Event:
    """One event, streamed or listed. ``data``'s shape depends on ``type``."""

    id: str
    type: str
    sequence: int
    chat_id: str
    created_at: str
    data: Mapping[str, Any]
    message_id: str | None = None
    campaign_id: str | None = None

    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_wire(cls, wire: dict[str, Any]) -> "Event":
        sequence = _get(wire, "sequence", (int,), required=True, nullable=False)
        data = _get(wire, "data", (dict,), required=True, nullable=False)
        return cls(
            id=_str(wire, "id", required=True),
            type=_str(wire, "type", required=True),
            sequence=int(sequence),
            chat_id=_str(wire, "chatId", required=True),
            created_at=_str(wire, "createdAt", required=True),
            data=data,
            message_id=_str(wire, "messageId"),
            campaign_id=_str(wire, "campaignId"),
            raw=wire,
        )

    def message(self) -> Message:
        """The Message a ``message.*`` status event carries."""
        return Message.from_wire(dict(self.data))
