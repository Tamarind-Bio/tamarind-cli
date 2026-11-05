"""Typed Agent API resources, reached as ``Tamarind().agent``.

One method per operation in the pinned spec (the table in ``_contract.OPERATIONS`` names
each), grouped as the spec's tags group them, plus two compositions: ``files.upload``
(create the slot, then PUT the bytes) and ``messages.wait`` (send, then follow the reply's
events to its end). Every call carries ``Tamarind-Version``; retries, rate limits and
idempotency keys are :class:`~tamarind.agent.transport.AgentTransport`'s.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping, Sequence
import os
from pathlib import Path
import tempfile
from typing import Any, Callable, TypeVar
from urllib.parse import unquote, urlsplit

import httpx

from tamarind.errors import NotFoundError, TamarindError
from tamarind.uploads import put_presigned_upload

from .events import EventStream, Until
from .models import (
    Approval,
    ArchivedChat,
    Candidate,
    Chat,
    ContractError,
    Event,
    Export,
    File,
    FileUpload,
    JobRef,
    Message,
    Page,
    Question,
    Subagent,
    TaskReport,
    Usage,
    Workflow,
    page_of,
)
from .transport import AgentTransport

T = TypeVar("T")
MAX_UPLOAD_BYTES = 209_715_200
_DOWNLOAD_TIMEOUT = 300.0
_DOWNLOAD_CHUNK = 1024 * 1024
# The Content-Type an upload declares (the PUT must repeat it exactly). A fixed table, not
# `mimetypes`: that reads the OS's own database, which differs by platform (`.pdb` is a
# Palm database on macOS), so the same file would upload differently from each machine.
CONTENT_TYPES = {
    "pdb": "chemical/x-pdb", "ent": "chemical/x-pdb", "cif": "chemical/x-mmcif",
    "mmcif": "chemical/x-mmcif", "sdf": "chemical/x-mdl-sdfile", "mol": "chemical/x-mdl-molfile",
    "mol2": "chemical/x-mol2", "fasta": "text/x-fasta", "fa": "text/x-fasta", "faa": "text/x-fasta",
    "csv": "text/csv", "tsv": "text/tab-separated-values", "txt": "text/plain", "md": "text/markdown",
    "json": "application/json", "yaml": "application/yaml", "yml": "application/yaml",
    "pdf": "application/pdf", "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
    "zip": "application/zip", "gz": "application/gzip",
}


def content_type_for(filename: str) -> str:
    ext = filename.rsplit(".", 1)[1].lower() if "." in filename else ""
    return CONTENT_TYPES.get(ext, "application/octet-stream")


def _json(resp: httpx.Response) -> Any:
    try:
        return resp.json()
    except ValueError as exc:
        raise ContractError("Agent API response is not JSON.") from exc


def _one(resp: httpx.Response, parse: Callable[[dict[str, Any]], T]) -> T:
    body = _json(resp)
    if not isinstance(body, dict):
        raise ContractError("Agent API response is not an object.")
    return parse(body)


def _page_params(limit: int | None, cursor: str | None, **extra: Any) -> dict[str, Any]:
    if limit is not None and (isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 200):
        raise ValueError("limit must be an integer from 1 to 200")
    return {"limit": limit, "cursor": cursor, **extra}


def _location(resp: httpx.Response) -> str:
    """The presigned URL a download redirect points at (a credential: never log it)."""
    url = resp.headers.get("Location")
    if not resp.is_redirect or not url:
        raise ContractError("Agent API download did not redirect to the file.")
    return url


def _compact(values: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in values.items() if value is not None}


def iterate(fetch: Callable[[str | None], Page[T]]) -> Iterator[T]:
    """Every item across pages, following ``next_cursor`` until it is None."""
    cursor: str | None = None
    while True:
        page = fetch(cursor)
        yield from page.items
        if page.next_cursor is None:
            return
        cursor = page.next_cursor


def text_input(text: str | None, file_ids: Sequence[str] = ()) -> list[dict[str, str]]:
    """A message ``input``: one text part, then one part per file id.

    The text is required: the server refuses a message whose text is blank (400), files
    or not, so a file needs a sentence saying what to do with it.
    """
    if not text or not text.strip():
        raise ValueError("a message needs text (say what to do with any files)")
    parts: list[dict[str, str]] = [{"type": "text", "text": text}]
    parts.extend({"type": "file", "fileId": file_id} for file_id in file_ids)
    return parts


class _Resource:
    def __init__(self, transport: AgentTransport):
        self._t = transport


class Chats(_Resource):
    def create(
        self, *, title: str | None = None, effort: str | None = None, agent_id: str | None = None,
        mode: str | None = None, workflow: str | None = None, budget_hours: float | None = None,
        per_job_hours: float | None = None, auto_approve: bool | None = None,
        idempotency_key: str | None = None,
    ) -> Chat:
        """``POST /chats``. Every field is optional; ``mode="campaign"`` starts a campaign."""
        body = _compact({
            "title": title, "effort": effort, "agentId": agent_id, "mode": mode,
            "workflow": workflow, "budgetHours": budget_hours, "perJobHours": per_job_hours,
            "autoApprove": auto_approve,
        })
        resp = self._t.call("createChat", json=body, idempotency_key=idempotency_key)
        return _one(resp, Chat.from_wire)

    def list(
        self, *, limit: int | None = None, cursor: str | None = None, source: str | None = None,
        status: str | None = None, mode: str | None = None, campaign_status: str | None = None,
    ) -> Page[Chat]:
        params = _page_params(limit, cursor, source=source, status=status, mode=mode,
                              campaignStatus=campaign_status)
        return page_of(_json(self._t.call("listChats", params=params)), Chat.from_wire)

    def get(self, chat_id: str) -> Chat:
        return _one(self._t.call("getChat", {"chatId": chat_id}), Chat.from_wire)

    def update(
        self, chat_id: str, *, title: str | None = None, effort: str | None = None,
        mode: str | None = None, workflow: str | None = None, budget_hours: float | None = None,
        per_job_hours: float | None = None, auto_approve: bool | None = None,
        campaign_status: str | None = None,
    ) -> Chat:
        """``PATCH /chats/{chatId}``: settings, mode, and campaign pause/resume/stop."""
        body = _compact({
            "title": title, "effort": effort, "mode": mode, "workflow": workflow,
            "budgetHours": budget_hours, "perJobHours": per_job_hours, "autoApprove": auto_approve,
        })
        if campaign_status is not None:
            body["campaign"] = {"status": campaign_status}
        if not body:
            raise ValueError("update needs at least one field")
        resp = self._t.call("updateChat", {"chatId": chat_id}, json=body)
        return _one(resp, Chat.from_wire)

    def archive(self, chat_id: str) -> ArchivedChat:
        """``DELETE /chats/{chatId}``: stops what is running and archives (not a hard delete)."""
        return _one(self._t.call("archiveChat", {"chatId": chat_id}), ArchivedChat.from_wire)

    def rewind(self, chat_id: str, before_message_id: str) -> Chat:
        """Hide ``before_message_id`` and everything after it, to edit and resend."""
        resp = self._t.call("rewindChat", {"chatId": chat_id},
                            json={"beforeMessageId": before_message_id})
        return _one(resp, Chat.from_wire)


class Messages(_Resource):
    def send(
        self, chat_id: str, text: str | None = None, *, file_ids: Sequence[str] = (),
        input: Sequence[Mapping[str, Any]] | None = None, interrupt: bool = False,
        idempotency_key: str | None = None,
    ) -> Message:
        """Send a message; returns the reply (status ``queued``) to follow or poll.

        Always ``stream: false``: the reply is then followed on the events stream, which
        resumes after a dropped connection, rather than on the POST's own response, which
        cannot be resumed once cut.
        """
        if input is not None:
            parts = [dict(part) for part in input]
            if not any(p.get("type") == "text" and str(p.get("text") or "").strip() for p in parts):
                raise ValueError("a message needs a non-blank text part")
        else:
            parts = text_input(text, file_ids)
        body: dict[str, Any] = {"input": parts, "stream": False}
        if interrupt:
            body["interrupt"] = True
        resp = self._t.call("sendMessage", {"chatId": chat_id}, json=body,
                            idempotency_key=idempotency_key)
        return _one(resp, Message.from_wire)

    def list(self, chat_id: str, *, limit: int | None = None, cursor: str | None = None) -> Page[Message]:
        resp = self._t.call("listMessages", {"chatId": chat_id}, params=_page_params(limit, cursor))
        return page_of(_json(resp), Message.from_wire)

    def get(self, chat_id: str, message_id: str) -> Message:
        resp = self._t.call("getMessage", {"chatId": chat_id, "messageId": message_id})
        return _one(resp, Message.from_wire)

    def cancel(self, chat_id: str, message_id: str) -> Message:
        """Stop this reply only. On a reply stopped at an approval, this DENIES it."""
        resp = self._t.call("cancelMessage", {"chatId": chat_id, "messageId": message_id})
        return _one(resp, Message.from_wire)

    def reply_to(self, chat_id: str, message_id: str) -> Message:
        """The reply for ``message_id``: itself when it is a reply, else the reply that
        answers it (a reply's ``inReplyTo``). Raises NotFoundError when none has started."""
        current = self.get(chat_id, message_id)
        if current.role != "user":
            return current
        for item in iterate(lambda cursor: self.list(chat_id, limit=200, cursor=cursor)):
            if item.role == "assistant" and item.in_reply_to == message_id:
                return item
        raise NotFoundError(f"No reply to message {message_id} yet.",
                            detail={"code": "not_found", "messageId": message_id})

    def follow(
        self, chat_id: str, message_id: str, *, after: str | None = None,
        follow_continuations: bool = False, until: Until | Iterable[str] | str | None = None,
    ) -> EventStream:
        """Stream one reply's events until it ends or stops on a card."""
        return EventStream(self._t, chat_id, message_id=message_id, after=after, until=until,
                           follow_continuations=follow_continuations)

    def wait(self, chat_id: str, message_id: str, *, follow_continuations: bool = True) -> Message:
        """Block until the reply ends, or stops on a card; returns it as it then stands."""
        stream = self.follow(chat_id, message_id, follow_continuations=follow_continuations)
        for _ in stream:
            pass
        if stream.message is not None and stream.stop_reason == "final":
            return stream.message
        return self.get(chat_id, stream.message_id or message_id)


class Events(_Resource):
    def list(
        self, chat_id: str, *, after: str | None = None, message_id: str | None = None,
        limit: int | None = None,
    ) -> Page[Event]:
        """One page of past events; pass ``next_cursor`` as ``after`` to continue."""
        params = _page_params(limit, None, after=after, messageId=message_id, stream="false")
        params.pop("cursor")
        return page_of(_json(self._t.call("listChatEvents", {"chatId": chat_id}, params=params)),
                       Event.from_wire)

    def stream(
        self, chat_id: str, *, after: str | None = None, message_id: str | None = None,
        until: Until | Iterable[str] | str | None = None, follow_continuations: bool = False,
        include_unknown: bool = False,
    ) -> EventStream:
        """Tail the chat's events (``GET .../events?stream=true``), reconnecting as needed."""
        return EventStream(self._t, chat_id, message_id=message_id, after=after, until=until,
                           follow_continuations=follow_continuations, include_unknown=include_unknown)


class Approvals(_Resource):
    def list(self, chat_id: str, *, status: str | None = None) -> tuple[Approval, ...]:
        resp = self._t.call("listApprovals", {"chatId": chat_id}, params={"status": status})
        return page_of(_json(resp), Approval.from_wire, cursor=False).items

    def resolve(
        self, chat_id: str, approval_id: str, decision: str, *, scope: str | None = None,
        budget_hours: float | None = None, workflow: str | None = None,
    ) -> Approval:
        if decision not in ("approve", "deny"):
            raise ValueError("decision must be 'approve' or 'deny'")
        body = _compact({"decision": decision, "scope": scope, "budgetHours": budget_hours,
                         "workflow": workflow})
        # Only the same BARE decision is safe to repeat (it returns the resolved approval);
        # with options, a repeat whose first answer was lost is 409 approval_not_pending.
        resp = self._t.call("resolveApproval", {"chatId": chat_id, "approvalId": approval_id},
                            json=body, retry_safe=False if len(body) > 1 else None)
        return _one(resp, Approval.from_wire)

    def approve(self, chat_id: str, approval_id: str, **options: Any) -> Approval:
        return self.resolve(chat_id, approval_id, "approve", **options)

    def deny(self, chat_id: str, approval_id: str) -> Approval:
        return self.resolve(chat_id, approval_id, "deny")


class Questions(_Resource):
    def answer(
        self, chat_id: str, question_id: str, *, answers: Mapping[str, str] | None = None,
        text: str | None = None, idempotency_key: str | None = None,
    ) -> Question:
        """Answer by question text (``answers``) or one ``text`` for every question."""
        body = _compact({"answers": dict(answers) if answers is not None else None, "text": text})
        if not body:
            raise ValueError("answer needs answers or text")
        resp = self._t.call("answerQuestion", {"chatId": chat_id, "questionId": question_id},
                            json=body, idempotency_key=idempotency_key)
        return _one(resp, Question.from_wire)


class Files(_Resource):
    def create_upload(self, filename: str, size: int, *, content_type: str | None = None) -> FileUpload:
        """``POST /chat-files``: an upload slot. PUT the bytes to ``upload_url`` next."""
        body = _compact({"filename": filename, "size": size, "contentType": content_type})
        return _one(self._t.call("createChatFile", json=body), FileUpload.from_wire)

    def upload(self, path: str | Path, *, filename: str | None = None,
               content_type: str | None = None) -> FileUpload:
        """Create a slot and PUT ``path`` to it; reference the ``file_id`` in a message."""
        path = Path(path)
        name = filename or path.name
        try:
            size = path.stat().st_size
        except OSError as exc:
            raise TamarindError(f"Could not read '{path}': {exc}.") from exc
        if size < 1 or size > MAX_UPLOAD_BYTES:
            raise ValueError("a chat file must be 1 byte to 200 MB")
        kind = content_type or content_type_for(name)
        slot = self.create_upload(name, size, content_type=kind)
        # The same Content-Type the slot was created with, as the presigned PUT requires.
        put_presigned_upload(slot.upload_url, path, content_type=kind, remote=name)
        return slot

    def get(self, file_id: str) -> File:
        return _one(self._t.call("getChatFile", {"fileId": file_id}), File.from_wire)

    def list(self, chat_id: str, *, limit: int | None = None, cursor: str | None = None) -> Page[File]:
        resp = self._t.call("listChatFiles", {"chatId": chat_id}, params=_page_params(limit, cursor))
        return page_of(_json(resp), File.from_wire)

    def download_url(self, chat_id: str, file_id: str) -> str:
        """A short-lived presigned URL for the file (a credential: do not log it)."""
        return _location(self._t.call("downloadChatFile", {"chatId": chat_id, "fileId": file_id}))

    def download(self, chat_id: str, file_id: str, dest: str | Path) -> Path:
        """Save the file to ``dest`` (a directory gets the file's own name)."""
        url = self.download_url(chat_id, file_id)
        target = Path(dest)
        if target.is_dir():
            target = target / safe_name(self.get(file_id).filename, fallback=file_id)
        return save_url(url, target)


class Subagents(_Resource):
    def list(
        self, chat_id: str, *, message_id: str | None = None, status: str | None = None,
        limit: int | None = None, cursor: str | None = None,
    ) -> Page[Subagent]:
        params = _page_params(limit, cursor, messageId=message_id, status=status)
        return page_of(_json(self._t.call("listSubagents", {"chatId": chat_id}, params=params)),
                       Subagent.from_wire)

    def get(self, chat_id: str, subagent_id: str) -> Subagent:
        resp = self._t.call("getSubagent", {"chatId": chat_id, "subagentId": subagent_id})
        return _one(resp, Subagent.from_wire)

    def cancel(self, chat_id: str, subagent_id: str) -> Subagent:
        resp = self._t.call("cancelSubagent", {"chatId": chat_id, "subagentId": subagent_id})
        return _one(resp, Subagent.from_wire)


class Workflows(_Resource):
    def list(self) -> tuple[Workflow, ...]:
        return page_of(_json(self._t.call("listAgentWorkflows")), Workflow.from_wire, cursor=False).items


class Campaigns(_Resource):
    """A chat's campaign collections. The campaign itself is ``Chat.campaign``; control it
    with ``chats.update(mode=..., campaign_status=...)``."""

    def candidates(
        self, chat_id: str, *, limit: int | None = None, cursor: str | None = None,
        sort: str | None = None,
    ) -> Page[Candidate]:
        params = _page_params(limit, cursor, sort=sort)
        return page_of(_json(self._t.call("listCandidates", {"chatId": chat_id}, params=params)),
                       Candidate.from_wire)

    def candidate_structure_url(self, chat_id: str, candidate_id: str) -> str:
        resp = self._t.call("getCandidateStructure", {"chatId": chat_id, "candidateId": candidate_id})
        return _location(resp)

    def download_structure(self, chat_id: str, candidate_id: str, dest: str | Path) -> Path:
        """Save the structure to ``dest`` (a directory gets the URL's file name)."""
        url = self.candidate_structure_url(chat_id, candidate_id)
        target = Path(dest)
        if target.is_dir():
            leaf = unquote(urlsplit(url).path.rsplit("/", 1)[-1])
            target = target / safe_name(leaf, fallback=f"{candidate_id}.cif")
        return save_url(url, target)

    def jobs(
        self, chat_id: str, *, limit: int | None = None, cursor: str | None = None,
        campaign_id: str | None = None,
    ) -> Page[JobRef]:
        params = _page_params(limit, cursor, campaignId=campaign_id)
        return page_of(_json(self._t.call("listChatJobs", {"chatId": chat_id}, params=params)),
                       JobRef.from_wire)

    def task(self, chat_id: str, task_id: str) -> TaskReport:
        resp = self._t.call("getChatTask", {"chatId": chat_id, "taskId": task_id})
        return _one(resp, TaskReport.from_wire)

    def create_export(self, chat_id: str, *, format: str | None = None,
                      idempotency_key: str | None = None) -> Export:
        resp = self._t.call("createChatExport", {"chatId": chat_id}, json=_compact({"format": format}),
                            idempotency_key=idempotency_key)
        return _one(resp, Export.from_wire)

    def get_export(self, chat_id: str, export_id: str) -> Export:
        resp = self._t.call("getChatExport", {"chatId": chat_id, "exportId": export_id})
        return _one(resp, Export.from_wire)


class UsageResource(_Resource):
    def chat(self, chat_id: str) -> Usage:
        return _one(self._t.call("getChatUsage", {"chatId": chat_id}), Usage.from_wire)

    def month(self, month: str | None = None) -> Usage:
        """The month's totals (``YYYY-MM``; default the current month)."""
        return _one(self._t.call("getAgentUsage", params={"month": month}), Usage.from_wire)


class Agent:
    """The Agent API: chats (campaigns included), replies, approvals, files and usage."""

    def __init__(self, transport: AgentTransport):
        self.transport = transport
        self.chats = Chats(transport)
        self.messages = Messages(transport)
        self.events = Events(transport)
        self.approvals = Approvals(transport)
        self.questions = Questions(transport)
        self.files = Files(transport)
        self.subagents = Subagents(transport)
        self.workflows = Workflows(transport)
        self.campaigns = Campaigns(transport)
        self.usage = UsageResource(transport)


def safe_name(name: str, *, fallback: str) -> str:
    """A server-named file's last path component, never one that leaves the directory."""
    leaf = Path(name.replace("\\", "/")).name
    return leaf if leaf not in ("", ".", "..") else fallback.replace("/", "_")


def save_url(url: str, target: Path) -> Path:
    """Stream a presigned URL to ``target``, without the API key and without echoing the URL.

    Written to a fresh, exclusively created temp file beside ``target`` and renamed into
    place, so two downloads cannot share a partial file and a planted symlink is never
    opened.
    """
    partial: Path | None = None
    try:
        with httpx.stream("GET", url, timeout=_DOWNLOAD_TIMEOUT, follow_redirects=True) as resp:
            resp.raise_for_status()
            fd, name = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".part", dir=target.parent)
            partial = Path(name)
            with os.fdopen(fd, "wb") as fh:
                for chunk in resp.iter_bytes(_DOWNLOAD_CHUNK):
                    fh.write(chunk)
        os.replace(partial, target)
        partial = None
    except httpx.HTTPStatusError as exc:
        raise TamarindError(f"Download of '{target.name}' failed with HTTP {exc.response.status_code}.") from exc
    except httpx.HTTPError as exc:
        raise TamarindError(f"Download of '{target.name}' failed ({type(exc).__name__}).") from exc
    except OSError as exc:
        raise TamarindError(f"Could not write '{target}': {exc}.") from exc
    finally:
        if partial is not None:
            partial.unlink(missing_ok=True)
    return target
