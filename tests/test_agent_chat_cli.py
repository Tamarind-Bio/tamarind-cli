"""``tamarind chat`` commands against a mocked Agent API."""

from __future__ import annotations

import json
import sys

import httpx
import pytest
import respx
from typer.testing import CliRunner

from agent_fakes import approval, frame, reply, sse
from tamarind.cli import main as main_module
from tamarind.cli.main import app
from tamarind.errors import ExitCode, TamarindError

runner = CliRunner()
API = "https://api.test/api/"
ENV = {"TAMARIND_API_KEY": "k", "TAMARIND_API_BASE": API, "TAMARIND_CATALOG_BASE": "https://cat.test/"}
CHAT = {"id": "chat_7Q", "object": "chat", "title": "PD-L1", "status": "idle", "source": "api",
        "createdAt": "2026-10-27T17:02:11Z", "updatedAt": "2026-10-27T17:02:11Z",
        "webUrl": "https://app.tamarind.bio/agent/chat_7Q"}


def _run(argv: list[str], monkeypatch, capsys) -> tuple[int, str, str]:
    """Through the console entry point, so exit codes and JSON errors are the real ones."""
    for key, value in ENV.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setattr(sys, "argv", ["tamarind", *argv])
    code = 0
    try:
        main_module.run()
    except SystemExit as exc:
        code = int(exc.code or 0)
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def _reply_stream(*frames: str) -> httpx.Response:
    return sse("".join(frames))


@respx.mock
def test_chat_new_creates_with_only_the_given_fields_and_a_key():
    route = respx.post(f"{API}chats").mock(return_value=httpx.Response(201, json=CHAT))
    res = runner.invoke(app, ["--json", "chat", "new", "--title", "PD-L1"], env=ENV)
    assert res.exit_code == 0, res.output
    assert json.loads(res.stdout)["id"] == "chat_7Q"
    request = route.calls.last.request
    assert json.loads(request.content) == {"title": "PD-L1"}
    assert request.headers["Idempotency-Key"]
    assert request.headers["Tamarind-Version"] == "2026-11-01"


@respx.mock
def test_send_wait_streams_the_reply_text_to_stdout():
    send = respx.post(f"{API}chats/chat_7Q/messages").mock(
        return_value=httpx.Response(202, json=reply("queued")))
    respx.get(f"{API}chats/chat_7Q/events").mock(return_value=_reply_stream(
        frame("1.0", "message.in_progress", reply("in_progress")),
        frame("2.0", "output_text.delta", {"partId": "p_0", "delta": "Mean pLDDT "}),
        frame(None, "ping", {}),
        frame("3.0", "output_text.delta", {"partId": "p_0", "delta": "87"}),
        frame("4.0", "output_text.done", {"partId": "p_0", "text": "Mean pLDDT 87.3"}),
        frame("5.0", "message.completed", reply("completed", text="Mean pLDDT 87.3")),
    ))

    res = runner.invoke(app, ["--no-json", "-q", "chat", "send", "chat_7Q", "Fold it", "--wait"], env=ENV)

    assert res.exit_code == 0, res.output
    assert res.stdout == "Mean pLDDT 87.3\n"
    body = json.loads(send.calls.last.request.content)
    assert body == {"input": [{"type": "text", "text": "Fold it"}], "stream": False}


@respx.mock
def test_send_wait_in_json_mode_prints_the_finished_reply():
    respx.post(f"{API}chats/chat_7Q/messages").mock(return_value=httpx.Response(202, json=reply("queued")))
    respx.get(f"{API}chats/chat_7Q/events").mock(return_value=_reply_stream(
        frame("2.0", "output_text.delta", {"partId": "p_0", "delta": "hi"}),
        frame("5.0", "message.completed", reply("completed", text="hi")),
    ))
    res = runner.invoke(app, ["--json", "chat", "send", "chat_7Q", "x", "--wait"], env=ENV)
    assert res.exit_code == 0, res.output
    assert json.loads(res.stdout)["status"] == "completed"


