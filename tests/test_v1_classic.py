"""Today's classic requests, answered by v1 when the server turns v1 on for the key.

``tamarind._v1.classic`` answers them inside :class:`~tamarind.http.HTTPClient`. These
tests check what each request asks v1, how its answer is rebuilt into classic's layout
(end to end: the same command prints the same thing with either API, given the same
data), that v1's refusals are raised as v1's errors (also the classic class for the
status) with no fallback, and that only the requests v1 has no form for yet go to
classic.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import httpx
import pytest
from typer.testing import CliRunner

from tamarind._v1 import classic
from tamarind.cli import main as cli_main
from tamarind.cli.main import app
from tamarind.errors import APIError, AuthError, JobTimeoutError, NotFoundError, TamarindError, ValidationError
from tamarind.http import HTTPClient
from tamarind._v1.errors import ProblemError

from conftest import turn_v1_on
from test_v1_cli import Recorder

runner = CliRunner()
JOB = "job_0f8fad5b-d9cb-469f-a165-70867728950e"
BATCH = "batch_0f8fad5b-d9cb-469f-a165-70867728950e"
SIGNED = "https://bucket.s3.amazonaws.com/u/result-0f8f.zip?X-Amz-Signature=abc"


def problem(status: int, code: str = "x") -> ProblemError:
    return ProblemError(status=status, code=code, title=code, detail=f"{status} {code}", problem={"status": status, "code": code})


class FakeClassic:
    """The classic API behind HTTPClient: records requests, answers from a table keyed by path."""

    calls: list[tuple[str, str, Any]] = []
    answers: dict[str, Any] = {}

    @staticmethod
    def answer(client: HTTPClient, method: str, path: str, *, params: Any = None, json: Any = None, timeout: Any = None) -> Any:
        payload = json if json is not None else params
        FakeClassic.calls.append((method, path, payload))
        if not client.api_key:
            raise AuthError("No API key configured. Set TAMARIND_API_KEY, pass --api-key, or run `tamarind auth login`.")
        answer = FakeClassic.answers.get(path)
        if isinstance(answer, BaseException):
            raise answer
        return answer(payload) if callable(answer) else answer


def classic_calls() -> list[tuple[str, str, Any]]:
    return list(FakeClassic.calls)


@pytest.fixture
def env(monkeypatch, tmp_path):
    """Both APIs faked: ``env.v1`` is the v1 SDK recorder; classic is ``FakeClassic``."""
    monkeypatch.setenv("TAMARIND_CONFIG_DIR", str(tmp_path))
    monkeypatch.setenv("TAMARIND_API_KEY", "test-key")
    FakeClassic.calls = []
    FakeClassic.answers = {}
    monkeypatch.setattr(HTTPClient, "_classic_json", FakeClassic.answer)
    recorder = Recorder({})
    turn_v1_on(monkeypatch, client=recorder)

    class Env:
        v1 = recorder

        @staticmethod
        def run(api: str, *args: str) -> Any:
            # "classic" is the escape hatch; otherwise the server says v1 is on.
            if api == "classic":
                monkeypatch.setenv("TAMARIND_API", "classic")
            else:
                monkeypatch.delenv("TAMARIND_API", raising=False)
            return runner.invoke(app, list(args))

    return Env


def same_output(env, *args: str) -> Any:
    """Run ``args`` with classic, then with v1; both must print the same and exit alike."""
    classic = env.run("classic", *args)
    v1 = env.run("v1", *args)
    assert (classic.exit_code, classic.stdout) == (v1.exit_code, v1.stdout), (classic.output, v1.output)
    return v1



def _page(*items: dict[str, Any], cursor: str | None = None) -> dict[str, Any]:
    return {"items": list(items), "nextCursor": cursor}


def _found(kind: str = "job", item_id: str = JOB, **extra: Any) -> dict[str, Any]:
    return _page({"id": item_id, "kind": kind, "name": "n1", "createdAt": "2026-11-19T05:27:02Z", **extra})


V1_JOB = {
    "kind": "job", "id": JOB, "name": "n1", "tool": "esmfold", "status": "Complete",
    "settings": {"sequence": "MK"}, "scores": {"plddt": 79.725, "ptm": 0.494},
    "batchId": None, "createdAt": "2026-11-19T05:27:02Z", "startedAt": "2026-11-19T05:35:36Z",
    "completedAt": "2026-11-19T05:36:01Z", "weightedHours": 0.0069, "lowPriority": False,
}
CLASSIC_ROW = {
    "JobName": "n1", "JobStatus": "Complete", "Created": "2026-11-19 05:27:02", "Type": "esmfold",
    "Settings": '{"sequence":"MK"}', "Score": '{"plddt": 79.725, "ptm": 0.494}',
    "Started": "2026-11-19 05:35:36", "Completed": "2026-11-19 05:36:01", "WeightedHours": 0.01,
}
STATUSES_ONE = {"Complete": 1, "In Queue": 0, "Running": 0, "Stopped": 0}


# -- which client --------------------------------------------------------------


def test_classic_mode_uses_the_classic_client_only(env):
    FakeClassic.answers["delete-job"] = "j1 deleted"
    res = env.run("classic", "--json", "delete", "j1", "--yes")
    assert res.exit_code == 0 and env.v1.calls == []
    assert classic_calls() == [("DELETE", "delete-job", {"jobName": "j1"})]


# -- job rows: status, wait, jobs -------------------------------------------------------


def test_status_is_v1s_job_in_classics_row(env):
    FakeClassic.answers["jobs"] = {**CLASSIC_ROW, "statuses": STATUSES_ONE}
    env.v1.answers["jobs.list"] = _found()
    env.v1.answers["jobs.get"] = V1_JOB
    same_output(env, "--json", "status", "n1")
    same_output(env, "--no-json", "status", "n1")
    assert env.v1.calls[:2] == [("jobs.list", (), {"name": "n1"}), ("jobs.get", (JOB,), {})]


def test_a_subjobs_row_names_its_batch(env):
    env.v1.answers["jobs.list"] = _found()
    env.v1.answers["jobs.get"] = lambda job_id: {**V1_JOB, "batchId": BATCH} if job_id == JOB else {"name": "b1"}
    out = json.loads(env.run("v1", "--json", "status", "n1").stdout)
    assert out["Batch"] == "b1"


def test_a_batch_row_is_classics(env):
    env.v1.answers["jobs.list"] = _found("batch", BATCH)
    env.v1.answers["jobs.get"] = {
        "kind": "batch", "id": BATCH, "name": "b1", "tool": "esmfold", "status": "Complete",
        "createdAt": "2026-11-19T05:36:12Z", "weightedHours": 0.0094, "counts": {"total": 2},
    }
    out = json.loads(env.run("v1", "--json", "status", "b1").stdout)
    assert out == {
        "JobName": "b1", "JobStatus": "Complete", "Created": "2026-11-19 05:36:12", "Type": "batch",
        "Settings": "esmfold", "WeightedHours": 0.01, "batchStatus": "Complete", "statuses": STATUSES_ONE,
    }


def test_an_unknown_job_reads_as_classic_words_it(env):
    FakeClassic.answers["jobs"] = NotFoundError("Job n1 not found")
    env.v1.answers["jobs.list"] = _page()
    classic = env.run("classic", "--json", "status", "n1")
    v1 = env.run("v1", "--json", "status", "n1")
    assert (type(classic.exception), str(classic.exception)) == (type(v1.exception), str(v1.exception))


def test_wait_looks_the_name_up_once(env, monkeypatch):
    import time

    monkeypatch.setattr(time, "sleep", lambda s: None)
    states = iter(["Running", "Complete"])
    env.v1.answers["jobs.list"] = _found()
    env.v1.answers["jobs.get"] = lambda job_id: {**V1_JOB, "status": next(states)}
    res = env.run("v1", "--json", "wait", "n1", "--poll-interval", "0")
    assert res.exit_code == 0 and json.loads(res.stdout)["JobStatus"] == "Complete"
    assert [c[0] for c in env.v1.calls] == ["jobs.list", "jobs.get", "jobs.get"]


def test_jobs_lists_v1s_page_in_classics_layout(env):
    row = {k: v for k, v in CLASSIC_ROW.items() if k != "Settings"}  # a list carries no settings
    FakeClassic.answers["jobs"] = {"jobs": [row], "startKey": "next", "statuses": STATUSES_ONE}
    env.v1.answers["jobs.list"] = _page({k: v for k, v in V1_JOB.items() if k != "settings"}, cursor="next")
    same_output(env, "--json", "jobs", "--limit", "5")
    same_output(env, "--no-json", "jobs", "--limit", "5")
    assert env.v1.calls[-1] == ("jobs.list", (), {"limit": 5})


def test_jobs_start_key_is_the_v1_cursor_and_batch_its_id(env):
    env.v1.answers["jobs.list"] = lambda **kw: _found("batch", BATCH) if kw.get("name") else _page()
    env.run("v1", "--json", "jobs", "--start-key", "c1", "--batch", "b1", "--limit", "2")
    assert env.v1.calls[-1] == ("jobs.list", (), {"limit": 2, "cursor": "c1", "batch_id": BATCH})


def test_jobs_of_an_unknown_batch_is_an_empty_list(env):
    env.v1.answers["jobs.list"] = _page()
    out = json.loads(env.run("v1", "--json", "jobs", "--batch", "nope").stdout)
    assert out == {"jobs": [], "count": 0, "statuses": {"Complete": 0, "In Queue": 0, "Running": 0, "Stopped": 0}}


@pytest.mark.parametrize(
    "args", [["jobs", "--include-subjobs"], ["status", "n1", "--organization"], ["jobs", "--batch", "b1", "--organization"]]
)
def test_reads_v1_has_no_form_for_yet_go_to_classic(env, args):
    # An organization-wide name or batch: classic answers every member's match (so a name
    # several members share is refused); v1's organization lookup answers only the newest.
    FakeClassic.answers["jobs"] = lambda params: (
        {"JobName": "n1", "JobStatus": "Complete", "User": "p@example.com"} if params.get("jobName") else {"jobs": [], "statuses": {}}
    )
    res = env.run("v1", "--json", *args)
    assert res.exit_code == 0 and env.v1.calls == [] and classic_calls()


PEER = "p@example.com"
PEER_ROW = {k: v for k, v in CLASSIC_ROW.items() if k != "Settings"} | {"User": PEER}
V1_PEER_JOB = {k: v for k, v in V1_JOB.items() if k != "settings"} | {"createdBy": PEER}


@pytest.mark.parametrize(
    "args, scope",
    [
        (["--organization"], {"scope": "org"}),
        (["--email", PEER], {"scope": "org", "created_by": PEER}),
        (["--organization", "--email", PEER], {"scope": "org", "created_by": PEER}),  # classic: the email wins
    ],
)
def test_jobs_of_the_organization_or_a_member_are_v1s_scope_org(env, args, scope):
    FakeClassic.answers["jobs"] = {"jobs": [PEER_ROW], "startKey": "next", "statuses": STATUSES_ONE}
    env.v1.answers["jobs.list"] = _page(V1_PEER_JOB, cursor="next")
    same_output(env, "--json", "jobs", "--limit", "5", *args)
    same_output(env, "--no-json", "jobs", "--limit", "5", *args)
    assert env.v1.calls[-1] == ("jobs.list", (), {"limit": 5, **scope})


def test_status_of_a_members_job_is_their_job_in_classics_row(env):
    FakeClassic.answers["jobs"] = {**CLASSIC_ROW, "User": PEER, "statuses": STATUSES_ONE}
    env.v1.answers["jobs.list"] = _found(createdBy=PEER)
    env.v1.answers["jobs.get"] = {**V1_JOB, "createdBy": PEER}
    same_output(env, "--json", "status", "n1", "--email", PEER)
    assert env.v1.calls[:2] == [
        ("jobs.list", (), {"name": "n1", "scope": "org", "created_by": PEER}), ("jobs.get", (JOB,), {})
    ]


def test_a_member_whose_jobs_you_cant_see_reads_as_classic_answers_it(env):
    FakeClassic.answers["jobs"] = AuthError("Unauthorized: Unauthorized to access jobs for this user")
    env.v1.answers["jobs.list"] = problem(403, "forbidden")
    for args in (["jobs", "--email", PEER], ["status", "n1", "--email", PEER]):
        res = same_output(env, "--json", *args)
        assert isinstance(res.exception, AuthError) and res.exception.exit_code == 3 and "Unauthorized to access jobs for this user" in str(res.exception)


def test_jobs_of_a_members_batch_are_listed_by_its_id(env):
    env.v1.answers["jobs.list"] = lambda **kw: _found("batch", BATCH) if kw.get("name") else _page(V1_PEER_JOB)
    out = json.loads(env.run("v1", "--json", "jobs", "--batch", "b1", "--email", PEER, "--limit", "2").stdout)
    assert env.v1.calls == [
        ("jobs.list", (), {"name": "b1", "kind": "batch", "scope": "org", "created_by": PEER}),
        ("jobs.list", (), {"limit": 2, "batch_id": BATCH}),
    ]
    assert out["jobs"][0]["User"] == PEER and out["jobs"][0]["Batch"] == "n1"


@pytest.mark.parametrize("batch_found", [False, True])
def test_a_members_batch_with_nothing_to_show_is_classics_not_found(env, batch_found):
    FakeClassic.answers["jobs"] = NotFoundError("Jobs in batch nope not found")
    env.v1.answers["jobs.list"] = lambda **kw: _found("batch", BATCH) if kw.get("name") and batch_found else _page()
    res = same_output(env, "--json", "jobs", "--batch", "nope", "--email", PEER)
    assert isinstance(res.exception, NotFoundError) and res.exception.exit_code == 4


# -- validate, submit, batch --------------------------------------------------------------


def test_validate_is_v1s_report_in_classics_verdict(env):
    FakeClassic.answers["validate-job"] = {"valid": True, "normalized": {"sequence": "MK"}, "job_name": "n1"}
    env.v1.answers["jobs.validate"] = {"valid": True, "checks": {}, "errors": [], "normalized": {"sequence": "MK"}, "name": "n1"}
    same_output(env, "--json", "validate", "esmfold", "--set", "sequence=MK", "--name", "n1")
    assert env.v1.calls == [("jobs.validate", (), {"body": {"kind": "job", "tool": "esmfold", "settings": {"sequence": "MK"}, "name": "n1"}})]


def test_an_invalid_setting_reads_as_classics_verdict(env):
    env.v1.answers["jobs.validate"] = {
        "valid": False,
        "errors": [{"code": "unknown_field", "pointer": "/settings/old_name", "detail": "Use oldName.", "suggestion": "oldName"}],
    }
    res = env.run("v1", "--json", "validate", "boltz", "--set", "old_name=1", "--name", "n1")
    assert res.exit_code == 5
    assert json.loads(res.stdout) == {
        "valid": False, "error": "Use oldName.",
        "errors": [{"rule": "unknown_field", "field": "old_name", "message": "Use oldName.", "suggestion": "oldName"}],
        "unrecognized_settings": ["old_name"],
    }


def test_submit_validates_and_submits_on_v1(env):
    FakeClassic.answers["validate-job"] = {"valid": True}
    FakeClassic.answers["submit-job"] = "n1 submitted to queue."
    env.v1.answers["jobs.validate"] = {"valid": True, "name": "n1"}
    env.v1.answers["jobs.submit"] = {"id": JOB}
    same_output(env, "--json", "submit", "esmfold", "--set", "sequence=MK", "--name", "n1")
    assert [c[0] for c in env.v1.calls] == ["jobs.validate", "jobs.submit"]
    assert env.v1.calls[1][2]["body"] == {"kind": "job", "tool": "esmfold", "name": "n1", "settings": {"sequence": "MK"}}


def test_low_priority_submit_keeps_classics_wording(env):
    FakeClassic.answers["submit-job"] = "n1 submitted to queue" + classic.LOW_PRIORITY_SUFFIX + "."
    env.v1.answers["jobs.submit"] = {"id": JOB}
    same_output(env, "--json", "submit", "esmfold", "--skip-validate", "--low-priority", "--set", "sequence=MK", "--name", "n1")
    assert env.v1.calls[0][2]["body"]["lowPriority"] is True


def test_a_name_already_used_reads_as_classic_words_it(env):
    FakeClassic.answers["submit-job"] = ValidationError("jobName n1 already exists, please choose a different name")
    env.v1.answers["jobs.submit"] = problem(409, "job_name_conflict")
    classic = env.run("classic", "--json", "submit", "esmfold", "--skip-validate", "--set", "sequence=MK", "--name", "n1")
    FakeClassic.calls = []
    v1 = env.run("v1", "--json", "submit", "esmfold", "--skip-validate", "--set", "sequence=MK", "--name", "n1")
    assert (type(classic.exception), str(classic.exception)) == (type(v1.exception), str(v1.exception))
    assert classic_calls() == []


def test_batch_submits_on_v1_with_classics_answer(env, tmp_path):
    rows = tmp_path / "rows.json"
    rows.write_text(json.dumps([{"sequence": "MK"}, {"sequence": "MKT"}]))
    FakeClassic.answers["submit-batch"] = "b1 batch submitted to queue."
    env.v1.answers["jobs.submit"] = {"id": BATCH}
    same_output(env, "--json", "batch", "esmfold", "--input", str(rows), "--name", "b1", "--max-runtime", "600")
    assert env.v1.calls[0][2]["body"] == {
        "kind": "batch", "tool": "esmfold", "name": "b1",
        "settings": [{"sequence": "MK"}, {"sequence": "MKT"}], "maxRuntimeSeconds": 600,
    }


def _rows(tmp_path, rows):
    path = tmp_path / "rows.json"
    path.write_text(json.dumps(rows))
    return str(path)


def _report(count, results=(), *, errors=(), truncated=False):
    """validateJob's BatchValidationReport: `results` lists only the rows with an error
    or a warning, their pointers into the row (`/settings/1/x`)."""
    results = list(results)
    return {
        "valid": not errors and all(r["valid"] for r in results),
        "count": count,
        "validCount": 0 if errors else count - sum(1 for r in results if not r["valid"]),
        "errors": list(errors),
        "results": results,
        "resultsTruncated": truncated,
    }


BAD_ROW = {
    "index": 1, "valid": False, "warnings": [],
    "errors": [{"code": "unknown_field", "pointer": "/settings/1/nonsense", "detail": "Unrecognized nonsense."}],
}


def test_prevalidate_passes_a_batch_v1_lists_no_rows_of(env, tmp_path):
    rows = _rows(tmp_path, [{"sequence": "MK"}, {"sequence": "MKT"}])
    env.v1.answers["jobs.validate"] = _report(2)
    env.v1.answers["jobs.submit"] = {"id": BATCH}
    res = env.run("v1", "--json", "batch", "esmfold", "--input", rows, "--name", "b1", "--prevalidate")
    assert res.exit_code == 0, res.output
    assert [c[0] for c in env.v1.calls] == ["jobs.validate", "jobs.submit"]


def test_prevalidate_reads_v1s_row_verdicts(env, tmp_path):
    rows = _rows(tmp_path, [{"sequence": "MK"}, {"nonsense": 1}])
    env.v1.answers["jobs.validate"] = _report(2, [BAD_ROW])
    res = env.run("v1", "--json", "batch", "esmfold", "--input", rows, "--name", "b1", "--prevalidate")
    assert isinstance(res.exception, ValidationError)
    assert str(res.exception) == "Batch item 2 settings invalid: Unrecognized nonsense."
    verdict = res.exception.detail["validation"]
    assert verdict["unrecognized_settings"] == ["nonsense"] and verdict["errors"][0]["field"] == "nonsense"
    assert env.v1.calls[0][2]["body"]["kind"] == "batch" and [c[0] for c in env.v1.calls] == ["jobs.validate"]


def test_prevalidate_refuses_rows_a_truncated_report_left_out(env, tmp_path):
    rows = _rows(tmp_path, [{"sequence": "MK"}, {"nonsense": 1}, {"sequence": "MKT"}])
    env.v1.answers["jobs.validate"] = _report(3, [BAD_ROW], truncated=True)
    res = env.run("v1", "--json", "batch", "esmfold", "--input", rows, "--name", "b1", "--prevalidate")
    assert isinstance(res.exception, ValidationError)
    assert str(res.exception).startswith("Batch validation answered for 1 of 3 rows")
    assert [c[0] for c in env.v1.calls] == ["jobs.validate"]


def test_prevalidate_refuses_a_batch_v1_refuses_as_a_whole(env, tmp_path):
    rows = _rows(tmp_path, [{"sequence": "MK"}])
    env.v1.answers["jobs.validate"] = _report(1, errors=[{"code": "quota_exceeded", "detail": "Over your monthly limit."}])
    res = env.run("v1", "--json", "batch", "esmfold", "--input", rows, "--name", "b1", "--prevalidate")
    assert isinstance(res.exception, ValidationError)
    assert str(res.exception) == "Batch validation was refused: Over your monthly limit."
    assert [c[0] for c in env.v1.calls] == ["jobs.validate"]


# -- v1's refusals are v1's -------------------------------------------------------------


WRITES = {
    "submit": (["submit", "esmfold", "--skip-validate", "--set", "sequence=MK", "--name", "n1"], {}, "jobs.submit"),
    "delete": (["delete", "n1", "--yes"], {"jobs.list": _found()}, "jobs.delete"),
    "cancel": (["cancel", "n1"], {"jobs.list": _found()}, "jobs.cancel"),
    "files delete": (["files", "delete", "a.pdb", "--yes"], {}, "files.delete"),
    "files upload": (None, {}, "files.upload"),
}


@pytest.mark.parametrize("command", sorted(WRITES))
@pytest.mark.parametrize(
    "status, code, exit_code",
    [(400, "bad_request", 5), (401, "invalid_api_key", 3), (403, "budget_exceeded", 8), (404, "not_found", 4),
     (409, "conflict", 1), (422, "unknown_field", 5), (429, "rate_limited", 6)],
)
def test_v1_refusals_are_raised_never_sent_to_classic(env, tmp_path, monkeypatch, command, status, code, exit_code):
    args, answers, method = WRITES[command]
    if args is None:
        local = tmp_path / "in.fasta"
        local.write_bytes(b">a\nMK\n")
        args = ["files", "upload", str(local)]
    env.v1.answers.update(answers)
    env.v1.answers[method] = problem(status, code)
    res = env.run("v1", "--json", *args)
    assert classic_calls() == []
    assert isinstance(res.exception, ProblemError) and res.exception.exit_code == exit_code


def test_a_submit_still_in_progress_is_an_unclear_outcome(env):
    env.v1.answers["jobs.submit"] = problem(409, "idempotency_in_progress")
    res = env.run("v1", "--json", "submit", "esmfold", "--skip-validate", "--set", "sequence=MK", "--name", "n1")
    assert classic_calls() == [] and res.exception.detail["outcomeMayBeAmbiguous"] is True


@pytest.mark.parametrize("failure", [problem(503, "service_unavailable"), TamarindError("Network error")])
def test_a_submit_with_no_clear_answer_is_not_sent_again(env, failure):
    env.v1.answers["jobs.submit"] = failure
    res = env.run("v1", "--json", "submit", "esmfold", "--skip-validate", "--set", "sequence=MK", "--name", "n1")
    assert classic_calls() == []
    assert res.exception.detail["outcomeMayBeAmbiguous"] is True
    if isinstance(failure, ProblemError):
        assert isinstance(res.exception, APIError) and res.exception.status_code == 503


# -- cancel ---------------------------------------------------------------------------


def test_cancel_a_job(env):
    env.v1.answers["jobs.list"] = _found(tool="esmfold", createdBy="a@b")
    env.v1.answers["jobs.cancel"] = {**V1_JOB, "status": "Stopped", "createdBy": "a@b"}
    out = json.loads(env.run("v1", "--json", "cancel", "n1").stdout)
    assert out == {
        "success": True, "message": "Job cancelled successfully", "jobId": JOB[4:],
        "cancelledJobs": [{"Id": JOB[4:], "Created": "2026-11-19 05:27:02", "JobName": "n1", "Type": "esmfold", "User": "a@b"}],
        "status": "Stopped",
    }


@pytest.mark.parametrize("args, cascaded", [(["cancel", "n1"], True), (["cancel", "--batch", "n1"], False)])
def test_cancel_a_batch_counts_what_was_live(env, args, cascaded):
    env.v1.answers["jobs.list"] = lambda **kw: _found("batch", BATCH) if kw.get("kind") in (None, "batch") else _page()
    env.v1.answers["jobs.get"] = {"kind": "batch", "id": BATCH, "status": "Running", "counts": {"total": 5, "inQueue": 2, "running": 1}}
    env.v1.answers["jobs.cancel"] = {"kind": "batch", "id": BATCH, "status": "Stopped"}
    out = json.loads(env.run("v1", "--json", *args).stdout)
    assert out["message"] == 'Cancelled 4 jobs in batch "n1"'
    assert (out["cancelledCount"], out["totalChildren"], out["cancellableChildren"], out["parentCancelled"]) == (4, 5, 3, True)
    assert out.get("cascaded", False) is cascaded


def _sdk_client() -> HTTPClient:
    return HTTPClient("https://app.tamarind.bio/api", "test-key")


def test_cancel_by_row_id_is_v1s_cancel_of_job_id(env):
    from tamarind import rest

    env.v1.answers["jobs.cancel"] = {**V1_JOB, "status": "Stopped", "createdBy": "a@b"}
    with _sdk_client() as client:
        out = rest.cancel_job(client, job_id=JOB[4:], job_name="ignored")  # classic: the id wins
    assert env.v1.calls == [("jobs.cancel", (JOB,), {"body": {}})] and classic_calls() == []
    assert out["jobId"] == JOB[4:] and out["cancelledJobs"][0]["JobName"] == "n1" and out["status"] == "Stopped"


def test_cancel_by_a_batch_rows_id_cancels_the_batch(env):
    from tamarind import rest

    def cancel(item_id: str, **kw: Any) -> Any:
        if item_id == JOB:
            raise problem(404, "not_found")
        return {"kind": "batch", "id": BATCH, "status": "Stopped"}

    env.v1.answers["jobs.cancel"] = cancel
    env.v1.answers["jobs.get"] = {"kind": "batch", "id": BATCH, "name": "b1", "status": "Running", "counts": {"total": 2, "running": 2}}
    with _sdk_client() as client:
        out = rest.cancel_job(client, job_id=JOB[4:])
    assert out["message"] == 'Cancelled 3 jobs in batch "b1"' and out["cascaded"] is True
    assert [c[:2] for c in env.v1.calls] == [("jobs.cancel", (JOB,)), ("jobs.get", (BATCH,)), ("jobs.cancel", (BATCH,))]


def test_cancel_by_an_unknown_row_id_is_classics_not_found(env):
    from tamarind import rest

    env.v1.answers["jobs.cancel"] = problem(404, "not_found")
    env.v1.answers["jobs.get"] = problem(404, "not_found")
    with _sdk_client() as client, pytest.raises(NotFoundError, match='Job with Id "abc" not found'):
        rest.cancel_job(client, job_id="abc")


def test_cancel_batch_of_an_unknown_name_is_classics_not_found(env):
    env.v1.answers["jobs.list"] = _page()
    res = env.run("v1", "--json", "cancel", "--batch", "nope")
    assert isinstance(res.exception, NotFoundError) and 'No batch or pipeline named "nope"' in str(res.exception)


# -- results, delete --------------------------------------------------------------------


@pytest.mark.parametrize("flag", ["--show-url", "--download"])
def test_results_come_from_the_v1_archive(env, tmp_path, monkeypatch, flag):
    monkeypatch.setattr("tamarind.cli.commands.jobs._download", lambda url, dest: 42)
    FakeClassic.answers["result"] = SIGNED
    env.v1.answers["jobs.list"] = _found()
    env.v1.answers["jobs.archive"] = {"status": "ready", "downloadUrl": SIGNED}
    same_output(env, "--json", "results", "n1", *([flag, str(tmp_path)] if flag == "--download" else [flag]))
    assert env.v1.calls[-1] == ("jobs.archive", (JOB,), {"body": {}})


def test_results_file_comes_from_get_job_file(env, tmp_path, monkeypatch):
    monkeypatch.setattr("tamarind.cli.commands.jobs._download", lambda url, dest: 3)
    FakeClassic.answers["result"] = SIGNED
    env.v1.answers["jobs.list"] = _found()
    env.v1.answers["jobs.get_file"] = {"url": SIGNED, "sizeBytes": 3}
    same_output(env, "--json", "results", "n1", "--file", "out/a.pdb", "--download", str(tmp_path))
    assert env.v1.calls[-1] == ("jobs.get_file", (JOB,), {"path": "out/a.pdb", "delivery": "url"})


def test_results_of_a_members_job_come_from_their_archive(env):
    FakeClassic.answers["result"] = SIGNED
    FakeClassic.answers["jobs"] = {**CLASSIC_ROW, "User": PEER, "statuses": STATUSES_ONE}
    env.v1.answers["jobs.list"] = _found(createdBy=PEER)
    env.v1.answers["jobs.get"] = {**V1_JOB, "createdBy": PEER}
    env.v1.answers["jobs.archive"] = {"status": "ready", "downloadUrl": SIGNED}
    same_output(env, "--json", "results", "n1", "--show-url", "--email", PEER)
    # The owner is read from the job's row, as classic's /result needs it; the lookup is kept.
    assert [c for c in env.v1.calls if c[0] == "jobs.list"] == [
        ("jobs.list", (), {"name": "n1", "scope": "org", "created_by": PEER})
    ]
    assert env.v1.calls[-1] == ("jobs.archive", (JOB,), {"body": {}})
    assert ("POST", "result", {"jobName": "n1", "jobEmail": PEER}) in classic_calls()


def test_results_file_of_a_members_job_comes_from_get_job_file(env):
    env.v1.answers["jobs.list"] = _found(createdBy=PEER)
    env.v1.answers["jobs.get"] = {**V1_JOB, "createdBy": PEER}
    env.v1.answers["jobs.get_file"] = {"url": SIGNED}
    out = json.loads(env.run("v1", "--json", "results", "n1", "--file", "a.pdb", "--show-url", "--email", PEER).stdout)
    assert out["url"] == SIGNED and env.v1.calls[-1] == ("jobs.get_file", (JOB,), {"path": "a.pdb", "delivery": "url"})


@pytest.mark.parametrize("kind, item_id", [("job", JOB), ("batch", BATCH)])
def test_results_pdbs_only_are_v1s_best_structures(env, kind, item_id):
    FakeClassic.answers["result"] = SIGNED
    env.v1.answers["jobs.list"] = _found(kind, item_id)
    env.v1.answers["jobs.archive"] = {"status": "ready", "downloadUrl": SIGNED}
    same_output(env, "--json", "results", "n1", "--show-url", "--pdbs-only")
    assert env.v1.calls[-1] == ("jobs.archive", (item_id,), {"body": {"bestStructures": True}})


def test_results_pdbs_only_of_a_job_with_none_reads_as_classic_words_it(env):
    FakeClassic.answers["result"] = ValidationError(classic.NO_BEST_STRUCTURES)
    env.v1.answers["jobs.list"] = _found()
    refusal = problem(422, "validation_failed")
    refusal.errors = [{"pointer": "/bestStructures", "code": "not_supported", "detail": "no stored zip"}]
    env.v1.answers["jobs.archive"] = refusal
    res = same_output(env, "--json", "results", "n1", "--show-url", "--pdbs-only")
    assert isinstance(res.exception, ValidationError) and res.exception.exit_code == 5 and classic.NO_BEST_STRUCTURES in str(res.exception)


def test_results_pdbs_only_waits_for_v1_to_build_a_batchs_zip(env, sleeps):
    # Classic's answer is the zip it builds while you wait; v1 builds it in the background.
    env.v1.answers["jobs.list"] = _found("batch", BATCH)
    env.v1.answers["jobs.get"] = {"kind": "batch", "id": BATCH, "status": "Complete"}
    answers = iter([{"status": "preparing", "retryAfterSeconds": 10}, {"status": "ready", "downloadUrl": SIGNED}])
    env.v1.answers["jobs.archive"] = lambda *a, **k: next(answers)
    out = json.loads(env.run("v1", "--json", "results", "n1", "--show-url", "--pdbs-only").stdout)
    assert out["url"] == SIGNED and sleeps == [10.0]


def test_results_pdbs_only_stops_waiting_for_a_build_after_its_limit(env, monkeypatch):
    now, slept = [0.0], []

    def sleep(seconds: float) -> None:
        slept.append(seconds)
        now[0] += seconds

    monkeypatch.setattr(classic.time, "monotonic", lambda: now[0])
    monkeypatch.setattr(classic.time, "sleep", sleep)
    env.v1.answers["jobs.list"] = _found("batch", BATCH)
    env.v1.answers["jobs.get"] = {"kind": "batch", "id": BATCH, "status": "Complete"}
    env.v1.answers["jobs.archive"] = {"status": "preparing", "retryAfterSeconds": 10}
    monkeypatch.setattr(classic, "BEST_BUILD_SECONDS", 25.0)
    res = env.run("v1", "--json", "results", "n1", "--show-url", "--pdbs-only")
    assert type(res.exception) is TamarindError and "weren't ready after 25 s" in str(res.exception) and slept == [10.0, 10.0]


def test_results_pdbs_only_of_a_pipeline_run_stays_on_classic(env):
    FakeClassic.answers["result"] = SIGNED
    env.v1.answers["jobs.list"] = _found("pipeline", "run_1")
    res = env.run("v1", "--json", "results", "n1", "--show-url", "--pdbs-only")
    assert res.exit_code == 0 and ("POST", "result") in [c[:2] for c in classic_calls()]
    assert "jobs.archive" not in [c[0] for c in env.v1.calls]


@pytest.mark.parametrize(
    "archive, status, message",
    [
        (problem(409, "archive_failed"), "Stopped", "Job n1 is not complete. Status: Stopped"),
        ({"status": "preparing", "retryAfterSeconds": 5}, "Running", "Job n1 is not complete. Status: Running"),
    ],
)
def test_results_of_an_unfinished_job_read_as_classic_words_them(env, archive, status, message):
    env.v1.answers["jobs.list"] = _found(status=status)
    env.v1.answers["jobs.archive"] = archive
    env.v1.answers["jobs.get"] = {**V1_JOB, "status": status}
    res = env.run("v1", "--json", "results", "n1", "--show-url")
    assert isinstance(res.exception, ValidationError) and str(res.exception) == message and classic_calls() == []


RUN = "run_0f8fad5b-d9cb-469f-a165-70867728950e"
READY = {"status": "ready", "downloadUrl": SIGNED}


def test_results_of_a_pipeline_run_come_from_archive_pipeline_run(env):
    env.v1.answers["jobs.list"] = _found("pipeline", RUN, status="Complete")
    env.v1.answers["pipelines.archive_run"] = READY
    res = env.run("v1", "--json", "results", "n1", "--show-url")
    assert res.exit_code == 0, res.output
    assert json.loads(res.stdout)["url"] == SIGNED
    assert ("pipelines.archive_run", (RUN,), {"body": {}}) in env.v1.calls
    assert "jobs.archive" not in [c[0] for c in env.v1.calls]


def _preparing_then_ready(times: int):
    answers = [{"status": "preparing", "retryAfterSeconds": 10}] * times + [READY]
    return lambda *a, **k: answers.pop(0)


@pytest.fixture
def sleeps(monkeypatch):
    slept: list[float] = []
    monkeypatch.setattr(classic.time, "sleep", slept.append)
    return slept


def test_results_wait_asks_again_while_a_complete_batchs_archive_is_preparing(env, sleeps):
    env.v1.answers["jobs.list"] = _found("batch", BATCH, status="Complete")
    env.v1.answers["jobs.get"] = {"kind": "batch", "id": BATCH, "name": "n1", "status": "Complete"}
    env.v1.answers["jobs.archive"] = _preparing_then_ready(2)
    res = env.run("v1", "--json", "results", "n1", "--wait", "--poll-interval", "1", "--show-url")
    assert res.exit_code == 0, res.output
    assert json.loads(res.stdout)["url"] == SIGNED and sleeps == [10.0, 10.0]


def test_results_without_wait_says_the_archive_is_preparing(env, sleeps):
    env.v1.answers["jobs.list"] = _found("batch", BATCH, status="Complete")
    env.v1.answers["jobs.get"] = {"kind": "batch", "id": BATCH, "name": "n1", "status": "Complete"}
    env.v1.answers["jobs.archive"] = _preparing_then_ready(1)
    res = env.run("v1", "--json", "results", "n1", "--show-url")
    assert type(res.exception) is TamarindError and "still being prepared" in str(res.exception)
    assert sleeps == []


def test_results_wait_stops_at_its_timeout(env, sleeps):
    env.v1.answers["jobs.list"] = _found("batch", BATCH, status="Complete")
    env.v1.answers["jobs.get"] = {"kind": "batch", "id": BATCH, "name": "n1", "status": "Complete"}
    env.v1.answers["jobs.archive"] = _preparing_then_ready(5)
    res = env.run("v1", "--json", "results", "n1", "--wait", "--poll-interval", "1", "--timeout", "5", "--show-url")
    assert isinstance(res.exception, JobTimeoutError) and sleeps == []


def test_results_wait_counts_its_timeout_from_the_commands_start(env, sleeps, monkeypatch):
    clock = iter([0.0])  # the command starts at 0; everything after reads 12 s later
    monkeypatch.setattr(classic.time, "monotonic", lambda: next(clock, 12.0))
    env.v1.answers["jobs.list"] = _found("batch", BATCH, status="Complete")
    env.v1.answers["jobs.get"] = {"kind": "batch", "id": BATCH, "name": "n1", "status": "Complete"}
    env.v1.answers["jobs.archive"] = _preparing_then_ready(1)
    res = env.run("v1", "--json", "results", "n1", "--wait", "--poll-interval", "1", "--timeout", "15", "--show-url")
    assert isinstance(res.exception, JobTimeoutError) and sleeps == []  # 12 + 10 > 15


def test_a_waits_status_request_is_one_try_bounded_by_its_deadline(env, monkeypatch):
    made: list[dict[str, Any]] = []
    turn_v1_on(monkeypatch, factory=lambda http, **options: (made.append(options), env.v1)[1])
    env.v1.answers["jobs.list"] = _found()
    env.v1.answers["jobs.get"] = V1_JOB
    res = env.run("v1", "--json", "wait", "n1", "--timeout", "30", "--poll-interval", "1")
    assert res.exit_code == 0, res.output
    bounded = [o for o in made if o]
    assert bounded and all(o["max_retries"] == 0 and 0 < o["timeout"] <= 30 for o in bounded)


def test_results_wait_bounds_each_archive_request_by_what_is_left(env, monkeypatch):
    made: list[dict[str, Any]] = []
    turn_v1_on(monkeypatch, factory=lambda http, **options: (made.append(options), env.v1)[1])
    seen: list[dict[str, Any]] = []
    env.v1.answers["jobs.list"] = _found()
    env.v1.answers["jobs.get"] = V1_JOB
    env.v1.answers["jobs.archive"] = lambda *a, **k: (seen.append(made[-1]), READY)[1]
    res = env.run("v1", "--json", "results", "n1", "--wait", "--poll-interval", "1", "--timeout", "30", "--show-url")
    assert res.exit_code == 0, res.output
    assert seen and seen[0]["max_retries"] == 0 and 0 < seen[0]["timeout"] <= 30


def _archive_failed(retry_after: str = "90") -> ProblemError:
    return ProblemError(
        status=409, code="archive_failed", title="Conflict", detail="The archive could not be built.",
        headers=httpx.Headers({"Retry-After": retry_after}),
    )


def test_results_wait_asks_a_pipeline_run_to_rebuild_its_archive(env, sleeps):
    answers = [_archive_failed(), READY]

    def archive_run(*a, **k):
        answer = answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer

    env.v1.answers["jobs.list"] = _found("pipeline", RUN, status="Complete")
    env.v1.answers["jobs.get"] = {"kind": "pipeline", "id": RUN, "name": "n1", "status": "Complete"}
    env.v1.answers["pipelines.archive_run"] = archive_run
    res = env.run("v1", "--json", "results", "n1", "--wait", "--poll-interval", "1", "--show-url")
    assert res.exit_code == 0, res.output
    assert json.loads(res.stdout)["url"] == SIGNED and sleeps == [90.0]


def test_results_wait_stops_asking_for_a_rebuild_after_three_tries(env, sleeps):
    env.v1.answers["jobs.list"] = _found("pipeline", RUN, status="Complete")
    env.v1.answers["jobs.get"] = {"kind": "pipeline", "id": RUN, "name": "n1", "status": "Complete"}
    env.v1.answers["pipelines.archive_run"] = _archive_failed("5")
    res = env.run("v1", "--json", "results", "n1", "--wait", "--poll-interval", "1", "--show-url")
    assert isinstance(res.exception, ProblemError) and res.exception.code == "archive_failed"
    assert sleeps == [5.0, 5.0, 5.0]


def test_results_without_wait_reports_a_runs_failed_archive(env, sleeps):
    env.v1.answers["jobs.list"] = _found("pipeline", RUN, status="Complete")
    env.v1.answers["pipelines.archive_run"] = _archive_failed()
    res = env.run("v1", "--json", "results", "n1", "--show-url")
    assert isinstance(res.exception, ProblemError) and sleeps == []


def test_results_file_of_a_pipeline_run_stays_on_classic(env):
    FakeClassic.answers["result"] = SIGNED
    env.v1.answers["jobs.list"] = _found("pipeline", RUN, status="Complete")
    res = env.run("v1", "--json", "results", "n1", "--file", "out/a.pdb", "--show-url")
    assert res.exit_code == 0, res.output
    assert ("POST", "result") in [c[:2] for c in classic_calls()]
    assert "jobs.get_file" not in [c[0] for c in env.v1.calls]


def _by_kind(**pages: dict[str, Any]):
    return lambda **query: pages.get(query.get("kind") or "any", _page())


def test_delete_resolves_a_name_among_jobs_and_batches(env):
    newer_run = {"id": RUN, "kind": "pipeline", "name": "n1", "createdAt": "2026-11-19T06:00:00Z"}
    env.v1.answers["jobs.list"] = _by_kind(job=_found(), any=_page(newer_run))
    env.v1.answers["jobs.delete"] = None
    res = env.run("v1", "--json", "delete", "n1", "--yes")
    assert res.exit_code == 0, res.output
    assert ("jobs.delete", (JOB,), {}) in env.v1.calls
    assert [c[2].get("kind") for c in env.v1.calls if c[0] == "jobs.list"] == ["job", "batch"]


def test_delete_of_a_name_only_a_run_has_stays_on_classic(env):
    FakeClassic.answers["delete-job"] = "n1 deleted"
    env.v1.answers["jobs.list"] = _by_kind(any=_found("pipeline", RUN))
    res = env.run("v1", "--json", "delete", "n1", "--yes")
    assert res.exit_code == 0, res.output
    assert ("DELETE", "delete-job") in [c[:2] for c in classic_calls()]
    assert "jobs.delete" not in [c[0] for c in env.v1.calls]


def test_delete_job_goes_to_v1(env):
    FakeClassic.answers["delete-job"] = "n1 deleted"
    env.v1.answers["jobs.list"] = _found("batch", BATCH)
    env.v1.answers["jobs.delete"] = None
    same_output(env, "--json", "delete", "n1", "--yes")
    assert ("jobs.delete", (BATCH,), {}) in env.v1.calls


def test_delete_of_a_missing_job_reads_as_classic_words_it(env):
    FakeClassic.answers["delete-job"] = NotFoundError("n1 does not exist")
    env.v1.answers["jobs.list"] = _page()
    classic = env.run("classic", "--json", "delete", "n1", "--yes")
    v1 = env.run("v1", "--json", "delete", "n1", "--yes")
    assert (type(classic.exception), str(classic.exception)) == (type(v1.exception), str(v1.exception))


# -- logs -----------------------------------------------------------------------------


LOG = "line 1\nline 2\nline 3\n"


# What classic's getJobLogs (mcp-server _log_page) answers for LOG: it splits on newlines,
# so the final newline ends in an empty line, which counts.
CLASSIC_TAILS = {
    "2": {
        "jobName": "n1", "logLines": 2, "truncated": True, "totalLines": 4, "totalBytes": 21,
        "startByte": 14, "endByte": 21, "olderBeforeByte": 14, "log": "line 3\n",
    },
    "500": {
        "jobName": "n1", "logLines": 4, "truncated": False, "totalLines": 4, "totalBytes": 21,
        "startByte": 0, "endByte": 21, "olderBeforeByte": None, "log": LOG,
    },
    "0": {
        "jobName": "n1", "logLines": 0, "truncated": True, "totalLines": 4, "totalBytes": 21,
        "startByte": 21, "endByte": 21, "olderBeforeByte": 21, "log": "",
    },
}


@pytest.mark.parametrize("max_lines", sorted(CLASSIC_TAILS))
def test_logs_are_v1s_in_classics_tail(env, max_lines):
    FakeClassic.answers["catalog/jobs/n1/logs"] = CLASSIC_TAILS[max_lines]
    env.v1.answers["jobs.list"] = _found()
    env.v1.answers["jobs.logs"] = {"content": LOG, "nextCursor": None, "complete": True}
    same_output(env, "--json", "logs", "n1", "--max-lines", max_lines)
    same_output(env, "--no-json", "logs", "n1", "--max-lines", max_lines)
    assert env.v1.calls[-1] == ("jobs.logs", (JOB,), {"max_bytes": 256 * 1024})


def test_a_log_with_older_output_has_no_offsets(env):
    env.v1.answers["jobs.list"] = _found()
    env.v1.answers["jobs.logs"] = {"content": LOG, "nextCursor": "older", "complete": False}
    res = env.run("v1", "--json", "logs", "n1", "--max-lines", "500")
    assert res.exit_code == 0, res.output
    out = json.loads(res.stdout)
    assert out["log"] == LOG and out["logLines"] == 4 and out["truncated"] is True
    assert [out[k] for k in ("totalLines", "totalBytes", "startByte", "endByte", "olderBeforeByte")] == [None] * 5


def test_logs_of_an_unknown_job_are_not_found(env):
    env.v1.answers["jobs.list"] = _page()
    res = env.run("v1", "--json", "logs", "nope")
    assert isinstance(res.exception, NotFoundError)


def test_the_catalog_stays_on_the_catalog(env):
    FakeClassic.answers["catalog/tools"] = {"tools": [], "totalTools": 0}
    res = env.run("v1", "--json", "tools")
    assert res.exit_code == 0 and env.v1.calls == []


# -- files ------------------------------------------------------------------------------


ENTRIES = [
    {"path": "b.pdb", "type": "file", "modifiedAt": "2026-11-02T00:00:00Z"},  # newer than A, listed after it
    {"path": "runs", "type": "folder", "modifiedAt": None},
    {"path": "A.pdb", "type": "file", "modifiedAt": "2026-11-01T00:00:00Z"},
    {"path": "old.zip", "type": "file", "modifiedAt": "2026-11-09T00:00:00Z"},
    *({"path": f"n{i}.fasta", "type": "file", "modifiedAt": f"2026-11-1{i}T00:00:00Z"} for i in range(5)),
]
CLASSIC_FILES = ["n4.fasta", "n3.fasta", "n2.fasta", "n1.fasta", "n0.fasta", "A.pdb", "b.pdb"]


def test_files_list_is_v1s_listing_in_classics_order(env):
    FakeClassic.answers["files"] = CLASSIC_FILES
    env.v1.answers["files.list"] = _page(*ENTRIES)
    same_output(env, "--json", "files", "list")
    same_output(env, "--no-json", "files", "list", "--types", "pdb")
    same_output(env, "--json", "files", "stats")


def test_files_list_in_a_folder(env):
    env.v1.answers["files.list"] = _page({"path": "runs/x.pdb", "type": "file"})
    out = json.loads(env.run("v1", "--json", "files", "list", "--folder", "runs").stdout)
    assert out["files"] == ["runs/x.pdb"] and env.v1.calls[-1][2]["folder"] == "runs"


def test_files_folders_are_v1s_folder_page(env):
    FakeClassic.answers["getFolders"] = {
        "folders": ["runs", "0f8fad5b"], "labels": {"0f8fad5b": "n1"}, "hasMore": True, "nextCursor": "c2",
    }
    env.v1.answers["files.list"] = _page(
        {"path": "runs", "type": "folder", "jobName": None},
        {"path": "0f8fad5b", "type": "folder", "jobName": "n1"},
        cursor="c2",
    )
    same_output(env, "--json", "files", "folders", "--limit", "2")
    same_output(env, "--no-json", "files", "folders", "--limit", "2")
    assert env.v1.calls[-1] == ("files.list", (), {"type_": "folder", "limit": 2})


def test_files_folders_of_a_last_page_have_no_labels_or_cursor(env):
    env.v1.answers["files.list"] = _page({"path": "n1", "type": "folder", "jobName": "n1"})
    out = json.loads(env.run("v1", "--json", "files", "folders").stdout)
    assert out == {"folders": ["n1"], "hasMore": False, "nextCursor": None}
    assert env.v1.calls[-1] == ("files.list", (), {"type_": "folder", "limit": 50})


@pytest.mark.parametrize(
    "args, message",
    [(["--all"], "Use cursor pagination"), (["--limit", "101"], "limit must be an integer between 1 and 100")],
)
def test_files_folders_refuse_what_classic_refuses(env, args, message):
    FakeClassic.answers["getFolders"] = ValidationError(message)
    res = same_output(env, "--json", "files", "folders", *args)
    assert isinstance(res.exception, ValidationError) and res.exception.exit_code == 5 and message in str(res.exception) and env.v1.calls == []


@pytest.mark.parametrize(
    "args, message, call",
    [
        (["a/b.pdb"], "File deleted successfully", {"path": "a/b.pdb"}),
        (["--folder", "runs"], "Folder deleted successfully", {"folder": "runs"}),
    ],
)
def test_files_delete_goes_to_v1(env, args, message, call):
    FakeClassic.answers["delete-file"] = {"message": message}
    env.v1.answers["files.delete"] = None
    same_output(env, "--json", "files", "delete", *args, "--yes")
    assert env.v1.calls == [("files.delete", (), call)]


def test_files_delete_of_a_file_and_a_folder_is_v1s_refusal(env):
    # Classic deletes the folder and ignores the path; v1 takes one of the two, and
    # refuses both with nothing deleted.
    env.v1.answers["files.delete"] = problem(422, "validation_failed")
    res = env.run("v1", "--json", "files", "delete", "a.pdb", "--folder", "runs", "--yes")
    assert isinstance(res.exception, ValidationError) and res.exception.exit_code == 5 and classic_calls() == []
    assert env.v1.calls == [("files.delete", (), {"path": "a.pdb", "folder": "runs"})]


def test_files_upload_goes_to_v1(env, tmp_path, monkeypatch):
    local = tmp_path / "in.fasta"
    local.write_bytes(b">a\nMK\n")
    FakeClassic.answers["getPresignedUploadUrl"] = {"uploadUrl": "https://bucket.s3.amazonaws.com/in.fasta?sig=1"}
    monkeypatch.setattr("tamarind.uploads.put_presigned_upload", lambda url, path, **k: Path(path).stat().st_size)
    env.v1.answers["files.upload"] = {"path": "in.fasta", "type": "file", "sizeBytes": 6}
    same_output(env, "--json", "files", "upload", str(local))
    assert env.v1.calls[0] == ("files.upload", (local,), {"path": "in.fasta", "content_type": "application/octet-stream"})
    assert [c[1] for c in classic_calls()] == ["getPresignedUploadUrl"]  # the classic run only


# -- auth -----------------------------------------------------------------------------


def test_auth_status_checks_the_key_on_v1_and_prints_classics_fields(env):
    # The key check is classic's own (one job listing); with v1 on, v1 answers it.
    FakeClassic.answers["jobs"] = {"jobs": [], "statuses": {}}
    env.v1.answers["jobs.list"] = _page()
    res = same_output(env, "--json", "auth", "status")
    assert json.loads(res.stdout) == {"profile": "default", "hasKey": True, "verified": True}
    assert ("jobs.list", (), {"limit": 1}) in env.v1.calls


def test_a_key_v1_refuses_is_not_verified(env):
    FakeClassic.answers["jobs"] = AuthError("Unauthorized: Invalid API key")
    env.v1.answers["jobs.list"] = problem(401, "invalid_api_key")
    res = same_output(env, "--json", "auth", "status")
    assert json.loads(res.stdout)["verified"] is False


def test_any_other_answer_to_the_key_check_is_v1s_error(env):
    env.v1.answers["jobs.list"] = problem(503, "service_unavailable")
    res = env.run("v1", "--json", "auth", "status")
    assert isinstance(res.exception, ProblemError) and isinstance(res.exception, APIError)
    assert classic_calls() == []


def test_without_a_key_classic_says_so(env, monkeypatch):
    monkeypatch.delenv("TAMARIND_API_KEY")
    classic = env.run("classic", "--json", "delete", "n1", "--yes")
    v1 = env.run("v1", "--json", "delete", "n1", "--yes")
    assert (type(classic.exception), str(classic.exception)) == (type(v1.exception), str(v1.exception))
    assert isinstance(v1.exception, AuthError) and env.v1.calls == []


# -- jobs and tools: today's flat commands, contract commands beside them with v1 --------


def test_jobs_with_v1_is_todays_listing_unless_a_contract_command_follows(env):
    env.v1.answers["jobs.list"] = _page()
    env.run("v1", "--json", "jobs", "--limit", "3")
    assert env.v1.calls[-1] == ("jobs.list", (), {"limit": 3})
    res = env.run("v1", "--json", "jobs", "list", "--kind", "batch")
    assert res.exit_code == 0 and env.v1.calls[-1] == ("jobs.list", (), {"kind": "batch"})
    # classic keeps today's answer to an extra argument
    assert env.run("classic", "--json", "jobs", "list").exit_code == 2


@pytest.mark.parametrize(
    "args",
    [
        ["jobs"], ["tools"], ["submit"], ["batch"], ["validate"], ["status"], ["wait"], ["results"],
        ["logs"], ["cancel"], ["delete"], ["schema"], ["modalities"], ["functions"],
        ["files", "list"], ["files", "upload"], ["files", "delete"], ["files", "stats"], ["files", "folders"],
        ["auth", "status"], ["auth", "login"], ["custom-tools", "list"],
    ],
)
def test_todays_commands_have_the_same_help_with_v1(env, args):
    same_output(env, *args, "--help")


def test_a_surfaced_v1_error_keeps_what_the_command_added(env, monkeypatch, capsys):
    import sys

    monkeypatch.delenv("TAMARIND_API", raising=False)
    env.v1.answers["jobs.submit"] = problem(429, "rate_limited")
    monkeypatch.setattr(sys, "argv", ["tamarind", "--json", "submit", "esmfold", "--skip-validate", "--set", "sequence=MK", "--name", "n1"])
    with pytest.raises(SystemExit) as raised:
        cli_main.run()
    assert raised.value.code == 6
    detail = json.loads(capsys.readouterr().err)["error"]["detail"]
    assert detail["code"] == "rate_limited" and detail["status"] == 429
    assert detail["jobName"] == "n1" and detail["phase"] == "submit" and detail["submitted"] is False
    assert detail["recoveryCommand"] == "tamarind --json status n1"
