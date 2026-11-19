"""The public SDK on v1: one client, today's signatures, v1 behind the server's switch."""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from tamarind import Tamarind, rest
from tamarind._v1.classic import APIProblem, NotFoundProblem, ValidationProblem
from tamarind._v1.errors import ProblemError
from tamarind._v1.switch import V1NotEnabledError
from tamarind.errors import APIError, AuthError, NotFoundError, ValidationError
from tamarind.http import HTTPClient

from conftest import turn_v1_on

CLASSIC = "https://app.tamarind.bio/api/"
V1 = "https://api.tamarind.bio"
JOB = "job_0f8fad5b-d9cb-469f-a165-70867728950e"


def _problem(status: int, code: str) -> httpx.Response:
    return httpx.Response(
        status,
        json={"type": "about:blank", "title": code, "status": status, "code": code, "detail": f"{status} {code}"},
        headers={"content-type": "application/problem+json"},
    )


@pytest.fixture
def on(monkeypatch):
    monkeypatch.delenv("TAMARIND_V1_API_BASE", raising=False)
    monkeypatch.delenv("TAMARIND_API", raising=False)
    turn_v1_on(monkeypatch)


def test_tamarind_is_the_one_public_entry_point():
    import tamarind

    assert tamarind.__all__ == ["Tamarind", "__version__"]
    assert "v1" not in dir(tamarind)


@respx.mock
def test_with_v1_off_todays_methods_are_classic_and_v1_is_never_called():
    classic = respx.post(f"{CLASSIC}submit-job").mock(return_value=httpx.Response(200, text="n1 submitted to queue."))
    v1 = respx.route(host="api.tamarind.bio")
    with Tamarind(api_key="k", api_base=CLASSIC) as client:
        assert client.jobs.submit("esmfold", {"sequence": "MK"}, name="n1") == "n1 submitted to queue."
    assert classic.called and not v1.called


@respx.mock
def test_with_v1_on_todays_submit_goes_to_v1_and_answers_as_classic(on):
    v1 = respx.post(f"{V1}/jobs").mock(
        return_value=httpx.Response(201, json={"kind": "job", "id": JOB, "name": "n1", "status": "In Queue"})
    )
    classic = respx.route(host="app.tamarind.bio")
    with Tamarind(api_key="k", api_base=CLASSIC) as client:
        assert client.jobs.submit("esmfold", {"sequence": "MK"}, name="n1") == "n1 submitted to queue."
    body = json.loads(v1.calls[0].request.content)
    assert body == {"kind": "job", "tool": "esmfold", "name": "n1", "settings": {"sequence": "MK"}}
    assert v1.calls[0].request.headers["idempotency-key"]
    assert not classic.called


@respx.mock
def test_tamarind_rest_with_a_callers_own_client_routes_too(on):
    respx.get(f"{V1}/jobs").mock(return_value=httpx.Response(200, json={"items": [], "nextCursor": None}))
    with HTTPClient(CLASSIC, "k") as client:
        assert rest.get_jobs(client, limit=5) == {
            "jobs": [], "statuses": {"Complete": 0, "In Queue": 0, "Running": 0, "Stopped": 0},
        }


@respx.mock
def test_v1_refusals_are_also_the_classic_error_class(on):
    respx.post(f"{V1}/jobs").mock(return_value=_problem(422, "unknown_field"))
    respx.get(f"{V1}/jobs").mock(return_value=_problem(404, "not_found"))
    respx.post(f"{V1}/jobs/validate").mock(return_value=_problem(503, "service_unavailable"))
    with Tamarind(api_key="k", api_base=CLASSIC) as client:
        with pytest.raises(ValidationError) as invalid:
            client.jobs.submit("esmfold", {"sequnce": "MK"}, name="n1")
        assert isinstance(invalid.value, ProblemError) and isinstance(invalid.value, ValidationProblem)
        assert invalid.value.code == "unknown_field" and invalid.value.exit_code == 5
        with pytest.raises(NotFoundError) as missing:
            client.jobs.list(limit=1)
        assert isinstance(missing.value, NotFoundProblem) and missing.value.exit_code == 4
    with HTTPClient(CLASSIC, "k") as http:
        http._v1 = http._new_v1(max_retries=0)
        with pytest.raises(APIError) as down:
            rest.validate_job(http, job_name="n", job_type="esmfold", settings={})
        assert isinstance(down.value, APIProblem) and down.value.status_code == 503


