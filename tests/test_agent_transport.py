"""The Agent API transport: version header, retries, rate limits and idempotency keys."""

from __future__ import annotations

import uuid

import httpx
import pytest

from agent_fakes import FakeAgentServer, approval, reply
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


def test_resolve_sends_only_the_options_given():
    server = FakeAgentServer().on("POST", "/chats/chat_7Q/approvals/apr_x",
                                  httpx.Response(200, json=approval(status="approved")))
    server.agent().approvals.approve("chat_7Q", "apr_x", scope="chat")
    import json

    assert json.loads(server.requests[0].content) == {"decision": "approve", "scope": "chat"}


@pytest.mark.parametrize(
    ("method", "path", "call", "status"),
    [
        ("GET", "/chats/chat_7Q", lambda a: a.chats.get("chat_7Q"), 301),
        # A download answers 302 only: a 307 (a proxy's login page) is not the file.
        ("GET", "/chats/chat_7Q/files/file_k2/content", lambda a: a.files.download_url("chat_7Q", "file_k2"), 307),
    ],
)
def test_a_redirect_is_returned_only_as_a_downloads_302_and_never_followed(method, path, call, status):
    server = FakeAgentServer().on(method, path, httpx.Response(status, headers={"Location": "https://elsewhere.test/"}))
    with pytest.raises(APIError) as raised:
        call(server.agent())
    assert raised.value.status_code == status  # the redirect itself, not a parse failure after it
    assert len(server.requests) == 1


@pytest.mark.parametrize(
    ("options", "attempts"),
    [
        ({}, 2),  # the same bare decision again returns the resolved approval: retried
        ({"scope": "chat"}, 1),  # with options a repeat is 409 after a lost success: not retried
        ({"scope": "once"}, 1),
        ({"budget_hours": 10}, 1),
        ({"workflow": "binder-design"}, 1),
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
