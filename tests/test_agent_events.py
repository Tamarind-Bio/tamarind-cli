"""The reconnecting event stream, against a fake server that cuts and replays."""

from __future__ import annotations

import httpx
import pytest

from agent_fakes import PING, FakeAgentServer, approval, frame, reply, sse
from tamarind.agent.events import SSEFrame, parse_cursor, parse_sse
from tamarind.errors import AgentStreamError, APIError, AuthError, JobTimeoutError, NotFoundError, RateLimitError, TamarindError

EVENTS = "/chats/chat_7Q/events"


def _delta(event_id: str, text: str) -> str:
    return frame(event_id, "output_text.delta", {"partId": "p_0", "delta": text})


def _status(event_id: str, status: str, **kw) -> str:
    return frame(event_id, f"message.{status}", reply(status, **kw))


def _types_and_ids(events) -> list[tuple[str, str]]:
    return [(e.type, e.id) for e in events]


# ── the parser ──

@pytest.mark.parametrize(
    ("lines", "expected"),
    [
        (["id: 1.0", "event: x", "data: {}", ""], [SSEFrame("x", "{}", "1.0", None)]),
        # Multi-line data is joined with newlines; one leading space is stripped.
        (["data: a", "data:  b", ""], [SSEFrame("message", "a\n b", None, None)]),
        # Comments are skipped; `retry` is read.
        ([": keepalive", "retry: 2000", "event: ping", "data: {}", ""], [SSEFrame("ping", "{}", None, 2000)]),
        # A frame with no blank line after it was cut mid-write: never dispatched.
        (["id: 1.0", "event: x", "data: {\"half\":"], []),
        # An id with a NUL is ignored, as SSE requires.
        (["id: 1\0.0", "data: {}", ""], [SSEFrame("message", "{}", None, None)]),
    ],
)
def test_the_sse_parser_follows_the_whatwg_rules(lines, expected):
    assert list(parse_sse(lines)) == expected


@pytest.mark.parametrize(
    ("raw", "cursor"),
    [("1042.3", (1042, 3)), ("1042", (1042, 1 << 30)), (" 7.0 ", (7, 0)), ("abc", None), ("1.2.3", None)],
)
def test_a_cursor_orders_by_sequence_then_index(raw, cursor):
    assert parse_cursor(raw) == cursor


# ── reconnecting ──

def test_a_cut_stream_resumes_from_the_last_whole_frame_and_drops_the_replayed_duplicate():
    server = FakeAgentServer()
    first = _status("1040.0", "created") + _delta("1042.0", "Hello, ") + _delta("1043.0", "wor")[:-20]
    # The server resends 1042.0 on the resumed connection (a duplicate), then goes on.
    second = (_delta("1042.0", "Hello, ") + PING + _delta("1043.0", "world.")
              + _status("1080.0", "completed", text="Hello, world."))
    server.on("GET", EVENTS, sse(first, cut=True), sse(second))

    stream = server.agent().messages.follow("chat_7Q", "msg_1")
    events = list(stream)

    assert _types_and_ids(events) == [
        ("message.created", "1040.0"),
        ("output_text.delta", "1042.0"),
        ("output_text.delta", "1043.0"),
        ("message.completed", "1080.0"),
    ]
    connects = server.requests_to("GET", EVENTS)
    assert len(connects) == 2
    assert "Last-Event-ID" not in connects[0].headers
    # The half-written 1043.0 was dropped at the cut, so the resume asks from 1042.0.
    assert connects[1].headers["Last-Event-ID"] == "1042.0"
    assert connects[1].url.params["messageId"] == "msg_1"
    assert connects[1].url.params["stream"] == "true"
    assert stream.stop_reason == "final"
    assert stream.message is not None and stream.message.text == "Hello, world."
    assert len(server.sleeps) == 1  # one backoff before the reconnect


def test_a_retryable_stream_error_reconnects_and_is_not_yielded():
    server = FakeAgentServer()
    interrupted = frame(None, "error", {"code": "stream_interrupted", "message": "Reconnect.",
                                        "retryable": True})
    server.on("GET", EVENTS,
              sse(_delta("5.0", "a") + interrupted),
              sse(_delta("6.0", "b") + _status("7.0", "completed")))

    events = list(server.agent().messages.follow("chat_7Q", "msg_1"))

    assert [e.id for e in events] == ["5.0", "6.0", "7.0"]
    assert server.requests_to("GET", EVENTS)[1].headers["Last-Event-ID"] == "5.0"


