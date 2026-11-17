"""``tamarind chat`` commands against a mocked Agent API."""

from __future__ import annotations

import json
import sys

import httpx
import pytest
import respx
from typer.testing import CliRunner

from agent_fakes import UPLOAD_FIELDS, UPLOAD_URL, approval, form_parts, frame, reply, sse, upload_slot
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
def test_files_upload_creates_a_slot_then_posts_the_form_without_the_api_key(tmp_path):
    target = tmp_path / "target.pdb"
    target.write_bytes(b"ATOM  1\n")
    create = respx.post(f"{API}chat-files").mock(return_value=httpx.Response(201, json=upload_slot()))
    post = respx.post(UPLOAD_URL).mock(return_value=httpx.Response(204))
    put = respx.put(url__regex=r"^https://s3\.test/").mock(return_value=httpx.Response(200))

    res = runner.invoke(app, ["--json", "chat", "files", "upload", str(target)], env=ENV)

    assert res.exit_code == 0, res.output
    assert json.loads(res.stdout) == {"fileId": "file_9f2", "expiresAt": "2026-10-27T17:17:11Z"}
    for credential in ("uploadUrl", "uploadFields", UPLOAD_URL, "topsecretsig", "POLICYB64"):
        assert credential not in res.stdout  # the form is a credential
    assert json.loads(create.calls.last.request.content) == {"filename": "target.pdb"}
    upload = post.calls.last.request
    # The fields as given and in order, then the file as the last field, named `file`.
    assert form_parts(upload) == [(name, None, value.encode()) for name, value in UPLOAD_FIELDS.items()] + [
        ("file", "target.pdb", b"ATOM  1\n")]
    assert "x-api-key" not in upload.headers and "Tamarind-Version" not in upload.headers
    assert not put.called  # a form POST, not a PUT


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
def test_approve_sends_a_decision_and_a_scope_and_nothing_else():
    resolve = respx.post(f"{API}chats/chat_7Q/approvals/apr_x").mock(
        return_value=httpx.Response(200, json=approval(status="approved")))
    res = runner.invoke(app, ["--json", "chat", "approve", "chat_7Q", "apr_x", "--scope", "chat"], env=ENV)
    assert res.exit_code == 0, res.output
    assert json.loads(resolve.calls.last.request.content) == {"decision": "approve", "scope": "chat"}


@pytest.mark.parametrize("option", ["--budget-hours", "--workflow"])
def test_approve_no_longer_takes_the_options_a_decision_dropped(option):
    res = runner.invoke(app, ["--json", "chat", "approve", "chat_7Q", "apr_x", option, "5"], env=ENV)
    assert res.exit_code == ExitCode.USAGE


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
    assert "Idempotency-Key" not in route.calls.last.request.headers  # a repeat is safe: no key


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
def test_delete_refuses_without_yes_in_json_mode_and_says_it_is_deleted():
    route = respx.delete(f"{API}chats/chat_7Q").mock(
        return_value=httpx.Response(200, json={"id": "chat_7Q", "object": "chat", "deleted": True}))
    refused = runner.invoke(app, ["--json", "chat", "delete", "chat_7Q"], env=ENV)
    allowed = runner.invoke(app, ["--json", "chat", "delete", "chat_7Q", "--yes"], env=ENV)
    human = runner.invoke(app, ["--no-json", "chat", "delete", "chat_7Q", "--yes"], env=ENV)
    assert refused.exit_code == ExitCode.USAGE
    assert allowed.exit_code == 0
    assert json.loads(allowed.stdout) == {"id": "chat_7Q", "object": "chat", "deleted": True}
    assert human.stdout.strip() == "chat_7Q deleted"
    assert len(route.calls) == 2


def test_there_is_no_archive_command_for_a_chat_that_the_api_now_deletes():
    assert runner.invoke(app, ["--json", "chat", "archive", "chat_7Q", "--yes"], env=ENV).exit_code == ExitCode.USAGE


