"""The Agent SDK against its pinned contract, ``openapi/agent-v1.yaml``.

These fail when a re-synced spec adds, moves or renames an operation, an event type or a
model field the SDK does not know yet: the drift check for a hand-written client.

Re-sync: ``git -C <tamarind-agent> show <sha>:docs/public-api/openapi.yaml >
openapi/agent-v1.yaml``, then set ``sourceCommit`` and ``artifactSha256`` in
``openapi/agent-v1.lock.json``. With ``TAMARIND_AGENT_CHECKOUT=<path>`` set, the last test
also checks the vendored bytes are that commit's.
"""

from __future__ import annotations

from dataclasses import fields
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import subprocess
from typing import Any

import httpx
import pytest
import yaml

from tamarind.agent import models
from tamarind.agent._contract import API_VERSION, EVENT_TYPES, OPERATIONS
from tamarind.agent.resources import Agent
from tamarind.agent.transport import AgentTransport

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "openapi/agent-v1.yaml"
LOCK = json.loads((ROOT / "openapi/agent-v1.lock.json").read_text())
SPEC = yaml.safe_load(SPEC_PATH.read_text())
_METHODS = ("get", "post", "put", "patch", "delete")


def _spec_operations() -> dict[str, tuple[str, str, dict[str, Any]]]:
    found = {}
    for path, item in SPEC["paths"].items():
        shared = item.get("parameters", [])
        for method in _METHODS:
            if method in item:
                op = item[method]
                op = {**op, "parameters": shared + op.get("parameters", [])}
                found[op["operationId"]] = (method.upper(), path, op)
    return found


SPEC_OPS = _spec_operations()


def _has_param(op: dict[str, Any], ref_name: str) -> bool:
    return any(p.get("$ref") == f"#/components/parameters/{ref_name}" for p in op["parameters"])


def test_the_vendored_spec_matches_its_provenance_lock():
    assert set(LOCK) == {"artifactSha256", "schemaVersion", "sourceCommit", "sourcePath", "sourceRepository"}
    assert LOCK["schemaVersion"] == 1
    assert LOCK["sourceRepository"] == "Tamarind-Bio/tamarind-agent"
    assert LOCK["sourcePath"] == "docs/public-api/openapi.yaml"
    assert re.fullmatch(r"[0-9a-f]{40}", LOCK["sourceCommit"])
    assert sha256(SPEC_PATH.read_bytes()).hexdigest() == LOCK["artifactSha256"]


def test_every_spec_operation_is_mapped_with_its_method_path_and_key():
    assert set(OPERATIONS) == set(SPEC_OPS)
    for op_id, (method, path, op) in SPEC_OPS.items():
        mine = OPERATIONS[op_id]
        assert (mine.method, mine.path) == (method, path), op_id
        assert mine.idempotency_key == _has_param(op, "IdempotencyKey"), op_id


def test_every_mapped_operation_names_a_real_sdk_method():
    agent = Agent(AgentTransport.__new__(AgentTransport))
    for op_id, op in OPERATIONS.items():
        namespace, method = op.sdk.split(".")
        assert callable(getattr(getattr(agent, namespace), method)), op_id


def test_a_version_header_the_spec_names_is_the_one_the_sdk_sends():
    """The spec at the locked commit names none (see ``_contract``): if it names one again, the
    SDK's pin has to be the date the spec defaults to."""
    param = SPEC["components"]["parameters"].get("TamarindVersion")
    if param is not None:
        assert param["name"] == "Tamarind-Version"
        assert param["schema"]["default"] == API_VERSION


def test_the_known_event_types_are_the_specs():
    assert EVENT_TYPES == frozenset(SPEC["components"]["schemas"]["EventType"]["enum"])


# Each model against the schema it reads: every property the spec names is a field
# (camelCase -> snake_case), except the constant `object` discriminator.
_MODEL_SCHEMAS = [
    (models.Chat, "Chat"),
    (models.Message, "Message"),
    (models.Approval, "Approval"),
    (models.Question, "Question"),
    (models.Step, "Step"),
    (models.Subagent, "Subagent"),
    (models.File, "File"),
    (models.Campaign, "Campaign"),
    (models.SharedChat, "SharedChat"),
    (models.Budget, "Budget"),
    (models.Usage, "Usage"),
    (models.AgentUsage, "AgentUsage"),
    (models.Workflow, "Workflow"),
    (models.Candidate, "Candidate"),
    (models.JobRef, "JobRef"),
    (models.Export, "Export"),
    (models.Event, "Event"),
]


