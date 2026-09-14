"""Finetune tools submit through POST /finetune, not /submit-job.

The server contract: /finetune takes the /submit-job body with the tool under
`model`. Once the server's switch is on, /submit-job and /submit-batch refuse a
finetune tool with HTTP 400 `code: "use_finetune_endpoint"`, and /finetune refuses
an ordinary tool with `code: "not_a_finetune_tool"`. There is no batch finetune
endpoint. The CLI follows the refusal: one resubmission for single jobs, and a
refused finetune batch is split into individual /finetune jobs.
"""

from __future__ import annotations

import json

import httpx
import pytest
import respx
from typer.testing import CliRunner

from tamarind.cli.main import app
from tamarind.errors import TamarindError, ValidationError

runner = CliRunner()
API = "https://api.test/"
CAT = "https://cat.test/"
ENV = {
    "TAMARIND_API_KEY": "k",
    "TAMARIND_API_BASE": API,
    "TAMARIND_CATALOG_BASE": CAT,
}

USE_FINETUNE_400 = httpx.Response(
    400,
    json={
        "error": "chemprop-finetune is a finetune tool; submit it to /finetune.",
        "code": "use_finetune_endpoint",
        "endpoint": "/finetune",
    },
)
NOT_A_FINETUNE_400 = httpx.Response(
    400,
    json={"error": "boltz is not a finetune tool.", "code": "not_a_finetune_tool"},
)


def _body(route, index=-1):
    return json.loads(route.calls[index].request.content)


def _invoke(args):
    return runner.invoke(app, ["--json", *args], env=ENV)


# ── submit ───────────────────────────────────────────────────────────────────────────


@respx.mock
def test_submit_resubmits_a_refused_finetune_tool_to_finetune_with_model():
    submit = respx.post(f"{API}submit-job").mock(return_value=USE_FINETUNE_400)
    finetune = respx.post(f"{API}finetune").mock(
        return_value=httpx.Response(200, json={"message": "queued"})
    )

    res = _invoke(
        ["submit", "chemprop-finetune", "--set", "csvFile=a.csv", "--name", "m1", "--skip-validate"]
    )

    assert res.exit_code == 0, res.output
    assert submit.call_count == 1 and finetune.call_count == 1
    assert _body(finetune) == {
        "jobName": "m1",
        "model": "chemprop-finetune",
        "settings": {"csvFile": "a.csv"},
        "jobSource": "CLI",
    }
    out = json.loads(res.stdout)
    assert out["endpoint"] == "/finetune"
    assert out["submit"] == {"message": "queued"}


@respx.mock
def test_submit_leaves_an_ordinary_tool_on_submit_job():
    submit = respx.post(f"{API}submit-job").mock(
        return_value=httpx.Response(200, json={"message": "queued"})
    )
    finetune = respx.post(f"{API}finetune")

    res = _invoke(["submit", "boltz", "--set", "sequence=MKT", "--name", "b1", "--skip-validate"])

    assert res.exit_code == 0, res.output
    assert _body(submit)["type"] == "boltz" and "model" not in _body(submit)
    assert not finetune.called
    assert json.loads(res.stdout)["endpoint"] == "/submit-job"


@respx.mock
@pytest.mark.parametrize(
    "refusal",
    [
        httpx.Response(400, json={"error": "invalid settings", "code": "invalid_settings"}),
        httpx.Response(400, json={"error": "Tool not found"}),
        httpx.Response(400, text="use_finetune_endpoint"),  # the code is a JSON field, not text
        NOT_A_FINETUNE_400,  # the OTHER endpoint's refusal does not redirect /submit-job
    ],
)
def test_submit_does_not_resubmit_on_any_other_rejection(refusal):
    submit = respx.post(f"{API}submit-job").mock(return_value=refusal)
    finetune = respx.post(f"{API}finetune")

    res = _invoke(["submit", "boltz", "--set", "sequence=MKT", "--name", "b1", "--skip-validate"])

    assert res.exit_code != 0
    assert submit.call_count == 1
    assert not finetune.called


@respx.mock
def test_resubmission_happens_once_and_the_second_refusal_surfaces():
    submit = respx.post(f"{API}submit-job").mock(return_value=USE_FINETUNE_400)
    finetune = respx.post(f"{API}finetune").mock(return_value=NOT_A_FINETUNE_400)

    res = _invoke(["submit", "odd-tool", "--name", "x1", "--skip-validate"])

    assert isinstance(res.exception, ValidationError)
    assert res.exception.detail["code"] == "not_a_finetune_tool"
    assert res.exception.detail["submitted"] is False
    assert submit.call_count == 1 and finetune.call_count == 1


# ── finetune ─────────────────────────────────────────────────────────────────────────


@respx.mock
def test_finetune_command_validates_then_posts_finetune_with_model():
    validate = respx.post(f"{API}validate-job").mock(
        return_value=httpx.Response(200, json={"valid": True})
    )
    submit = respx.post(f"{API}submit-job")
    finetune = respx.post(f"{API}finetune").mock(
        return_value=httpx.Response(200, json={"message": "queued"})
    )

    res = _invoke(["finetune", "chemprop-finetune", "--set", "csvFile=a.csv", "--name", "m1"])

    assert res.exit_code == 0, res.output
    assert _body(validate)["type"] == "chemprop-finetune"
    assert _body(finetune)["model"] == "chemprop-finetune"
    assert "type" not in _body(finetune)
    assert not submit.called
    out = json.loads(res.stdout)
    assert out["endpoint"] == "/finetune" and out["jobName"] == "m1"