SHARED = {"id": "chat_9Z", "object": "chat", "readOnly": True, "title": "Antibody notes",
          "ownerEmail": "ana@lab.test", "source": "ui", "mode": "chat",
          "webUrl": "https://app.tamarind.bio/agent/chat_9Z", "createdAt": "2026-10-25T09:12:00Z",
          "updatedAt": "2026-10-26T16:30:41Z"}


@respx.mock
def test_list_scope_org_reads_teammates_chats_as_read_only_items_with_an_owner():
    route = respx.get(f"{API}chats").mock(return_value=httpx.Response(200, json={
        "data": [SHARED], "nextCursor": None}))
    res = runner.invoke(app, ["--no-json", "chat", "list", "--scope", "org"], env=ENV)
    assert res.exit_code == 0, res.output
    assert route.calls.last.request.url.params["scope"] == "org"
    assert "ana@lab.test" in res.stdout and "Antibody notes" in res.stdout


@respx.mock
def test_showing_a_teammates_chat_says_it_is_read_only_and_whose():
    respx.get(f"{API}chats/chat_9Z").mock(return_value=httpx.Response(200, json=SHARED))
    res = runner.invoke(app, ["--no-json", "chat", "show", "chat_9Z"], env=ENV)
    assert res.exit_code == 0, res.output
    assert "read-only, ana@lab.test's" in res.stdout


@respx.mock
def test_list_never_offers_the_removed_campaign_status_filter():
    route = respx.get(f"{API}chats")
    res = runner.invoke(app, ["--json", "chat", "list", "--campaign-status", "running"], env=ENV)
    assert res.exit_code == ExitCode.USAGE
    assert not route.called


@respx.mock
def test_jobs_never_offers_the_removed_campaign_filter():
    route = respx.get(f"{API}chats/chat_7Q/jobs")
    res = runner.invoke(app, ["--json", "chat", "jobs", "chat_7Q", "--campaign", "cmp_7Q"], env=ENV)
    assert res.exit_code == ExitCode.USAGE
    assert not route.called


@respx.mock
def test_files_list_says_when_the_listing_is_truncated():
    respx.get(f"{API}chats/chat_7Q/files").mock(return_value=httpx.Response(200, json={
        "data": [], "nextCursor": None, "truncated": True}))
    res = runner.invoke(app, ["--no-json", "chat", "files", "list", "chat_7Q"], env=ENV)
    assert res.exit_code == 0, res.output
    assert "only the first 20,000 by path are listed" in res.stdout


@respx.mock
def test_workflows_lists_what_each_supports():
    respx.get(f"{API}agent-workflows").mock(return_value=httpx.Response(200, json={"data": [
        {"id": "binder-design", "label": "Binder design", "supports": ["plan", "pause", "budget"]}]}))
    res = runner.invoke(app, ["--no-json", "chat", "workflows"], env=ENV)
    assert res.exit_code == 0, res.output
    assert "binder-design" in res.stdout and "plan, pause, budget" in res.stdout


@respx.mock
def test_new_with_approve_all_names_it_whole_and_needs_a_yes():
    route = respx.post(f"{API}chats").mock(return_value=httpx.Response(201, json={
        **CHAT, "autoApprove": True, "dangerouslyApproveAll": True}))
    argv = ["--json", "chat", "new", "--auto-approve", "--dangerously-approve-all"]

    refused = runner.invoke(app, argv, env=ENV)
    allowed = runner.invoke(app, [*argv, "--yes"], env=ENV)

    assert refused.exit_code == ExitCode.USAGE
    assert len(route.calls) == 1  # only the confirmed one was sent
    assert json.loads(route.calls.last.request.content) == {"autoApprove": True, "dangerouslyApproveAll": True}
    assert allowed.exit_code == 0