def _snake(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


@pytest.mark.parametrize(("model", "schema"), _MODEL_SCHEMAS, ids=[s for _, s in _MODEL_SCHEMAS])
def test_each_model_reads_every_property_its_schema_names(model, schema):
    spec = SPEC["components"]["schemas"][schema]
    names = {f.name for f in fields(model)}
    missing = {_snake(p) for p in spec.get("properties", {}) if p != "object"} - names
    assert not missing, f"{model.__name__} lacks {sorted(missing)}"
    required = {_snake(p) for p in spec.get("required", []) if p != "object"}
    assert required <= names


def _example(op: dict[str, Any]) -> tuple[int, Any]:
    for status in ("200", "201", "202"):
        response = op["responses"].get(status)
        content = (response or {}).get("content", {}).get("application/json")
        if content and "example" in content:
            return int(status), content["example"]
    raise LookupError


def _call_for(agent: Agent, op_id: str, tmp_path: Path):
    """One SDK call for each operation, with ids taken from the spec's examples."""
    a = agent
    calls = {
        "createChat": lambda: a.chats.create(title="t"),
        "listChats": lambda: a.chats.list(),
        "getChat": lambda: a.chats.get("chat_7Q"),
        "updateChat": lambda: a.chats.update("chat_7Q", budget_hours=60),
        "deleteChat": lambda: a.chats.delete("chat_7Q"),
        "sendMessage": lambda: a.messages.send("chat_7Q", "hi"),
        "listMessages": lambda: a.messages.list("chat_7Q"),
        "getMessage": lambda: a.messages.get("chat_7Q", "msg_1"),
        "cancelMessage": lambda: a.messages.cancel("chat_7Q", "msg_1"),
        "rewindChat": lambda: a.chats.rewind("chat_7Q", "msg_0"),
        "listChatEvents": lambda: a.events.list("chat_7Q"),
        "listApprovals": lambda: a.approvals.list("chat_7Q"),
        "answerQuestion": lambda: a.questions.answer("chat_7Q", "q_8c", text="Chain A"),
        "resolveApproval": lambda: a.approvals.approve("chat_7Q", "apr_x"),
        "createChatFile": lambda: a.files.create_upload("target.pdb"),
        "getChatFile": lambda: a.files.get("file_9f2"),
        "listChatFiles": lambda: a.files.list("chat_7Q"),
        "downloadChatFile": lambda: a.files.download_url("chat_7Q", "file_k2"),
        "listAgentWorkflows": lambda: a.workflows.list(),
        "listCandidates": lambda: a.campaigns.candidates("chat_7Q"),
        "getCandidateStructure": lambda: a.campaigns.download_structure("chat_7Q", "cand_07", tmp_path),
        "listChatJobs": lambda: a.campaigns.jobs("chat_7Q"),
        "getChatTask": lambda: a.campaigns.task("chat_7Q", "t1"),
        "listSubagents": lambda: a.subagents.list("chat_7Q"),
        "getSubagent": lambda: a.subagents.get("chat_7Q", "sub_3h"),
        "cancelSubagent": lambda: a.subagents.cancel("chat_7Q", "sub_5c"),
        "createChatExport": lambda: a.campaigns.create_export("chat_7Q"),
        "getChatExport": lambda: a.campaigns.get_export("chat_7Q", "exp_5d"),
        "getChatUsage": lambda: a.usage.chat("chat_7Q"),
        "getAgentUsage": lambda: a.usage.month("2026-10"),
    }
    assert set(calls) == set(OPERATIONS)
    return calls[op_id]


def _agent_serving(op: dict[str, Any], seen: list[httpx.Request]) -> Agent:
    """An Agent whose server answers every request as the spec describes the operation."""

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if "302" in op["responses"]:
            return httpx.Response(302, headers={"Location": "https://s3.test/signed?X-Amz-Signature=x"})
        try:
            status, body = _example(op)
        except LookupError:
            # No JSON example: a file served as it is (the structure route), named by its header.
            return httpx.Response(200, content=b"data_\n", headers={
                "Content-Type": "chemical/x-pdb", "Content-Disposition": 'attachment; filename="pdl1-b07.pdb"'})
        return httpx.Response(status, json=body)

    from tamarind.http import HTTPClient

    http = HTTPClient("https://api.test/api", "key")
    http._client = httpx.Client(base_url="https://api.test/api", headers=http._headers,
                                transport=httpx.MockTransport(handler))
    return Agent(AgentTransport(http, sleep=lambda _s: None))


@pytest.mark.parametrize("op_id", sorted(OPERATIONS))
def test_each_sdk_call_hits_its_operation_and_parses_the_specs_example(op_id, tmp_path):
    method, path_template, op = SPEC_OPS[op_id]
    seen: list[httpx.Request] = []
    result = _call_for(_agent_serving(op, seen), op_id, tmp_path)()

    assert len(seen) == 1
    request = seen[0]
    assert request.method == method
    pattern = "^/api" + re.sub(r"\\\{[^/]+?\\\}", "[^/]+", re.escape(path_template)) + "$"
    assert re.match(pattern, request.url.path), (request.url.path, path_template)
    assert request.headers["Tamarind-Version"] == API_VERSION
    assert ("Idempotency-Key" in request.headers) == OPERATIONS[op_id].idempotency_key
    assert result is not None
    if "302" in op["responses"]:
        assert result.startswith("https://s3.test/")
    if op_id == "getCandidateStructure":
        assert (tmp_path / "pdl1-b07.pdb").read_bytes() == b"data_\n"  # the name the response gave


# Every optional argument of each SDK call that sends a body or a query, all set: the request
# may carry nothing the spec's operation does not list, and what it requires.
_AGENT_ID = "agt_" + "0" * 20
_FULL_CALLS = {
    "createChat": lambda a: a.chats.create(
        title="t", effort="high", agent_id=_AGENT_ID, mode="campaign", workflow="w", budget_hours=1,
        per_job_hours=1, auto_approve=True, dangerously_approve_all=True, idempotency_key="k"),
    "listChats": lambda a: a.chats.list(
        limit=5, cursor="c", scope="own", source="api", status="idle", mode="chat"),
    "updateChat": lambda a: a.chats.update(
        "c", title="t", effort="high", mode="campaign", workflow="w", budget_hours=1, per_job_hours=1,
        auto_approve=True, dangerously_approve_all=True, campaign_status="running"),
    "sendMessage": lambda a: a.messages.send("c", "hi", file_ids=["f"], interrupt=True, idempotency_key="k"),
    "listMessages": lambda a: a.messages.list("c", limit=5, cursor="c"),
    "rewindChat": lambda a: a.chats.rewind("c", "m"),
    "listChatEvents": lambda a: a.events.list("c", after="1.0", message_id="m", limit=5),
    "listApprovals": lambda a: a.approvals.list("c", status="pending"),
    "resolveApproval": lambda a: a.approvals.approve("c", "a", scope="chat"),
    "answerQuestion": lambda a: a.questions.answer("c", "q", answers={"Which?": "A"}),
    "createChatFile": lambda a: a.files.create_upload("target.pdb"),
    "listChatFiles": lambda a: a.files.list("c", limit=5, cursor="c"),
    "listCandidates": lambda a: a.campaigns.candidates("c", limit=5, cursor="c", sort="-iptm"),
    "listChatJobs": lambda a: a.campaigns.jobs("c", limit=5, cursor="c"),
    "listSubagents": lambda a: a.subagents.list("c", message_id="m", status="running", limit=5, cursor="c"),
    "createChatExport": lambda a: a.campaigns.create_export("c", format="csv", idempotency_key="k"),
    "getAgentUsage": lambda a: a.usage.month("2026-10"),
}


def _resolved(schema: dict[str, Any]) -> dict[str, Any]:
    ref = schema.get("$ref")
    return SPEC["components"]["schemas"][ref.rsplit("/", 1)[1]] if ref else schema


def _declared_query_names(op: dict[str, Any]) -> set[str]:
    names = set()
    for param in op["parameters"]:
        ref = param.get("$ref")
        param = SPEC["components"]["parameters"][ref.rsplit("/", 1)[1]] if ref else param
        if param["in"] == "query":
            names.add(param["name"])
    return names


@pytest.mark.parametrize("op_id", sorted(_FULL_CALLS))
def test_a_request_carries_only_what_the_operation_lists(op_id):
    """The server refuses a field it does not list (400): sending one is a break, not a no-op."""
    _, _, op = SPEC_OPS[op_id]
    seen: list[httpx.Request] = []
    _FULL_CALLS[op_id](_agent_serving(op, seen))
    request = seen[0]

    assert {name for name in request.url.params} <= _declared_query_names(op), op_id
    body_spec = op.get("requestBody", {}).get("content", {}).get("application/json", {}).get("schema")
    if body_spec is None:
        assert not request.content, op_id
        return
    schema = _resolved(body_spec)
    body = json.loads(request.content)
    assert set(body) <= set(schema["properties"]), (op_id, set(body) - set(schema["properties"]))
    assert set(schema.get("required", [])) <= set(body), op_id
    if "campaign" in body:  # PATCH /chats/{chatId}: `campaign.status`
        assert set(body["campaign"]) <= set(schema["properties"]["campaign"]["properties"])
        assert body["campaign"]["status"] in schema["properties"]["campaign"]["properties"]["status"]["enum"]


def test_send_message_example_bodies_conform_to_the_input_schema():
    """What ``messages.send`` builds is the spec's ``MessageCreate`` shape."""
    from tamarind.agent.resources import text_input

    parts = text_input("Fold this", ["file_9f2"])
    example = SPEC["paths"]["/chats/{chatId}/messages"]["post"]["requestBody"]["content"][
        "application/json"]["examples"]["streamed"]["value"]["input"]
    assert [sorted(p) for p in parts] == [sorted(p) for p in example]


@pytest.mark.skipif(not os.environ.get("TAMARIND_AGENT_CHECKOUT"),
                    reason="set TAMARIND_AGENT_CHECKOUT to compare against the producer")
def test_the_vendored_spec_is_the_locked_commits_bytes():
    checkout = Path(os.environ["TAMARIND_AGENT_CHECKOUT"])
    raw = subprocess.run(
        ["git", "-C", str(checkout), "show", f"{LOCK['sourceCommit']}:{LOCK['sourcePath']}"],
        check=True, capture_output=True,
    ).stdout
    assert raw == SPEC_PATH.read_bytes()


def test_a_requires_action_events_approvals_are_the_replys_pending_approvals():
    """`message.requires_action` adds `approvals[]` (MessageEventData): read as the reply's cards."""
    from tamarind.agent.models import Message

    assert "approvals" in SPEC["components"]["schemas"]["MessageEventData"]["allOf"][1]["properties"]
    wire = {"id": "msg_1", "object": "message", "chatId": "c", "role": "assistant", "content": [],
            "createdAt": "x", "status": "requires_action", "pendingApprovals": [],
            "approvals": [{"id": "apr_x", "status": "pending", "kind": "platform", "summary": "s",
                           "createdAt": "x"}]}
    assert [a.id for a in Message.from_wire(wire).pending_approvals] == ["apr_x"]


# What the contract added or stopped sending, read off a wire object as the spec's own examples
# show it: (model, wire, attribute, expected).
_CHAT = {"id": "chat_7Q", "object": "chat", "title": "t", "status": "idle", "source": "api",
         "createdAt": "x", "updatedAt": "y"}
_APPROVAL = {"id": "apr_x", "status": "approved", "kind": "platform", "summary": "s", "createdAt": "x"}
_CAMPAIGN = {"id": "cmp_7Q", "workflow": "binder-design", "status": "running"}  # no `engine`
_SHARED = {"id": "chat_9Z", "object": "chat", "readOnly": True, "title": "t", "ownerEmail": "ana@lab.test",
           "source": "ui", "mode": "chat", "webUrl": "u", "createdAt": "x", "updatedAt": "y"}
_READS = [
    (models.Chat, {**_CHAT, "dangerouslyApproveAll": True}, "dangerously_approve_all", True),
    (models.Chat, _CHAT, "dangerously_approve_all", None),  # not in `GET /chats` items
    (models.Approval, {**_APPROVAL, "resolvedBy": "dangerouslyApproveAll"}, "resolved_by", "dangerouslyApproveAll"),
    (models.Approval, {**_APPROVAL, "resolvedBy": None}, "resolved_by", None),
    (models.Question, {"id": "q", "status": "answered", "questions": [], "createdAt": "x",
                       "answerMessageId": "msg_u1052"}, "answer_message_id", "msg_u1052"),
    (models.Campaign, {**_CAMPAIGN, "finalDesigns": {"ids": ["cand_07"], "note": "n"}}, "final_designs",
     {"ids": ["cand_07"], "note": "n"}),
    (models.Campaign, _CAMPAIGN, "workflow", "binder-design"),  # a server that sends no engine
    (models.Workflow, {"id": "binder-design", "label": "Binder design", "supports": ["plan", "pause", "budget"]},
     "supports", ("plan", "pause", "budget")),
    (models.Candidate, {"id": "c", "sequence": "MK", "final": True, "hasStructure": False}, "final", True),
    (models.Candidate, {"id": "c", "sequence": "MK", "final": True, "hasStructure": False}, "has_structure", False),
    (models.JobRef, {"jobName": "j", "tool": "boltz", "status": "Complete", "submittedAt": None},
     "submitted_at", None),
    (models.File, {"id": "f", "filename": "a", "status": "expired", "origin": "campaign"}, "origin", "campaign"),
    (models.Usage, {"agentHours": 1, "jobsHours": 2, "totalHours": 3, "capHours": None}, "cap_hours", None),
    (models.AgentUsage, {"month": "2026-10", "agentHours": 12.4, "remainingHours": None}, "remaining_hours", None),
    (models.AgentUsage, {"month": "2026-10", "agentHours": 12.4, "remainingHours": 925.7}, "remaining_hours", 925.7),
    (models.DeletedChat, {"id": "chat_7Q", "object": "chat", "deleted": True}, "deleted", True),
    (models.SharedChat, _SHARED, "owner_email", "ana@lab.test"),
    (models.SharedChat, {**_SHARED, "campaign": _CAMPAIGN}, "campaign", models.Campaign.from_wire(_CAMPAIGN)),
]


@pytest.mark.parametrize(("model", "wire", "attribute", "expected"), _READS,
                         ids=[f"{m.__name__}.{a}" for m, _, a, _ in _READS])
def test_the_fields_the_contract_added_are_read(model, wire, attribute, expected):
    assert getattr(model.from_wire(wire), attribute) == expected


@pytest.mark.parametrize("gone", [
    (models.Message, "model"), (models.Usage, "agent_usd"), (models.Usage, "by_model"), (models.Usage, "tokens"),
    (models.Campaign, "engine"), (models.Campaign, "paused_workflows"), (models.Candidate, "structure_file_id"),
    (models.Event, "campaign_id"), (models.JobRef, "campaign_id"), (models.Workflow, "engine"),
    (models.Question, "expires_at"), (models.TaskReport, "trace"),
], ids=lambda pair: f"{pair[0].__name__}.{pair[1]}")
def test_a_field_the_contract_dropped_is_not_kept(gone):
    model, name = gone
    assert name not in {f.name for f in fields(model)}


def test_a_chat_is_yours_or_a_teammates_by_its_read_only_flag():
    assert type(models.chat_from_wire(_CHAT)) is models.Chat
    shared = models.chat_from_wire(_SHARED)
    assert type(shared) is models.SharedChat and shared.read_only
    assert not hasattr(shared, "status")  # a teammate's chat has no state of its own


def test_an_upload_slot_keeps_its_fields_in_the_order_given_and_shows_none_of_them():
    wire = {"fileId": "file_9f2", "uploadUrl": "https://s3.test/u/", "expiresAt": "x",
            "uploadFields": {"key": "k", "Content-Type": "c", "policy": "POLICYB64", "x-amz-signature": "sig"}}
    slot = models.FileUpload.from_wire(wire)
    assert list(slot.upload_fields) == ["key", "Content-Type", "policy", "x-amz-signature"]
    assert "POLICYB64" not in repr(slot) and "sig" not in repr(slot) and "s3.test" not in repr(slot)


@pytest.mark.parametrize("fields_value", [None, ["key"], {"key": 1}, {"key": None}])
def test_an_upload_slot_without_a_form_of_strings_is_a_contract_break(fields_value):
    wire = {"fileId": "f", "uploadUrl": "https://s3.test/u/", "expiresAt": "x"}
    if fields_value is not None:
        wire["uploadFields"] = fields_value
    with pytest.raises(models.ContractError):
        models.FileUpload.from_wire(wire)


def test_a_page_says_when_its_listing_was_cut_short():
    page = models.page_of({"data": [], "nextCursor": None, "truncated": True}, models.File.from_wire)
    assert page.truncated is True and page.next_cursor is None
    assert models.page_of({"data": [], "nextCursor": None}, models.File.from_wire).truncated is False