@respx.mock
def test_send_wait_exits_10_with_the_approval_to_answer_when_the_reply_stops_on_a_card(monkeypatch, capsys):
    respx.post(f"{API}chats/chat_7Q/messages").mock(return_value=httpx.Response(202, json=reply("queued")))
    respx.get(f"{API}chats/chat_7Q/events").mock(return_value=_reply_stream(
        frame("4.0", "message.requires_action", reply("requires_action", approvals=[approval()])),
    ))
    respx.get(f"{API}chats/chat_7Q/messages/msg_1").mock(
        return_value=httpx.Response(200, json=reply("requires_action", approvals=[approval()])))

    code, out, err = _run(["--json", "chat", "send", "chat_7Q", "x", "--wait"], monkeypatch, capsys)

    assert code == ExitCode.ACTION_REQUIRED == 10
    assert out == ""
    error = json.loads(err)["error"]
    assert error["type"] == "AgentActionRequiredError"
    assert [a["id"] for a in error["detail"]["approvals"]] == ["apr_x"]
    assert "tamarind chat approve chat_7Q apr_x" in error["message"]


@respx.mock
@pytest.mark.parametrize("status", ["failed", "cancelled", "incomplete"])
def test_send_wait_exits_9_when_the_reply_ends_badly(status, monkeypatch, capsys):
    respx.post(f"{API}chats/chat_7Q/messages").mock(return_value=httpx.Response(202, json=reply("queued")))
    respx.get(f"{API}chats/chat_7Q/events").mock(return_value=_reply_stream(
        frame("5.0", f"message.{status}", reply(status)),
    ))
    code, out, err = _run(["--json", "chat", "send", "chat_7Q", "x", "--wait"], monkeypatch, capsys)
    assert code == ExitCode.JOB_FAILED
    assert json.loads(out)["status"] == status
    assert json.loads(err)["error"]["detail"]["status"] == status


@respx.mock
@pytest.mark.parametrize("file_id", [
    "file_u0123456789abcdef0123456789abcdef",  # an upload
    "file_wboltz-model_0.0123456789abcdef0123456789abcdef",  # a listed file: opaque, with a dot
])
def test_send_with_a_file_id_attaches_it_without_uploading(file_id):
    send = respx.post(f"{API}chats/chat_7Q/messages").mock(return_value=httpx.Response(202, json=reply("queued")))
    res = runner.invoke(app, ["--json", "chat", "send", "chat_7Q", "look", "--file", file_id], env=ENV)
    assert res.exit_code == 0, res.output
    assert json.loads(send.calls.last.request.content)["input"][1] == {"type": "file", "fileId": file_id}


@respx.mock
@pytest.mark.parametrize(("argv", "code"), [
    (["chat_7Q", "--file", "file_9f2"], 2),  # no text: the server refuses a blank message
    (["chat_7Q", "look", "--file", "missing.pdb"], 1),  # neither a local file nor an id
])
def test_send_refuses_before_sending_what_the_api_would_reject(argv, code):
    send = respx.post(f"{API}chats/chat_7Q/messages").mock(return_value=httpx.Response(202, json=reply("queued")))
    res = runner.invoke(app, ["--json", "chat", "send", *argv], env=ENV)
    assert res.exit_code == code or (code == 1 and isinstance(res.exception, TamarindError))
    assert not send.called


@respx.mock
def test_files_upload_creates_a_slot_then_puts_the_bytes_without_the_api_key(tmp_path):
    target = tmp_path / "target.pdb"
    target.write_bytes(b"ATOM  1\n")
    create = respx.post(f"{API}chat-files").mock(return_value=httpx.Response(201, json={
        "fileId": "file_9f2", "uploadUrl": "https://s3.test/u/file_9f2?X-Amz-Signature=s",
        "expiresAt": "2026-10-27T17:17:11Z"}))
    put = respx.put("https://s3.test/u/file_9f2").mock(return_value=httpx.Response(200))

    res = runner.invoke(app, ["--json", "chat", "files", "upload", str(target)], env=ENV)

    assert res.exit_code == 0, res.output
    assert json.loads(res.stdout)["fileId"] == "file_9f2"
    assert "uploadUrl" not in res.stdout  # a presigned URL is a credential
    assert json.loads(create.calls.last.request.content) == {
        "filename": "target.pdb", "size": 8, "contentType": "chemical/x-pdb"}
    upload = put.calls.last.request
    assert upload.content == b"ATOM  1\n"
    assert upload.headers["Content-Type"] == "chemical/x-pdb"
    assert "x-api-key" not in upload.headers