@respx.mock
@pytest.mark.parametrize(("flag", "yes", "sent"), [
    (["--auto-approve", "--dangerously-approve-all"], [], None),  # refused: nothing to confirm with
    (["--auto-approve", "--dangerously-approve-all"], ["--yes"], {"autoApprove": True, "dangerouslyApproveAll": True}),
    # Turning it OFF is the safe direction: no confirmation.
    (["--no-dangerously-approve-all"], [], {"dangerouslyApproveAll": False}),
])
def test_update_asks_for_a_yes_only_to_turn_approve_all_on(flag, yes, sent):
    route = respx.patch(f"{API}chats/chat_7Q").mock(return_value=httpx.Response(200, json=CHAT))
    res = runner.invoke(app, ["--json", "chat", "update", "chat_7Q", *flag, *yes], env=ENV)
    if sent is None:
        assert res.exit_code == ExitCode.USAGE and not route.called
    else:
        assert res.exit_code == 0, res.output
        assert json.loads(route.calls.last.request.content) == sent


@pytest.mark.parametrize("command", ["new", "update"])
def test_the_approve_all_flag_says_in_help_that_it_is_dangerous_and_what_it_does(command):
    argv = ["chat", command, *(["chat_7Q"] if command == "update" else []), "--help"]
    res = runner.invoke(app, argv, env={**ENV, "COLUMNS": "200"})
    assert res.exit_code == 0, res.output
    text = " ".join(res.stdout.split())
    assert "--dangerously-approve-all" in text and "DANGEROUS" in text
    assert "deletes and cancels" in text and "Needs --yes" in text


@respx.mock
def test_showing_a_chat_says_when_approve_all_is_on():
    respx.get(f"{API}chats/chat_7Q").mock(return_value=httpx.Response(200, json={
        **CHAT, "autoApprove": True, "dangerouslyApproveAll": True}))
    res = runner.invoke(app, ["--no-json", "chat", "show", "chat_7Q"], env=ENV)
    assert "approve-all is ON" in res.stdout


@respx.mock
def test_usage_without_a_chat_reads_the_month_without_jobs():
    route = respx.get(f"{API}agent-usage").mock(return_value=httpx.Response(200, json={
        "month": "2026-10", "agentHours": 1.5, "remainingHours": 925.7}))
    res = runner.invoke(app, ["--no-json", "chat", "usage", "--month", "2026-10"], env=ENV)
    assert res.exit_code == 0, res.output
    assert route.calls.last.request.url.params["month"] == "2026-10"
    assert res.stdout.strip() == "2026-10: 1.5 h agent (jobs are not counted here), 925.7 h left of your tightest budget"


@respx.mock
def test_usage_of_a_chat_reads_its_jobs_too():
    respx.get(f"{API}chats/chat_7Q/usage").mock(return_value=httpx.Response(200, json={
        "agentHours": 0.42, "jobsHours": 1.1, "totalHours": 1.52, "capHours": 40}))
    res = runner.invoke(app, ["--no-json", "chat", "usage", "chat_7Q"], env=ENV)
    assert res.exit_code == 0, res.output
    assert res.stdout.strip() == "1.52 h total (0.42 h agent, 1.1 h jobs)"


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
@pytest.mark.parametrize(("headers", "saved_as"), [
    ({"Content-Disposition": 'attachment; filename="pdl1-b07.pdb"'}, "pdl1-b07.pdb"),
    # A name that tries to leave the directory stays in it.
    ({"Content-Disposition": 'attachment; filename="../../evil.pdb"'}, "evil.pdb"),
    # No name: the candidate's id, and an extension for the type.
    ({"Content-Type": "chemical/x-mmcif"}, "cand_07.cif"),
])
def test_structure_into_a_directory_takes_the_name_the_file_carries(headers, saved_as, tmp_path):
    served = respx.get(f"{API}chats/chat_7Q/candidates/cand_07/structure").mock(
        return_value=httpx.Response(200, content=b"data_\n", headers=headers))
    res = runner.invoke(app, ["--json", "chat", "structure", "chat_7Q", "cand_07", "--out", str(tmp_path)], env=ENV)
    assert res.exit_code == 0, res.output
    assert (tmp_path / saved_as).read_bytes() == b"data_\n"
    assert served.calls.last.request.headers["x-api-key"] == "k"  # served by the API itself, not a redirect
    assert [p.name for p in tmp_path.iterdir()] == [saved_as]  # no partial file left behind


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
                "fileId": "file_u0", "uploadUrl": signed, "uploadFields": {**UPLOAD_FIELDS, "policy": "secretpolicy"},
                "expiresAt": "x"}))
            respx.post(url__regex=r"^https://s3\.test/").mock(return_value=httpx.Response(
                403, text="<Error><Code>AccessDenied</Code><Message>Policy expired: secretpolicy</Message></Error>"))
            action = lambda: client.agent.files.upload(target)  # noqa: E731
        with pytest.raises(TamarindError) as raised:
            action()
    rendered = "".join(traceback.format_exception(raised.value))
    assert "X-Amz-Signature" not in rendered and "secret" not in rendered
    assert "topsecretsig" not in rendered and "POLICYB64" not in rendered


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


