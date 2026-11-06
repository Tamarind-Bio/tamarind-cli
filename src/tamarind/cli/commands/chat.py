"""``tamarind chat`` — drive the Tamarind agent: chats, replies, approvals, files.

A thin layer over :mod:`tamarind.agent` (``Tamarind().agent``): each command is one SDK
call, and JSON mode prints the API's own object. ``send --wait`` / ``wait`` stream the
reply's text to stdout (human mode) or print the finished reply (JSON mode), and exit
``10`` when the reply stops on an approval or a question, with the ids to answer it in
the error detail.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Optional

import typer

from ...agent import Approval, Chat, Event, EventStream, Message
from ...agent._contract import FINAL_MESSAGE_EVENTS
from ...errors import AgentActionRequiredError, AgentReplyFailedError, JobTimeoutError, TamarindError
from .. import output

app = typer.Typer(no_args_is_help=True)
files_app = typer.Typer(no_args_is_help=True)
subagents_app = typer.Typer(no_args_is_help=True)
app.add_typer(files_app, name="files", help="Upload inputs and download what the agent made.")
app.add_typer(subagents_app, name="subagents", help="Helper agents a reply started.")

def _raw(obj: Any) -> Any:
    return dict(obj.raw) if hasattr(obj, "raw") else obj


def _page(items: Iterable[Any], next_cursor: Optional[str]) -> dict[str, Any]:
    return {"data": [_raw(item) for item in items], "nextCursor": next_cursor}


def _more(next_cursor: Optional[str]) -> str:
    return f"\n\nMore: --cursor {next_cursor}" if next_cursor else ""


def _chat_line(chat: Chat) -> dict[str, Any]:
    campaign = chat.campaign.status if chat.campaign else ""
    return {"id": chat.id, "status": chat.status, "mode": chat.mode or "", "campaign": campaign,
            "title": chat.title, "updated": chat.updated_at}


def _approval_line(approval: Approval) -> dict[str, Any]:
    return {"id": approval.id, "status": approval.status, "kind": approval.kind,
            "summary": approval.summary, "message": approval.message_id or ""}


# ── chats ──

@app.command("new")
def new(
    ctx: typer.Context,
    title: Optional[str] = typer.Option(None, "--title", help="Shown in the web app sidebar."),
    effort: Optional[str] = typer.Option(None, "--effort", help="low, medium, high or max."),
    mode: Optional[str] = typer.Option(None, "--mode", help="chat (default) or campaign."),
    workflow: Optional[str] = typer.Option(None, "--workflow", help="Campaign workflow (see `chat workflows`)."),
    budget_hours: Optional[float] = typer.Option(None, "--budget-hours", help="Spend cap for the chat."),
    per_job_hours: Optional[float] = typer.Option(None, "--per-job-hours", help="Largest job auto-approve may submit."),
    auto_approve: Optional[bool] = typer.Option(None, "--auto-approve/--no-auto-approve", help="Submit jobs within budget without asking."),
    agent_id: Optional[str] = typer.Option(None, "--agent-id", help="A saved agent from the agent builder."),
) -> None:
    """Create a chat."""
    state = ctx.obj
    with state.sdk_client() as client:
        chat = client.agent.chats.create(
            title=title, effort=effort, mode=mode, workflow=workflow, budget_hours=budget_hours,
            per_job_hours=per_job_hours, auto_approve=auto_approve, agent_id=agent_id,
        )
    output.emit(_raw(chat), state.output, human=f"{chat.id}  {chat.web_url or ''}".rstrip())


@app.command("list")
def list_chats(
    ctx: typer.Context,
    limit: Optional[int] = typer.Option(None, "--limit", help="Page size, 1-200."),
    cursor: Optional[str] = typer.Option(None, "--cursor", help="From the previous page."),
    source: Optional[str] = typer.Option(None, "--source", help="api, ui or all."),
    status: Optional[str] = typer.Option(None, "--status", help="e.g. requires_action."),
    mode: Optional[str] = typer.Option(None, "--mode", help="chat, campaign or all."),
    campaign_status: Optional[str] = typer.Option(None, "--campaign-status", help="e.g. running."),
) -> None:
    """List chats, most recently updated first."""
    state = ctx.obj
    with state.sdk_client() as client:
        page = client.agent.chats.list(limit=limit, cursor=cursor, source=source, status=status,
                                       mode=mode, campaign_status=campaign_status)
    human = output.render_table([_chat_line(c) for c in page.items],
                                ["id", "status", "mode", "campaign", "title", "updated"])
    output.emit(_page(page.items, page.next_cursor), state.output, human=human + _more(page.next_cursor))


@app.command("show")
def show(ctx: typer.Context, chat_id: str = typer.Argument(..., help="The chat id.")) -> None:
    """Show a chat, its replies in progress and its campaign."""
    state = ctx.obj
    with state.sdk_client() as client:
        chat = client.agent.chats.get(chat_id)
    lines = [f"{chat.id}  {chat.status}  {chat.title}"]
    if chat.active_message_ids:
        lines.append("active replies: " + ", ".join(chat.active_message_ids))
    if chat.campaign:
        lines.append(f"campaign {chat.campaign.id}: {chat.campaign.status} ({chat.campaign.workflow})")
    if chat.web_url:
        lines.append(chat.web_url)
    output.emit(_raw(chat), state.output, human="\n".join(lines))


@app.command("update")
def update(
    ctx: typer.Context,
    chat_id: str = typer.Argument(..., help="The chat id."),
    title: Optional[str] = typer.Option(None, "--title"),
    effort: Optional[str] = typer.Option(None, "--effort"),
    mode: Optional[str] = typer.Option(None, "--mode", help="campaign hands the task to a campaign; chat pauses it."),
    workflow: Optional[str] = typer.Option(None, "--workflow"),
    budget_hours: Optional[float] = typer.Option(None, "--budget-hours"),
    per_job_hours: Optional[float] = typer.Option(None, "--per-job-hours"),
    auto_approve: Optional[bool] = typer.Option(None, "--auto-approve/--no-auto-approve"),
    campaign_status: Optional[str] = typer.Option(None, "--campaign-status", help="paused, running or cancelled."),
) -> None:
    """Change a chat's settings, mode or campaign (pause, resume, stop)."""
    state = ctx.obj
    with state.sdk_client() as client:
        chat = client.agent.chats.update(
            chat_id, title=title, effort=effort, mode=mode, workflow=workflow,
            budget_hours=budget_hours, per_job_hours=per_job_hours, auto_approve=auto_approve,
            campaign_status=campaign_status,
        )
    output.emit(_raw(chat), state.output, human=f"{chat.id}  {chat.status}  {chat.title}")


