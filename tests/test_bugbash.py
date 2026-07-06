"""Tests for the CLI bug-bash fixes (reproduced live against staging first):

- #1  `schema <tool> --example` fails loudly when a tool ships no example,
      instead of printing an empty `{}` at exit 0.
- #2  `wait --timeout` raises a typed JobTimeoutError (exit 7), not a bare
      builtin TimeoutError traceback.
- #3  an input file's `type:` may not silently override the `<tool>` argument.
- #4  destructive `delete` / `files delete` refuse to run non-interactively
      without `--yes`/`-y`.
"""

import json

import httpx
import pytest
import respx
import typer
from typer.testing import CliRunner

from tamarind.cli import output
from tamarind.cli.inputs import effective_job_type
from tamarind.cli.main import app
from tamarind.cli.output import OutputMode
from tamarind.errors import ExitCode, JobTimeoutError, NotFoundError, TamarindError, ValidationError
from tamarind import jobs as jh
from tamarind.http import HTTPClient

runner = CliRunner()

API = "https://api.test/"
CAT = "https://cat.test/"
ENV = {"TAMARIND_API_KEY": "k", "TAMARIND_API_BASE": API, "TAMARIND_CATALOG_BASE": CAT}


# --- #3: file `type:` must not silently override the `<tool>` arg -------------

def test_effective_job_type_agrees_or_defaults():
    assert effective_job_type("boltz", None) == "boltz"
    assert effective_job_type("boltz", "boltz") == "boltz"
    # comparison ignores surrounding whitespace and case
    assert effective_job_type("boltz", "  Boltz ") == "boltz"


def test_effective_job_type_rejects_conflict():
    with pytest.raises(ValidationError) as exc:
        effective_job_type("boltz", "esmfold")
    assert exc.value.exit_code == ExitCode.VALIDATION
    assert "boltz" in exc.value.message and "esmfold" in exc.value.message


@respx.mock
def test_validate_rejects_mismatched_file_type(tmp_path):
    # The bug: `validate boltz -i esmfold.yaml` validated as esmfold and returned
    # valid:true. Now it must error out *before* any HTTP call.
    route = respx.post(f"{API}validate-job").mock(return_value=httpx.Response(200, json={"valid": True}))
    f = tmp_path / "job.yaml"
    f.write_text("type: esmfold\nsettings:\n  sequence: MKT\n")
    res = runner.invoke(app, ["validate", "boltz", "-i", str(f)], env=ENV)
    assert res.exit_code != 0
    assert isinstance(res.exception, ValidationError)
    assert not route.called  # never reached the backend


@respx.mock
def test_validate_allows_matching_file_type(tmp_path):
    respx.post(f"{API}validate-job").mock(return_value=httpx.Response(200, json={"valid": True}))
    f = tmp_path / "job.yaml"
    f.write_text("type: boltz\nsettings:\n  inputFormat: sequence\n  sequence: MKT\n")
    res = runner.invoke(app, ["--json", "validate", "boltz", "-i", str(f)], env=ENV)
    assert res.exit_code == 0, res.stdout
    assert json.loads(res.stdout)["valid"] is True


@respx.mock
def test_submit_rejects_mismatched_file_type(tmp_path):
    v = respx.post(f"{API}validate-job").mock(return_value=httpx.Response(200, json={"valid": True}))
    s = respx.post(f"{API}submit-job").mock(return_value=httpx.Response(200, json={"message": "ok"}))
    f = tmp_path / "job.yaml"
    f.write_text("type: esmfold\nsettings:\n  sequence: MKT\n")
    res = runner.invoke(app, ["submit", "boltz", "-i", str(f)], env=ENV)
    assert res.exit_code != 0
    assert isinstance(res.exception, ValidationError)
    assert not v.called and not s.called


# --- #2: wait timeout -> typed JobTimeoutError (exit 7) ----------------------

@respx.mock
def test_wait_for_job_raises_typed_timeout():
    respx.get(f"{API}jobs").mock(
        return_value=httpx.Response(200, json={"JobName": "x", "JobStatus": "Running"})
    )
    with pytest.raises(JobTimeoutError) as exc:
        jh.wait_for_job(HTTPClient(API, "k"), "x", poll_interval=0, timeout=0)
    assert exc.value.exit_code == ExitCode.TIMEOUT == 7
    assert "Running" in exc.value.message


@respx.mock
def test_wait_command_surfaces_timeout_not_traceback():
    # CliRunner bypasses run()'s exit-code mapping, so assert on the typed
    # exception the entry point maps to exit 7 (no raw builtin TimeoutError).
    respx.get(f"{API}jobs").mock(
        return_value=httpx.Response(200, json={"JobName": "x", "JobStatus": "In Queue"})
    )
    res = runner.invoke(app, ["wait", "x", "--timeout", "0", "--poll-interval", "0"], env=ENV)
    assert res.exit_code != 0
    assert isinstance(res.exception, JobTimeoutError)
    assert res.exception.exit_code == 7