@respx.mock
def test_requires_action_names_only_the_followed_replys_own_approvals(monkeypatch, capsys):
    # A card outlived an earlier, cancelled turn: it is pending, but not this reply's.
    stale = {**approval("apr_old"), "messageId": "msg_0"}
    respx.post(f"{API}chats/chat_7Q/messages").mock(return_value=httpx.Response(202, json=reply("queued")))
    respx.get(f"{API}chats/chat_7Q/events").mock(return_value=_reply_stream(
        frame("4.0", "message.requires_action", reply("requires_action"))))
    respx.get(f"{API}chats/chat_7Q/messages/msg_1").mock(
        return_value=httpx.Response(200, json=reply("requires_action")))  # cards not inlined
    respx.get(f"{API}chats/chat_7Q/approvals").mock(return_value=httpx.Response(200, json={
        "data": [stale, approval("apr_x")]}))

    code, out, err = _run(["--json", "chat", "send", "chat_7Q", "x", "--wait"], monkeypatch, capsys)

    assert code == ExitCode.ACTION_REQUIRED
    error = json.loads(err)["error"]
    assert [a["id"] for a in error["detail"]["approvals"]] == ["apr_x"]
    assert "apr_old" not in error["message"]


@respx.mock
def test_a_send_whose_answer_is_lost_names_its_idempotency_key(monkeypatch, capsys):
    route = respx.post(f"{API}chats/chat_7Q/messages").mock(side_effect=httpx.ReadTimeout("lost"))
    from tamarind.agent.transport import AgentTransport

    monkeypatch.setitem(AgentTransport.__init__.__kwdefaults__, "sleep", lambda _s: None)  # no real backoff
    code, out, err = _run(["--json", "chat", "send", "chat_7Q", "x"], monkeypatch, capsys)

    key = route.calls.last.request.headers["Idempotency-Key"]
    error = json.loads(err)["error"]
    assert code == 1
    assert error["detail"]["idempotencyKey"] == key
    assert f"--idempotency-key {key}" in error["message"]


@respx.mock
@pytest.mark.parametrize(("argv", "method", "path", "ok"), [
    (["chat", "new", "--title", "t"], "POST", "chats", (201, CHAT)),
    (["chat", "send", "chat_7Q", "hi"], "POST", "chats/chat_7Q/messages", (202, reply("queued"))),
    (["chat", "export", "chat_7Q"], "POST", "chats/chat_7Q/exports", (202, {"id": "exp_5d", "status": "pending"})),
])
def test_the_printed_idempotency_key_advice_is_runnable(argv, method, path, ok, monkeypatch, capsys):
    """Every keyed command takes --idempotency-key, so the advice after a lost answer works."""
    from tamarind.agent.transport import AgentTransport

    monkeypatch.setitem(AgentTransport.__init__.__kwdefaults__, "sleep", lambda _s: None)  # no real backoff
    route = respx.route(method=method, url=f"{API}{path}").mock(
        side_effect=[httpx.ReadTimeout("lost")] * 4 + [httpx.Response(ok[0], json=ok[1])])

    code, _, err = _run(["--json", *argv], monkeypatch, capsys)
    assert code == 1
    key = json.loads(err)["error"]["detail"]["idempotencyKey"]
    assert f"--idempotency-key {key}" in json.loads(err)["error"]["message"]

    code, _, err = _run(["--json", *argv, "--idempotency-key", key], monkeypatch, capsys)
    assert code == 0, err
    assert route.calls.last.request.headers["Idempotency-Key"] == key


