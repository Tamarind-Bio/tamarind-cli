"""The CLI through the real v1 SDK, down to the HTTP requests it sends.

``tests/test_v1_cli.py`` and ``tests/test_v1_classic_routes.py`` check what each
command asks the SDK for; these run a few commands through ``tamarind._v1.Tamarind``
over a mock transport, so the requests on the wire (path, query, body, headers) and
the error mapping are checked too.
"""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest
from typer.testing import CliRunner

from tamarind.cli.main import app
from tamarind._v1 import ProblemError, Tamarind

from conftest import turn_v1_on

runner = CliRunner()
BASE = "https://api.test"


@pytest.fixture
def wire(monkeypatch, tmp_path):
    monkeypatch.setenv("TAMARIND_CONFIG_DIR", str(tmp_path))
    monkeypatch.setenv("TAMARIND_API_KEY", "test-key")
    monkeypatch.setenv("TAMARIND_V1_API_BASE", BASE)
    seen: list[httpx.Request] = []
    routes: dict[tuple[str, str], Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        answer = routes.get((request.method, request.url.path))
        if answer is None:
            return httpx.Response(404, json={"type": "about:blank", "title": "Not Found", "status": 404, "code": "not_found", "detail": "no route", "requestId": "req_1"})
        status, body = answer
        return httpx.Response(status, json=body) if body is not None else httpx.Response(status)

    def make_client(http: Any, **options: Any) -> Tamarind:
        return Tamarind(
            http.api_key,
            base_url=http.v1_base,
            max_retries=0,
            http_client=httpx.Client(transport=httpx.MockTransport(handler)),
        )

    turn_v1_on(monkeypatch, factory=make_client)
    return seen, routes


def test_submit_sends_the_v1_body_key_and_an_idempotency_key(wire):
    seen, routes = wire
    routes[("POST", "/jobs")] = (201, {"kind": "job", "id": "job_00000000-0000-0000-0000-000000000001", "name": "n", "status": "In Queue"})
    res = runner.invoke(app, ["--json", "submit", "esmfold", "--skip-validate", "--name", "n", "--set", "sequence=MKT"])
    assert res.exit_code == 0, res.output
    request = seen[-1]
    assert str(request.url) == f"{BASE}/jobs"
    assert json.loads(request.content) == {"kind": "job", "tool": "esmfold", "name": "n", "settings": {"sequence": "MKT"}}
    assert request.headers["x-api-key"] == "test-key" or request.headers.get("authorization") == "Bearer test-key"
    assert request.headers.get("idempotency-key")
    # today's output: classic's answer to /submit-job
    assert json.loads(res.stdout) == {"jobName": "n", "type": "esmfold", "submit": "n submitted to queue."}


def test_list_filters_go_comma_joined(wire):
    seen, routes = wire
    routes[("GET", "/jobs")] = (200, {"items": [], "nextCursor": None})
    res = runner.invoke(app, ["--json", "jobs", "list", "--status", "Running,In Queue", "--limit", "7"])
    assert res.exit_code == 0, res.output
    params = seen[-1].url.params
    assert params["status"] == "Running,In Queue"
    assert params["limit"] == "7"


def test_generic_command_reaches_its_route(wire):
    seen, routes = wire
    routes[("GET", "/projects/prj_1/members")] = (200, {"items": [{"email": "a@example.com"}], "nextCursor": None})
    res = runner.invoke(app, ["--json", "projects", "members", "prj_1", "--limit", "2"])
    assert res.exit_code == 0, res.output
    assert json.loads(res.stdout)["items"] == [{"email": "a@example.com"}]
    assert seen[-1].url.path == "/projects/prj_1/members" and seen[-1].url.params["limit"] == "2"


def test_problem_answers_keep_exit_codes(wire):
    res = runner.invoke(app, ["--json", "jobs", "get", "job_abababababababababababababababab"])
    assert isinstance(res.exception, ProblemError)
    assert res.exception.exit_code == 4
    assert res.exception.problem["code"] == "not_found"


def test_small_upload_goes_inline(wire, tmp_path):
    seen, routes = wire
    routes[("POST", "/files")] = (201, {"file": {"path": "x/t.pdb", "type": "file", "sizeBytes": 4, "modifiedAt": None}, "upload": None})
    local = tmp_path / "t.pdb"
    local.write_text("ATOM")
    res = runner.invoke(app, ["--json", "files", "upload", str(local), "--name", "x/t.pdb"])
    assert res.exit_code == 0, res.output
    body = json.loads(seen[-1].content)
    assert body["path"] == "x/t.pdb" and body["contentBase64"]
    # today's output: what classic's upload answers
    assert json.loads(res.stdout) == {"ok": True, "filename": "x/t.pdb", "bytes": 4}


def test_auth_status_with_a_rejected_key_says_not_verified(wire):
    # With v1 on, the key check is classic's (one job listing), answered from v1.
    seen, routes = wire
    routes[("GET", "/jobs")] = (401, {"type": "about:blank", "title": "Unauthorized", "status": 401, "code": "invalid_api_key", "detail": "bad key"})
    res = runner.invoke(app, ["--json", "auth", "status"])
    assert res.exit_code == 0, res.output
    assert json.loads(res.stdout) == {"profile": "default", "hasKey": True, "verified": False}
    assert seen[-1].url.path == "/jobs"


def test_auth_login_refuses_a_rejected_key(wire):
    seen, routes = wire
    routes[("GET", "/jobs")] = (401, {"type": "about:blank", "title": "Unauthorized", "status": 401, "code": "invalid_api_key"})
    res = runner.invoke(app, ["--json", "auth", "login", "--api-key", "nope"])
    assert res.exception is not None and res.exception.exit_code == 3
    assert seen[-1].url.path == "/jobs" and seen[-1].headers["x-api-key"] == "nope"


def test_a_members_jobs_ask_for_scope_org_and_created_by(wire):
    seen, routes = wire
    routes[("GET", "/jobs")] = (200, {"items": [], "nextCursor": None})
    res = runner.invoke(app, ["--json", "jobs", "--email", "p@example.com", "--limit", "3"])
    assert res.exit_code == 0, res.output
    params = seen[-1].url.params
    assert (params["scope"], params["createdBy"], params["limit"]) == ("org", "p@example.com", "3")


def test_files_folders_ask_for_type_folder(wire):
    seen, routes = wire
    routes[("GET", "/files")] = (200, {"items": [{"path": "runs", "type": "folder", "jobName": None}], "nextCursor": None})
    res = runner.invoke(app, ["--json", "files", "folders", "--limit", "4"])
    assert res.exit_code == 0, res.output
    assert (seen[-1].url.params["type"], seen[-1].url.params["limit"]) == ("folder", "4")
    assert json.loads(res.stdout) == {"folders": ["runs"], "hasMore": False, "nextCursor": None}


def test_results_pdbs_only_send_best_structures(wire, tmp_path):
    seen, routes = wire
    job = "job_00000000-0000-0000-0000-000000000001"
    routes[("GET", "/jobs")] = (200, {"items": [{"kind": "job", "id": job, "name": "n", "status": "Complete"}], "nextCursor": None})
    routes[("POST", f"/jobs/{job}/archive")] = (200, {"status": "ready", "downloadUrl": "https://s3.test/n-pdbs.zip"})
    res = runner.invoke(app, ["--json", "results", "n", "--show-url", "--pdbs-only"])
    assert res.exit_code == 0, res.output
    assert json.loads(seen[-1].content) == {"bestStructures": True}
    assert json.loads(res.stdout)["url"] == "https://s3.test/n-pdbs.zip"