# --- #1: schema --example fails loudly with no example -----------------------

def _schema_route(tool, exampleJob):
    payload = {"displayName": tool, "parameters": [{"name": "sequence", "type": "string"}]}
    if exampleJob is not None:
        payload["exampleJob"] = exampleJob
    return respx.get(f"{CAT}catalog/tools/{tool}/schema").mock(
        return_value=httpx.Response(200, json=payload)
    )


@respx.mock
def test_schema_example_missing_exits_nonzero():
    _schema_route("afcluster", exampleJob=None)  # no exampleJob at all
    res = runner.invoke(app, ["schema", "afcluster", "--example"], env=ENV)
    assert res.exit_code != 0
    assert isinstance(res.exception, NotFoundError)
    assert "afcluster" in res.exception.message


@respx.mock
def test_schema_example_empty_settings_exits_nonzero():
    _schema_route("afcluster", exampleJob={"settings": {}})  # present but empty
    res = runner.invoke(app, ["schema", "afcluster", "--example"], env=ENV)
    assert res.exit_code != 0
    assert isinstance(res.exception, NotFoundError)


@respx.mock
def test_schema_example_present_prints_settings():
    _schema_route("boltz", exampleJob={"settings": {"inputFormat": "sequence", "sequence": "MKT"}})
    res = runner.invoke(app, ["--json", "schema", "boltz", "--example"], env=ENV)
    assert res.exit_code == 0, res.stdout
    out = json.loads(res.stdout)
    assert out["settings"] == {"inputFormat": "sequence", "sequence": "MKT"}


# --- #4: destructive commands refuse non-interactive without --yes -----------

def test_confirm_destructive_yes_bypasses():
    # Explicit --yes: no prompt, no raise, in any mode.
    output.confirm_destructive("delete job 'x'", yes=True, mode=OutputMode(json=True, quiet=False))


def test_confirm_destructive_refuses_in_json_mode():
    with pytest.raises(typer.Exit) as exc:
        output.confirm_destructive("delete job 'x'", yes=False, mode=OutputMode(json=True, quiet=False))
    assert exc.value.exit_code == ExitCode.USAGE


@respx.mock
def test_delete_refuses_without_yes_non_interactive():
    route = respx.request("DELETE", f"{API}delete-job").mock(
        return_value=httpx.Response(200, json={"message": "deleted"})
    )
    res = runner.invoke(app, ["--json", "delete", "somejob"], env=ENV)
    assert res.exit_code == ExitCode.USAGE
    assert not route.called  # never hit the backend


@respx.mock
def test_delete_proceeds_with_yes():
    route = respx.request("DELETE", f"{API}delete-job").mock(
        return_value=httpx.Response(200, json={"message": "deleted"})
    )
    res = runner.invoke(app, ["--json", "delete", "somejob", "-y"], env=ENV)
    assert res.exit_code == 0, res.stdout
    assert route.called


@respx.mock
def test_files_delete_refuses_without_yes_non_interactive():
    route = respx.request("DELETE", f"{API}delete-file").mock(
        return_value=httpx.Response(200, json={"message": "deleted"})
    )
    res = runner.invoke(app, ["--json", "files", "delete", "a.pdb"], env=ENV)
    assert res.exit_code == ExitCode.USAGE
    assert not route.called


def test_delete_prompts_in_interactive_mode(monkeypatch):
    # With a real terminal on BOTH ends (monkeypatched) and human output, the
    # legacy interactive confirmation still applies: "n" aborts before any HTTP.
    monkeypatch.setattr(output, "is_tty", lambda: True)
    monkeypatch.setattr(output, "is_stdin_tty", lambda: True)
    with respx.mock:
        route = respx.request("DELETE", f"{API}delete-job").mock(
            return_value=httpx.Response(200, json={"message": "deleted"})
        )
        res = runner.invoke(app, ["delete", "somejob"], env=ENV, input="n\n")
        assert res.exit_code != 0  # aborted
        assert not route.called


def test_confirm_destructive_refuses_piped_stdin(monkeypatch):
    # stdout is a TTY but stdin is piped (`printf 'y\n' | tamarind delete x`):
    # no human to answer, so refuse rather than let typer.confirm eat the piped
    # 'y' as a confirmation. Isolates the `not is_stdin_tty()` disjunct.
    monkeypatch.setattr(output, "is_tty", lambda: True)
    monkeypatch.setattr(output, "is_stdin_tty", lambda: False)
    with pytest.raises(typer.Exit) as exc:
        output.confirm_destructive(
            "delete job 'x'", yes=False, mode=OutputMode(json=False, quiet=False)
        )
    assert exc.value.exit_code == ExitCode.USAGE