@respx.mock
@pytest.mark.parametrize(("location_leaf", "saved_as"), [
    ("model_0.cif", "model_0.cif"),
    ("..%2F..%2Fevil", "evil"),  # an encoded traversal in the URL's name never leaves the directory
])
def test_files_download_follows_the_redirect_without_the_api_key(location_leaf, saved_as, tmp_path):
    # A listed (agent-made) file: no files.get lookup, which reads uploads only.
    respx.get(f"{API}chats/chat_7Q/files/file_wboltz.0123456789abcdef0123456789abcdef/content").mock(
        return_value=httpx.Response(302, headers={"Location": f"https://s3.test/f/{location_leaf}?sig=1"}))
    s3 = respx.get(url__regex=r"^https://s3\.test/f/").mock(return_value=httpx.Response(200, content=b"data_x\n"))
    victim = tmp_path.parent / f"victim-{saved_as}"
    victim.write_bytes(b"keep me")
    (tmp_path / f"{saved_as}.part").symlink_to(victim)

    res = runner.invoke(app, ["--json", "chat", "files", "download", "chat_7Q",
                              "file_wboltz.0123456789abcdef0123456789abcdef", "--out", str(tmp_path)], env=ENV)

    assert res.exit_code == 0, res.output
    assert (tmp_path / saved_as).read_bytes() == b"data_x\n"
    assert "x-api-key" not in s3.calls.last.request.headers
    assert [p.name for p in tmp_path.glob("*.part")] == [f"{saved_as}.part"]  # only the planted one
    assert victim.read_bytes() == b"keep me"  # a planted <name>.part symlink is never opened


@respx.mock
def test_approvals_lists_and_approve_resolves():
    respx.get(f"{API}chats/chat_7Q/approvals").mock(return_value=httpx.Response(200, json={"data": [approval()]}))
    resolve = respx.post(f"{API}chats/chat_7Q/approvals/apr_x").mock(
        return_value=httpx.Response(200, json=approval(status="approved")))

    listed = runner.invoke(app, ["--json", "chat", "approvals", "chat_7Q", "--status", "pending"], env=ENV)
    approved = runner.invoke(app, ["--json", "chat", "approve", "chat_7Q", "apr_x", "--scope", "once"], env=ENV)
    denied = runner.invoke(app, ["--json", "chat", "deny", "chat_7Q", "apr_x"], env=ENV)

    assert listed.exit_code == approved.exit_code == denied.exit_code == 0
    assert json.loads(listed.stdout)["data"][0]["id"] == "apr_x"
    bodies = [json.loads(call.request.content) for call in resolve.calls]
    assert bodies == [{"decision": "approve", "scope": "once"}, {"decision": "deny"}]


@respx.mock
def test_answer_sends_answers_keyed_by_question_text():
    route = respx.post(f"{API}chats/chat_7Q/questions/q_8c").mock(return_value=httpx.Response(200, json={
        "id": "q_8c", "status": "answered", "questions": [], "createdAt": "x"}))
    res = runner.invoke(app, ["--json", "chat", "answer", "chat_7Q", "q_8c",
                              "--question", "Which chain is the target?", "--choice", "Chain A",
                              "--question", "Buffer pH?", "--choice", "pH=7.4"], env=ENV)
    assert res.exit_code == 0, res.output
    # Either side may hold an '='.
    assert json.loads(route.calls.last.request.content) == {
        "answers": {"Which chain is the target?": "Chain A", "Buffer pH?": "pH=7.4"}}
    assert route.calls.last.request.headers["Idempotency-Key"]


@respx.mock
def test_events_follow_prints_one_json_object_per_event():
    respx.get(f"{API}chats/chat_7Q/events").mock(return_value=_reply_stream(
        frame("1.0", "output_text.delta", {"partId": "p_0", "delta": "a"}),
        frame("2.0", "message.completed", reply("completed")),
    ))
    res = runner.invoke(app, ["--json", "chat", "events", "chat_7Q", "--follow", "--message", "msg_1"], env=ENV)
    assert res.exit_code == 0, res.output
    assert [json.loads(line)["id"] for line in res.stdout.splitlines()] == ["1.0", "2.0"]


@respx.mock
def test_archive_refuses_without_yes_in_json_mode():
    route = respx.delete(f"{API}chats/chat_7Q").mock(return_value=httpx.Response(200, json={"id": "chat_7Q", "status": "archived"}))
    refused = runner.invoke(app, ["--json", "chat", "archive", "chat_7Q"], env=ENV)
    allowed = runner.invoke(app, ["--json", "chat", "archive", "chat_7Q", "--yes"], env=ENV)
    assert refused.exit_code == ExitCode.USAGE
    assert allowed.exit_code == 0
    assert len(route.calls) == 1