@pytest.mark.parametrize(
    ("code", "error_type"),
    [("key_revoked", AuthError), ("not_found", NotFoundError), ("something_new", AgentStreamError)],
)
def test_a_final_stream_error_raises_its_typed_error(code, error_type):
    server = FakeAgentServer()
    server.on("GET", EVENTS, sse(frame(None, "error", {"code": code, "message": "no", "retryable": False})))

    with pytest.raises(error_type) as raised:
        list(server.agent().events.stream("chat_7Q"))
    assert raised.value.code == code


def test_unknown_event_types_are_skipped_but_still_move_the_cursor():
    server = FakeAgentServer()
    server.on("GET", EVENTS,
              # A new `message.*` type whose data is not a Message is skipped, not parsed.
              sse(_delta("1.0", "a") + frame("1.5", "message.progress", {"percent": 40})
                  + frame("2.0", "brand.new_thing", {"x": 1}), cut=True),
              sse(_status("3.0", "completed")))

    events = list(server.agent().messages.follow("chat_7Q", "msg_1"))

    assert [e.type for e in events] == ["output_text.delta", "message.completed"]
    assert server.requests_to("GET", EVENTS)[1].headers["Last-Event-ID"] == "2.0"


def test_include_unknown_yields_unknown_types():
    server = FakeAgentServer()
    server.on("GET", EVENTS, sse(frame("2.0", "brand.new_thing", {}) + _status("3.0", "completed")))

    events = list(server.agent().events.stream("chat_7Q", message_id="msg_1", include_unknown=True))

    assert [e.type for e in events] == ["brand.new_thing", "message.completed"]


def test_until_stops_after_the_matching_event_and_leaves_a_resumable_cursor():
    server = FakeAgentServer()
    server.on("GET", EVENTS, sse(frame("1.0", "job.submitted", {"jobName": "j", "status": "In Queue"}, message=None)
                                 + frame("2.0", "candidates.updated", {"count": 3}, message=None)
                                 + frame("3.0", "plan.updated", {"plan": {}}, message=None)))

    stream = server.agent().events.stream("chat_7Q", until="candidates.updated")
    events = list(stream)

    assert [e.id for e in events] == ["1.0", "2.0"]
    assert stream.stop_reason == "until"
    assert stream.last_event_id == "2.0"


def test_a_chat_stream_closed_while_idle_reconnects_from_its_cursor():
    server = FakeAgentServer()
    server.on("GET", EVENTS,
              sse(frame("10.0", "job.completed", {"jobName": "j", "status": "Complete"}, message=None)),
              sse(frame("11.0", "campaign.status", {"campaignId": "c", "status": "paused"}, message=None)))

    stream = server.agent().events.stream("chat_7Q", after="9.0", until="campaign.status")
    assert [e.id for e in stream] == ["10.0", "11.0"]
    connects = server.requests_to("GET", EVENTS)
    assert [c.headers["Last-Event-ID"] for c in connects] == ["9.0", "10.0"]
    assert "messageId" not in connects[0].url.params


@pytest.mark.parametrize(
    ("now", "stop_reason"),
    [
        ("requires_action", "requires_action"),
        # Decided elsewhere between the event and the close: the re-read is the truth.
        ("completed", "final"),
    ],
)
def test_a_reply_that_stops_on_a_card_ends_the_follow_on_its_reread_status(now, stop_reason):
    server = FakeAgentServer()
    server.on("GET", EVENTS, sse(_status("4.0", "requires_action")))
    server.on("GET", "/chats/chat_7Q/messages/msg_1", httpx.Response(200, json=reply(now)))

    stream = server.agent().messages.follow("chat_7Q", "msg_1")
    assert [e.type for e in stream] == ["message.requires_action"]
    assert stream.stop_reason == stop_reason
    assert len(server.requests_to("GET", EVENTS)) == 1


