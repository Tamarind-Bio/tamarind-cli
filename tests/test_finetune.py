"""Finetune tools submit through POST /finetune and /finetune-batch.

The server contract: /finetune and /finetune-batch take the /submit-job and
/submit-batch bodies with the tool under `model`. Once the server's switch is on,
/submit-job and /submit-batch refuse a finetune tool with HTTP 400
`code: "use_finetune_endpoint"`, and the finetune routes refuse an ordinary tool with
`code: "not_a_finetune_tool"`. Until the server ships the finetune routes they 404.

The CLI follows the server's answer and resends ONCE:
  /submit-job     400 use_finetune_endpoint      -> /finetune       (type -> model)
  /submit-batch   400 use_finetune_endpoint      -> /finetune-batch (type -> model)
  /finetune       400 not_a_finetune_tool or 404 -> /submit-job     (model -> type)
  /finetune-batch 400 not_a_finetune_tool or 404 -> /submit-batch   (model -> type)
A batch is always one request — never split into jobs.
"""

from __future__ import annotations

import json
from types import SimpleNamespace

import httpx
import pytest
import respx
from typer.testing import CliRunner

from tamarind.cli.commands import jobs as jobs_commands
from tamarind.cli.main import app
from tamarind.cli.output import OutputMode
from tamarind.errors import TamarindError, ValidationError
from tamarind.http import HTTPClient

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
NOT_FOUND = httpx.Response(404, text="<html>404: This page could not be found.</html>")
OK = httpx.Response(200, json={"message": "queued"})


def _body(route, index=-1):
    return json.loads(route.calls[index].request.content)


def _invoke(args):
    return runner.invoke(app, ["--json", *args], env=ENV)


# ── the resend rule, endpoint by endpoint ────────────────────────────────────────────


def _post_to(endpoint):
    """Send a job (or batch) to ``endpoint`` through the command helpers."""
    state = SimpleNamespace(output=OutputMode(json=True, quiet=True))
    with HTTPClient(API, "k") as client:
        if "batch" in endpoint:
            return jobs_commands._submit_batch(
                client, state, endpoint=endpoint, batch_name="b", tool="some-tool",
                settings_list=[{"x": 1}], job_names=["j"], max_runtime=None,
            )
        return jobs_commands._submit_single(
            client, state, endpoint=endpoint, job_name="j", tool="some-tool", settings={"x": 1},
        )


# (endpoint posted to, its answer, the endpoint it must be resent to or None)
RESEND_RULES = [
    # the ordinary endpoints: only the exact use_finetune_endpoint refusal moves them
    ("/submit-job", USE_FINETUNE_400, "/finetune"),
    ("/submit-batch", USE_FINETUNE_400, "/finetune-batch"),
    ("/submit-job", NOT_FOUND, None),
    ("/submit-batch", NOT_FOUND, None),
    ("/submit-job", NOT_A_FINETUNE_400, None),
    ("/submit-batch", NOT_A_FINETUNE_400, None),
    ("/submit-batch", httpx.Response(400, json={"error": "bad", "code": "invalid_settings"}), None),
    ("/submit-job", httpx.Response(400, text="use_finetune_endpoint"), None),  # the code is a JSON field
    ("/submit-job", httpx.Response(422, json=USE_FINETUNE_400.json()), None),  # only a 400 is the refusal
    ("/submit-batch", httpx.Response(403, json=USE_FINETUNE_400.json()), None),
    # the finetune endpoints: not_a_finetune_tool, or a 404 before the server ships them
    ("/finetune", NOT_A_FINETUNE_400, "/submit-job"),
    ("/finetune-batch", NOT_A_FINETUNE_400, "/submit-batch"),
    ("/finetune", NOT_FOUND, "/submit-job"),
    ("/finetune-batch", NOT_FOUND, "/submit-batch"),
    ("/finetune", USE_FINETUNE_400, None),
    ("/finetune-batch", httpx.Response(400, json={"error": "bad", "code": "invalid_settings"}), None),
    # a 400 whose message says "not found" maps to NotFoundError too — it is not a 404
    ("/finetune", httpx.Response(400, json={"error": "Tool not found"}), None),
    ("/finetune", httpx.Response(405, text="Method Not Allowed"), None),
    ("/finetune-batch", httpx.Response(500, text="boom"), None),
]


