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
import inspect
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
        assert _has_param(op, "TamarindVersion"), op_id


def test_every_mapped_operation_names_a_real_sdk_method():
    agent = Agent(AgentTransport.__new__(AgentTransport))
    for op_id, op in OPERATIONS.items():
        namespace, method = op.sdk.split(".")
        assert callable(getattr(getattr(agent, namespace), method)), op_id


def test_the_sdk_sends_the_specs_default_version():
    param = SPEC["components"]["parameters"]["TamarindVersion"]
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
    (models.Budget, "Budget"),
    (models.Usage, "Usage"),
    (models.TokenCounts, "TokenCounts"),
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


def _call_for(agent: Agent, op_id: str):
    """One SDK call for each operation, with ids taken from the spec's examples."""
    a = agent
    calls = {
        "createChat": lambda: a.chats.create(title="t"),
        "listChats": lambda: a.chats.list(),
        "getChat": lambda: a.chats.get("chat_7Q"),
        "updateChat": lambda: a.chats.update("chat_7Q", budget_hours=60),
        "archiveChat": lambda: a.chats.archive("chat_7Q"),
        "sendMessage": lambda: a.messages.send("chat_7Q", "hi"),
        "listMessages": lambda: a.messages.list("chat_7Q"),
        "getMessage": lambda: a.messages.get("chat_7Q", "msg_1"),
        "cancelMessage": lambda: a.messages.cancel("chat_7Q", "msg_1"),
        "rewindChat": lambda: a.chats.rewind("chat_7Q", "msg_0"),
        "listChatEvents": lambda: a.events.list("chat_7Q"),
        "listApprovals": lambda: a.approvals.list("chat_7Q"),
        "answerQuestion": lambda: a.questions.answer("chat_7Q", "q_8c", text="Chain A"),
        "resolveApproval": lambda: a.approvals.approve("chat_7Q", "apr_x"),
        "createChatFile": lambda: a.files.create_upload("target.pdb", 88140),
        "getChatFile": lambda: a.files.get("file_9f2"),
        "listChatFiles": lambda: a.files.list("chat_7Q"),
        "downloadChatFile": lambda: a.files.download_url("chat_7Q", "file_k2"),
        "listAgentWorkflows": lambda: a.workflows.list(),
        "listCandidates": lambda: a.campaigns.candidates("chat_7Q"),
        "getCandidateStructure": lambda: a.campaigns.candidate_structure_url("chat_7Q", "cand_07"),
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


@pytest.mark.parametrize("op_id", sorted(OPERATIONS))
def test_each_sdk_call_hits_its_operation_and_parses_the_specs_example(op_id):
    method, path_template, op = SPEC_OPS[op_id]
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if "302" in op["responses"]:
            return httpx.Response(302, headers={"Location": "https://s3.test/signed?X-Amz-Signature=x"})
        status, body = _example(op)
        return httpx.Response(status, json=body)

    from tamarind.http import HTTPClient

    http = HTTPClient("https://api.test/api", "key")
    http._client = httpx.Client(base_url="https://api.test/api", headers=http._headers,
                                transport=httpx.MockTransport(handler))
    agent = Agent(AgentTransport(http, sleep=lambda _s: None))
    result = _call_for(agent, op_id)()

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


def test_send_message_example_bodies_conform_to_the_input_schema():
    """What ``messages.send`` builds is the spec's ``MessageCreate`` shape."""
    from tamarind.agent.resources import text_input

    parts = text_input("Fold this", ["file_9f2"])
    example = SPEC["paths"]["/chats/{chatId}/messages"]["post"]["requestBody"]["content"][
        "application/json"]["examples"]["streamed"]["value"]["input"]
    assert [sorted(p) for p in parts] == [sorted(p) for p in example]
    assert inspect.signature(Agent).parameters  # the facade takes its transport


@pytest.mark.skipif(not os.environ.get("TAMARIND_AGENT_CHECKOUT"),
                    reason="set TAMARIND_AGENT_CHECKOUT to compare against the producer")
def test_the_vendored_spec_is_the_locked_commits_bytes():
    checkout = Path(os.environ["TAMARIND_AGENT_CHECKOUT"])
    raw = subprocess.run(
        ["git", "-C", str(checkout), "show", f"{LOCK['sourceCommit']}:{LOCK['sourcePath']}"],
        check=True, capture_output=True,
    ).stdout
    assert raw == SPEC_PATH.read_bytes()
