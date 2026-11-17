"""The Agent API contract the SDK is written against, as data.

Pinned to ``openapi/agent-v1.yaml`` (vendored from tamarind-agent
``docs/public-api/openapi.yaml``; provenance in ``openapi/agent-v1.lock.json``).
``tests/test_agent_api_contract.py`` checks every row here against that file, so a
re-synced spec that adds, moves or renames an operation fails CI until this table, and
the resource method it names, follow.

The client is hand-written rather than generated: run on this spec, the pinned generator
(openapi-python-client 0.28.4) drops ``ApprovalDetail``, ``Approval``, ``Message`` and
``MessageEventData`` over an array with no ``items`` (``settingChanges.added``), so it types
neither a reply nor an approval.

The vendored spec (7972531f1) no longer documents a ``Tamarind-Version`` header; the copy
this SDK was first written against took it on every path. The SDK still sends the date it
was written against, unchanged: nothing in the current spec says whether the server reads it,
so it is a pin the contract does not describe, kept until the agent team says to drop it.
"""

from __future__ import annotations

from typing import NamedTuple

API_VERSION = "2026-11-01"
VERSION_HEADER = "Tamarind-Version"


class Operation(NamedTuple):
    method: str
    path: str
    # The spec lists ``Idempotency-Key`` for this operation: the SDK sends one per logical
    # call (the caller's, or a fresh UUID) and reuses it on every retry of that call.
    idempotency_key: bool
    # A retry after a lost response or a 5xx/429 cannot apply the request twice: reads,
    # set-to-value writes, calls the spec documents as idempotent, and keyed POSTs.
    retry_safe: bool
    # The resource method that implements it (``<namespace>.<method>`` on ``Agent``).
    sdk: str


OPERATIONS: dict[str, Operation] = {
    "createChat": Operation("POST", "/chats", True, True, "chats.create"),
    "listChats": Operation("GET", "/chats", False, True, "chats.list"),
    "getChat": Operation("GET", "/chats/{chatId}", False, True, "chats.get"),
    "updateChat": Operation("PATCH", "/chats/{chatId}", False, True, "chats.update"),
    # Not retried after a lost response: the chat is gone once the first DELETE lands, and
    # the spec answers every later request for it 404, so a retry would report a delete that
    # happened as "not found".
    "deleteChat": Operation("DELETE", "/chats/{chatId}", False, False, "chats.delete"),
    "sendMessage": Operation("POST", "/chats/{chatId}/messages", True, True, "messages.send"),
    "listMessages": Operation("GET", "/chats/{chatId}/messages", False, True, "messages.list"),
    "getMessage": Operation("GET", "/chats/{chatId}/messages/{messageId}", False, True, "messages.get"),
    # Documented idempotent ("cancelling a reply that has already finished returns it").
    "cancelMessage": Operation(
        "POST", "/chats/{chatId}/messages/{messageId}/cancel", False, True, "messages.cancel"
    ),
    # A second rewind to the same message is a different request (that message is now
    # hidden), so a lost response is reported, not retried.
    "rewindChat": Operation("POST", "/chats/{chatId}/rewind", False, False, "chats.rewind"),
    "listChatEvents": Operation("GET", "/chats/{chatId}/events", False, True, "events.list"),
    "listApprovals": Operation("GET", "/chats/{chatId}/approvals", False, True, "approvals.list"),
    # Not keyed, and safe to repeat: "Repeating the same answer after a lost response returns
    # the answered question and sends nothing twice."
    "answerQuestion": Operation(
        "POST", "/chats/{chatId}/questions/{questionId}", False, True, "questions.answer"
    ),
    # "Retrying needs no Idempotency-Key, since the approval is the key": the same bare
    # decision again returns the resolved approval and runs nothing twice.
    "resolveApproval": Operation(
        "POST", "/chats/{chatId}/approvals/{approvalId}", False, True, "approvals.resolve"
    ),
    # Not keyed: a retry would mint a second (harmless, never-filled) upload slot, so a lost
    # response is reported instead. The bytes then go to the slot by a presigned form POST.
    "createChatFile": Operation("POST", "/chat-files", False, False, "files.create_upload"),
    "getChatFile": Operation("GET", "/chat-files/{fileId}", False, True, "files.get"),
    "listChatFiles": Operation("GET", "/chats/{chatId}/files", False, True, "files.list"),
    "downloadChatFile": Operation(
        "GET", "/chats/{chatId}/files/{fileId}/content", False, True, "files.download_url"
    ),
    "listAgentWorkflows": Operation("GET", "/agent-workflows", False, True, "workflows.list"),
    "listCandidates": Operation("GET", "/chats/{chatId}/candidates", False, True, "campaigns.candidates"),
    # The structure file itself (up to 10 MiB), not a redirect to one.
    "getCandidateStructure": Operation(
        "GET", "/chats/{chatId}/candidates/{candidateId}/structure", False, True,
        "campaigns.download_structure",
    ),
    "listChatJobs": Operation("GET", "/chats/{chatId}/jobs", False, True, "campaigns.jobs"),
    "getChatTask": Operation("GET", "/chats/{chatId}/tasks/{taskId}", False, True, "campaigns.task"),
    "listSubagents": Operation("GET", "/chats/{chatId}/subagents", False, True, "subagents.list"),
    "getSubagent": Operation(
        "GET", "/chats/{chatId}/subagents/{subagentId}", False, True, "subagents.get"
    ),
    # "A subagent that already finished is returned unchanged."
    "cancelSubagent": Operation(
        "POST", "/chats/{chatId}/subagents/{subagentId}/cancel", False, True, "subagents.cancel"
    ),
    "createChatExport": Operation(
        "POST", "/chats/{chatId}/exports", True, True, "campaigns.create_export"
    ),
    "getChatExport": Operation(
        "GET", "/chats/{chatId}/exports/{exportId}", False, True, "campaigns.get_export"
    ),
    "getChatUsage": Operation("GET", "/chats/{chatId}/usage", False, True, "usage.chat"),
    "getAgentUsage": Operation("GET", "/agent-usage", False, True, "usage.month"),
}

# ``EventType`` in the spec. The stream yields only these (plus nothing for ``ping``);
# an unknown type is skipped, as the contract requires of clients, but still moves the
# resume cursor so it is never asked for again.
EVENT_TYPES: frozenset[str] = frozenset(
    {
        "message.created",
        "message.in_progress",
        "message.requires_action",
        "message.completed",
        "message.failed",
        "message.cancelled",
        "message.incomplete",
        "message.continued",
        "output_text.delta",
        "output_text.done",
        "output_text.discarded",
        "step.started",
        "step.waiting",
        "step.completed",
        "subagent.started",
        "subagent.updated",
        "subagent.completed",
        "approval.requested",
        "approval.resolved",
        "question.asked",
        "question.resolved",
        "job.completed",
        "job.failed",
        "chat.rewound",
        "usage.updated",
        "error",
        "ping",
    }
)

# ``MessageStatus`` final states, and the events that announce them.
FINAL_MESSAGE_STATUSES: frozenset[str] = frozenset({"completed", "failed", "cancelled", "incomplete"})
FINAL_MESSAGE_EVENTS: frozenset[str] = frozenset(f"message.{s}" for s in FINAL_MESSAGE_STATUSES)