def test_a_reply_stream_closed_early_asks_the_reply_and_reconnects_while_it_runs():
    server = FakeAgentServer()
    server.on("GET", EVENTS, sse(_delta("1.0", "a")), sse(_status("2.0", "completed")))
    server.on("GET", "/chats/chat_7Q/messages/msg_1", httpx.Response(200, json=reply("in_progress")))

    stream = server.agent().messages.follow("chat_7Q", "msg_1")
    assert [e.id for e in stream] == ["1.0", "2.0"]
    assert len(server.requests_to("GET", "/chats/chat_7Q/messages/msg_1")) == 1
    assert stream.stop_reason == "final"


def test_a_reply_that_already_ended_before_the_cursor_stops_on_its_status():
    server = FakeAgentServer()
    server.on("GET", EVENTS, sse(""))
    server.on("GET", "/chats/chat_7Q/messages/msg_1", httpx.Response(200, json=reply("completed")))

    stream = server.agent().messages.follow("chat_7Q", "msg_1", after="99.0")
    assert list(stream) == []
    assert stream.stop_reason == "final"
    assert stream.message is not None and stream.message.status == "completed"


def test_follow_continuations_hands_over_to_the_continuing_reply_from_its_start():
    server = FakeAgentServer()
    rewound = frame("3.0", "chat.rewound", {"fromSequence": 1, "toSequence": 2}, message=None)
    # The new reply's stream replays from the start: its own early event (4.0, filtered
    # out of the first stream) must come through, the chat.rewound already seen must not.
    server.on("GET", EVENTS,
              sse(rewound + _status("5.0", "completed", continued_by="msg_2")),
              sse(rewound
                  + frame("4.0", "message.created", reply("queued", message_id="msg_2"), message="msg_2")
                  + frame("6.0", "message.in_progress", reply("in_progress", message_id="msg_2"), message="msg_2")
                  + frame("8.0", "message.completed", reply("completed", message_id="msg_2"), message="msg_2")))

    stream = server.agent().messages.follow("chat_7Q", "msg_1", follow_continuations=True)
    events = list(stream)

    assert [e.id for e in events] == ["3.0", "5.0", "4.0", "6.0", "8.0"]
    second = server.requests_to("GET", EVENTS)[1]
    assert second.url.params["messageId"] == "msg_2"
    assert "Last-Event-ID" not in second.headers
    assert stream.message_id == "msg_2"
    assert stream.message is not None and stream.message.id == "msg_2"


def test_a_rate_limited_reconnect_waits_retry_after():
    server = FakeAgentServer()
    server.on("GET", EVENTS,
              httpx.Response(429, headers={"Retry-After": "7"}, json={"code": "rate_limited", "detail": "10 streams"}),
              sse(_status("1.0", "completed")))

    assert [e.id for e in server.agent().messages.follow("chat_7Q", "msg_1")] == ["1.0"]
    assert server.sleeps == [7.0]  # the server's wait, and no backoff on top


def test_a_rate_limit_longer_than_the_cap_is_raised():
    server = FakeAgentServer()
    server.on("GET", EVENTS, httpx.Response(429, headers={"Retry-After": "3600"},
                                            json={"code": "rate_limited", "detail": "limit"}))

    with pytest.raises(RateLimitError):
        list(server.agent().messages.follow("chat_7Q", "msg_1"))


@pytest.mark.parametrize("status", [401, 403, 404])
def test_a_refused_connect_is_raised_not_retried(status):
    server = FakeAgentServer()
    server.on("GET", EVENTS, httpx.Response(status, json={"code": "x", "detail": "no"}))

    with pytest.raises(TamarindError):
        list(server.agent().events.stream("chat_7Q"))
    assert len(server.requests_to("GET", EVENTS)) == 1


def test_it_gives_up_after_max_reconnects_without_progress():
    server = FakeAgentServer()
    server.on("GET", EVENTS, httpx.ConnectError("refused"))

    from tamarind.agent.events import EventStream

    stream = EventStream(server.agent().transport, "chat_7Q", max_reconnects=3)
    with pytest.raises(TamarindError, match="could not resume after 3 reconnects"):
        list(stream)
    assert len(server.requests_to("GET", EVENTS)) == 4


