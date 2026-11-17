"""The Agent API transport: version header, retries, rate limits and idempotency keys."""

from __future__ import annotations

import json
import re
import traceback
import uuid

import httpx
import pytest
import respx

from agent_fakes import UPLOAD_FIELDS, UPLOAD_URL, FakeAgentServer, approval, form_parts, reply, upload_slot
from tamarind.errors import APIError, BudgetError, NotFoundError, RateLimitError, TamarindError, ValidationError

SEND = "/chats/chat_7Q/messages"
QUEUED = httpx.Response(202, json=reply("queued"))


def test_every_request_carries_the_version_and_the_api_key():
    server = FakeAgentServer().on("GET", "/agent-workflows", httpx.Response(200, json={"data": []}))
    server.agent().workflows.list()
    request = server.requests[0]
    assert request.headers["Tamarind-Version"] == "2026-11-01"
    assert request.headers["x-api-key"] == "key"


def test_a_send_gets_a_fresh_idempotency_key_reused_across_its_retries():
    server = FakeAgentServer().on(
        "POST", SEND,
        httpx.ReadTimeout("lost"),
        httpx.Response(503, json={"code": "unavailable", "retryable": True}),
        QUEUED,
        QUEUED,
    )
    agent = server.agent()
    agent.messages.send("chat_7Q", "hi")
    agent.messages.send("chat_7Q", "again")

    keys = [r.headers["Idempotency-Key"] for r in server.requests_to("POST", SEND)]
    assert len(keys) == 4
    assert keys[0] == keys[1] == keys[2]  # one logical call, retried twice
    assert keys[3] != keys[0]  # a new call, a new key
    uuid.UUID(keys[0])


def test_a_caller_supplied_idempotency_key_is_sent_as_is():
    server = FakeAgentServer().on("POST", SEND, QUEUED)
    server.agent().messages.send("chat_7Q", "hi", idempotency_key="mine-1")
    assert server.requests[0].headers["Idempotency-Key"] == "mine-1"


@pytest.mark.parametrize(
    ("operation_id", "path_params", "key"),
    [
        ("getChat", {"chatId": "c"}, "k"),  # an operation that takes no key
        ("answerQuestion", {"chatId": "c", "questionId": "q"}, "k"),  # ...once took one
        ("sendMessage", {"chatId": "c"}, ""),  # a blank key is refused, never replaced
        ("createChat", {}, "   "),
    ],
)
def test_an_idempotency_key_the_call_cannot_use_is_refused_before_sending(operation_id, path_params, key):
    server = FakeAgentServer()
    with pytest.raises(ValueError):
        server.agent().transport.call(operation_id, path_params, idempotency_key=key, json={})
    assert server.requests == []


@pytest.mark.parametrize(
    ("headers", "slept"),
    [
        ({"Retry-After": "3"}, [3.0]),
        ({"x-ratelimit-reset": "5"}, [5.0]),
        # Retry-After wins over the hourly counter's reset.
        ({"Retry-After": "2", "x-ratelimit-reset": "40"}, [2.0]),
    ],
)
def test_a_429_waits_what_the_server_asked_then_retries(headers, slept):
    server = FakeAgentServer().on(
        "POST", SEND, httpx.Response(429, headers=headers, json={"code": "rate_limited"}), QUEUED
    )
    message = server.agent().messages.send("chat_7Q", "hi")
    assert message.status == "queued"
    assert server.sleeps == slept


def test_a_429_longer_than_the_cap_is_raised_with_the_wait():
    server = FakeAgentServer().on(
        "POST", SEND, httpx.Response(429, headers={"x-ratelimit-reset": "1800"},
                                     json={"code": "rate_limited", "detail": "Hourly message limit."})
    )
    with pytest.raises(RateLimitError, match="retry in 1800s"):
        server.agent().messages.send("chat_7Q", "hi")
    assert server.sleeps == []


