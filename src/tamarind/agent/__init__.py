"""The Tamarind Agent API: drive the AI agent from code.

Reached as ``Tamarind().agent``::

    from tamarind import Tamarind

    with Tamarind() as client:
        chat = client.agent.chats.create(title="PD-L1 binders")
        reply = client.agent.messages.send(chat.id, "Fold this and summarize pLDDT")
        for event in client.agent.messages.follow(chat.id, reply.id):
            if event.type == "output_text.delta":
                print(event.data["delta"], end="", flush=True)

The contract is tamarind-agent's ``docs/public-api/openapi.yaml``, vendored in this repo
as ``openapi/agent-v1.yaml`` and checked against this package in CI.
"""

from ._contract import API_VERSION, EVENT_TYPES
from .events import EventStream
from .models import (
    Approval,
    ArchivedChat,
    Budget,
    Campaign,
    Candidate,
    Chat,
    ContractError,
    Event,
    Export,
    File,
    FileUpload,
    JobRef,
    Message,
    ModelUsage,
    Page,
    Question,
    Step,
    Subagent,
    TaskReport,
    TokenCounts,
    Usage,
    Workflow,
)
from .resources import Agent, iterate
from .transport import AgentTransport

__all__ = [
    "API_VERSION",
    "EVENT_TYPES",
    "Agent",
    "AgentTransport",
    "Approval",
    "ArchivedChat",
    "Budget",
    "Campaign",
    "Candidate",
    "Chat",
    "ContractError",
    "Event",
    "EventStream",
    "Export",
    "File",
    "FileUpload",
    "JobRef",
    "Message",
    "ModelUsage",
    "Page",
    "Question",
    "Step",
    "Subagent",
    "TaskReport",
    "TokenCounts",
    "Usage",
    "Workflow",
    "iterate",
]