@respx.mock
def test_usage_without_a_chat_reads_the_month():
    route = respx.get(f"{API}agent-usage").mock(return_value=httpx.Response(200, json={
        "month": "2026-10", "agentHours": 1, "jobsHours": 2, "totalHours": 3}))
    res = runner.invoke(app, ["--no-json", "chat", "usage", "--month", "2026-10"], env=ENV)
    assert res.exit_code == 0, res.output
    assert route.calls.last.request.url.params["month"] == "2026-10"
    assert "2026-10: 3 h total" in res.stdout


@respx.mock
def test_send_wait_keeps_a_continuing_replys_parts_apart():
    # The continuing reply numbers its parts from p_0 again.
    respx.post(f"{API}chats/chat_7Q/messages").mock(return_value=httpx.Response(202, json=reply("queued")))
    respx.get(f"{API}chats/chat_7Q/events").mock(side_effect=[
        _reply_stream(
            frame("1.0", "output_text.delta", {"partId": "p_0", "delta": "First."}),
            frame("2.0", "output_text.done", {"partId": "p_0", "text": "First."}),
            frame("3.0", "message.completed", reply("completed", continued_by="msg_2", text="First.")),
        ),
        _reply_stream(
            frame("4.0", "output_text.delta", {"partId": "p_0", "delta": "Sec"}, message="msg_2"),
            frame("5.0", "output_text.done", {"partId": "p_0", "text": "Second."}, message="msg_2"),
            frame("6.0", "message.completed", reply("completed", message_id="msg_2", text="Second."), message="msg_2"),
        ),
    ])
    res = runner.invoke(app, ["--no-json", "-q", "chat", "send", "chat_7Q", "x", "--wait"], env=ENV)
    assert res.exit_code == 0, res.output
    assert res.stdout == "First.\n\nSecond.\n"


@respx.mock
def test_structure_into_a_directory_takes_the_urls_file_name(tmp_path):
    respx.get(f"{API}chats/chat_7Q/candidates/cand_07/structure").mock(return_value=httpx.Response(
        302, headers={"Location": "https://s3.test/u/candidates/pdl1-b07.cif?X-Amz-Signature=s"}))
    s3 = respx.get("https://s3.test/u/candidates/pdl1-b07.cif").mock(return_value=httpx.Response(200, content=b"data_\n"))
    res = runner.invoke(app, ["--json", "chat", "structure", "chat_7Q", "cand_07", "--out", str(tmp_path)], env=ENV)
    assert res.exit_code == 0, res.output
    assert (tmp_path / "pdl1-b07.cif").read_bytes() == b"data_\n"
    assert "x-api-key" not in s3.calls.last.request.headers


@respx.mock
@pytest.mark.parametrize(
    ("frames", "final", "expected"),
    [
        # Piped (not a terminal): only the authoritative text, never the corrected draft.
        ([frame("1.0", "output_text.delta", {"partId": "p_0", "delta": "The answer is 5"}),
          frame("2.0", "output_text.done", {"partId": "p_0", "text": "The answer is 6."})],
         "The answer is 6.", "The answer is 6.\n"),
        # A discarded draft never reaches stdout.
        ([frame("1.0", "output_text.delta", {"partId": "p_0", "delta": "draft"}),
          frame("2.0", "output_text.discarded", {"partId": "p_0"}),
          frame("3.0", "output_text.delta", {"partId": "p_1", "delta": "final"}),
          frame("4.0", "output_text.done", {"partId": "p_1", "text": "final"})],
         "final", "final\n"),
        # ...even one discarded after its output_text.done.
        ([frame("1.0", "output_text.done", {"partId": "p_0", "text": "draft"}),
          frame("2.0", "output_text.discarded", {"partId": "p_0"}),
          frame("3.0", "output_text.done", {"partId": "p_1", "text": "final"})],
         "final", "final\n"),
    ],
)
def test_piped_human_output_is_exactly_the_final_text(frames, final, expected):
    respx.post(f"{API}chats/chat_7Q/messages").mock(return_value=httpx.Response(202, json=reply("queued")))
    respx.get(f"{API}chats/chat_7Q/events").mock(return_value=_reply_stream(
        *frames, frame("9.0", "message.completed", reply("completed", text=final))))
    res = runner.invoke(app, ["--no-json", "-q", "chat", "send", "chat_7Q", "x", "--wait"], env=ENV)
    assert res.exit_code == 0, res.output
    assert res.stdout == expected


