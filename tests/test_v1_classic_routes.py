"""Today's commands with v1 selected: same output, some requests answered by v1.

``ClassicOverV1`` stands in for the classic client. These tests check which requests
go to v1 and how its answers are rebuilt into classic's, that everything else (and any
v1 refusal) goes to classic, and, end to end, that a command prints exactly the same
thing whichever API is selected.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from tamarind.cli import main as cli_main
from tamarind.cli.main import app
from tamarind.cli.v1 import classic_routes, sdk
from tamarind.errors import APIError, AuthError, NotFoundError, TamarindError
from tamarind.v1.errors import ProblemError

from test_v1_cli import Recorder

runner = CliRunner()
JOB = "job_0f8fad5b-d9cb-469f-a165-70867728950e"
BATCH = "batch_0f8fad5b-d9cb-469f-a165-70867728950e"
SIGNED = "https://bucket.s3.amazonaws.com/u/result-0f8f.zip?X-Amz-Signature=abc"


def problem(status: int, code: str = "x") -> ProblemError:
    return ProblemError(status=status, code=code, title=code, detail=f"{status} {code}", problem={"status": status, "code": code})


class FakeClassic:
    """The classic HTTPClient: records requests, answers from a table keyed by path."""

    instances: list["FakeClassic"] = []
    answers: dict[str, Any] = {}

    def __init__(self, base_url: str, api_key: str | None, **_: Any) -> None:
        self.base_url, self.api_key = base_url, api_key
        self.calls: list[tuple[str, str, Any]] = []
        FakeClassic.instances.append(self)

    def __enter__(self) -> "FakeClassic":
        return self

    def __exit__(self, *exc: object) -> None:
        return None

    def close(self) -> None:
        return None

    def _answer(self, method: str, path: str, payload: Any) -> Any:
        self.calls.append((method, path, payload))
        if not self.api_key:
            raise AuthError("No API key configured. Set TAMARIND_API_KEY, pass --api-key, or run `tamarind auth login`.")
        answer = FakeClassic.answers.get(path)
        if isinstance(answer, BaseException):
            raise answer
        return answer(payload) if callable(answer) else answer

    def get_json(self, path: str, *, params: Any = None, timeout: Any = None) -> Any:
        return self._answer("GET", path, params)

    def post_json(self, path: str, *, json: Any = None) -> Any:
        return self._answer("POST", path, json)

    def delete_json(self, path: str, *, params: Any = None, json: Any = None) -> Any:
        return self._answer("DELETE", path, json if json is not None else params)


def classic_calls() -> list[tuple[str, str, Any]]:
    return [call for client in FakeClassic.instances for call in client.calls]


@pytest.fixture
def env(monkeypatch, tmp_path):
    """Both APIs faked: ``env.v1`` is the v1 SDK recorder; classic is ``FakeClassic``."""
    monkeypatch.setenv("TAMARIND_CONFIG_DIR", str(tmp_path))
    monkeypatch.setenv("TAMARIND_API_KEY", "test-key")
    monkeypatch.delenv("TAMARIND_API", raising=False)
    FakeClassic.instances = []
    FakeClassic.answers = {}
    monkeypatch.setattr(cli_main, "HTTPClient", FakeClassic)
    monkeypatch.setattr(classic_routes, "HTTPClient", FakeClassic)
    monkeypatch.setattr("tamarind.cli.commands.auth.HTTPClient", FakeClassic)
    recorder = Recorder({})
    monkeypatch.setattr(sdk, "make_client", lambda state, api_key=None: recorder)

    class Env:
        v1 = recorder

        @staticmethod
        def run(api: str, *args: str) -> Any:
            monkeypatch.setenv("TAMARIND_API", api)
            return runner.invoke(app, list(args))

    return Env


def same_output(env, *args: str) -> Any:
    """Run ``args`` with classic, then with v1; both must print the same and exit alike."""
    classic = env.run("classic", *args)
    v1 = env.run("v1", *args)
    assert (classic.exit_code, classic.stdout) == (v1.exit_code, v1.stdout), (classic.output, v1.output)
    return v1


# -- which client --------------------------------------------------------------


def test_classic_mode_uses_the_classic_client_only(env):
    FakeClassic.answers["delete-job"] = "j1 deleted"
    res = env.run("classic", "--json", "delete", "j1", "--yes")
    assert res.exit_code == 0 and env.v1.calls == []
    assert classic_calls() == [("DELETE", "delete-job", {"jobName": "j1"})]


# -- submit-job -------------------------------------------------------------------


def test_submit_goes_to_v1_and_prints_what_classic_prints(env):
    FakeClassic.answers["submit-job"] = "n1 submitted to queue."
    env.v1.answers["jobs.submit"] = {"id": JOB, "name": "n1", "status": "In Queue"}
    res = same_output(env, "--json", "submit", "esmfold", "--skip-validate", "--set", "sequence=MK", "--name", "n1")
    assert json.loads(res.stdout)["submit"] == "n1 submitted to queue."
    assert env.v1.calls == [
        ("jobs.submit", (), {"body": {"kind": "job", "tool": "esmfold", "name": "n1", "settings": {"sequence": "MK"}}})
    ]
    # classic answered only the classic run
    assert [c[1] for c in classic_calls()] == ["submit-job"]


def test_low_priority_submit_keeps_classics_wording(env):
    FakeClassic.answers["submit-job"] = "n1 submitted to queue" + classic_routes.LOW_PRIORITY_SUFFIX + "."
    env.v1.answers["jobs.submit"] = {"id": JOB}
    same_output(env, "--json", "submit", "esmfold", "--skip-validate", "--low-priority", "--set", "sequence=MK", "--name", "n1")
    assert env.v1.calls[0][2]["body"]["lowPriority"] is True


def test_validate_stays_on_classic(env):
    FakeClassic.answers["validate-job"] = {"valid": True, "normalized": {"sequence": "MK"}, "job_name": "n1"}
    FakeClassic.answers["submit-job"] = "n1 submitted to queue."
    env.v1.answers["jobs.submit"] = {"id": JOB}
    same_output(env, "--json", "submit", "esmfold", "--set", "sequence=MK", "--name", "n1")
    assert [c[1] for c in classic_calls()] == ["validate-job", "submit-job", "validate-job"]


def test_a_submit_v1_refuses_is_sent_to_classic(env):
    FakeClassic.answers["submit-job"] = "n1 submitted to queue."
    env.v1.answers["jobs.submit"] = problem(422, "unknown_field")
    res = env.run("v1", "--json", "submit", "boltz", "--skip-validate", "--set", "old_name=1", "--name", "n1")
    assert res.exit_code == 0 and json.loads(res.stdout)["submit"] == "n1 submitted to queue."
    assert [c[1] for c in classic_calls()] == ["submit-job"]


def test_a_name_already_used_reads_as_classic_words_it_without_asking_classic(env):
    from tamarind.errors import ValidationError

    FakeClassic.answers["submit-job"] = ValidationError("jobName n1 already exists, please choose a different name")
    env.v1.answers["jobs.submit"] = problem(409, "job_name_conflict")
    classic = env.run("classic", "--json", "submit", "esmfold", "--skip-validate", "--set", "sequence=MK", "--name", "n1")
    FakeClassic.instances = []
    v1 = env.run("v1", "--json", "submit", "esmfold", "--skip-validate", "--set", "sequence=MK", "--name", "n1")
    assert (type(classic.exception), str(classic.exception)) == (type(v1.exception), str(v1.exception))
    assert classic.exception.detail == v1.exception.detail
    assert classic_calls() == []  # rebuilt from v1's answer, not asked again


@pytest.mark.parametrize("status", [400, 401, 404, 422])
def test_a_write_v1_refused_before_acting_goes_to_classic(env, status):
    FakeClassic.answers["submit-job"] = "n1 submitted to queue."
    env.v1.answers["jobs.submit"] = problem(status, "refused")
    res = env.run("v1", "--json", "submit", "esmfold", "--skip-validate", "--set", "sequence=MK", "--name", "n1")
    assert res.exit_code == 0 and [c[1] for c in classic_calls()] == ["submit-job"]


WRITES = {
    "submit": (["submit", "esmfold", "--skip-validate", "--set", "sequence=MK", "--name", "n1"], {}, "jobs.submit"),
    "delete": (["delete", "n1", "--yes"], {"jobs.list": {"items": [{"id": JOB, "kind": "job"}], "nextCursor": None}}, "jobs.delete"),
    "files delete": (["files", "delete", "a.pdb", "--yes"], {}, "files.delete"),
    "files upload": (None, {}, "files.upload"),
}


@pytest.mark.parametrize("command", sorted(WRITES))
@pytest.mark.parametrize("status, code, exit_code", [(409, "conflict", 1), (403, "budget_exceeded", 8), (429, "rate_limited", 6)])
def test_a_write_v1_answered_is_surfaced_never_redone_on_classic(env, tmp_path, monkeypatch, command, status, code, exit_code):
    args, answers, method = WRITES[command]
    if args is None:
        local = tmp_path / "in.fasta"
        local.write_text(">a\nMK\n")
        args = ["files", "upload", str(local)]
    monkeypatch.setattr("tamarind.uploads.upload_file", lambda *a, **k: pytest.fail("classic upload"))
    env.v1.answers.update(answers)
    env.v1.answers[method] = problem(status, code)
    res = env.run("v1", "--json", *args)
    assert classic_calls() == []
    assert isinstance(res.exception, ProblemError) and res.exception.exit_code == exit_code


@pytest.mark.parametrize("failure", [problem(503, "service_unavailable"), TamarindError("Network error")])
def test_a_submit_with_no_clear_answer_is_not_sent_again(env, failure):
    env.v1.answers["jobs.submit"] = failure
    res = env.run("v1", "--json", "submit", "esmfold", "--skip-validate", "--set", "sequence=MK", "--name", "n1")
    assert classic_calls() == []
    # the command's own classic handling: the outcome may be ambiguous
    assert res.exception.detail["outcomeMayBeAmbiguous"] is True
    if isinstance(failure, ProblemError):
        assert isinstance(res.exception, APIError) and res.exception.status_code == 503


def test_a_submit_still_in_progress_is_not_sent_to_classic(env):
    env.v1.answers["jobs.submit"] = problem(409, "idempotency_in_progress")
    res = env.run("v1", "--json", "submit", "esmfold", "--skip-validate", "--set", "sequence=MK", "--name", "n1")
    assert classic_calls() == []  # the first attempt may still be making the job
    assert res.exception.detail["outcomeMayBeAmbiguous"] is True


# -- result ------------------------------------------------------------------------


def _job(kind: str = "job", job_id: str = JOB) -> dict[str, Any]:
    return {"items": [{"id": job_id, "kind": kind, "name": "n1"}], "nextCursor": None}


def test_results_show_url_prints_classics_link(env):
    FakeClassic.answers["result"] = SIGNED
    env.v1.answers["jobs.list"] = _job()
    env.v1.answers["jobs.archive"] = {"status": "ready", "downloadUrl": SIGNED}
    same_output(env, "--json", "results", "n1", "--show-url")
    same_output(env, "--json", "results", "n1", "--file", "a.pdb", "--show-url")
    assert env.v1.calls == []  # v1 signs a different (global-endpoint) link


def test_results_download_saves_the_same_archive(env, tmp_path, monkeypatch):
    fetched: list[str] = []
    monkeypatch.setattr("tamarind.cli.commands.jobs._download", lambda url, dest: fetched.append(url) or 42)
    FakeClassic.answers["result"] = SIGNED
    env.v1.answers["jobs.list"] = _job("batch", BATCH)
    env.v1.answers["jobs.archive"] = {"status": "ready", "downloadUrl": SIGNED}
    same_output(env, "--json", "results", "n1", "--download", str(tmp_path))
    assert fetched == [SIGNED, SIGNED]


def test_results_file_comes_from_get_job_file(env, tmp_path, monkeypatch):
    monkeypatch.setattr("tamarind.cli.commands.jobs._download", lambda url, dest: 3)
    FakeClassic.answers["result"] = SIGNED
    env.v1.answers["jobs.list"] = _job()
    env.v1.answers["jobs.get_file"] = {"url": SIGNED, "sizeBytes": 3}
    same_output(env, "--json", "results", "n1", "--file", "out/a.pdb", "--download", str(tmp_path))
    assert env.v1.calls[-1] == ("jobs.get_file", (JOB,), {"path": "out/a.pdb", "delivery": "url"})


def test_results_rate_limited_by_v1_is_surfaced(env, tmp_path):
    env.v1.answers["jobs.list"] = _job()
    env.v1.answers["jobs.archive"] = problem(429, "rate_limited")
    res = env.run("v1", "--json", "results", "n1", "--download", str(tmp_path))
    assert classic_calls() == [] and res.exception.exit_code == 6


READY = {"status": "ready", "downloadUrl": SIGNED}


@pytest.mark.parametrize(
    "args, v1_answers, archived",
    [
        # classic's best structures (v1's archive selection isn't built yet), even though v1 could answer
        (["--pdbs-only"], {"jobs.list": _job(), "jobs.archive": READY}, False),
        # another member's job
        (["--email", "peer@example.com"], {"jobs.list": _job(), "jobs.archive": READY}, False),
        # no such job: classic says so
        ([], {"jobs.list": {"items": [], "nextCursor": None}}, False),
        ([], {"jobs.list": _job("pipeline", "run_0f8fad5b-d9cb-469f-a165-70867728950e"), "jobs.archive": READY}, False),
        # v1 still preparing it: classic builds it its own way
        ([], {"jobs.list": _job(), "jobs.archive": {"status": "preparing", "retryAfterSeconds": 5}}, True),
        # one file of a batch
        (["--file", "out/a.pdb"], {"jobs.list": _job("batch", BATCH), "jobs.get_file": {"url": SIGNED}}, False),
    ],
)
def test_results_v1_cant_answer_go_to_classic(env, tmp_path, monkeypatch, args, v1_answers, archived):
    monkeypatch.setattr("tamarind.cli.commands.jobs._download", lambda url, dest: 3)
    FakeClassic.answers["result"] = SIGNED
    FakeClassic.answers["jobs"] = {"JobName": "n1", "JobStatus": "Complete", "User": "peer@example.com"}
    env.v1.answers.update(v1_answers)
    res = env.run("v1", "--json", "results", "n1", "--download", str(tmp_path), *args)
    assert res.exit_code == 0, res.output
    assert ("POST", "result") in [(c[0], c[1]) for c in classic_calls()]
    called = [c[0] for c in env.v1.calls]
    assert ("jobs.archive" in called) is archived and "jobs.get_file" not in called


def test_a_stopped_jobs_archive_reads_as_classic_words_it(env, tmp_path):
    # results only reads, so v1's 409 archive_failed may go to classic for its wording
    FakeClassic.answers["result"] = TamarindError("Job n1 is not complete. Status: Stopped")
    env.v1.answers["jobs.list"] = _job()
    env.v1.answers["jobs.archive"] = problem(409, "archive_failed")
    classic = env.run("classic", "--json", "results", "n1", "--download", str(tmp_path))
    v1 = env.run("v1", "--json", "results", "n1", "--download", str(tmp_path))
    assert (type(classic.exception), str(classic.exception)) == (type(v1.exception), str(v1.exception))


# -- delete-job, delete-file, upload ------------------------------------------------------


def test_delete_job_goes_to_v1(env):
    FakeClassic.answers["delete-job"] = "n1 deleted"
    env.v1.answers["jobs.list"] = _job("batch", BATCH)
    env.v1.answers["jobs.delete"] = None
    same_output(env, "--json", "delete", "n1", "--yes")
    same_output(env, "--no-json", "delete", "n1", "--yes")
    assert ("jobs.delete", (BATCH,), {}) in env.v1.calls


def test_delete_of_a_missing_job_reads_as_classic_words_it(env):
    FakeClassic.answers["delete-job"] = NotFoundError("n1 does not exist")
    env.v1.answers["jobs.list"] = {"items": [], "nextCursor": None}
    classic = env.run("classic", "--json", "delete", "n1", "--yes")
    v1 = env.run("v1", "--json", "delete", "n1", "--yes")
    assert (type(classic.exception), str(classic.exception)) == (type(v1.exception), str(v1.exception))
    assert isinstance(v1.exception, NotFoundError)


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
    assert env.v1.calls == [("files.delete", (), call)] * 1


def test_files_delete_of_a_file_and_a_folder_is_classics_to_decide(env):
    FakeClassic.answers["delete-file"] = {"message": "Folder deleted successfully"}
    same_output(env, "--json", "files", "delete", "a.pdb", "--folder", "runs", "--yes")
    assert env.v1.calls == []


def test_files_delete_v1_refuses_goes_to_classic(env):
    FakeClassic.answers["delete-file"] = {"message": "File deleted successfully"}
    env.v1.answers["files.delete"] = problem(404, "not_found")
    res = same_output(env, "--json", "files", "delete", "gone.pdb", "--yes")
    assert json.loads(res.stdout) == {"message": "File deleted successfully"}


def test_files_upload_goes_to_v1(env, tmp_path, monkeypatch):
    local = tmp_path / "in.fasta"
    local.write_text(">a\nMK\n")
    monkeypatch.setattr(
        "tamarind.uploads.upload_file",
        lambda client, path, remote: {"ok": True, "filename": remote, "bytes": Path(path).stat().st_size},
    )
    env.v1.answers["files.upload"] = {"path": "in.fasta", "type": "file", "sizeBytes": 6}
    same_output(env, "--json", "files", "upload", str(local))
    same_output(env, "--json", "files", "upload", str(local), "--name", "dir/x.fasta")
    assert env.v1.calls[0] == ("files.upload", (local,), {"path": "in.fasta"})


def test_files_upload_v1_refuses_goes_to_classic(env, tmp_path, monkeypatch):
    local = tmp_path / "in.fasta"
    local.write_text(">a\nMK\n")
    used: list[str] = []
    monkeypatch.setattr(
        "tamarind.uploads.upload_file",
        lambda client, path, remote: used.append(remote) or {"ok": True, "filename": remote, "bytes": 6},
    )
    env.v1.answers["files.upload"] = problem(422, "invalid_path")
    res = env.run("v1", "--json", "files", "upload", str(local))
    assert res.exit_code == 0 and used == ["in.fasta"]


# -- auth -----------------------------------------------------------------------------


def test_auth_status_checks_the_key_on_v1_and_prints_classics_fields(env):
    FakeClassic.answers["jobs"] = {"jobs": [], "statuses": {}}
    env.v1.answers["me.get"] = {"user": {"email": "a@b"}}
    res = same_output(env, "--json", "auth", "status")
    assert json.loads(res.stdout) == {"profile": "default", "hasKey": True, "verified": True}
    same_output(env, "--no-json", "auth", "status")
    assert ("me.get", (), {}) in env.v1.calls


def test_a_key_v1_refuses_is_not_verified(env):
    FakeClassic.answers["jobs"] = AuthError("Unauthorized: Invalid API key")
    env.v1.answers["me.get"] = problem(401, "invalid_api_key")
    res = same_output(env, "--json", "auth", "status")
    assert json.loads(res.stdout)["verified"] is False


def test_when_v1_cant_say_classic_checks_the_key(env):
    FakeClassic.answers["jobs"] = {"jobs": [], "statuses": {}}
    env.v1.answers["me.get"] = problem(404, "not_found")  # v1 not on for this account
    res = env.run("v1", "--json", "auth", "status")
    assert json.loads(res.stdout)["verified"] is True
    assert [c[1] for c in classic_calls()] == ["jobs"]


# -- the rest stays on classic -------------------------------------------------------------


@pytest.mark.parametrize(
    "args, path, answer",
    [
        (["jobs", "--limit", "2"], "jobs", {"jobs": [{"JobName": "n1", "JobStatus": "Complete"}], "statuses": {"Complete": 1}}),
        (["status", "n1"], "jobs", {"JobName": "n1", "JobStatus": "Complete", "statuses": {"Complete": 1}}),
        (["cancel", "n1"], "cancelJob", {"success": True, "message": "Job cancelled successfully"}),
        (["cancel", "--batch", "b1"], "cancelBatch", {"success": True, "message": 'Cancelled 2 jobs in batch "b1"'}),
        (["validate", "esmfold", "--set", "sequence=MK", "--name", "n1"], "validate-job", {"valid": True, "normalized": {}}),
        (["files", "list"], "files", ["a.pdb", "b.pdb"]),
        (["files", "stats"], "files", ["a.pdb", "b.pdb"]),
        (["files", "folders"], "getFolders", {"folders": ["runs"], "hasMore": False}),
    ],
)
def test_requests_v1_cant_answer_exactly_stay_on_classic(env, args, path, answer):
    FakeClassic.answers[path] = answer
    same_output(env, "--json", *args)
    same_output(env, "--no-json", *args)
    assert env.v1.calls == []


def test_without_a_key_classic_says_so(env, monkeypatch):
    monkeypatch.delenv("TAMARIND_API_KEY")
    classic = env.run("classic", "--json", "delete", "n1", "--yes")
    v1 = env.run("v1", "--json", "delete", "n1", "--yes")
    assert (type(classic.exception), str(classic.exception)) == (type(v1.exception), str(v1.exception))
    assert isinstance(v1.exception, AuthError)
    assert env.v1.calls == []


# -- jobs and tools: today's flat commands, contract commands beside them with v1 --------


def test_jobs_with_v1_is_todays_listing_unless_a_contract_command_follows(env):
    FakeClassic.answers["jobs"] = {"jobs": [], "statuses": {}}
    same_output(env, "--json", "jobs", "--limit", "3")
    env.v1.answers["jobs.list"] = {"items": [], "nextCursor": None}
    res = env.run("v1", "--json", "jobs", "list", "--kind", "batch")
    assert res.exit_code == 0 and env.v1.calls == [("jobs.list", (), {"kind": "batch"})]
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

    monkeypatch.setenv("TAMARIND_API", "v1")
    env.v1.answers["jobs.submit"] = problem(429, "rate_limited")
    monkeypatch.setattr(sys, "argv", ["tamarind", "--json", "submit", "esmfold", "--skip-validate", "--set", "sequence=MK", "--name", "n1"])
    with pytest.raises(SystemExit) as raised:
        cli_main.run()
    assert raised.value.code == 6
    detail = json.loads(capsys.readouterr().err)["error"]["detail"]
    # v1's problem document and submit's own recovery context, together
    assert detail["code"] == "rate_limited" and detail["status"] == 429
    assert detail["jobName"] == "n1" and detail["phase"] == "submit" and detail["submitted"] is False
    assert detail["recoveryCommand"] == "tamarind --json status n1"