def test_progress_resets_the_reconnect_budget():
    server = FakeAgentServer()
    # Each connection brings one new event and is then cut: never more than one failure
    # in a row, so a budget of 1 is enough.
    server.on("GET", EVENTS, *[sse(_delta(f"{i}.0", "x"), cut=True) for i in range(1, 5)],
              sse(_status("9.0", "completed")))

    from tamarind.agent.events import EventStream

    events = list(EventStream(server.agent().transport, "chat_7Q", message_id="msg_1", max_reconnects=1))
    assert [e.id for e in events] == ["1.0", "2.0", "3.0", "4.0", "9.0"]


def test_after_must_be_a_cursor():
    server = FakeAgentServer()
    with pytest.raises(ValueError):
        server.agent().events.stream("chat_7Q", after="not-a-cursor")


def test_a_reply_ended_by_a_decided_card_is_followed_into_the_answer_once_it_starts():
    server = FakeAgentServer()
    server.on("GET", EVENTS,
              sse(_status("4.0", "requires_action") + frame("5.0", "approval.resolved", approval(status="approved"))
                  + _status("6.0", "completed")),
              sse(frame("8.0", "message.completed", reply("completed", message_id="msg_2", text="Done."),
                        message="msg_2")))
    # The answer reply starts after the old reply's stream closed: named on a later read.
    server.on("GET", "/chats/chat_7Q/messages/msg_1",
              httpx.Response(200, json=reply("completed")),
              httpx.Response(200, json=reply("completed", continued_by="msg_2")))

    stream = server.agent().messages.follow("chat_7Q", "msg_1", follow_continuations=True)
    assert [e.id for e in stream] == ["4.0", "5.0", "6.0", "8.0"]
    assert stream.message is not None and stream.message.text == "Done."
    assert len(server.requests_to("GET", "/chats/chat_7Q/messages/msg_1")) == 2


@pytest.mark.parametrize("before", [
    "",  # nothing was decided
    # Decided while the turn still ran: it went on in place, no new reply answers it.
    frame("4.0", "approval.resolved", approval(status="approved")) + _status("5.0", "in_progress"),
])
def test_a_reply_that_just_completes_is_not_polled_for_a_continuation(before):
    server = FakeAgentServer()
    server.on("GET", EVENTS, sse(before + _status("6.0", "completed")))

    stream = server.agent().messages.follow("chat_7Q", "msg_1", follow_continuations=True)
    assert [e.id for e in stream][-1] == "6.0"
    assert stream.stop_reason == "final"
    assert server.requests_to("GET", "/chats/chat_7Q/messages/msg_1") == []
    assert server.sleeps == []


@pytest.mark.parametrize(
    ("reread", "raises"),
    [
        # Gone (a rewind hid it): nothing to follow, and the reply itself ended fine.
        (httpx.Response(404, json={"code": "not_found"}), None),
        # A revoked key is never "nothing to follow".
        (httpx.Response(401, json={"code": "invalid_api_key", "detail": "Invalid API key"}), AuthError),
        # Nor is a refusal that maps to a plain APIError.
        (httpx.Response(403, json={"code": "organization_read_disabled", "detail": "Read disabled"}), APIError),
    ],
)
def test_a_failed_reread_for_a_continuation_ends_cleanly_unless_it_is_an_auth_failure(reread, raises):
    server = FakeAgentServer()
    server.on("GET", EVENTS, sse(frame("5.0", "approval.resolved", approval(status="approved"))
                                 + _status("6.0", "completed")))
    server.on("GET", "/chats/chat_7Q/messages/msg_1", reread)

    stream = server.agent().messages.follow("chat_7Q", "msg_1", follow_continuations=True)
    if raises is not None:
        with pytest.raises(raises):
            list(stream)
        return
    assert [e.id for e in stream] == ["5.0", "6.0"]
    assert stream.stop_reason == "final"