@app.command("archive")
def archive(
    ctx: typer.Context,
    chat_id: str = typer.Argument(..., help="The chat id."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Confirm without prompting."),
) -> None:
    """Stop everything running in a chat (campaigns included) and archive it."""
    state = ctx.obj
    output.confirm_destructive(f"archive chat '{chat_id}' and stop what it is running", yes=yes, mode=state.output)
    with state.sdk_client() as client:
        done = client.agent.chats.archive(chat_id)
    output.emit(_raw(done), state.output, human=f"{done.id} archived")


@app.command("rewind")
def rewind(
    ctx: typer.Context,
    chat_id: str = typer.Argument(..., help="The chat id."),
    before_message_id: str = typer.Argument(..., help="It and everything after it are hidden."),
) -> None:
    """Rewind a chat to before a message, to edit and resend."""
    state = ctx.obj
    with state.sdk_client() as client:
        chat = client.agent.chats.rewind(chat_id, before_message_id)
    output.emit(_raw(chat), state.output, human=f"{chat.id} rewound to before {before_message_id}")


# ── messages ──

def _file_ids(client: Any, files: list[str], state: Any) -> list[str]:
    """``--file`` values: an existing local file is uploaded first; anything else starting
    ``file_`` is a file id, used as is (ids are opaque: a listed one is ``file_w<path>.<tag>``)."""
    ids: list[str] = []
    for value in files:
        if not Path(value).is_file():
            if not value.startswith("file_"):
                raise TamarindError(f"--file {value!r} is neither a local file nor a file_ id.")
            ids.append(value)
            continue
        slot = client.agent.files.upload(value)
        output.info(f"uploaded {value} as {slot.file_id}", state.output)
        ids.append(slot.file_id)
    return ids


@app.command("send")
def send(
    ctx: typer.Context,
    chat_id: str = typer.Argument(..., help="The chat id."),
    text: str = typer.Argument(..., help="Your message (also say what to do with any --file)."),
    file: list[str] = typer.Option([], "--file", "-f", help="A local path to upload, or a file_ id. Repeatable."),
    interrupt: bool = typer.Option(False, "--interrupt", help="Stop the reply in progress and run this next."),
    wait: bool = typer.Option(False, "--wait", help="Stream the reply and wait for it to finish."),
    idempotency_key: Optional[str] = typer.Option(None, "--idempotency-key", help="Reuse to make a retried send safe."),
) -> None:
    """Send a message. With --wait, stream the reply's text to stdout."""
    state = ctx.obj
    with state.sdk_client() as client:
        file_ids = _file_ids(client, file, state)
        reply = client.agent.messages.send(chat_id, text, file_ids=file_ids, interrupt=interrupt,
                                           idempotency_key=idempotency_key)
        if not wait:
            output.emit(_raw(reply), state.output, human=f"{reply.id}  {reply.status}")
            return
        output.info(f"reply {reply.id}", state.output)
        _follow(client, chat_id, reply.id, state)


@app.command("wait")
def wait_reply(
    ctx: typer.Context,
    chat_id: str = typer.Argument(..., help="The chat id."),
    message_id: str = typer.Argument(..., help="The reply to follow (or your message's)."),
) -> None:
    """Follow a reply to its end, streaming its text (e.g. after approving a card)."""
    state = ctx.obj
    with state.sdk_client() as client:
        # The stream filters by the exact id: a user message's id is mapped to its reply.
        target = client.agent.messages.reply_to(chat_id, message_id)
        _follow(client, chat_id, target.id, state)


@app.command("messages")
def messages(
    ctx: typer.Context,
    chat_id: str = typer.Argument(..., help="The chat id."),
    limit: Optional[int] = typer.Option(None, "--limit"),
    cursor: Optional[str] = typer.Option(None, "--cursor"),
) -> None:
    """The chat's transcript, oldest first."""
    state = ctx.obj
    with state.sdk_client() as client:
        page = client.agent.messages.list(chat_id, limit=limit, cursor=cursor)
    human = "\n\n".join(f"[{m.role} {m.id}{' ' + m.status if m.status else ''}]\n{m.text}" for m in page.items)
    output.emit(_page(page.items, page.next_cursor), state.output, human=(human or "(none)") + _more(page.next_cursor))


@app.command("message")
def message(
    ctx: typer.Context,
    chat_id: str = typer.Argument(..., help="The chat id."),
    message_id: str = typer.Argument(..., help="The message id."),
) -> None:
    """Show one message or reply, with its status."""
    state = ctx.obj
    with state.sdk_client() as client:
        msg = client.agent.messages.get(chat_id, message_id)
    output.emit(_raw(msg), state.output, human=f"[{msg.role} {msg.id} {msg.status or ''}]\n{msg.text}")


@app.command("cancel")
def cancel(
    ctx: typer.Context,
    chat_id: str = typer.Argument(..., help="The chat id."),
    message_id: str = typer.Argument(..., help="The reply to stop."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Confirm without prompting."),
) -> None:
    """Stop one reply. On a reply waiting at an approval, this denies it."""
    state = ctx.obj
    output.confirm_destructive(f"cancel reply '{message_id}'", yes=yes, mode=state.output)
    with state.sdk_client() as client:
        msg = client.agent.messages.cancel(chat_id, message_id)
    output.emit(_raw(msg), state.output, human=f"{msg.id}  {msg.status}")


@app.command("events")
def events(
    ctx: typer.Context,
    chat_id: str = typer.Argument(..., help="The chat id."),
    follow: bool = typer.Option(False, "--follow", help="Stream live events (one JSON object per line)."),
    after: Optional[str] = typer.Option(None, "--after", help="Only events after this event id."),
    message_id: Optional[str] = typer.Option(None, "--message", help="Only this reply's events."),
    limit: Optional[int] = typer.Option(None, "--limit", help="Page size when not following."),
) -> None:
    """List a chat's events, or follow them live (reconnecting as needed)."""
    import json

    state = ctx.obj
    with state.sdk_client() as client:
        if not follow:
            page = client.agent.events.list(chat_id, after=after, message_id=message_id, limit=limit)
            human = "\n".join(f"{e.id}  {e.type}" for e in page.items) or "(none)"
            more = f"\n\nMore: --after {page.next_cursor}" if page.next_cursor else ""
            output.emit(_page(page.items, page.next_cursor), state.output, human=human + more)
            return
        stream = client.agent.events.stream(chat_id, after=after, message_id=message_id)
        try:
            for event in stream:
                typer.echo(json.dumps(_raw(event), default=str) if state.output.json
                           else f"{event.id}  {event.type}  {_summary(event)}".rstrip())
        except KeyboardInterrupt:
            output.info(f"stopped; resume with --after {stream.last_event_id}", state.output)
            raise typer.Exit(130)  # a partial feed is not a finished one


def _summary(event: Event) -> str:
    data = event.data
    for key in ("delta", "text", "title", "summary", "jobName", "status"):
        value = data.get(key)
        if isinstance(value, str) and value:
            return " ".join(value.split())[:120]
    return ""


# ── following a reply ──

@dataclass
class _ReplyPrinter:
    """Writes a reply's text to stdout as it is written.

    ``live`` (stdout is a terminal): deltas as they come, then ``output_text.done`` as the
    authority, writing only what the deltas had not shown; a correction or a discarded
    draft already on screen cannot be taken back, so it is flagged on stderr and the
    corrected text written. Not live (piped): nothing until a reply ends, then that
    reply's final text (its Message), so stdout holds exactly what the transcript keeps:
    a part can still be discarded after its ``output_text.done``.
    Parts are keyed by (reply, part): a continuing reply numbers its parts from p_0 again.
    """

    json_mode: bool
    quiet: bool
    live: bool = True
    printed: dict[tuple[Optional[str], str], str] = field(default_factory=dict)
    last_part: Optional[tuple[Optional[str], str]] = None
    wrote: bool = False

    def handle(self, event: Event) -> None:
        if self.json_mode:
            return
        data = event.data
        part = (event.message_id, str(data.get("partId") or ""))
        if not self.live:
            if event.type in FINAL_MESSAGE_EVENTS:
                self._write((event.message_id, ""), event.message().text)
            elif event.type in ("step.started", "approval.requested", "question.asked"):
                pass  # status lines below
            else:
                return
        if event.type == "output_text.delta":
            if self.live:
                self._write(part, str(data.get("delta") or ""))
        elif event.type == "output_text.done":
            text = str(data.get("text") or "")
            seen = self.printed.get(part, "")
            if text.startswith(seen):
                self._write(part, text[len(seen):])
            else:
                self._status("(the agent corrected the text above; final text follows)")
                self.printed[part] = ""
                self._write(part, text)
        elif event.type == "output_text.discarded":
            if self.printed.get(part):
                self._status("(the agent discarded the draft above)")
            self.printed.pop(part, None)
        elif event.type == "step.started":
            self._status(f"> {data.get('title') or 'working'}")
        elif event.type == "approval.requested":
            self._status(f"? approval {data.get('id')}: {data.get('summary') or ''}")
        elif event.type == "question.asked":
            self._status(f"? question {data.get('id')}")

    def _write(self, part: tuple[Optional[str], str], text: str) -> None:
        if not text:
            return
        if self.wrote and part != self.last_part:
            typer.echo("\n\n", nl=False)
        self.last_part = part
        self.wrote = True
        self.printed[part] = self.printed.get(part, "") + text
        typer.echo(text, nl=False)

    def _status(self, line: str) -> None:
        if self.quiet:
            return
        if self.wrote and self.last_part is not None:
            typer.echo("")  # end the text line before a status line
            self.last_part = None
            self.wrote = False
        typer.secho(line, err=True, fg=typer.colors.BRIGHT_BLACK)

    def finish(self) -> None:
        if self.wrote:
            typer.echo("")


def _follow(client: Any, chat_id: str, message_id: str, state: Any, *, decided: bool = False) -> None:
    stream: EventStream = client.agent.messages.follow(
        chat_id, message_id, follow_continuations=True, expect_continuation=decided)
    printer = _ReplyPrinter(json_mode=state.output.json, quiet=state.output.quiet, live=output.is_tty())
    try:
        for event in stream:
            printer.handle(event)
    except KeyboardInterrupt:
        printer.finish()
        output.info(f"stopped following; the reply goes on. Resume: tamarind chat wait {chat_id} "
                    f"{stream.message_id}", state.output)
        raise typer.Exit(130)
    printer.finish()
    reply: Message = stream.message or client.agent.messages.get(chat_id, stream.message_id or message_id)
    if stream.stop_reason == "continuation_pending":
        raise JobTimeoutError(
            f"Reply {reply.id} ended on your decision, and the agent's answer has not started yet. "
            f"Follow it later: tamarind chat wait {chat_id} {reply.id}",
            detail={"messageId": reply.id, "status": reply.status},
        )
    if stream.stop_reason == "requires_action" or reply.status == "requires_action":
        _requires_action(client, chat_id, reply, state)
    if state.output.json:
        output.emit(_raw(reply), state.output)
    if reply.status in ("failed", "cancelled", "incomplete"):
        reason = reply.incomplete_reason or (reply.error or {}).get("message") or reply.status
        raise AgentReplyFailedError(f"Reply {reply.id} ended {reply.status}: {reason}.",
                                    detail={"messageId": reply.id, "status": reply.status,
                                            "incompleteReason": reply.incomplete_reason,
                                            "error": reply.error})


def _requires_action(client: Any, chat_id: str, reply: Message, state: Any) -> None:
    """The reply stopped on a card: say what is waiting and how to answer, exit 10."""
    approvals = list(reply.pending_approvals)
    if not approvals and not reply.pending_questions:
        approvals = list(client.agent.approvals.list(chat_id, status="pending"))
    lines = [f"Reply {reply.id} is waiting on you."]
    for approval in approvals:
        lines.append(f"  approval {approval.id} ({approval.kind}): {approval.summary}")
        lines.append(f"    tamarind chat approve {chat_id} {approval.id}   |   tamarind chat deny {chat_id} {approval.id}")
    for question in reply.pending_questions:
        asked = "; ".join(str(q.get("question") or "") for q in question.questions)
        lines.append(f"  question {question.id}: {asked}")
        lines.append(f"    tamarind chat answer {chat_id} {question.id} --text \"...\"")
    lines.append(f"Then follow the reply: tamarind chat wait {chat_id} {reply.id}")
    raise AgentActionRequiredError(
        "\n".join(lines),
        detail={
            "messageId": reply.id,
            "approvals": [_raw(a) for a in approvals],
            "questions": [_raw(q) for q in reply.pending_questions],
        },
    )


# ── approvals and questions ──

@app.command("approvals")
def approvals(
    ctx: typer.Context,
    chat_id: str = typer.Argument(..., help="The chat id."),
    status: Optional[str] = typer.Option(None, "--status", help="e.g. pending. Default: all."),
) -> None:
    """List a chat's approvals, newest first."""
    state = ctx.obj
    with state.sdk_client() as client:
        items = client.agent.approvals.list(chat_id, status=status)
    human = output.render_table([_approval_line(a) for a in items],
                                ["id", "status", "kind", "summary", "message"])
    output.emit({"data": [_raw(a) for a in items]}, state.output, human=human)


def _resolve(ctx: typer.Context, chat_id: str, approval_id: str, decision: str, *,
             scope: Optional[str], wait: bool, **options: Any) -> None:
    state = ctx.obj
    with state.sdk_client() as client:
        approval = client.agent.approvals.resolve(chat_id, approval_id, decision, scope=scope, **options)
        if not wait:
            output.emit(_raw(approval), state.output, human=f"{approval.id}  {approval.status}")
            return
        output.info(f"{approval.id} {approval.status}", state.output)
        if approval.message_id is None:
            output.emit(_raw(approval), state.output, human="(no reply to follow)")
            return
        _follow(client, chat_id, approval.message_id, state, decided=True)


@app.command("approve")
def approve(
    ctx: typer.Context,
    chat_id: str = typer.Argument(..., help="The chat id."),
    approval_id: str = typer.Argument(..., help="The approval id (see `chat approvals`)."),
    scope: Optional[str] = typer.Option(None, "--scope", help="once (default), chat, site, all, connector or package."),
    budget_hours: Optional[float] = typer.Option(None, "--budget-hours", help="campaign_start only: the budget to accept with."),
    workflow: Optional[str] = typer.Option(None, "--workflow", help="campaign_start only: run this workflow instead."),
    wait: bool = typer.Option(False, "--wait", help="Then follow the agent's answer."),
) -> None:
    """Approve a pending action."""
    _resolve(ctx, chat_id, approval_id, "approve", scope=scope, wait=wait,
             budget_hours=budget_hours, workflow=workflow)


@app.command("deny")
def deny(
    ctx: typer.Context,
    chat_id: str = typer.Argument(..., help="The chat id."),
    approval_id: str = typer.Argument(..., help="The approval id (see `chat approvals`)."),
    wait: bool = typer.Option(False, "--wait", help="Then follow the agent's answer."),
) -> None:
    """Deny a pending action; the agent goes on without it."""
    _resolve(ctx, chat_id, approval_id, "deny", scope=None, wait=wait)


@app.command("answer")
def answer(
    ctx: typer.Context,
    chat_id: str = typer.Argument(..., help="The chat id."),
    question_id: str = typer.Argument(..., help="The question id."),
    text: Optional[str] = typer.Option(None, "--text", help="One answer for every question on the card."),
    questions: list[str] = typer.Option([], "--question", help="A question's text. Repeatable; pairs with --choice."),
    choices: list[str] = typer.Option([], "--choice", help="Your answer to the --question in the same position."),
) -> None:
    """Answer a question the agent is waiting on (--text, or --question/--choice pairs)."""
    state = ctx.obj
    # Paired options, not 'question=answer': either side may contain any character.
    if len(questions) != len(choices):
        raise typer.BadParameter("give one --choice for each --question", param_hint="--choice")
    answers: dict[str, str] = dict(zip(questions, choices))
    with state.sdk_client() as client:
        result = client.agent.questions.answer(chat_id, question_id, answers=answers or None, text=text)
    output.emit(_raw(result), state.output, human=f"{result.id}  {result.status}")


# ── files ──

@files_app.command("upload")
def files_upload(
    ctx: typer.Context,
    path: Path = typer.Argument(..., exists=True, dir_okay=False, readable=True, help="Local file (up to 200 MB)."),
    filename: Optional[str] = typer.Option(None, "--name", help="The name the agent sees."),
    content_type: Optional[str] = typer.Option(None, "--content-type", help="Default: from the extension."),
) -> None:
    """Upload a file; pass its id to `chat send --file`."""
    state = ctx.obj
    with state.sdk_client() as client:
        slot = client.agent.files.upload(path, filename=filename, content_type=content_type)
    output.emit({"fileId": slot.file_id, "expiresAt": slot.expires_at}, state.output, human=slot.file_id)


@files_app.command("get")
def files_get(ctx: typer.Context, file_id: str = typer.Argument(..., help="The file id.")) -> None:
    """Show an uploaded file's status."""
    state = ctx.obj
    with state.sdk_client() as client:
        item = client.agent.files.get(file_id)
    output.emit(_raw(item), state.output, human=f"{item.id}  {item.status}  {item.path or item.filename}")


@files_app.command("list")
def files_list(
    ctx: typer.Context,
    chat_id: str = typer.Argument(..., help="The chat id."),
    limit: Optional[int] = typer.Option(None, "--limit"),
    cursor: Optional[str] = typer.Option(None, "--cursor"),
) -> None:
    """List the chat's workspace: your inputs and what the agent produced."""
    state = ctx.obj
    with state.sdk_client() as client:
        page = client.agent.files.list(chat_id, limit=limit, cursor=cursor)
    rows = [{"id": f.id, "path": f.path or f.filename, "size": f.size, "origin": f.origin or ""} for f in page.items]
    human = output.render_table(rows, ["id", "path", "size", "origin"])
    output.emit(_page(page.items, page.next_cursor), state.output, human=human + _more(page.next_cursor))


@files_app.command("download")
def files_download(
    ctx: typer.Context,
    chat_id: str = typer.Argument(..., help="The chat id."),
    file_id: str = typer.Argument(..., help="The file id."),
    out: Path = typer.Option(Path("."), "--out", "-o", help="A directory, or the file path to write."),
) -> None:
    """Download a file from the chat's workspace."""
    state = ctx.obj
    with state.sdk_client() as client:
        saved = client.agent.files.download(chat_id, file_id, out)
    output.emit({"fileId": file_id, "path": str(saved)}, state.output, human=str(saved))


# ── subagents ──

@subagents_app.command("list")
def subagents_list(
    ctx: typer.Context,
    chat_id: str = typer.Argument(..., help="The chat id."),
    message_id: Optional[str] = typer.Option(None, "--message", help="Only this reply's subagents."),
    status: Optional[str] = typer.Option(None, "--status", help="e.g. running."),
    limit: Optional[int] = typer.Option(None, "--limit"),
    cursor: Optional[str] = typer.Option(None, "--cursor"),
) -> None:
    """List a chat's subagents, newest first."""
    state = ctx.obj
    with state.sdk_client() as client:
        page = client.agent.subagents.list(chat_id, message_id=message_id, status=status, limit=limit, cursor=cursor)
    rows = [{"id": s.id, "status": s.status, "name": s.name, "title": s.title} for s in page.items]
    human = output.render_table(rows, ["id", "status", "name", "title"])
    output.emit(_page(page.items, page.next_cursor), state.output, human=human + _more(page.next_cursor))


@subagents_app.command("show")
def subagents_show(
    ctx: typer.Context,
    chat_id: str = typer.Argument(..., help="The chat id."),
    subagent_id: str = typer.Argument(..., help="The subagent id."),
) -> None:
    """Show a subagent's brief, steps and result."""
    state = ctx.obj
    with state.sdk_client() as client:
        sub = client.agent.subagents.get(chat_id, subagent_id)
    lines = [f"{sub.id}  {sub.status}  {sub.title}"] + [f"  - {s.title} ({s.status})" for s in sub.steps]
    if sub.result:
        lines.append(sub.result)
    output.emit(_raw(sub), state.output, human="\n".join(lines))


@subagents_app.command("cancel")
def subagents_cancel(
    ctx: typer.Context,
    chat_id: str = typer.Argument(..., help="The chat id."),
    subagent_id: str = typer.Argument(..., help="The subagent id."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Confirm without prompting."),
) -> None:
    """Stop one subagent; its reply goes on."""
    state = ctx.obj
    output.confirm_destructive(f"stop subagent '{subagent_id}'", yes=yes, mode=state.output)
    with state.sdk_client() as client:
        sub = client.agent.subagents.cancel(chat_id, subagent_id)
    output.emit(_raw(sub), state.output, human=f"{sub.id}  {sub.status}")


# ── campaign mode ──

@app.command("workflows")
def workflows(ctx: typer.Context) -> None:
    """List the campaign workflows your account can run."""
    state = ctx.obj
    with state.sdk_client() as client:
        items = client.agent.workflows.list()
    rows = [{"id": w.id, "engine": w.engine, "label": w.label} for w in items]
    output.emit({"data": [_raw(w) for w in items]}, state.output,
                human=output.render_table(rows, ["id", "engine", "label"]))


@app.command("candidates")
def candidates(
    ctx: typer.Context,
    chat_id: str = typer.Argument(..., help="The chat id."),
    sort: Optional[str] = typer.Option(None, "--sort", help="A metric, '-' for descending, e.g. -iptm."),
    limit: Optional[int] = typer.Option(None, "--limit"),
    cursor: Optional[str] = typer.Option(None, "--cursor"),
) -> None:
    """List the designs a campaign in this chat produced, ranked."""
    state = ctx.obj
    with state.sdk_client() as client:
        page = client.agent.campaigns.candidates(chat_id, sort=sort, limit=limit, cursor=cursor)
    rows = [{"rank": c.rank, "id": c.id, "name": c.name or "",
             "metrics": ", ".join(f"{k}={v}" for k, v in c.metrics.items())} for c in page.items]
    human = output.render_table(rows, ["rank", "id", "name", "metrics"])
    output.emit(_page(page.items, page.next_cursor), state.output, human=human + _more(page.next_cursor))


@app.command("structure")
def structure(
    ctx: typer.Context,
    chat_id: str = typer.Argument(..., help="The chat id."),
    candidate_id: str = typer.Argument(..., help="The candidate id."),
    out: Path = typer.Option(Path("."), "--out", "-o", help="A directory, or the file path to write."),
) -> None:
    """Download a candidate's predicted structure."""
    state = ctx.obj
    with state.sdk_client() as client:
        saved = client.agent.campaigns.download_structure(chat_id, candidate_id, out)
    output.emit({"candidateId": candidate_id, "path": str(saved)}, state.output, human=str(saved))


@app.command("jobs")
def jobs(
    ctx: typer.Context,
    chat_id: str = typer.Argument(..., help="The chat id."),
    campaign_id: Optional[str] = typer.Option(None, "--campaign", help="Only one campaign's jobs."),
    limit: Optional[int] = typer.Option(None, "--limit"),
    cursor: Optional[str] = typer.Option(None, "--cursor"),
) -> None:
    """List the platform jobs the agent submitted in this chat."""
    state = ctx.obj
    with state.sdk_client() as client:
        page = client.agent.campaigns.jobs(chat_id, campaign_id=campaign_id, limit=limit, cursor=cursor)
    rows = [{"jobName": j.job_name, "tool": j.tool, "status": j.status, "hours": j.compute_hours} for j in page.items]
    human = output.render_table(rows, ["jobName", "tool", "status", "hours"])
    output.emit(_page(page.items, page.next_cursor), state.output, human=human + _more(page.next_cursor))


@app.command("task")
def task(
    ctx: typer.Context,
    chat_id: str = typer.Argument(..., help="The chat id."),
    task_id: str = typer.Argument(..., help="A task from the campaign's plan."),
) -> None:
    """Show a campaign task's report."""
    state = ctx.obj
    with state.sdk_client() as client:
        report = client.agent.campaigns.task(chat_id, task_id)
    output.emit(_raw(report), state.output, human=f"{report.id}  {report.status}  {report.title}\n\n{report.report or ''}".rstrip())


@app.command("export")
def export(
    ctx: typer.Context,
    chat_id: str = typer.Argument(..., help="The chat id."),
    export_id: Optional[str] = typer.Option(None, "--id", help="Check an export already started."),
    format: Optional[str] = typer.Option(None, "--format", help="zip (default) or csv."),
) -> None:
    """Start an export of the chat's campaign results, or check one with --id."""
    state = ctx.obj
    with state.sdk_client() as client:
        if export_id:
            result = client.agent.campaigns.get_export(chat_id, export_id)
        else:
            result = client.agent.campaigns.create_export(chat_id, format=format)
    # downloadUrl is presigned: JSON carries it (that is what it is for), the human line does not.
    output.emit(_raw(result), state.output, human=f"{result.id}  {result.status}")


@app.command("usage")
def usage(
    ctx: typer.Context,
    chat_id: Optional[str] = typer.Argument(None, help="A chat id. Omit for your monthly totals."),
    month: Optional[str] = typer.Option(None, "--month", help="YYYY-MM, for monthly totals."),
) -> None:
    """What the agent cost: one chat, or your month."""
    state = ctx.obj
    if chat_id and month:
        raise TamarindError("Pass a chat id or --month, not both.")
    with state.sdk_client() as client:
        result = client.agent.usage.chat(chat_id) if chat_id else client.agent.usage.month(month)
    head = f"{result.month}: " if result.month else ""
    human = (f"{head}{result.total_hours:g} h total ({result.agent_hours:g} h agent, "
             f"{result.jobs_hours:g} h jobs)")
    output.emit(_raw(result), state.output, human=human)
