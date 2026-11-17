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
    # ``files.list`` only: the chat holds more than 20,000 files and only the first 20,000 by
    # path are listed, so ``next_cursor is None`` ends that part of the list, not the chat's files.
    truncated: bool = False


def page_of(wire: Any, parse: Callable[[dict[str, Any]], T], *, cursor: bool = True) -> Page[T]:
    body = _as_object(wire)
    items = _objects(body, "data", parse, required=True)
    return Page(items=items, next_cursor=_str(body, "nextCursor") if cursor else None,
                truncated=_bool(body, "truncated") is True)


# ── usage ──

@dataclass(frozen=True)
class Usage:
    """What a chat has used, in hours (``usage.chat``, and the ``usage`` of a chat or reply)."""

    agent_hours: float
    jobs_hours: float
    total_hours: float
    cap_hours: float | None = None
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_wire(cls, wire: dict[str, Any]) -> "Usage":
        return cls(
            agent_hours=_num(wire, "agentHours", required=True),
            jobs_hours=_num(wire, "jobsHours", required=True),
            total_hours=_num(wire, "totalHours", required=True),
            cap_hours=_num(wire, "capHours"),
            raw=wire,
        )


@dataclass(frozen=True)
class AgentUsage:
    """Your own agent usage for one month (``usage.month``), in hours, without jobs."""

    month: str
    agent_hours: float
    # What is left of the tightest Tamarind budget that caps you; None when nothing does,
    # when it cannot be read, and for any month but the current one.
    remaining_hours: float | None = None
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_wire(cls, wire: dict[str, Any]) -> "AgentUsage":
        return cls(
            month=_str(wire, "month", required=True),
            agent_hours=_num(wire, "agentHours", required=True),
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
    workflow: str
    status: str
    plan: Mapping[str, Any] | None
    # The designs the agent marked final (``ids``, ``note``, ...); only on ``chats.get``.
    final_designs: Mapping[str, Any] | None
    candidate_count: int | None
    started_at: str | None
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_wire(cls, wire: dict[str, Any]) -> "Campaign":
        return cls(
            id=_str(wire, "id", required=True),
            workflow=_str(wire, "workflow", required=True),
            status=_str(wire, "status", required=True),
            plan=_obj(wire, "plan"),
            final_designs=_obj(wire, "finalDesigns"),
            candidate_count=_int(wire, "candidateCount"),
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
    # Every action the agent asks about is approved without asking; off whenever
    # ``auto_approve`` is. Not in ``chats.list`` items.
    dangerously_approve_all: bool | None = None
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
            dangerously_approve_all=_bool(wire, "dangerouslyApproveAll"),
            mode=_str(wire, "mode"),
            workflow=_str(wire, "workflow"),
            campaign=Campaign.from_wire(campaign) if campaign is not None else None,
            usage=Usage.from_wire(usage) if usage is not None else None,
            web_url=_str(wire, "webUrl"),
            raw=wire,
        )


@dataclass(frozen=True)
class SharedChat:
    """A teammate's chat that you may read and not change (``chats.list(scope="org")``, or
    ``chats.get`` of a chat that is not yours). It has no status, budget or usage: those
    are its owner's."""

    id: str
    title: str
    owner_email: str
    source: str
    created_at: str
    updated_at: str
    read_only: bool = True
    mode: str | None = None
    # Only on ``chats.get``.
    campaign: Campaign | None = None
    web_url: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_wire(cls, wire: dict[str, Any]) -> "SharedChat":
        campaign = _obj(wire, "campaign")
        return cls(
            id=_str(wire, "id", required=True),
            title=_str(wire, "title", required=True),
            owner_email=_str(wire, "ownerEmail", required=True),
            source=_str(wire, "source", required=True),
            created_at=_str(wire, "createdAt", required=True),
            updated_at=_str(wire, "updatedAt", required=True),
            read_only=_bool(wire, "readOnly") is not False,
            mode=_str(wire, "mode"),
            campaign=Campaign.from_wire(campaign) if campaign is not None else None,
            web_url=_str(wire, "webUrl"),
            raw=wire,
        )


def chat_from_wire(wire: dict[str, Any]) -> Chat | SharedChat:
    """A chat of yours, or a teammate's (``readOnly: true``, no status): the spec's ``oneOf``."""
    return SharedChat.from_wire(wire) if wire.get("readOnly") is True else Chat.from_wire(wire)


@dataclass(frozen=True)
class DeletedChat:
    """What ``chats.delete`` answers: the chat is gone and cannot be restored."""

    id: str
    deleted: bool

    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_wire(cls, wire: dict[str, Any]) -> "DeletedChat":
        return cls(
            id=_str(wire, "id", required=True),
            deleted=_get(wire, "deleted", (bool,), required=True, nullable=False),
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
    # ``user`` (your approve or deny) or ``dangerouslyApproveAll`` (the chat approved it by
    # itself); None while pending, expired or superseded.
    resolved_by: str | None = None
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
            resolved_by=_str(wire, "resolvedBy"),
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
    # The message that answered it (yours, sent here or not).
    answer_message_id: str | None = None
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
            answer_message_id=_str(wire, "answerMessageId"),
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
    """An upload slot: a presigned form to ``POST`` the file to before ``expires_at``.

    ``upload_url`` and ``upload_fields`` are a credential (the fields carry the signed
    policy), so neither is shown in ``repr`` nor to be logged. ``upload_fields`` is in the
    order the server gave, and is to be sent exactly so, then the file as the last field.
    """

    file_id: str
    upload_url: str = field(repr=False)
    upload_fields: Mapping[str, str] = field(repr=False)
    expires_at: str

    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_wire(cls, wire: dict[str, Any]) -> "FileUpload":
        form = _get(wire, "uploadFields", (dict,), required=True, nullable=False)
        if not all(isinstance(name, str) and isinstance(value, str) for name, value in form.items()):
            raise ContractError("Agent API response field 'uploadFields' is not a map of strings.")
        return cls(
            file_id=_str(wire, "fileId", required=True),
            upload_url=_str(wire, "uploadUrl", required=True),
            upload_fields=dict(form),
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
    label: str
    description: str | None = None
    supports: tuple[str, ...] = ()

    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_wire(cls, wire: dict[str, Any]) -> "Workflow":
        return cls(
            id=_str(wire, "id", required=True),
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
    # The agent marked it as one of the final designs (``Campaign.final_designs``).
    final: bool | None = None
    metrics: Mapping[str, float] = field(default_factory=dict)
    # Whether ``campaigns.download_structure`` has a file for it. False can also mean it
    # could not be checked just now: ask for the structure anyway if you need it.
    has_structure: bool | None = None
    job_name: str | None = None

    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_wire(cls, wire: dict[str, Any]) -> "Candidate":
        return cls(
            id=_str(wire, "id", required=True),
            sequence=_str(wire, "sequence", required=True),
            name=_str(wire, "name"),
            rank=_int(wire, "rank"),
            final=_bool(wire, "final"),
            metrics=_obj(wire, "metrics") or {},
            has_structure=_bool(wire, "hasStructure"),
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

    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_wire(cls, wire: dict[str, Any]) -> "JobRef":
        return cls(
            job_name=_str(wire, "jobName", required=True),
            tool=_str(wire, "tool", required=True),
            status=_str(wire, "status", required=True),
            submitted_at=_str(wire, "submittedAt"),
            compute_hours=_num(wire, "computeHours"),
            raw=wire,
        )


@dataclass(frozen=True)
class TaskReport:
    id: str
    title: str
    status: str
    report: str | None = None

    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_wire(cls, wire: dict[str, Any]) -> "TaskReport":
        return cls(
            id=_str(wire, "id", required=True),
            title=_str(wire, "title", required=True),
            status=_str(wire, "status", required=True),
            report=_str(wire, "report"),
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
            raw=wire,
        )

    def message(self) -> Message:
        """The Message a ``message.*`` status event carries."""
        return Message.from_wire(dict(self.data))