@respx.mock
@pytest.mark.parametrize(("endpoint", "answer", "resent_to"), RESEND_RULES)
def test_resend_rule(endpoint, answer, resent_to):
    first = respx.post(f"{API}{endpoint.lstrip('/')}").mock(return_value=answer)
    others = {
        e: respx.post(f"{API}{e.lstrip('/')}").mock(return_value=OK)
        for e in ("/submit-job", "/submit-batch", "/finetune", "/finetune-batch")
        if e != endpoint
    }

    if resent_to is None:
        with pytest.raises(TamarindError) as exc:
            _post_to(endpoint)
        assert exc.value.http_status == answer.status_code
        assert first.call_count == 1
        assert not any(route.called for route in others.values())
        return

    response, used = _post_to(endpoint)
    assert used == resent_to and response == {"message": "queued"}
    assert first.call_count == 1 and others[resent_to].call_count == 1
    assert sum(route.call_count for route in others.values()) == 1
    sent_first, resent = _body(first), _body(others[resent_to])
    to_key, from_key = ("model", "type") if "finetune" in resent_to else ("type", "model")
    assert resent[to_key] == "some-tool" and from_key not in resent
    assert {k: v for k, v in resent.items() if k != to_key} == {
        k: v for k, v in sent_first.items() if k != from_key
    }


@respx.mock
@pytest.mark.parametrize(
    ("endpoint", "other", "second"),
    [
        ("/submit-job", "/finetune", NOT_A_FINETUNE_400),
        ("/submit-batch", "/finetune-batch", NOT_FOUND),
        ("/finetune", "/submit-job", USE_FINETUNE_400),
        ("/finetune-batch", "/submit-batch", USE_FINETUNE_400),
    ],
)
def test_resend_happens_once_and_the_second_answer_surfaces(endpoint, other, second):
    first_answer = USE_FINETUNE_400 if endpoint.startswith("/submit") else NOT_FOUND
    first = respx.post(f"{API}{endpoint.lstrip('/')}").mock(return_value=first_answer)
    resend = respx.post(f"{API}{other.lstrip('/')}").mock(return_value=second)

    with pytest.raises(TamarindError) as exc:
        _post_to(endpoint)

    assert exc.value.http_status == second.status_code
    assert first.call_count == 1 and resend.call_count == 1


# ── submit ───────────────────────────────────────────────────────────────────────────


@respx.mock
def test_submit_resubmits_a_refused_finetune_tool_to_finetune_with_model():
    submit = respx.post(f"{API}submit-job").mock(return_value=USE_FINETUNE_400)
    finetune = respx.post(f"{API}finetune").mock(return_value=OK)

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
    submit = respx.post(f"{API}submit-job").mock(return_value=OK)
    finetune = respx.post(f"{API}finetune")

    res = _invoke(["submit", "boltz", "--set", "sequence=MKT", "--name", "b1", "--skip-validate"])

    assert res.exit_code == 0, res.output
    assert _body(submit) == {
        "jobName": "b1", "type": "boltz", "settings": {"sequence": "MKT"}, "jobSource": "CLI",
    }
    assert not finetune.called
    assert json.loads(res.stdout)["endpoint"] == "/submit-job"


@respx.mock
def test_a_second_refusal_surfaces_with_the_submit_context():
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
    finetune = respx.post(f"{API}finetune").mock(return_value=OK)

    res = _invoke(["finetune", "chemprop-finetune", "--set", "csvFile=a.csv", "--name", "m1"])

    assert res.exit_code == 0, res.output
    assert _body(validate)["type"] == "chemprop-finetune"
    assert _body(finetune)["model"] == "chemprop-finetune"
    assert "type" not in _body(finetune)
    assert not submit.called
    out = json.loads(res.stdout)
    assert out["endpoint"] == "/finetune" and out["jobName"] == "m1"