def test_a_429_is_retried_even_for_an_operation_that_is_not_retry_safe():
    # A 429 is refused before anything ran; rewind is otherwise never retried.
    server = FakeAgentServer().on(
        "POST", "/chats/chat_7Q/rewind",
        httpx.Response(429, headers={"Retry-After": "1"}, json={"code": "rate_limited"}),
        httpx.Response(200, json={"id": "chat_7Q", "object": "chat", "title": "t", "status": "idle",
                                  "source": "api", "createdAt": "x", "updatedAt": "y"}),
    )
    assert server.agent().chats.rewind("chat_7Q", "msg_0").id == "chat_7Q"


@pytest.mark.parametrize(
    "failure",
    [httpx.ReadTimeout("lost"), httpx.Response(503, json={"code": "unavailable", "retryable": True})],
)
def test_an_operation_that_is_not_retry_safe_is_not_retried(failure):
    server = FakeAgentServer().on("POST", "/chats/chat_7Q/rewind", failure)
    with pytest.raises(TamarindError):
        server.agent().chats.rewind("chat_7Q", "msg_0")
    assert len(server.requests_to("POST", "/chats/chat_7Q/rewind")) == 1


@pytest.mark.parametrize(
    ("failure", "message"),
    [
        (httpx.ReadTimeout("lost"), "may have been applied"),
        (httpx.Response(503, json={"code": "unavailable", "retryable": True, "detail": "Try later."}), "Try later"),
    ],
)
def test_a_delete_whose_answer_was_lost_is_reported_not_retried(failure, message):
    # The chat is gone once the first DELETE lands and every later request for it is 404, so a
    # retry would report a delete that happened as "not found".
    server = FakeAgentServer().on("DELETE", "/chats/chat_7Q", failure,
                                  httpx.Response(200, json={"id": "chat_7Q", "object": "chat", "deleted": True}))
    with pytest.raises(TamarindError, match=message):
        server.agent().chats.delete("chat_7Q")
    assert len(server.requests_to("DELETE", "/chats/chat_7Q")) == 1


def test_a_delete_answers_the_chat_id_and_that_it_is_deleted():
    server = FakeAgentServer().on("DELETE", "/chats/chat_7Q",
                                  httpx.Response(200, json={"id": "chat_7Q", "object": "chat", "deleted": True}))
    done = server.agent().chats.delete("chat_7Q")
    assert (done.id, done.deleted) == ("chat_7Q", True)


def test_retries_stop_at_max_retries():
    server = FakeAgentServer().on("GET", "/chats/chat_7Q", httpx.Response(500, json={"code": "internal_error"}))
    with pytest.raises(TamarindError):
        server.agent(max_retries=2).chats.get("chat_7Q")
    assert len(server.requests_to("GET", "/chats/chat_7Q")) == 3


@pytest.mark.parametrize(
    ("status", "code", "error_type"),
    [
        (402, "budget_exhausted", BudgetError),
        (404, "not_found", NotFoundError),
        (422, "unknown_workflow", ValidationError),
        (409, "approval_not_pending", TamarindError),
    ],
)
def test_a_refusal_is_typed_and_keeps_its_problem_code(status, code, error_type):
    server = FakeAgentServer().on(
        "POST", "/chats/chat_7Q/approvals/apr_x",
        httpx.Response(status, json={"type": "about:blank", "title": "t", "status": status,
                                     "code": code, "detail": "Refused."}),
    )
    with pytest.raises(error_type) as raised:
        server.agent().approvals.approve("chat_7Q", "apr_x")
    assert raised.value.code == code
    assert len(server.requests) == 1  # a 4xx is never retried


def test_path_ids_are_percent_encoded_whole():
    server = FakeAgentServer().on("POST", "/chats/a%2Fb/approvals/x%20y",
                                  httpx.Response(200, json=approval("x y", "approved")))
    server.agent().approvals.approve("a/b", "x y")
    assert server.requests[0].url.raw_path == b"/api/chats/a%2Fb/approvals/x%20y"


