from __future__ import annotations

from copy import deepcopy
import json

import httpx
import pytest
import respx

from tamarind import Tamarind
from tamarind.errors import TamarindError
from tamarind.pipelines import NodeRunStatus, RunStatus, Source

BASE = "https://api.test/api/"


def _run() -> dict[str, object]:
    return {
        "id": "run/one",
        "templateId": "template-1",
        "templateVersion": "v2",
        "name": "screen",
        "source": "production",
        "status": "running",
        "startedAt": "2026-08-25T12:00:00Z",
        "completedAt": None,
        "inputs": {"input": {"group": "group-1"}},
        "nodeRuns": [
            {
                "id": "node/run one",
                "nodeId": "dock",
                "label": "Dock candidates",
                "nodeType": "tool",
                "status": "finished",
                "startedAt": "2026-08-25T12:01:00Z",
                "completedAt": "2026-08-25T12:05:00Z",
                "outputCount": 1,
                "jobsTotal": 1,
                "jobsComplete": 1,
                "outputGroup": None,
            }
        ],
    }


def _page() -> dict[str, object]:
    return {
        "molecules": [
            {
                "id": "molecule-1",
                "name": "candidate-1",
                "type": "protein",
                "sequence": "MKT",
                "scores": {"dock": {"score": -8.2}},
                "hasStructure": True,
            }
        ],
        "nextCursor": "page-2",
    }


@respx.mock
def test_get_run_exposes_node_runs_and_their_molecule_pages() -> None:
    run_route = respx.get(f"{BASE}pipelines/runs/run%2Fone").mock(
        return_value=httpx.Response(200, json=_run())
    )
    molecule_route = respx.get(
        f"{BASE}pipelines/runs/run%2Fone/node-runs/node%2Frun%20one/molecules"
    ).mock(return_value=httpx.Response(200, json=_page()))

    with Tamarind(api_key="key", api_base=BASE) as client:
        run = client.pipelines.get_run("run/one")
        page = run.node_runs[0].molecules(limit=1, cursor="page-1")

    assert run.id == "run/one"
    assert run.status is RunStatus.RUNNING
    assert run.source is Source.PRODUCTION
    assert run.node_runs[0].node_id == "dock"
    assert run.node_runs[0].node_type == "tool"
    assert run.node_runs[0].status is NodeRunStatus.FINISHED
    assert page.next_cursor == "page-2"
    assert page.items[0].id == "molecule-1"
    assert page.items[0].type == "protein"
    assert page.items[0].scores == {"dock": {"score": -8.2}}
    assert run_route.called
    assert molecule_route.called
    assert dict(molecule_route.calls.last.request.url.params) == {
        "limit": "1",
        "cursor": "page-1",
    }


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("id",), 7),
        (("inputs",), []),
        (("nodeRuns",), {}),
        (("nodeRuns", 0, "jobsTotal"), "1"),
        (("nodeRuns", 0, "outputCount"), True),
        (("nodeRuns", 0, "status"), "unknown"),
    ],
)
@respx.mock
def test_get_run_rejects_malformed_contract_values(
    path: tuple[str | int, ...], value: object
) -> None:
    body = deepcopy(_run())
    target: object = body
    for part in path[:-1]:
        target = target[part]  # type: ignore[index]
    target[path[-1]] = value  # type: ignore[index]
    respx.get(f"{BASE}pipelines/runs/run-1").mock(return_value=httpx.Response(200, json=body))

    with Tamarind(api_key="key", api_base=BASE) as client:
        with pytest.raises(TamarindError, match="generated contract"):
            client.pipelines.get_run("run-1")


@pytest.mark.parametrize("limit", [0, 101, True, 1.5])
@respx.mock
def test_node_run_molecules_validates_page_size_before_request(limit: object) -> None:
    respx.get(f"{BASE}pipelines/runs/run%2Fone").mock(return_value=httpx.Response(200, json=_run()))
    with Tamarind(api_key="key", api_base=BASE) as client:
        node_run = client.pipelines.get_run("run/one").node_runs[0]
        with pytest.raises(ValueError, match="1 to 100"):
            node_run.molecules(limit=limit)  # type: ignore[arg-type]


@respx.mock
def test_node_run_molecules_rejects_malformed_page() -> None:
    respx.get(f"{BASE}pipelines/runs/run%2Fone").mock(return_value=httpx.Response(200, json=_run()))
    malformed = _page()
    malformed["nextCursor"] = 2
    respx.get(f"{BASE}pipelines/runs/run%2Fone/node-runs/node%2Frun%20one/molecules").mock(
        return_value=httpx.Response(200, json=malformed)
    )

    with Tamarind(api_key="key", api_base=BASE) as client:
        with pytest.raises(TamarindError, match="generated contract"):
            client.pipelines.get_run("run/one").node_runs[0].molecules()


def test_vendored_pipelines_contract_is_exactly_scoped_and_pinned() -> None:
    from hashlib import sha256
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    raw = (root / "openapi/pipelines-v1.json").read_bytes()
    document = json.loads(raw)
    lock = json.loads((root / "openapi/pipelines-v1.lock.json").read_text())

    assert tuple(document["paths"]) == (
        "/pipelines/runs/{runId}",
        "/pipelines/runs/{runId}/node-runs/{nodeRunId}/molecules",
    )
    # Git may materialize text files with CRLF on Windows; the lock hashes the
    # canonical LF bytes produced by the sync script.
    assert sha256(raw.replace(b"\r\n", b"\n")).hexdigest() == lock["artifactSha256"]
    assert lock["sourceRepository"] == "Tamarind-Bio/tamarind-website"
    assert lock["sourceCommit"] == "2be38e2bd91c0ed5eac576883da7e12e16f6d5cc"
    assert lock["sourcePath"] == "backend/app/public_api/openapi/public-v1.generated.json"
    assert lock["generator"] == "openapi-python-client==0.28.4"