@respx.mock
@pytest.mark.parametrize(
    "finetune_answer",
    [
        NOT_A_FINETUNE_400,  # an ordinary tool
        NOT_FOUND,  # a server that has not shipped /finetune yet
    ],
)
def test_finetune_command_resends_to_submit_job_with_type(finetune_answer):
    finetune = respx.post(f"{API}finetune").mock(return_value=finetune_answer)
    submit = respx.post(f"{API}submit-job").mock(return_value=OK)

    res = _invoke(
        ["finetune", "chemprop-finetune", "--set", "csvFile=a.csv", "--name", "m1", "--skip-validate"]
    )

    assert res.exit_code == 0, res.output
    assert finetune.call_count == 1 and submit.call_count == 1
    assert _body(submit) == {
        "jobName": "m1", "type": "chemprop-finetune", "settings": {"csvFile": "a.csv"},
        "jobSource": "CLI",
    }
    assert json.loads(res.stdout)["endpoint"] == "/submit-job"


# ── batch: sends what it always sent; one resend of the whole batch ──────────────────


def _batch_file(tmp_path, doc):
    path = tmp_path / "batch.json"
    path.write_text(json.dumps(doc))
    return str(path)


BATCH_DOC = {"settings": [{"csvFile": "a.csv"}, {"csvFile": "b.csv"}], "jobNames": ["one", "two"]}


def _batch_args(tmp_path, tool="chemprop-finetune", doc=BATCH_DOC):
    return ["batch", tool, "--name", "ft", "--max-runtime", "600", "--input", _batch_file(tmp_path, doc)]


def _main_batch_body(tool):
    """Exactly what `batch` posted to /submit-batch before finetune routing existed."""
    return {
        "batchName": "ft", "type": tool, "settings": BATCH_DOC["settings"],
        "jobSource": "CLI", "jobNames": ["one", "two"], "maxRuntimeSeconds": 600,
    }


@respx.mock
def test_refused_finetune_batch_is_resent_whole_to_finetune_batch(tmp_path):
    batch = respx.post(f"{API}submit-batch").mock(return_value=USE_FINETUNE_400)
    finetune_batch = respx.post(f"{API}finetune-batch").mock(return_value=OK)
    finetune = respx.post(f"{API}finetune")

    res = _invoke(_batch_args(tmp_path))

    assert res.exit_code == 0, res.output
    assert batch.call_count == 1 and finetune_batch.call_count == 1, "one atomic request, never split"
    assert not finetune.called
    assert _body(batch) == _main_batch_body("chemprop-finetune")
    expected = _main_batch_body("chemprop-finetune")
    expected["model"] = expected.pop("type")
    assert _body(finetune_batch) == expected
    out = json.loads(res.stdout)
    assert out["endpoint"] == "/finetune-batch"
    assert out["count"] == 2 and out["submit"] == {"message": "queued"}


@respx.mock
@pytest.mark.parametrize("tool", ["chemprop-finetune", "boltz"])  # finetune: before the switch
def test_an_accepted_batch_is_sent_once_unchanged(tmp_path, tool):
    batch = respx.post(f"{API}submit-batch").mock(return_value=OK)
    finetune_batch = respx.post(f"{API}finetune-batch")
    finetune = respx.post(f"{API}finetune")

    res = _invoke(_batch_args(tmp_path, tool))

    assert res.exit_code == 0, res.output
    assert batch.call_count == 1 and _body(batch) == _main_batch_body(tool)
    assert not finetune_batch.called and not finetune.called
    assert json.loads(res.stdout)["endpoint"] == "/submit-batch"