@pytest.mark.parametrize(("call", "body"), [
    (lambda a: a.approvals.approve("chat_7Q", "apr_x", scope="chat"), {"decision": "approve", "scope": "chat"}),
    (lambda a: a.approvals.approve("chat_7Q", "apr_x"), {"decision": "approve"}),
    (lambda a: a.approvals.deny("chat_7Q", "apr_x"), {"decision": "deny"}),
])
def test_an_approval_decision_is_a_decision_and_at_most_a_scope(call, body):
    """`budgetHours` and `workflow` are gone from the decision: the server refuses them (400)."""
    server = FakeAgentServer().on("POST", "/chats/chat_7Q/approvals/apr_x",
                                  httpx.Response(200, json=approval(status="approved")))
    call(server.agent())
    assert json.loads(server.requests[0].content) == body


@pytest.mark.parametrize(("call", "option"), [
    (lambda a: a.approvals.approve("chat_7Q", "apr_x", budget_hours=10), "budget_hours"),
    (lambda a: a.approvals.approve("chat_7Q", "apr_x", workflow="binder-design"), "workflow"),
    (lambda a: a.chats.list(campaign_status="running"), "campaign_status"),
    (lambda a: a.campaigns.jobs("chat_7Q", campaign_id="cmp_7Q"), "campaign_id"),
    (lambda a: a.questions.answer("chat_7Q", "q_8c", text="A", idempotency_key="k"), "idempotency_key"),
    (lambda a: a.files.create_upload("target.pdb", size=8), "size"),
    (lambda a: a.files.create_upload("target.pdb", content_type="chemical/x-pdb"), "content_type"),
    (lambda a: a.files.upload("target.pdb", content_type="chemical/x-pdb"), "content_type"),
])
def test_an_option_the_spec_removed_is_refused_before_anything_is_sent(call, option):
    server = FakeAgentServer()
    with pytest.raises(TypeError, match=option):
        call(server.agent())
    assert server.requests == []


def test_listing_chats_sends_only_the_filters_the_spec_lists():
    """The server answers 400 to `campaignStatus`: it is a filter of the removed campaigns."""
    server = FakeAgentServer().on("GET", "/chats", httpx.Response(200, json={"data": [], "nextCursor": None}))
    server.agent().chats.list(limit=5, cursor="c", scope="own", source="api", status="idle", mode="campaign")
    assert dict(server.requests[0].url.params) == {
        "limit": "5", "cursor": "c", "scope": "own", "source": "api", "status": "idle", "mode": "campaign"}


def test_answering_a_question_sends_no_idempotency_key():
    """A repeated answer returns the answered question, so the operation takes no key."""
    server = FakeAgentServer().on("POST", "/chats/chat_7Q/questions/q_8c", httpx.ReadTimeout("lost"),
                                  httpx.Response(200, json={"id": "q_8c", "status": "answered",
                                                            "questions": [], "createdAt": "x"}))
    assert server.agent().questions.answer("chat_7Q", "q_8c", text="A").status == "answered"
    sent = server.requests_to("POST", "/chats/chat_7Q/questions/q_8c")
    assert len(sent) == 2  # a lost answer is retried: repeating it is safe
    assert all("Idempotency-Key" not in request.headers for request in sent)


@pytest.mark.parametrize(
    ("method", "path", "call", "status"),
    [
        ("GET", "/chats/chat_7Q", lambda a: a.chats.get("chat_7Q"), 301),
        # A download answers 302 only: a 307 (a proxy's login page) is not the file.
        ("GET", "/chats/chat_7Q/files/file_k2/content", lambda a: a.files.download_url("chat_7Q", "file_k2"), 307),
        # The structure route serves its file itself: a 302 from it is not a download link.
        ("GET", "/chats/chat_7Q/candidates/cand_07/structure",
         lambda a: a.campaigns.download_structure("chat_7Q", "cand_07", "/nonexistent/out.pdb"), 302),
    ],
)
def test_a_redirect_is_returned_only_as_a_downloads_302_and_never_followed(method, path, call, status):
    # A proxy's page may echo the URL it was sent: never in the error.
    page = "<html>moved to https://s3.test/f?X-Amz-Signature=secret</html>"
    server = FakeAgentServer().on(method, path, httpx.Response(
        status, headers={"Location": "https://elsewhere.test/", "Content-Type": "text/html"}, text=page))
    with pytest.raises(APIError) as raised:
        call(server.agent())
    assert raised.value.status_code == status  # the redirect itself, not a parse failure after it
    assert "secret" not in str(raised.value)
    assert len(server.requests) == 1