@respx.mock
def test_finetune_command_resubmits_an_ordinary_tool_to_submit_job():
    finetune = respx.post(f"{API}finetune").mock(return_value=NOT_A_FINETUNE_400)
    submit = respx.post(f"{API}submit-job").mock(
        return_value=httpx.Response(200, json={"message": "queued"})
    )

    res = _invoke(["finetune", "boltz", "--set", "sequence=MKT", "--name", "b1", "--skip-validate"])

    assert res.exit_code == 0, res.output
    assert finetune.call_count == 1
    assert _body(submit)["type"] == "boltz" and "model" not in _body(submit)
    assert json.loads(res.stdout)["endpoint"] == "/submit-job"


# ── batch ────────────────────────────────────────────────────────────────────────────


def _batch_file(tmp_path, doc):
    path = tmp_path / "batch.json"
    path.write_text(json.dumps(doc))
    return str(path)


@respx.mock
@pytest.mark.parametrize(
    ("job_names", "expected"),
    [
        # Supplied names gain the batch prefix unless they already carry it — the
        # names /submit-batch itself would have created.
        (["one", "ft-two"], ["ft-one", "ft-two"]),
        # No names: the server's `<batchName>-<index>` from 0.
        (None, ["ft-0", "ft-1"]),
    ],
)
def test_refused_finetune_batch_is_split_into_individual_finetune_jobs(
    tmp_path, job_names, expected
):
    batch = respx.post(f"{API}submit-batch").mock(return_value=USE_FINETUNE_400)
    finetune = respx.post(f"{API}finetune").mock(
        return_value=httpx.Response(200, json={"message": "queued"})
    )
    doc = {"settings": [{"csvFile": "a.csv"}, {"csvFile": "b.csv"}]}
    if job_names is not None:
        doc["jobNames"] = job_names

    res = _invoke(
        ["batch", "chemprop-finetune", "--name", "ft", "--max-runtime", "600",
         "--input", _batch_file(tmp_path, doc)]
    )

    assert res.exit_code == 0, res.output
    assert batch.call_count == 1 and finetune.call_count == 2
    bodies = [json.loads(call.request.content) for call in finetune.calls]
    assert [b["jobName"] for b in bodies] == expected
    assert [b["settings"] for b in bodies] == doc["settings"]
    for b in bodies:
        assert b["model"] == "chemprop-finetune" and "type" not in b
        assert b["maxRuntimeSeconds"] == 600
        assert b["jobSource"] == "CLI"
    out = json.loads(res.stdout)
    assert out["endpoint"] == "/finetune"
    assert out["jobNames"] == expected
    assert out["count"] == 2 and len(out["submit"]) == 2


@respx.mock
def test_split_stops_at_the_first_rejection_and_names_what_went_in(tmp_path):
    respx.post(f"{API}submit-batch").mock(return_value=USE_FINETUNE_400)
    finetune = respx.post(f"{API}finetune").mock(
        side_effect=[
            httpx.Response(200, json={"message": "queued"}),
            httpx.Response(400, json={"error": "Your org requires a project tag."}),
        ]
    )
    doc = {"settings": [{}, {}, {}], "jobNames": ["a", "b", "c"]}

    res = _invoke(["batch", "chemprop-finetune", "--name", "ft", "--input", _batch_file(tmp_path, doc)])

    assert isinstance(res.exception, TamarindError)
    assert finetune.call_count == 2
    detail = res.exception.detail
    assert detail["failedJob"] == "ft-b"
    assert detail["submittedJobs"] == ["ft-a"]
    assert detail["notSubmittedJobs"] == ["ft-b", "ft-c"]
    assert detail["submitted"] is True
    assert detail["endpoint"] == "/finetune"


@respx.mock
def test_split_is_capped_before_anything_is_submitted(tmp_path, monkeypatch):
    from tamarind.cli.commands import jobs as jobs_commands

    monkeypatch.setattr(jobs_commands, "_MAX_FINETUNE_SPLIT", 2)
    respx.post(f"{API}submit-batch").mock(return_value=USE_FINETUNE_400)
    finetune = respx.post(f"{API}finetune")

    res = _invoke(
        ["batch", "chemprop-finetune", "--name", "ft", "--input", _batch_file(tmp_path, [{}, {}, {}])]
    )

    assert isinstance(res.exception, ValidationError)
    assert not finetune.called


@respx.mock
def test_an_ordinary_batch_rejection_is_not_split(tmp_path):
    respx.post(f"{API}submit-batch").mock(
        return_value=httpx.Response(400, json={"error": "bad", "code": "invalid_settings"})
    )
    finetune = respx.post(f"{API}finetune")

    res = _invoke(["batch", "boltz", "--name", "b", "--input", _batch_file(tmp_path, [{}, {}])])

    assert isinstance(res.exception, ValidationError)
    assert res.exception.detail["phase"] == "submit-batch"
    assert not finetune.called


@respx.mock
def test_an_accepted_batch_is_not_split(tmp_path):
    # Before the server's switch is on, /submit-batch still takes finetune tools.
    respx.post(f"{API}submit-batch").mock(return_value=httpx.Response(200, json={"ok": True}))
    finetune = respx.post(f"{API}finetune")

    res = _invoke(
        ["batch", "chemprop-finetune", "--name", "ft", "--input", _batch_file(tmp_path, [{}, {}])]
    )

    assert res.exit_code == 0, res.output
    assert not finetune.called
    assert json.loads(res.stdout)["endpoint"] == "/submit-batch"