def test_an_answer_that_has_not_started_within_the_wait_is_reported_pending_not_over():
    server = FakeAgentServer()
    server.on("GET", EVENTS, sse(frame("5.0", "approval.resolved", approval(status="approved"))
                                 + _status("6.0", "completed")))
    server.on("GET", "/chats/chat_7Q/messages/msg_1", httpx.Response(200, json=reply("completed")))

    stream = server.agent().messages.follow("chat_7Q", "msg_1", follow_continuations=True,
                                            continuation_wait=10)
    assert [e.id for e in stream] == ["5.0", "6.0"]
    assert stream.stop_reason == "continuation_pending"
    assert sum(server.sleeps) >= 10


def test_a_reply_that_ended_before_the_cursor_is_followed_into_its_continuation():
    server = FakeAgentServer()
    server.on("GET", EVENTS, sse(""),
              sse(frame("8.0", "message.completed", reply("completed", message_id="msg_2"), message="msg_2")))
    server.on("GET", "/chats/chat_7Q/messages/msg_1",
              httpx.Response(200, json=reply("completed", continued_by="msg_2")))

    stream = server.agent().messages.follow("chat_7Q", "msg_1", after="99.0", follow_continuations=True)
    assert [e.id for e in stream] == ["8.0"]
    assert stream.message_id == "msg_2"
    assert server.requests_to("GET", EVENTS)[1].url.params["messageId"] == "msg_2"


def test_wait_raises_rather_than_returning_the_old_reply_when_the_answer_is_pending():
    server = FakeAgentServer()
    server.on("GET", EVENTS, sse(frame("5.0", "approval.resolved", approval(status="approved"))
                                 + _status("6.0", "completed")))
    server.on("GET", "/chats/chat_7Q/messages/msg_1", httpx.Response(200, json=reply("completed")))
    agent = server.agent()

    from tamarind.agent.events import EventStream

    original = EventStream.__init__.__kwdefaults__["continuation_wait"]
    EventStream.__init__.__kwdefaults__["continuation_wait"] = 3.0
    try:
        with pytest.raises(JobTimeoutError) as raised:
            agent.messages.wait("chat_7Q", "msg_1")
    finally:
        EventStream.__init__.__kwdefaults__["continuation_wait"] = original
    assert raised.value.detail["stopReason"] == "continuation_pending"


def test_a_transient_reread_failure_keeps_waiting_for_the_answer():
    server = FakeAgentServer()
    server.on("GET", EVENTS,
              sse(frame("5.0", "approval.resolved", approval(status="approved")) + _status("6.0", "completed")),
              sse(frame("8.0", "message.completed", reply("completed", message_id="msg_2"), message="msg_2")))
    # Four 503s exhaust one re-read's retries; the next re-read names the answer.
    unavailable = httpx.Response(503, json={"code": "unavailable", "retryable": True})
    server.on("GET", "/chats/chat_7Q/messages/msg_1", unavailable, unavailable, unavailable, unavailable,
              httpx.Response(200, json=reply("completed", continued_by="msg_2")))

    stream = server.agent().messages.follow("chat_7Q", "msg_1", follow_continuations=True)
    assert [e.id for e in stream] == ["5.0", "6.0", "8.0"]
    assert stream.message_id == "msg_2"


def test_the_continuation_wait_counts_time_spent_in_requests(monkeypatch):
    import tamarind.agent.events as events_module

    now = [0.0]
    monkeypatch.setattr(events_module, "_monotonic", lambda: now[0])

    def slow_reread(request: httpx.Request) -> httpx.Response:
        now[0] += 6  # each re-read takes 6 s; the (fake) pauses take none
        return httpx.Response(200, json=reply("completed"))

    server = FakeAgentServer()
    server.on("GET", EVENTS, sse(frame("5.0", "approval.resolved", approval(status="approved"))
                                 + _status("6.0", "completed")))
    server.on("GET", "/chats/chat_7Q/messages/msg_1", slow_reread)

    stream = server.agent().messages.follow("chat_7Q", "msg_1", follow_continuations=True,
                                            continuation_wait=10)
    list(stream)
    assert stream.stop_reason == "continuation_pending"
    # Pauses alone (1, 2, 3 s) would allow three re-reads; with the requests' own time, two.
    assert len(server.requests_to("GET", "/chats/chat_7Q/messages/msg_1")) == 2