@pytest.mark.parametrize(
    ("options", "attempts"),
    [
        ({}, 2),  # the same bare decision again returns the resolved approval: retried
        ({"scope": "chat"}, 1),  # with options a repeat is 409 after a lost success: not retried
        ({"scope": "once"}, 1),
    ],
)
def test_a_lost_approval_answer_is_retried_only_for_a_bare_decision(options, attempts):
    server = FakeAgentServer().on("POST", "/chats/chat_7Q/approvals/apr_x", httpx.ReadTimeout("lost"),
                                  httpx.Response(200, json=approval(status="approved")))
    agent = server.agent()
    if attempts == 1:
        with pytest.raises(TamarindError, match="may have been applied"):
            agent.approvals.approve("chat_7Q", "apr_x", **options)
    else:
        assert agent.approvals.approve("chat_7Q", "apr_x").status == "approved"
    assert len(server.requests) == attempts


@pytest.mark.parametrize(
    ("headers", "slept_fixed"),
    [
        # The hourly counter's reset rides on every counted send; on a 500 it is not a wait.
        ({"x-ratelimit-reset": "3500"}, None),
        ({"Retry-After": "2", "x-ratelimit-reset": "3500"}, 2.0),
    ],
)
def test_a_retryable_5xx_is_retried_on_retry_after_or_backoff_never_the_hourly_reset(headers, slept_fixed):
    server = FakeAgentServer().on(
        "POST", SEND,
        httpx.Response(500, headers=headers, json={"code": "internal_error", "retryable": True}),
        QUEUED,
    )
    server.agent().messages.send("chat_7Q", "hi")
    keys = [r.headers["Idempotency-Key"] for r in server.requests_to("POST", SEND)]
    assert len(keys) == 2 and keys[0] == keys[1]
    assert len(server.sleeps) == 1
    if slept_fixed is None:
        assert server.sleeps[0] <= 30  # a backoff, not 3500 s
    else:
        assert server.sleeps == [slept_fixed]


@pytest.mark.parametrize("parts", [
    [{"type": "file", "fileId": "file_9f2"}],  # no text part
    [{"type": "text", "text": "  "}, {"type": "file", "fileId": "file_9f2"}],  # blank text
])
def test_raw_input_parts_need_a_non_blank_text_part(parts):
    server = FakeAgentServer().on("POST", SEND, QUEUED)
    with pytest.raises(ValueError):
        server.agent().messages.send("chat_7Q", input=parts)
    assert server.requests == []


@pytest.mark.parametrize("kwargs", [{}, {"answers": {"Which chain?": "A"}, "text": "A"}])
def test_an_answer_is_answers_or_text_exactly_one(kwargs):
    server = FakeAgentServer()
    with pytest.raises(ValueError):
        server.agent().questions.answer("chat_7Q", "q_8c", **kwargs)
    assert server.requests == []


@pytest.mark.parametrize("failure", [
    httpx.ReadTimeout("lost"),
    httpx.Response(503, json={"code": "unavailable", "retryable": True}),
])
def test_a_keyed_call_that_ends_unanswered_names_its_key_for_a_safe_retry(failure):
    server = FakeAgentServer().on("POST", SEND, failure)
    with pytest.raises(TamarindError) as raised:
        server.agent(max_retries=1).messages.send("chat_7Q", "hi")
    keys = {r.headers["Idempotency-Key"] for r in server.requests_to("POST", SEND)}
    assert len(keys) == 1
    (key,) = keys
    assert raised.value.detail["idempotencyKey"] == key
    assert f"--idempotency-key {key}" in raised.value.message


@pytest.mark.parametrize("url", [
    "https://a\x00b/x",  # httpx.InvalidURL
    "http://" + "a" * 300 + ".com/x",  # a host label too long for idna: a bare UnicodeError
])
def test_a_malformed_download_url_is_a_typed_error(url, tmp_path):
    from tamarind.agent.resources import save_url

    with pytest.raises(TamarindError):
        save_url(url, tmp_path / "x")


