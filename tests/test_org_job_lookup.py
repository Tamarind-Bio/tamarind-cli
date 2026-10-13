"""`status` / `wait` / `results` can address a job owned by another org member."""

import json

import httpx
import respx
from typer.testing import CliRunner

from tamarind import Tamarind
from tamarind.cli.main import app

runner = CliRunner()

API = "https://api.test/"
ENV = {"TAMARIND_API_KEY": "k", "TAMARIND_API_BASE": API}
MEMBER = "member@example.com"


def _job(status="Complete", user=MEMBER):
    row = {"JobName": "job-1", "Type": "boltz", "JobStatus": status}
    if user is not None:
        row["User"] = user
    return {"0": row, "statuses": {status: 1}}


@respx.mock
def test_status_organization_sends_org_lookup():
    route = respx.get(f"{API}jobs").mock(return_value=httpx.Response(200, json=_job()))

    res = runner.invoke(app, ["--json", "status", "job-1", "--organization"], env=ENV)

    assert res.exit_code == 0, res.stdout
    params = route.calls.last.request.url.params
    assert params["jobName"] == "job-1"
    assert params["organization"] == "true"
    assert "jobEmail" not in params
    assert json.loads(res.stdout)["User"] == MEMBER


@respx.mock
def test_status_email_sends_member_lookup():
    route = respx.get(f"{API}jobs").mock(return_value=httpx.Response(200, json=_job()))

    res = runner.invoke(app, ["--json", "status", "job-1", "--email", MEMBER], env=ENV)

    assert res.exit_code == 0, res.stdout
    params = route.calls.last.request.url.params
    assert params["jobEmail"] == MEMBER
    assert "organization" not in params


@respx.mock
def test_status_default_stays_caller_scoped():
    route = respx.get(f"{API}jobs").mock(return_value=httpx.Response(200, json=_job(user=None)))

    res = runner.invoke(app, ["--json", "status", "job-1"], env=ENV)

    assert res.exit_code == 0, res.stdout
    params = route.calls.last.request.url.params
    assert "organization" not in params
    assert "jobEmail" not in params


@respx.mock
def test_wait_organization_polls_org_lookup():
    route = respx.get(f"{API}jobs").mock(return_value=httpx.Response(200, json=_job()))

    res = runner.invoke(
        app, ["--json", "wait", "job-1", "--organization", "--poll-interval", "0"], env=ENV
    )

    assert res.exit_code == 0, res.stdout
    assert route.calls.last.request.url.params["organization"] == "true"


@respx.mock
def test_results_organization_resolves_owner_then_requests_their_result():
    jobs = respx.get(f"{API}jobs").mock(return_value=httpx.Response(200, json=_job()))
    result = respx.post(f"{API}result").mock(
        return_value=httpx.Response(200, json="https://storage.test/r.zip?signature=s")
    )

    res = runner.invoke(
        app, ["--json", "results", "job-1", "--organization", "--show-url"], env=ENV
    )

    assert res.exit_code == 0, res.stdout
    assert jobs.calls.last.request.url.params["organization"] == "true"
    assert json.loads(result.calls.last.request.content) == {
        "jobName": "job-1",
        "jobEmail": MEMBER,
    }


@respx.mock
def test_results_email_skips_owner_lookup():
    jobs = respx.get(f"{API}jobs").mock(return_value=httpx.Response(200, json=_job()))
    result = respx.post(f"{API}result").mock(
        return_value=httpx.Response(200, json="https://storage.test/r.zip?signature=s")
    )

    res = runner.invoke(
        app, ["--json", "results", "job-1", "--email", MEMBER, "--show-url"], env=ENV
    )

    assert res.exit_code == 0, res.stdout
    assert not jobs.called
    assert json.loads(result.calls.last.request.content)["jobEmail"] == MEMBER


@respx.mock
def test_results_organization_without_owner_refuses_before_requesting_result():
    respx.get(f"{API}jobs").mock(return_value=httpx.Response(200, json=_job(user=None)))
    result = respx.post(f"{API}result").mock(
        return_value=httpx.Response(200, json="https://storage.test/r.zip?signature=s")
    )

    res = runner.invoke(
        app, ["--json", "results", "job-1", "--organization", "--show-url"], env=ENV
    )

    assert res.exit_code != 0
    assert not result.called


@respx.mock
def test_sdk_status_forwards_org_scope():
    route = respx.get(f"{API}jobs").mock(return_value=httpx.Response(200, json=_job()))

    with Tamarind(api_key="k", api_base=API) as tm:
        job = tm.jobs.status("job-1", organization=True)

    assert job["User"] == MEMBER
    assert route.calls.last.request.url.params["organization"] == "true"
