"""`tamarind submit --low-priority` and `tamarind batch --low-priority`.

The request bodies are what these pin: a flag the CLI accepted and didn't send would bill full price.
"""

import json

import httpx
import pytest
import respx
from typer.testing import CliRunner

from tamarind.cli import output
from tamarind.cli.main import app
from tamarind import Tamarind
from tamarind.errors import ExitCode, ValidationError

API = "https://app.tamarind.bio/api/"
ENV = {"TAMARIND_API_KEY": "k", "NO_COLOR": "1"}
runner = CliRunner()


def _mock_submit():
    respx.post(f"{API}validate-job").mock(return_value=httpx.Response(200, json={"valid": True}))
    return respx.post(f"{API}submit-job").mock(return_value=httpx.Response(200, text="j submitted to queue."))


def _submit(*args):
    return runner.invoke(app, ["--json", "submit", "boltz", "--name", "j", "--set", "sequence=MKT", *args], env=ENV)


@respx.mock
def test_submit_sends_it_and_reports_it():
    route = _mock_submit()
    result = _submit("--low-priority")
    assert result.exit_code == 0, result.output
    assert json.loads(route.calls.last.request.content)["lowPriority"] is True
    assert json.loads(result.stdout)["lowPriority"] is True


@respx.mock
def test_submit_says_what_it_means_to_a_person(monkeypatch):
    monkeypatch.setattr(output, "is_tty", lambda: True)
    _mock_submit()
    result = runner.invoke(app, ["submit", "boltz", "--name", "j", "--set", "sequence=MKT", "--low-priority"], env=ENV)
    assert result.exit_code == 0, result.output
    assert "20% off" in result.output
    assert "no completion guarantee" in result.output
    assert "7 days" in result.output


@respx.mock
def test_submit_without_the_flag_sends_nothing_new():
    route = _mock_submit()
    result = _submit()
    assert result.exit_code == 0, result.output
    assert "lowPriority" not in json.loads(route.calls.last.request.content)
    assert "lowPriority" not in json.loads(result.stdout)


@respx.mock
def test_an_input_file_can_ask_for_it(tmp_path):
    route = _mock_submit()
    path = tmp_path / "job.json"
    path.write_text(json.dumps({"jobName": "j", "type": "boltz", "lowPriority": True, "settings": {"sequence": "MKT"}}))
    result = runner.invoke(app, ["--json", "submit", "boltz", "--input", str(path)], env=ENV)
    assert result.exit_code == 0, result.output
    body = json.loads(route.calls.last.request.content)
    assert body["lowPriority"] is True
    assert body["settings"] == {"sequence": "MKT"}


@respx.mock
def test_a_refusal_is_reported_as_a_failure_and_nothing_claims_success():
    respx.post(f"{API}validate-job").mock(return_value=httpx.Response(200, json={"valid": True}))
    respx.post(f"{API}submit-job").mock(
        return_value=httpx.Response(
            422,
            json={"error": "Low priority isn't enabled for your organization.", "lowPriorityRefused": True, "code": "not_enabled"},
        )
    )
    result = _submit("--low-priority")
    # CliRunner bypasses the run() exit-code mapping, so assert the exception.
    assert result.exit_code != ExitCode.OK
    assert isinstance(result.exception, ValidationError)
    assert "enabled for your organization" in str(result.exception)


def _batch(tmp_path, doc, *args):
    path = tmp_path / "batch.json"
    path.write_text(json.dumps(doc))
    return runner.invoke(app, ["--json", "batch", "boltz", "--name", "b", "--input", str(path), *args], env=ENV)


@respx.mock
def test_batch_sends_it_and_reports_it(tmp_path):
    route = respx.post(f"{API}submit-batch").mock(return_value=httpx.Response(200, text="b batch submitted to queue."))
    result = _batch(tmp_path, [{"sequence": "MKT"}], "--low-priority")
    assert result.exit_code == 0, result.output
    assert json.loads(route.calls.last.request.content)["lowPriority"] is True
    assert json.loads(result.stdout)["lowPriority"] is True


@respx.mock
def test_a_batch_file_can_ask_for_it(tmp_path):
    route = respx.post(f"{API}submit-batch").mock(return_value=httpx.Response(200, text="ok"))
    result = _batch(tmp_path, {"settings": [{"sequence": "MKT"}], "lowPriority": True})
    assert result.exit_code == 0, result.output
    assert json.loads(route.calls.last.request.content)["lowPriority"] is True


@respx.mock
def test_a_batch_value_that_is_null_is_refused_before_any_request(tmp_path):
    route = respx.post(f"{API}submit-batch").mock(return_value=httpx.Response(200, text="ok"))
    result = _batch(tmp_path, {"settings": [{"sequence": "MKT"}], "lowPriority": None})
    assert result.exit_code != 0
    assert not route.called


@respx.mock
def test_batch_without_the_flag_sends_nothing_new(tmp_path):
    route = respx.post(f"{API}submit-batch").mock(return_value=httpx.Response(200, text="ok"))
    result = _batch(tmp_path, [{"sequence": "MKT"}])
    assert result.exit_code == 0, result.output
    assert "lowPriority" not in json.loads(route.calls.last.request.content)


@respx.mock
def test_a_batch_value_that_is_not_a_boolean_is_refused_before_any_request(tmp_path):
    route = respx.post(f"{API}submit-batch").mock(return_value=httpx.Response(200, text="ok"))
    result = _batch(tmp_path, {"settings": [{"sequence": "MKT"}], "lowPriority": "yes"})
    assert result.exit_code != 0
    assert not route.called


@respx.mock
@pytest.mark.parametrize("asked", [True, False])
def test_the_sdk_passes_it_through(asked):
    job = respx.post(f"{API}submit-job").mock(return_value=httpx.Response(200, json={"ok": True}))
    batch = respx.post(f"{API}submit-batch").mock(return_value=httpx.Response(200, json={"ok": True}))
    with Tamarind(api_key="k", api_base=API) as client:
        client.jobs.submit("boltz", {"sequence": "A"}, name="j", low_priority=asked)
        client.jobs.submit_batch("boltz", [{"sequence": "A"}], name="b", low_priority=asked)
    for route in (job, batch):
        body = json.loads(route.calls.last.request.content)
        assert body.get("lowPriority", False) is asked
