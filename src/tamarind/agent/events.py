"""Server-sent events for a chat: a parser and a reconnecting iterator.

:class:`EventStream` tails ``GET /chats/{chatId}/events?stream=true`` (optionally one
reply's events, ``messageId``) and survives the connection:

- Each event's SSE ``id`` (``<sequence>.<index>``) is the resume cursor. After a dropped
  connection, a clean close of a chat-wide stream (the server closes idle ones about
  hourly), or a retryable ``error`` event (``stream_interrupted``), it reconnects with
  ``Last-Event-ID`` after a backoff, and the server sends exactly what was missed.
- A frame at or before the cursor (a duplicate replayed after a resume) is dropped, so a
  caller sees each event once.
- Unknown event types are skipped, as the contract requires, but still move the cursor.
- ``ping`` (no id) never moves the cursor and is never yielded.
- It stops after an event the caller's ``until`` matches, or, following one reply, after
  that reply's final ``message.*`` event, or when the reply stopped on an approval or a
  question (``stop_reason == "requires_action"``): nothing more comes until someone answers.

A half-written frame at a cut is discarded (the SSE rule: a frame is dispatched only at
its blank line), and the reconnect fetches it whole.
"""

from __future__ import annotations

from collections.abc import Callable, Generator, Iterable, Iterator
from dataclasses import dataclass
import json
import re
import time
from typing import TYPE_CHECKING, Any

import httpx

from tamarind.errors import (
    AgentStreamError,
    APIError,
    AuthError,
    NotFoundError,
    RateLimitError,
    TamarindError,
)

from ._contract import EVENT_TYPES, FINAL_MESSAGE_EVENTS, FINAL_MESSAGE_STATUSES, OPERATIONS
from .models import ContractError, Event, Message
from .transport import agent_error, backoff, build_path, wait_seconds

if TYPE_CHECKING:
    from .transport import AgentTransport

DEFAULT_MAX_RECONNECTS = 10
_monotonic = time.monotonic  # the continuation wait's clock (a test replaces it)
# How long to keep re-reading a reply that a decided approval ended, waiting for the reply
# that answers the decision to start. Past it, the stream stops with
# ``stop_reason == "continuation_pending"`` rather than reporting the exchange over.
DEFAULT_CONTINUATION_WAIT = 120.0
# The ``message.*`` events whose data is a Message (``message.continued`` is not, and an
# unknown ``message.*`` type is skipped, never parsed as one).
STATUS_EVENTS = frozenset({"message.created"} | {
    f"message.{s}" for s in ("in_progress", "requires_action", "completed", "failed", "cancelled", "incomplete")
})
_CURSOR = re.compile(r"^\s*(\d+)(?:\.(\d+))?\s*$")
# A bare `<seq>` cursor means every event of that row (the server's own reading).
_WHOLE_ROW = 1 << 30


@dataclass(frozen=True)
class SSEFrame:
    event: str
    data: str
    id: str | None
    retry: int | None


def parse_sse(lines: Iterable[str]) -> Iterator[SSEFrame]:
    """Frames from SSE lines (line endings already removed), per the WHATWG rules."""
    event = ""
    data: list[str] = []
    frame_id: str | None = None
    retry: int | None = None
    for line in lines:
        if line == "":
            if data or frame_id is not None:
                yield SSEFrame(event or "message", "\n".join(data), frame_id, retry)
            event, data, frame_id, retry = "", [], None, None
            continue
        if line.startswith(":"):
            continue
        name, _, value = line.partition(":")
        if value.startswith(" "):
            value = value[1:]
        if name == "event":
            event = value
        elif name == "data":
            data.append(value)
        elif name == "id":
            if "\0" not in value:
                frame_id = value
        elif name == "retry" and value.isdigit():
            retry = int(value)
    # A frame with no blank line after it was cut mid-write: dropped, as SSE requires.


def parse_cursor(value: str) -> tuple[int, int] | None:
    matched = _CURSOR.match(value or "")
    if not matched:
        return None
    return int(matched.group(1)), int(matched.group(2)) if matched.group(2) else _WHOLE_ROW