@respx.mock
def test_v1_only_operations_work_with_v1_on(on):
    route = respx.get(f"{V1}/projects").mock(
        return_value=httpx.Response(200, json={"items": [{"id": "p1"}], "nextCursor": None})
    )
    respx.get(f"{V1}/jobs/{JOB}").mock(return_value=httpx.Response(200, json={"id": JOB, "kind": "job"}))
    with Tamarind(api_key="k", api_base=CLASSIC) as client:
        assert client.projects.list(limit=10)["items"] == [{"id": "p1"}]
        assert list(Tamarind.paginate(client.projects.list)) == [{"id": "p1"}]
        assert client.jobs.get(JOB)["id"] == JOB
    assert route.calls[0].request.url.params["limit"] == "10"


@pytest.mark.parametrize(
    "call",
    [
        lambda c: c.projects.list(),
        lambda c: c.projects.notes.get("p1"),
        lambda c: c.me.get(),
        lambda c: c.jobs.get(JOB),
        lambda c: c.tools.facets(),
        lambda c: c.files.get(path="a.pdb"),
        lambda c: c.pipelines.submit({}),
        lambda c: c.custom_tools.validate_config({}),
        lambda c: c.jobs.list(kind="batch"),
        lambda c: c.jobs.list(status=["Running"]),
        lambda c: Tamarind.paginate(c.projects.list),
    ],
)
@respx.mock
def test_with_v1_off_v1_only_operations_send_nothing(call):
    everything = respx.route()
    with Tamarind(api_key="k", api_base=CLASSIC) as client:
        with pytest.raises(V1NotEnabledError, match="isn't enabled for this account yet") as refused:
            result = call(client)
            if hasattr(result, "__next__"):
                next(result)
    assert refused.value.exit_code == 2
    assert not everything.called


def test_without_a_key_a_v1_only_operation_says_so(monkeypatch):
    monkeypatch.delenv("TAMARIND_API_KEY", raising=False)
    with Tamarind(api_key=None, api_base=CLASSIC, profile="nobody") as client:
        with pytest.raises(AuthError, match="No API key"):
            client.projects.list()


@respx.mock
def test_jobs_list_v1_filters_reach_list_jobs(on):
    route = respx.get(f"{V1}/jobs").mock(return_value=httpx.Response(200, json={"items": [], "nextCursor": None}))
    with Tamarind(api_key="k", api_base=CLASSIC) as client:
        client.jobs.list(kind="batch", status=["Running", "In Queue"], tool="boltz", limit=3)
        params = route.calls[0].request.url.params
        assert (params["kind"], params["status"], params["tool"], params["limit"]) == (
            "batch", "Running,In Queue", "boltz", "3",
        )
        with pytest.raises(ValidationError, match="can't be combined"):
            client.jobs.list(kind="batch", organization=True)
        with pytest.raises(ValidationError, match="can't be combined"):
            client.jobs.list(kind="batch", job_name="n1")


@respx.mock
def test_pipeline_run_reads_go_to_the_v1_base(on):
    run = {
        "id": "run_1", "templateId": "t1", "templateVersion": None, "name": None, "source": "production", "failureReason": None,
        "status": "finished", "startedAt": "2026-11-19T00:00:00Z", "completedAt": None, "inputs": {},
        "nodeRuns": [],
    }
    v1 = respx.get(f"{V1}/pipelines/runs/run_1").mock(return_value=httpx.Response(200, json=run))
    with Tamarind(api_key="k", api_base=CLASSIC) as client:
        assert client.pipelines.get_run("run_1").id == "run_1"
    assert v1.called


@respx.mock
def test_uploads_go_to_v1(on, tmp_path):
    local = tmp_path / "a.fasta"
    local.write_text(">a\nMK\n")
    route = respx.post(f"{V1}/files").mock(
        return_value=httpx.Response(201, json={"file": {"path": "a.fasta"}, "upload": None})
    )
    with Tamarind(api_key="k", api_base=CLASSIC) as client:
        assert client.files.upload(local) == {"ok": True, "filename": "a.fasta", "bytes": 6}
    assert json.loads(route.calls[0].request.content)["path"] == "a.fasta"