@respx.mock
def test_approve_wait_exits_7_when_the_poll_hangs_past_the_deadline(monkeypatch, capsys):
    import threading
    import time as real_time

    from tamarind.agent.events import EventStream

    release = threading.Event()
    monkeypatch.setitem(EventStream.__init__.__kwdefaults__, "continuation_wait", 1.4)
    from tamarind.agent.transport import AgentTransport

    monkeypatch.setitem(AgentTransport.__init__.__kwdefaults__, "sleep", lambda _s: None)
    respx.post(f"{API}chats/chat_7Q/approvals/apr_x").mock(
        return_value=httpx.Response(200, json=approval(status="approved")))
    respx.get(f"{API}chats/chat_7Q/events").mock(return_value=_reply_stream(
        frame("5.0", "approval.resolved", approval(status="approved")),
        frame("6.0", "message.completed", reply("completed")),
    ))

    def hang(request: httpx.Request) -> httpx.Response:
        release.wait(30)
        return httpx.Response(200, json=reply("completed"))

    respx.get(f"{API}chats/chat_7Q/messages/msg_1").mock(side_effect=hang)
    try:
        started = real_time.monotonic()
        code, out, err = _run(["--json", "chat", "approve", "chat_7Q", "apr_x", "--wait"], monkeypatch, capsys)
        elapsed = real_time.monotonic() - started
    finally:
        release.set()
    assert elapsed < 3
    assert code == ExitCode.TIMEOUT
    assert json.loads(err)["error"]["type"] == "JobTimeoutError"


@respx.mock
def test_a_send_with_an_uploaded_file_can_be_retried_with_the_same_key_and_body(tmp_path, monkeypatch, capsys):
    """The key is bound to the body: rerunning with the local path would re-upload (a new
    file id) and be refused 409; the error names the ids so the retry sends the same body."""
    from tamarind.agent.transport import AgentTransport

    monkeypatch.setitem(AgentTransport.__init__.__kwdefaults__, "sleep", lambda _s: None)  # no real backoff
    target = tmp_path / "target.pdb"
    target.write_bytes(b"ATOM\n")
    file_id = "file_u0123456789abcdef0123456789abcdef"
    create = respx.post(f"{API}chat-files").mock(return_value=httpx.Response(201, json=upload_slot(file_id)))
    respx.post(UPLOAD_URL).mock(return_value=httpx.Response(204))
    send = respx.post(f"{API}chats/chat_7Q/messages").mock(
        side_effect=[httpx.ReadTimeout("lost")] * 4 + [httpx.Response(202, json=reply("queued"))])

    code, _, err = _run(["--json", "chat", "send", "chat_7Q", "look", "--file", str(target)], monkeypatch, capsys)
    error = json.loads(err)["error"]
    assert code == 1
    key = error["detail"]["idempotencyKey"]
    assert error["detail"]["uploadedFiles"] == [{"path": str(target), "fileId": file_id}]
    assert f"--idempotency-key {key}" in error["message"] and file_id in error["message"]
    first_body = send.calls.last.request.content

    code, _, err = _run(["--json", "chat", "send", "chat_7Q", "look", "--file", file_id,
                         "--idempotency-key", key], monkeypatch, capsys)
    assert code == 0, err
    assert create.call_count == 1  # not uploaded again
    assert send.calls.last.request.content == first_body  # the body the key is bound to
    assert send.calls.last.request.headers["Idempotency-Key"] == key