Until = Callable[[Event], bool]


def _until(value: Until | Iterable[str] | str | None) -> Until | None:
    if value is None or callable(value):
        return value
    types = frozenset([value] if isinstance(value, str) else value)
    return lambda event: event.type in types


class EventStream(Iterator[Event]):
    """Iterate a chat's (or one reply's) events, reconnecting until a stop condition.

    ``after`` resumes from a stored cursor. ``until`` is an event type, a set of them, or a
    predicate; the matching event is yielded, then the stream stops. With
    ``follow_continuations`` a followed reply that ends ``completed`` with ``continuedBy``
    hands over to that reply (an approval's answer, a steering message), so one loop reads
    the whole exchange. After ``max_reconnects`` reconnects in a row with no new event it
    gives up with :class:`~tamarind.errors.TamarindError`.

    Read ``last_event_id`` to resume later, ``stop_reason`` (``"final"``,
    ``"requires_action"``, ``"until"``, or ``"continuation_pending"``: a decided card ended
    the reply and its answer had not started within ``continuation_wait`` seconds) and ``message`` (the followed reply as of its last
    status event) when it ends.
    """

    def __init__(
        self,
        transport: "AgentTransport",
        chat_id: str,
        *,
        message_id: str | None = None,
        after: str | None = None,
        until: Until | Iterable[str] | str | None = None,
        follow_continuations: bool = False,
        include_unknown: bool = False,
        max_reconnects: int = DEFAULT_MAX_RECONNECTS,
        continuation_wait: float = DEFAULT_CONTINUATION_WAIT,
    ):
        if after is not None and parse_cursor(after) is None:
            raise ValueError("after must be an event id such as '1042.0'")
        self._transport = transport
        self._path = build_path(OPERATIONS["listChatEvents"].path, {"chatId": chat_id})
        self.chat_id = chat_id
        self.message_id = message_id
        self.last_event_id = after
        self._cursor = parse_cursor(after) if after is not None else None
        # After a continuation switch: the old stream's cursor. The new reply's events at or
        # before it were filtered out of the old stream, so they still pass; anything else
        # there (a `chat.rewound`, whose messageId is null) was already yielded.
        self._floor: tuple[int, int] | None = None
        self._until = _until(until)
        self._follow_continuations = follow_continuations
        self._include_unknown = include_unknown
        self._max_reconnects = max_reconnects
        self._continuation_wait = continuation_wait
        self._pending = False
        self._retry_base = 0.5
        self.stop_reason: str | None = None
        self.message: Message | None = None
        self._status: str | None = None
        self._continued_by: str | None = None
        self._card_decided = False
        self._iterator = self._run()

    def __iter__(self) -> "EventStream":
        return self

    def __next__(self) -> Event:
        return next(self._iterator)

    def close(self) -> None:
        self._iterator.close()

    # ── the loop ──

    def _run(self) -> Generator[Event, None, None]:
        failures = 0
        while True:
            outcome = yield from self._connect()
            if outcome == "stop":
                return
            if outcome == "switch":
                failures = 0
                continue
            if outcome == "progress":
                failures = 0
            failures += 1
            if failures > self._max_reconnects:
                raise TamarindError(
                    f"Lost the event stream for chat {self.chat_id} and could not resume after "
                    f"{self._max_reconnects} reconnects. Resume later with after={self.last_event_id!r}."
                )
            if outcome != "waited":
                self._transport.sleep(backoff(failures, base=self._retry_base))

    def _connect(self) -> Generator[Event, None, str]:
        """One connection. Returns "stop", "switch" (follow a continuation now), "progress"
        (new events, then lost or closed), "lost" (nothing new) or "waited" (refused, and
        already waited the server's ``Retry-After``)."""
        params: dict[str, Any] = {"stream": "true"}
        if self.message_id is not None:
            params["messageId"] = self.message_id
        progressed = False
        try:
            with self._transport.open_stream(
                self._path, params=params, last_event_id=self.last_event_id
            ) as resp:
                if not resp.is_success:
                    return "waited" if self._refused(resp) else "lost"
                for frame in parse_sse(resp.iter_lines()):
                    if frame.retry is not None:
                        self._retry_base = max(frame.retry / 1000.0, 0.1)
                    if frame.event == "ping":
                        continue
                    wire = _frame_json(frame)
                    if wire.get("type") == "error" or frame.event == "error":
                        self._stream_error(wire)
                        return "progress" if progressed else "lost"
                    if frame.id is not None:
                        cursor = parse_cursor(frame.id)
                        if cursor is not None:
                            if self._cursor is not None and cursor <= self._cursor:
                                continue  # replayed after a resume: already seen
                            if (self._floor is not None and cursor <= self._floor
                                    and wire.get("messageId") != self.message_id):
                                continue  # seen before a continuation switch (chat.rewound)
                            self._cursor = cursor
                        self.last_event_id = frame.id
                        progressed = True
                    event = Event.from_wire(wire)
                    self._track(event)
                    if event.type not in EVENT_TYPES and not self._include_unknown:
                        continue
                    yield event
                    if self._until is not None and self._until(event):
                        self.stop_reason = "until"
                        return "stop"
                    if self._ends_followed_reply(event):
                        assert self.message is not None
                        following = self._continuation() if self._follow_continuations else None
                        if following:
                            self._switch(following)
                            return "switch"
                        self.stop_reason = "continuation_pending" if self._pending else "final"
                        return "stop"
        except (httpx.TransportError, httpx.StreamError) as exc:
            del exc  # a cut connection: resume from the cursor
            return "progress" if progressed else "lost"
        # A clean close. A chat-wide stream closes when idle; a reply's stream closes at its
        # end, or when it stopped on a card. Ask the reply which.
        if self.message_id is not None:
            settled = self._settled()
            if settled is not None:
                return settled
        return "progress" if progressed else "lost"

    # ── pieces ──

    def _refused(self, resp: httpx.Response) -> bool:
        """A refused (re)connect: retry what is transient, raise the rest. True when it
        already waited as long as the server asked (so no backoff is added on top)."""
        status = resp.status_code
        if status == 429 or status >= 500:
            asked = wait_seconds(resp)
            if asked is None:
                return False
            if asked > self._transport.max_rate_limit_wait:
                raise agent_error(resp, request_path=self._path)
            self._transport.sleep(asked)
            return True
        raise agent_error(resp, request_path=self._path)

    def _stream_error(self, wire: dict[str, Any]) -> None:
        raw = wire.get("data")
        data: dict[str, Any] = raw if isinstance(raw, dict) else {}
        code = str(data.get("code") or "error")
        message = str(data.get("message") or "The event stream ended with an error.")
        if data.get("retryable") is True or code == "stream_interrupted":
            return  # reconnect from the cursor
        detail = {"code": code, "message": message}
        if code == "key_revoked":
            raise AuthError(message, detail=detail)
        if code == "not_found":
            raise NotFoundError(message, detail=detail)
        raise AgentStreamError(message, detail=detail)

    def _track(self, event: Event) -> None:
        """Keep the followed reply as its last ``message.*`` status event showed it."""
        if self.message_id is None or event.message_id != self.message_id:
            return
        if event.type in STATUS_EVENTS:
            self.message = event.message()
            self._status = self.message.status
            if event.type == "message.in_progress":
                # Decided while its turn still ran: the reply went on in place, so no new
                # reply will answer that decision.
                self._card_decided = False
        elif event.type == "message.continued":
            continued = event.data.get("continuedBy")
            if isinstance(continued, str) and continued:
                self._continued_by = continued
        elif event.type in ("approval.resolved", "approval.requested"):
            # A decided card ends this reply, and the answer comes as a NEW reply named by
            # this one's continuedBy once it starts (after this stream has closed).
            self._card_decided = event.type == "approval.resolved" or self._card_decided

    def _ends_followed_reply(self, event: Event) -> bool:
        return (
            self.message_id is not None
            and event.message_id == self.message_id
            and event.type in FINAL_MESSAGE_EVENTS
        )

    def _continuation(self) -> str | None:
        """The reply that carries this one's work on, if any.

        Named on the final event when a steering message was read into it. When a decided
        approval ended it, the answer reply starts after this stream closed, so the reply is
        re-read until it names one (bounded: a reply that ends with nothing to follow is
        just done)."""
        assert self.message is not None
        named = self.message.continued_by or self._continued_by
        if named or not self._card_decided or self.message.status != "completed":
            return named
        assert self.message_id is not None
        # Wall clock plus the pauses: a fake sleep (tests) adds no time, a real one adds both.
        started = _monotonic()
        paused, attempt = 0.0, 0
        while paused + (_monotonic() - started) < self._continuation_wait:
            attempt += 1
            pause = float(min(attempt, 5))
            self._transport.sleep(pause)
            paused += pause
            try:
                resp = self._transport.call(
                    "getMessage", {"chatId": self.chat_id, "messageId": self.message_id}
                )
                current = Message.from_wire(_object(resp))
            except NotFoundError:
                return None  # gone (a rewind hid it): there is nothing left to follow
            except TamarindError as exc:
                if _transient(exc):
                    continue  # not an answer either way: ask again until the wait is spent
                raise  # a revoked key, a refusal (403) or a broken contract is never "done"
            if current.continued_by:
                return current.continued_by
        self._pending = True
        return None

    def _switch(self, message_id: str) -> None:
        """Follow ``message_id`` from its own start: a filtered stream's cursor only skips
        what this one already read, and the new reply may have begun before it."""
        self.message_id = message_id
        self.last_event_id = None
        if self._cursor is not None:
            self._floor = max(self._floor or self._cursor, self._cursor)
        self._cursor = None
        self.message = None
        self._status = None
        self._continued_by = None
        self._card_decided = False

    def _settled(self) -> str | None:
        """After a clean close of a reply's stream: "stop" when that reply ended or waits on
        a card, "switch" when it ended and a continuing reply is to be followed, None when
        the connection closed early (reconnect). Always re-read, even after a
        ``requires_action`` event: the card may have been decided elsewhere since."""
        assert self.message_id is not None
        resp = self._transport.call(
            "getMessage", {"chatId": self.chat_id, "messageId": self.message_id}
        )
        current = Message.from_wire(_object(resp))
        if current.status in FINAL_MESSAGE_STATUSES:
            # Read as if its final event had arrived (a resume from a cursor past it gets
            # an empty stream), so a continuation is followed here too.
            self.message = current
            following = self._continuation() if self._follow_continuations else None
            if following:
                self._switch(following)
                return "switch"
            self.stop_reason = "continuation_pending" if self._pending else "final"
            return "stop"
        if current.status == "requires_action":
            self.message = current
            self.stop_reason = "requires_action"
            return "stop"
        return None


def _transient(exc: TamarindError) -> bool:
    """A re-read failure that says nothing about the reply: rate limited, the server briefly
    unavailable, or the connection lost (a refusal or a broken contract is not)."""
    if isinstance(exc, RateLimitError):
        return True
    if isinstance(exc, APIError):
        return exc.status_code >= 500
    return type(exc) is TamarindError  # the transport's network-error wrapper


def _frame_json(frame: SSEFrame) -> dict[str, Any]:
    try:
        wire = json.loads(frame.data) if frame.data else {}
    except ValueError as exc:
        raise ContractError(f"Agent event stream sent a frame that is not JSON ({frame.event}).") from exc
    if not isinstance(wire, dict):
        raise ContractError("Agent event stream sent a frame that is not an object.")
    return wire


def _object(resp: httpx.Response) -> dict[str, Any]:
    try:
        body = resp.json()
    except ValueError as exc:
        raise ContractError("Agent API response is not JSON.") from exc
    if not isinstance(body, dict):
        raise ContractError("Agent API response is not an object.")
    return body