def test_paginate_takes_only_v1_operations():
    with Tamarind(api_key="k", api_base=CLASSIC) as client:
        with pytest.raises(TypeError, match="v1 list operation"):
            Tamarind.paginate(client.jobs.list)


@respx.mock
def test_node_run_molecules_from_v1_are_read_in_classics_shape(on):
    run = {
        "id": "run_1", "templateId": "t1", "templateVersion": None, "name": None, "source": "production",
        "failureReason": None, "status": "finished", "startedAt": "2026-11-19T00:00:00Z", "completedAt": None,
        "inputs": {},
        "nodeRuns": [{
            "id": "nr_1", "nodeId": "dock", "label": "Dock", "nodeType": "tool", "status": "finished",
            "startedAt": None, "completedAt": None, "outputCount": 1, "jobsTotal": 1, "jobsComplete": 1,
            "outputGroup": None, "failureReason": None,
        }],
    }
    respx.get(f"{V1}/pipelines/runs/run_1").mock(return_value=httpx.Response(200, json=run))
    page = respx.get(f"{V1}/pipelines/runs/run_1/node-runs/nr_1/molecules").mock(
        return_value=httpx.Response(200, json={
            "items": [{"id": "mol_1", "name": "c1", "moleculeType": "protein", "sequence": "MK",
                       "scores": {"dock": {"score": -8.2}}, "hasStructure": True}],
            "nextCursor": "page-2", "inputGroupId": "grp_1", "inputGroupExact": True,
        })
    )
    with Tamarind(api_key="k", api_base=CLASSIC) as client:
        molecules = client.pipelines.get_run("run_1").node_runs[0].molecules(limit=1)
    assert molecules.next_cursor == "page-2"
    assert [(m.complex_id, m.name, m.has_structure) for m in molecules.items] == [("mol_1", "c1", True)]
    assert page.calls[0].request.url.params["limit"] == "1"


@respx.mock
def test_uploads_send_the_callers_content_type_to_v1(on, tmp_path):
    local = tmp_path / "a.pdb"
    local.write_text("ATOM\n")
    route = respx.post(f"{V1}/files").mock(
        return_value=httpx.Response(201, json={"file": {"path": "a.pdb"}, "upload": None})
    )
    with Tamarind(api_key="k", api_base=CLASSIC) as client:
        client.files.upload(local, content_type="chemical/x-pdb")
    assert json.loads(route.calls[0].request.content)["contentType"] == "chemical/x-pdb"


@respx.mock
def test_files_list_with_folders_lists_them_as_classic_does(on):
    respx.get(f"{V1}/files").mock(return_value=httpx.Response(200, json={"items": [
        {"path": "runs", "type": "folder"},
        {"path": "a.pdb", "type": "file", "modifiedAt": "2026-11-19T01:00:00Z"},
        {"path": "b.zip", "type": "file", "modifiedAt": "2026-11-19T02:00:00Z"},
    ], "nextCursor": None}))
    with Tamarind(api_key="k", api_base=CLASSIC) as client:
        assert client.files.list(include_folders=True) == ["runs/", "a.pdb"]
        assert client.files.list() == ["a.pdb"]


def test_an_async_request_asks_the_switch_off_the_event_loop(monkeypatch):
    import asyncio
    import threading
    import time

    from tamarind._v1 import switch

    main = threading.get_ident()
    seen: list[int] = []

    def slow_probe(*args, **kwargs):
        seen.append(threading.get_ident())
        time.sleep(0.2)
        return False

    monkeypatch.setattr(switch, "probe", slow_probe)
    monkeypatch.setattr(HTTPClient, "_classic_request_async", lambda self, *a, **k: asyncio.sleep(0, "answered"))

    async def run() -> tuple[str, int]:
        ticks = 0

        async def tick() -> None:
            nonlocal ticks
            while True:
                ticks += 1
                await asyncio.sleep(0.01)

        ticker = asyncio.create_task(tick())
        with HTTPClient(CLASSIC, "k") as client:
            answer = await client.request_async("GET", "custom-tools")
        ticker.cancel()
        return answer, ticks

    answer, ticks = asyncio.run(run())
    assert answer == "answered" and seen and seen[0] != main and ticks >= 5