@respx.mock
@pytest.mark.parametrize(
    ("submit_batch_answer", "finetune_batch_answer"),
    [
        # an ordinary rejection is not resent
        (httpx.Response(400, json={"error": "bad", "code": "invalid_settings"}), None),
        # a rejected resend surfaces with the batch's error context
        (USE_FINETUNE_400, httpx.Response(400, json={"error": "Your org requires a project tag."})),
    ],
)
def test_a_rejected_batch_surfaces_with_the_batch_context(
    tmp_path, submit_batch_answer, finetune_batch_answer
):
    batch = respx.post(f"{API}submit-batch").mock(return_value=submit_batch_answer)
    finetune_batch = respx.post(f"{API}finetune-batch").mock(
        return_value=finetune_batch_answer or OK
    )

    res = _invoke(_batch_args(tmp_path))

    assert isinstance(res.exception, ValidationError)
    assert res.exception.detail["phase"] == "submit-batch"
    assert res.exception.detail["submitted"] is False
    assert batch.call_count == 1
    assert finetune_batch.call_count == (1 if finetune_batch_answer else 0)


# ── an input file may name the tool as `model` ───────────────────────────────────────


def _input_file(tmp_path, doc):
    path = tmp_path / "job.json"
    path.write_text(json.dumps(doc))
    return str(path)


@respx.mock
@pytest.mark.parametrize(
    ("command", "tool", "doc", "route"),
    [
        # `model` makes {jobName, model, settings} a wrapper, exactly like `type`
        ("finetune", "chemprop-finetune",
         {"jobName": "m1", "model": "chemprop-finetune", "settings": {"csvFile": "a.csv"}}, "finetune"),
        ("finetune", "chemprop-finetune",
         {"model": " Chemprop-Finetune ", "settings": {"csvFile": "a.csv"}}, "finetune"),
        ("submit", "chemprop-finetune",
         {"jobName": "m1", "model": "chemprop-finetune", "settings": {"csvFile": "a.csv"}}, "submit-job"),
    ],
)
def test_an_input_file_carrying_a_matching_model_is_a_wrapper(tmp_path, command, tool, doc, route):
    posted = respx.post(f"{API}{route}").mock(return_value=OK)

    res = _invoke([command, tool, "--input", _input_file(tmp_path, doc), "--skip-validate"])

    assert res.exit_code == 0, res.output
    body = _body(posted)
    assert body["settings"] == {"csvFile": "a.csv"}, "the wrapper's settings, not the wrapper"
    if "jobName" in doc:
        assert body["jobName"] == doc["jobName"]


@respx.mock
@pytest.mark.parametrize(
    ("args", "doc"),
    [
        (["finetune", "chemprop-finetune"], {"model": "esmc-finetune", "settings": {}}),
        (["finetune", "chemprop-finetune"], {"jobName": "m1", "model": 1, "settings": {}}),
        (["finetune", "chemprop-finetune"], {"type": "boltz", "settings": {}}),
        (["submit", "boltz"], {"model": "esmfold", "settings": {}}),
        (["validate", "boltz"], {"model": "esmfold", "settings": {}}),
        # a type that agrees does not excuse a model that does not
        (["submit", "boltz"], {"type": "boltz", "model": "esmfold", "settings": {}}),
    ],
)
def test_an_input_file_model_that_differs_from_the_command_tool_is_rejected(tmp_path, args, doc):
    routes = [respx.post(f"{API}{r}").mock(return_value=OK)
              for r in ("validate-job", "submit-job", "finetune")]

    res = _invoke([*args, "--input", _input_file(tmp_path, doc), "--skip-validate"]
                  if args[0] != "validate" else [*args, "--input", _input_file(tmp_path, doc)])

    assert isinstance(res.exception, ValidationError), res.output
    assert "Tool mismatch" in res.exception.message
    assert not any(route.called for route in routes)


@respx.mock
def test_a_batch_file_model_that_differs_from_the_command_tool_is_rejected(tmp_path):
    batch = respx.post(f"{API}submit-batch").mock(return_value=OK)

    res = _invoke(_batch_args(tmp_path, doc={**BATCH_DOC, "model": "esmc-finetune"}))

    assert isinstance(res.exception, ValidationError)
    assert "model" in res.exception.message
    assert not batch.called
