"""The Agent API transport: version header, retries, rate limits and idempotency keys."""

from __future__ import annotations

import uuid

import httpx
import pytest

from agent_fakes import FakeAgentServer, approval, reply
from tamarind.errors import BudgetError, NotFoundError, RateLimitError, TamarindError, ValidationError

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


def test_an_operation_without_a_key_refuses_one():
    server = FakeAgentServer()
    with pytest.raises(ValueError):
        server.agent().transport.call("getChat", {"chatId": "c"}, idempotency_key="k")


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
