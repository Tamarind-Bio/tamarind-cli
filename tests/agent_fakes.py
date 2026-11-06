"""A scripted fake Agent API for the SDK and CLI tests (no network).

``FakeAgentServer`` answers each request from a queue per route, records every request,
and serves SSE bodies that can be cut mid-frame, so the reconnect path runs against real
``httpx`` streaming.
"""

from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Callable, Iterator
import json
from typing import Any

import httpx

from tamarind.agent.resources import Agent
from tamarind.agent.transport import AgentTransport
from tamarind.http import HTTPClient

BASE = "https://api.test/api"


def frame(event_id: str | None, event_type: str, data: dict[str, Any], *, chat: str = "chat_7Q",
          message: str | None = "msg_1", sequence: int | None = None) -> str:
    """One SSE frame carrying a public Event envelope."""
    seq = sequence if sequence is not None else int((event_id or "0").split(".")[0])
    envelope = {"id": event_id or "0.0", "type": event_type, "sequence": seq, "chatId": chat,
                "messageId": message, "campaignId": None, "createdAt": "2026-10-27T17:02:11Z",
                "data": data}
    head = f"id: {event_id}\n" if event_id is not None else ""
    return f"{head}event: {event_type}\ndata: {json.dumps(envelope)}\n\n"


PING = "event: ping\ndata: {}\n\n"


def reply(status: str, *, message_id: str = "msg_1", continued_by: str | None = None,
          text: str = "", approvals: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    body: dict[str, Any] = {
        "id": message_id, "object": "message", "chatId": "chat_7Q", "role": "assistant",
        "createdAt": "2026-10-27T17:02:11Z",
        "content": [{"type": "text", "id": "p_0", "text": text}] if text else [],
        "status": status, "startedBy": "user", "inReplyTo": "msg_0",
        "pendingApprovals": approvals or [], "pendingQuestions": [],
        "completedAt": None, "continuedBy": continued_by,
    }
    return body


def approval(approval_id: str = "apr_x", status: str = "pending") -> dict[str, Any]:
    return {"id": approval_id, "messageId": "msg_1", "status": status, "kind": "platform",
            "summary": "Submit 24 Boltz-2 jobs (~3.1 h)", "detail": {"operation": "submit"},
            "createdAt": "2026-10-27T17:05:40Z", "expiresAt": None, "resolvedAt": None}


class CutStream(httpx.SyncByteStream):
    """Yields ``body`` and then, when ``cut``, fails like a dropped connection."""

    def __init__(self, body: str, *, cut: bool):
        self._body = body.encode()
        self._cut = cut

    def __iter__(self) -> Iterator[bytes]:
        # Two chunks, so a frame can straddle the cut point.
        middle = len(self._body) // 2
        yield self._body[:middle]
        yield self._body[middle:]
        if self._cut:
            raise httpx.RemoteProtocolError("peer closed connection without sending complete message body")


def sse(body: str, *, cut: bool = False, status: int = 200) -> httpx.Response:
    return httpx.Response(status, headers={"Content-Type": "text/event-stream"},
                          stream=CutStream(body, cut=cut))


Responder = httpx.Response | Callable[[httpx.Request], httpx.Response] | Exception


def _raw_path(request: httpx.Request) -> str:
    """The path as sent (still percent-encoded), so an encoded id is matched exactly."""
    return request.url.raw_path.decode().split("?", 1)[0]


class FakeAgentServer:
    def __init__(self) -> None:
        self.routes: dict[tuple[str, str], deque[Responder]] = defaultdict(deque)
        self.requests: list[httpx.Request] = []
        self.sleeps: list[float] = []

    def on(self, method: str, path: str, *responses: Responder) -> "FakeAgentServer":
        self.routes[(method, "/api" + path)].extend(responses)
        return self

    def handle(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        queue = self.routes.get((request.method, _raw_path(request)))
        if not queue:
            return httpx.Response(599, json={"error": f"unscripted {request.method} {request.url.path}"})
        responder = queue.popleft() if len(queue) > 1 else queue[0]
        if isinstance(responder, Exception):
            raise responder
        if callable(responder) and not isinstance(responder, httpx.Response):
            return responder(request)
        return responder

    def requests_to(self, method: str, path: str) -> list[httpx.Request]:
        return [r for r in self.requests if r.method == method and _raw_path(r) == "/api" + path]

    def http(self) -> HTTPClient:
        client = HTTPClient(BASE, "key")
        client._client = httpx.Client(base_url=BASE, headers=client._headers,
                                      transport=httpx.MockTransport(self.handle))
        return client

    def agent(self, **transport_options: Any) -> Agent:
        transport_options.setdefault("sleep", self.sleeps.append)
        return Agent(AgentTransport(self.http(), **transport_options))