def test_the_continuation_wait_counts_a_real_pause_once(monkeypatch):
    import tamarind.agent.events as events_module

    now = [0.0]

    def real_sleep(seconds: float) -> None:  # a sleep that passes (fake) wall-clock time
        now[0] += seconds

    monkeypatch.setattr(events_module, "_monotonic", lambda: now[0])
    server = FakeAgentServer()
    server.on("GET", EVENTS, sse(frame("5.0", "approval.resolved", approval(status="approved"))
                                 + _status("6.0", "completed")))
    server.on("GET", "/chats/chat_7Q/messages/msg_1", httpx.Response(200, json=reply("completed")))

    stream = server.agent(sleep=real_sleep).messages.follow(
        "chat_7Q", "msg_1", follow_continuations=True, continuation_wait=30)
    list(stream)
    assert stream.stop_reason == "continuation_pending"
    assert now[0] >= 30  # the whole wait, not half of it


def test_a_card_decided_elsewhere_after_the_close_is_followed_into_its_answer():
    server = FakeAgentServer()
    server.on("GET", EVENTS, sse(_status("4.0", "requires_action", approvals=[approval()])),
              sse(frame("8.0", "message.completed", reply("completed", message_id="msg_2"), message="msg_2")))
    # Decided by another client after the close: completed, the answer not yet named.
    server.on("GET", "/chats/chat_7Q/messages/msg_1",
              httpx.Response(200, json=reply("completed")),
              httpx.Response(200, json=reply("completed", continued_by="msg_2")))

    stream = server.agent().messages.follow("chat_7Q", "msg_1", follow_continuations=True)
    assert [e.id for e in stream] == ["4.0", "8.0"]
    assert stream.message_id == "msg_2"


def test_a_question_answered_elsewhere_after_the_close_is_not_waited_on():
    """An answered question goes on in the same reply: completed is the end of it."""
    question = {"id": "q_8c", "messageId": "msg_1", "status": "pending", "createdAt": "x",
                "questions": [{"question": "Which chain?", "options": [{"label": "A"}]}]}
    waiting = reply("requires_action")
    waiting["pendingQuestions"] = [question]
    server = FakeAgentServer()
    server.on("GET", EVENTS, sse(frame("4.0", "message.requires_action", waiting)))
    server.on("GET", "/chats/chat_7Q/messages/msg_1", httpx.Response(200, json=reply("completed", text="A it is.")))

    stream = server.agent().messages.follow("chat_7Q", "msg_1", follow_continuations=True)
    assert [e.id for e in stream] == ["4.0"]
    assert stream.stop_reason == "final"
    assert server.sleeps == []


def test_a_rate_limited_reread_is_not_slept_out_past_the_wait():
    server = FakeAgentServer()
    server.on("GET", EVENTS,
              sse(frame("5.0", "approval.resolved", approval(status="approved")) + _status("6.0", "completed")),
              sse(frame("8.0", "message.completed", reply("completed", message_id="msg_2"), message="msg_2")))
    server.on("GET", "/chats/chat_7Q/messages/msg_1",
              httpx.Response(429, headers={"Retry-After": "60"}, json={"code": "rate_limited"}),
              httpx.Response(200, json=reply("completed", continued_by="msg_2")))

    stream = server.agent().messages.follow("chat_7Q", "msg_1", follow_continuations=True,
                                            continuation_wait=30)
    assert [e.id for e in stream][-1] == "8.0"
    assert 60.0 not in server.sleeps  # the poll is the retry, inside the wait


def test_the_continuation_wait_is_a_deadline_for_pauses_and_requests(monkeypatch):
    import tamarind.agent.events as events_module

    now = [0.0]
    monkeypatch.setattr(events_module, "_monotonic", lambda: now[0])

    def real_sleep(seconds: float) -> None:
        now[0] += seconds

    server = FakeAgentServer()
    server.on("GET", EVENTS, sse(frame("5.0", "approval.resolved", approval(status="approved"))
                                 + _status("6.0", "completed")))
    server.on("GET", "/chats/chat_7Q/messages/msg_1", httpx.Response(200, json=reply("completed")))

    stream = server.agent(sleep=real_sleep).messages.follow(
        "chat_7Q", "msg_1", follow_continuations=True, continuation_wait=1.5)
    list(stream)
    assert stream.stop_reason == "continuation_pending"
    assert now[0] <= 1.5  # never paused past the deadline
    timeouts = [r.extensions["timeout"]["read"] for r in server.requests_to("GET", "/chats/chat_7Q/messages/msg_1")]
    # One re-read, at 1 s, given only the 0.5 s left; none once the wait is spent.
    assert timeouts == [0.5]