@respx.mock
def test_wait_on_your_own_message_follows_its_reply():
    user = {"id": "msg_0", "object": "message", "chatId": "chat_7Q", "role": "user", "content": [],
            "createdAt": "2026-10-27T17:02:11Z"}
    respx.get(f"{API}chats/chat_7Q/messages/msg_0").mock(return_value=httpx.Response(200, json=user))
    respx.get(f"{API}chats/chat_7Q/messages").mock(return_value=httpx.Response(200, json={
        "data": [user, reply("in_progress")], "nextCursor": None}))
    events = respx.get(f"{API}chats/chat_7Q/events").mock(return_value=_reply_stream(
        frame("5.0", "message.completed", reply("completed"))))
    res = runner.invoke(app, ["--json", "chat", "wait", "chat_7Q", "msg_0"], env=ENV)
    assert res.exit_code == 0, res.output
    assert events.calls.last.request.url.params["messageId"] == "msg_1"


@respx.mock
def test_approve_wait_exits_7_when_the_answer_has_not_started(monkeypatch, capsys):
    from tamarind.agent.events import EventStream

    monkeypatch.setitem(EventStream.__init__.__kwdefaults__, "continuation_wait", 0.0)
    respx.post(f"{API}chats/chat_7Q/approvals/apr_x").mock(
        return_value=httpx.Response(200, json=approval(status="approved")))
    respx.get(f"{API}chats/chat_7Q/events").mock(return_value=_reply_stream(
        frame("5.0", "approval.resolved", approval(status="approved")),
        frame("6.0", "message.completed", reply("completed")),
    ))
    code, out, err = _run(["--json", "chat", "approve", "chat_7Q", "apr_x", "--wait"], monkeypatch, capsys)
    assert code == ExitCode.TIMEOUT
    error = json.loads(err)["error"]
    assert error["type"] == "JobTimeoutError"
    assert "tamarind chat wait chat_7Q msg_1" in error["message"]


@respx.mock
@pytest.mark.parametrize("direction", ["download", "upload"])
def test_a_failed_presigned_transfer_never_carries_the_signed_url(direction, tmp_path):
    import traceback

    from tamarind import Tamarind

    signed = "https://s3.test/f/model_0.cif?X-Amz-Credential=AKIA&X-Amz-Signature=secret"
    with Tamarind(api_key="k", api_base=API) as client:
        if direction == "download":
            respx.get(f"{API}chats/chat_7Q/files/file_k2/content").mock(
                return_value=httpx.Response(302, headers={"Location": signed}))
            respx.get(url__regex=r"^https://s3\.test/").mock(return_value=httpx.Response(403))
            action = lambda: client.agent.files.download("chat_7Q", "file_k2", tmp_path / "out.cif")  # noqa: E731
        else:
            target = tmp_path / "target.pdb"
            target.write_bytes(b"ATOM\n")
            respx.post(f"{API}chat-files").mock(return_value=httpx.Response(201, json={
                "fileId": "file_u0", "uploadUrl": signed, "expiresAt": "x"}))
            respx.put(url__regex=r"^https://s3\.test/").mock(return_value=httpx.Response(403))
            action = lambda: client.agent.files.upload(target)  # noqa: E731
        with pytest.raises(TamarindError) as raised:
            action()
    rendered = "".join(traceback.format_exception(raised.value))
    assert "X-Amz-Signature" not in rendered and "secret" not in rendered


@pytest.mark.parametrize("extra", [["--text", "A", "--question", "Which?", "--choice", "A"], []])
def test_an_answer_with_both_forms_or_neither_is_a_structured_error(extra, monkeypatch, capsys):
    code, out, err = _run(["--json", "chat", "answer", "chat_7Q", "q_8c", *extra], monkeypatch, capsys)
    assert code == ExitCode.VALIDATION
    assert out == ""
    assert json.loads(err)["error"]["type"] == "ArgumentError"


@respx.mock
def test_an_interrupted_events_follow_exits_130_not_0(monkeypatch):
    from tamarind.agent.events import EventStream

    def interrupted(self):
        raise KeyboardInterrupt

    monkeypatch.setattr(EventStream, "__next__", interrupted)
    res = runner.invoke(app, ["--json", "chat", "events", "chat_7Q", "--follow"], env=ENV)
    assert res.exit_code == 130
