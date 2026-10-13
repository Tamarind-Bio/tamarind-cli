"""`status` / `wait` / `results` can address a job owned by another org member."""

import json

import httpx
import respx
from typer.testing import CliRunner

from tamarind import Tamarind
from tamarind.cli.main import app
from tamarind.errors import NotFoundError

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
def test_results_email_sends_the_stored_owner_not_the_typed_one():
    jobs = respx.get(f"{API}jobs").mock(return_value=httpx.Response(200, json=_job()))
    result = respx.post(f"{API}result").mock(
        return_value=httpx.Response(200, json="https://storage.test/r.zip?signature=s")
    )

    res = runner.invoke(
        app, ["--json", "results", "job-1", "--email", MEMBER.upper(), "--show-url"], env=ENV
    )

    assert res.exit_code == 0, res.stdout
    assert jobs.calls.last.request.url.params["jobEmail"] == MEMBER.upper()
    assert json.loads(result.calls.last.request.content)["jobEmail"] == MEMBER


@respx.mock
def test_blank_email_is_refused_before_any_request():
    jobs = respx.get(f"{API}jobs").mock(return_value=httpx.Response(200, json=_job()))
    result = respx.post(f"{API}result").mock(
        return_value=httpx.Response(200, json="https://storage.test/r.zip?signature=s")
    )

    for cmd in (["status", "job-1"], ["results", "job-1", "--show-url"]):
        res = runner.invoke(app, ["--json", *cmd, "--email", " "], env=ENV)
        assert res.exit_code != 0

    assert not jobs.called
    assert not result.called


@respx.mock
def test_wait_organization_pins_the_first_match():
    route = respx.get(f"{API}jobs").mock(
        side_effect=[
            httpx.Response(200, json=_job(status="Running")),
            httpx.Response(200, json=_job(status="Complete")),
        ]
    )

    res = runner.invoke(
        app, ["--json", "wait", "job-1", "--organization", "--poll-interval", "0"], env=ENV
    )

    assert res.exit_code == 0, res.stdout
    first, second = (call.request.url.params for call in route.calls)
    assert first["organization"] == "true" and "jobEmail" not in first
    assert second["jobEmail"] == MEMBER and "organization" not in second


@respx.mock
def test_organization_not_found_points_at_email():
    respx.get(f"{API}jobs").mock(
        return_value=httpx.Response(404, json={"error": "Job job-1 not found"})
    )

    with Tamarind(api_key="k", api_base=API) as tm:
        try:
            tm.jobs.status("job-1", organization=True)
        except NotFoundError as exc:
            assert "owner's email" in exc.message
        else:
            raise AssertionError("expected NotFoundError")


@respx.mock
def test_sdk_results_organization_resolves_owner():
    respx.get(f"{API}jobs").mock(return_value=httpx.Response(200, json=_job()))
    result = respx.post(f"{API}result").mock(
        return_value=httpx.Response(200, json="https://storage.test/r.zip?signature=s")
    )

    with Tamarind(api_key="k", api_base=API) as tm:
        tm.jobs.results("job-1", organization=True)

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


@respx.mock
def test_organization_name_shared_by_two_members_is_refused():
    other = "other@example.com"
    collision = {
        "0": {"JobName": "job-1", "JobStatus": "Complete", "User": other},
        "1": {"JobName": "job-1", "JobStatus": "Complete", "User": MEMBER},
        "statuses": {"Complete": 2},
    }
    respx.get(f"{API}jobs").mock(return_value=httpx.Response(200, json=collision))
    result = respx.post(f"{API}result").mock(
        return_value=httpx.Response(200, json="https://storage.test/r.zip?signature=s")
    )

    for cmd in (["status", "job-1"], ["results", "job-1", "--show-url"]):
        res = runner.invoke(app, ["--json", *cmd, "--organization"], env=ENV)
        assert res.exit_code != 0
        assert "pass the owner's email" in str(res.exception or res.output)

    assert not result.called


@respx.mock
def test_results_email_falls_back_to_the_given_owner_when_user_is_absent():
    respx.get(f"{API}jobs").mock(return_value=httpx.Response(200, json=_job(user=None)))
    result = respx.post(f"{API}result").mock(
        return_value=httpx.Response(200, json="https://storage.test/r.zip?signature=s")
    )

    res = runner.invoke(
        app, ["--json", "results", "job-1", "--email", MEMBER, "--show-url"], env=ENV
    )

    assert res.exit_code == 0, res.stdout
    assert json.loads(result.calls.last.request.content)["jobEmail"] == MEMBER