@pytest.mark.parametrize("retry_block", [
    "retry: 3000\n\n",  # on its own
    "retry: 3000\n" + frame("1.0", "output_text.delta", {"partId": "p_0", "delta": "a"}),  # on a frame
])
def test_the_servers_retry_is_the_least_wait_before_reconnecting(retry_block):
    server = FakeAgentServer()
    server.on("GET", EVENTS, sse(retry_block, cut=True), sse(_status("9.0", "completed")))

    list(server.agent().messages.follow("chat_7Q", "msg_1"))
    assert server.sleeps and server.sleeps[0] >= 3.0


def test_a_refused_reconnect_still_waits_the_servers_retry():
    server = FakeAgentServer()
    server.on("GET", EVENTS, sse("retry: 3000\n\n", cut=True),
              httpx.Response(503, headers={"Retry-After": "1"}, json={"code": "unavailable"}),
              sse(_status("9.0", "completed")))

    list(server.agent().messages.follow("chat_7Q", "msg_1"))
    assert server.sleeps[:2] == [server.sleeps[0], 3.0] and server.sleeps[0] >= 3.0


@pytest.mark.parametrize(("expect", "followed"), [(True, True), (False, False)])
def test_a_card_that_outlived_a_cancelled_turn_is_followed_when_its_decision_was_ours(expect, followed):
    server = FakeAgentServer()
    server.on("GET", EVENTS,
              sse(frame("4.0", "approval.requested", approval()) + _status("5.0", "cancelled")),
              sse(frame("8.0", "message.completed", reply("completed", message_id="msg_2"), message="msg_2")))
    server.on("GET", "/chats/chat_7Q/messages/msg_1",
              httpx.Response(200, json=reply("cancelled", continued_by="msg_2")))

    stream = server.agent().messages.follow("chat_7Q", "msg_1", follow_continuations=True,
                                            decided_approval="apr_x" if expect else None)
    ids = [e.id for e in stream]
    assert (ids[-1] == "8.0") is followed
    # Without the caller's decision, a cancelled reply is just over: not re-read.
    assert bool(server.requests_to("GET", "/chats/chat_7Q/messages/msg_1")) is expect


def test_a_decision_taken_up_in_place_is_not_awaited_even_when_the_reply_then_ends_early():
    server = FakeAgentServer()
    server.on("GET", EVENTS, sse(frame("4.0", "approval.requested", approval())
                                 + frame("5.0", "approval.resolved", approval(status="approved"))
                                 + _status("6.0", "in_progress") + _status("7.0", "incomplete")))

    stream = server.agent().messages.follow("chat_7Q", "msg_1", follow_continuations=True,
                                            decided_approval="apr_x")
    assert [e.id for e in stream][-1] == "7.0"
    assert stream.stop_reason == "final"
    assert server.requests_to("GET", "/chats/chat_7Q/messages/msg_1") == []


def test_a_decision_spent_in_place_does_not_carry_to_a_later_card():
    server = FakeAgentServer()
    server.on("GET", EVENTS, sse(frame("4.0", "approval.requested", approval("apr_a"))
                                 + frame("5.0", "approval.resolved", approval("apr_a", "approved"))
                                 + _status("6.0", "in_progress")
                                 + frame("7.0", "approval.requested", approval("apr_b"))
                                 + _status("8.0", "cancelled")))

    stream = server.agent().messages.follow("chat_7Q", "msg_1", follow_continuations=True,
                                            decided_approval="apr_a")
    assert [e.id for e in stream][-1] == "8.0"
    assert stream.stop_reason == "final"
    assert server.requests_to("GET", "/chats/chat_7Q/messages/msg_1") == []


