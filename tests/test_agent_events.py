"""The reconnecting event stream, against a fake server that cuts and replays."""

from __future__ import annotations

import httpx
import pytest

from agent_fakes import PING, FakeAgentServer, approval, frame, reply, sse
from tamarind.agent.events import SSEFrame, parse_cursor, parse_sse
from tamarind.errors import AgentStreamError, AuthError, NotFoundError, RateLimitError, TamarindError

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


def test_a_reply_that_stops_on_a_card_ends_the_follow_without_reconnecting():
    server = FakeAgentServer()
    server.on("GET", EVENTS, sse(_status("4.0", "requires_action")))

    stream = server.agent().messages.follow("chat_7Q", "msg_1")
    assert [e.type for e in stream] == ["message.requires_action"]
    assert stream.stop_reason == "requires_action"
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


def test_a_failed_reread_for_a_continuation_still_ends_the_follow_cleanly():
    server = FakeAgentServer()
    server.on("GET", EVENTS, sse(frame("5.0", "approval.resolved", approval(status="approved"))
                                 + _status("6.0", "completed")))
    server.on("GET", "/chats/chat_7Q/messages/msg_1", httpx.Response(404, json={"code": "not_found"}))

    stream = server.agent().messages.follow("chat_7Q", "msg_1", follow_continuations=True)
    assert [e.id for e in stream] == ["5.0", "6.0"]
    assert stream.stop_reason == "final"