@respx.mock
def test_delete_refuses_piped_yes_with_tty_stdout(monkeypatch):
    # End-to-end `printf 'y\n' | tamarind delete somejob`: the piped 'y' must NOT
    # delete — the guard refuses (exit 2) and never hits the backend.
    monkeypatch.setattr(output, "is_tty", lambda: True)
    monkeypatch.setattr(output, "is_stdin_tty", lambda: False)
    route = respx.request("DELETE", f"{API}delete-job").mock(
        return_value=httpx.Response(200, json={"message": "deleted"})
    )
    res = runner.invoke(app, ["delete", "somejob"], env=ENV, input="y\n")
    assert res.exit_code == ExitCode.USAGE
    assert not route.called


def test_confirm_destructive_refuses_non_tty_human_mode(monkeypatch):
    # The guard is `mode.json or not is_tty()`. Human (--no-json) output over a
    # pipe hits the `not is_tty()` half — which the --json tests never reach
    # (they short-circuit on mode.json). Isolate it directly: json=False + no TTY
    # must still refuse, so a piped `tamarind delete x` can't destroy data.
    monkeypatch.setattr(output, "is_tty", lambda: False)
    with pytest.raises(typer.Exit) as exc:
        output.confirm_destructive(
            "delete job 'x'", yes=False, mode=OutputMode(json=False, quiet=False)
        )
    assert exc.value.exit_code == ExitCode.USAGE


# --- #3: the batch command shares the type-conflict guard --------------------

@respx.mock
def test_batch_rejects_mismatched_file_type(tmp_path):
    route = respx.post(f"{API}submit-batch").mock(return_value=httpx.Response(200, json={"message": "ok"}))
    f = tmp_path / "batch.yaml"
    f.write_text("type: esmfold\nsettings:\n  - sequence: MKT\n  - sequence: MKV\n")
    res = runner.invoke(app, ["batch", "boltz", "-i", str(f)], env=ENV)
    assert res.exit_code != 0
    assert isinstance(res.exception, ValidationError)
    assert not route.called  # errored before the backend


@respx.mock
def test_batch_bare_list_uses_tool_arg(tmp_path):
    route = respx.post(f"{API}submit-batch").mock(return_value=httpx.Response(200, json={"message": "ok"}))
    f = tmp_path / "batch.yaml"
    f.write_text("- {inputFormat: sequence, sequence: MKT}\n- {inputFormat: sequence, sequence: MKV}\n")
    res = runner.invoke(app, ["--json", "batch", "boltz", "-i", str(f)], env=ENV)
    assert res.exit_code == 0, res.stdout
    out = json.loads(res.stdout)
    assert out["type"] == "boltz" and out["count"] == 2
    assert json.loads(route.calls.last.request.content)["type"] == "boltz"


@respx.mock
def test_batch_matching_envelope_type(tmp_path):
    route = respx.post(f"{API}submit-batch").mock(return_value=httpx.Response(200, json={"message": "ok"}))
    f = tmp_path / "batch.yaml"
    f.write_text("type: boltz\nbatchName: b1\nsettings:\n  - {inputFormat: sequence, sequence: MKT}\n")
    res = runner.invoke(app, ["--json", "batch", "boltz", "-i", str(f)], env=ENV)
    assert res.exit_code == 0, res.stdout
    body = json.loads(route.calls.last.request.content)
    assert body["type"] == "boltz" and body["batchName"] == "b1"


# --- #4: files delete --folder and the empty-args guard ----------------------

@respx.mock
def test_files_delete_folder_refuses_without_yes_non_interactive():
    # The higher-blast-radius --folder form (deletes every file under a folder)
    # must also refuse non-interactively without --yes.
    route = respx.request("DELETE", f"{API}delete-file").mock(
        return_value=httpx.Response(200, json={"message": "deleted"})
    )
    res = runner.invoke(app, ["--json", "files", "delete", "--folder", "foo"], env=ENV)
    assert res.exit_code == ExitCode.USAGE
    assert not route.called


@respx.mock
def test_files_delete_requires_path_or_folder():
    route = respx.request("DELETE", f"{API}delete-file").mock(
        return_value=httpx.Response(200, json={"message": "deleted"})
    )
    res = runner.invoke(app, ["--json", "files", "delete"], env=ENV)
    assert res.exit_code != 0
    assert isinstance(res.exception, TamarindError)
    assert not route.called