def test_the_decided_approval_is_followed_even_after_an_earlier_card_was_taken_up_in_place():
    # A decided in place earlier; B, the one just decided, outlived the cancelled turn.
    server = FakeAgentServer()
    server.on("GET", EVENTS,
              sse(frame("4.0", "approval.requested", approval("apr_a"))
                  + frame("5.0", "approval.resolved", approval("apr_a", "approved"))
                  + _status("6.0", "in_progress")
                  + frame("7.0", "approval.requested", approval("apr_b"))
                  + _status("8.0", "cancelled")),
              sse(frame("9.0", "message.completed", reply("completed", message_id="msg_2"), message="msg_2")))
    server.on("GET", "/chats/chat_7Q/messages/msg_1",
              httpx.Response(200, json=reply("cancelled", continued_by="msg_2")))

    stream = server.agent().messages.follow("chat_7Q", "msg_1", follow_continuations=True,
                                            decided_approval="apr_b")
    assert [e.id for e in stream][-1] == "9.0"
    assert stream.message_id == "msg_2"


def test_a_resumed_follow_trusts_the_decided_approval_it_cannot_see_raised():
    server = FakeAgentServer()
    server.on("GET", EVENTS, sse(_status("8.0", "cancelled")),
              sse(frame("9.0", "message.completed", reply("completed", message_id="msg_2"), message="msg_2")))
    server.on("GET", "/chats/chat_7Q/messages/msg_1",
              httpx.Response(200, json=reply("cancelled", continued_by="msg_2")))

    stream = server.agent().messages.follow("chat_7Q", "msg_1", after="7.0", follow_continuations=True,
                                            decided_approval="apr_b")
    assert [e.id for e in stream][-1] == "9.0"


def test_a_follow_resumed_past_the_decision_still_follows_its_answer():
    server = FakeAgentServer()
    server.on("GET", EVENTS, sse(_status("6.0", "completed")),
              sse(frame("9.0", "message.completed", reply("completed", message_id="msg_2"), message="msg_2")))
    server.on("GET", "/chats/chat_7Q/messages/msg_1",
              httpx.Response(200, json=reply("completed")),
              httpx.Response(200, json=reply("completed", continued_by="msg_2")))

    stream = server.agent().messages.follow("chat_7Q", "msg_1", after="5.0", follow_continuations=True,
                                            decided_approval="apr_x")
    assert [e.id for e in stream][-1] == "9.0"


def test_a_quiet_chat_streams_clean_closes_are_never_counted_as_failures():
    server = FakeAgentServer()
    # Twelve hourly idle closes, then an event: well past a budget of 3.
    server.on("GET", EVENTS, *[sse("") for _ in range(12)],
              sse(frame("10.0", "job.completed", {"jobName": "j", "status": "Complete"}, message=None)))

    from tamarind.agent.events import EventStream

    stream = EventStream(server.agent().transport, "chat_7Q", until="job.completed", max_reconnects=3)
    assert [e.id for e in stream] == ["10.0"]
    assert len(server.sleeps) == 12 and all(s >= 1.0 for s in server.sleeps)  # paced, not busy


def test_a_queued_replys_stream_closing_until_it_starts_is_never_counted_as_failures():
    server = FakeAgentServer()
    server.on("GET", EVENTS, *[sse("") for _ in range(8)], sse(_status("9.0", "completed")))
    server.on("GET", "/chats/chat_7Q/messages/msg_1", httpx.Response(200, json=reply("queued")))

    from tamarind.agent.events import EventStream

    stream = EventStream(server.agent().transport, "chat_7Q", message_id="msg_1", max_reconnects=3)
    assert [e.id for e in stream] == ["9.0"]
    assert stream.stop_reason == "final"


def test_a_follow_resumed_past_a_decision_taken_up_in_place_ends_at_once_on_completion():
    server = FakeAgentServer()
    # Resumed after the approval.resolved: the reply runs again, then completes. Nothing to await.
    server.on("GET", EVENTS, sse(_status("6.0", "in_progress") + _status("7.0", "completed")))

    stream = server.agent().messages.follow("chat_7Q", "msg_1", after="5.0", follow_continuations=True,
                                            decided_approval="apr_x")
    assert [e.id for e in stream] == ["6.0", "7.0"]
    assert stream.stop_reason == "final"
    assert server.requests_to("GET", "/chats/chat_7Q/messages/msg_1") == []