# ── uploads: a slot from the API, then the file to the form it names ──

def _uploading(tmp_path, content=b"ATOM  1\n", name="target.pdb"):
    target = tmp_path / name
    target.write_bytes(content)
    server = FakeAgentServer().on("POST", "/chat-files", httpx.Response(201, json=upload_slot()))
    return server, target


@respx.mock
def test_an_upload_asks_for_a_slot_by_filename_alone_and_sends_the_form_to_storage(tmp_path):
    server, target = _uploading(tmp_path)
    post = respx.post(UPLOAD_URL).mock(return_value=httpx.Response(204))

    slot = server.agent().files.upload(target)

    assert slot.file_id == "file_9f2"
    assert json.loads(server.requests_to("POST", "/chat-files")[0].content) == {"filename": "target.pdb"}
    request = post.calls.last.request
    assert request.method == "POST"
    # The fields exactly as given and in that order, then the file, last, named `file`.
    assert form_parts(request) == [(k, None, v.encode()) for k, v in UPLOAD_FIELDS.items()] + [
        ("file", "target.pdb", b"ATOM  1\n")]
    # Storage gets the form and nothing of ours: no key, no API headers.
    for name in ("x-api-key", "authorization", "tamarind-version", "idempotency-key"):
        assert name not in request.headers


@respx.mock
def test_the_name_an_upload_is_given_is_the_filename_asked_for_and_the_slots_own_type_is_kept(tmp_path):
    server, target = _uploading(tmp_path, name="local.bin")
    post = respx.post(UPLOAD_URL).mock(return_value=httpx.Response(204))

    server.agent().files.upload(target, filename="inputs/target.pdb")

    assert json.loads(server.requests_to("POST", "/chat-files")[0].content) == {"filename": "inputs/target.pdb"}
    body = post.calls.last.request.content
    assert form_parts(post.calls.last.request)[-1][:2] == ("file", "inputs/target.pdb")
    # The form's `Content-Type` field is the type; the file's own part says the same, not a
    # guess from this machine's tables (`.bin` would be octet-stream, `.pdb` a Palm database).
    assert b"Content-Type: chemical/x-pdb" in body[body.index(b'name="file"'):].split(b"\r\n\r\n")[0]


@respx.mock
@pytest.mark.parametrize(("answer", "message"), [
    (httpx.Response(400, text="<Error><Code>EntityTooLarge</Code><Message>x-amz-signature=topsecretsig</Message></Error>"),
     "failed with HTTP 400 (EntityTooLarge)."),
    (httpx.Response(403, text="<Error><Code>AccessDenied</Code></Error>"), "failed with HTTP 403 (AccessDenied)."),
    (httpx.Response(500, text="not xml: POLICYB64"), "failed with HTTP 500."),
    (httpx.ReadTimeout("slow"), "timed out"),
    (httpx.ConnectError("no route"), "transfer failed"),
])
def test_a_refused_or_failed_form_is_a_typed_error_that_quotes_no_secret(tmp_path, answer, message):
    server, target = _uploading(tmp_path)
    route = respx.post(UPLOAD_URL)
    if isinstance(answer, Exception):
        route.mock(side_effect=answer)
    else:
        route.mock(return_value=answer)

    with pytest.raises(TamarindError, match=re.escape(message)) as raised:
        server.agent().files.upload(target)

    # Neither the message nor anything a traceback prints carries the URL or the form's values.
    rendered = "".join(traceback.format_exception(raised.value))
    for secret in ("topsecretsig", "POLICYB64", "AKIAEXAMPLE", "s3.test"):
        assert secret not in rendered


@pytest.mark.parametrize("size", [0, 209_715_201])
def test_a_file_storage_would_refuse_is_refused_before_a_slot_is_asked_for(tmp_path, size, monkeypatch):
    server, target = _uploading(tmp_path, content=b"")
    if size:
        monkeypatch.setattr("tamarind.agent.resources.MAX_UPLOAD_BYTES", 4)
        target.write_bytes(b"12345")
    with pytest.raises(ValueError, match="1 byte to 200 MB"):
        server.agent().files.upload(target)
    assert server.requests == []
