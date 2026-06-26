import httpx
import pytest
import respx

from tamarind import jobs as jh
from tamarind.errors import NotFoundError
from tamarind.http import HTTPClient

BASE = "https://api.test/"


def client():
    return HTTPClient(BASE, "k")


def test_status_normalization():
    assert jh.job_status({"JobStatus": "Running"}) == "Running"
    assert jh.job_status({"status": "completed"}) == "completed"
    assert jh.job_status({}) is None


def test_terminal_and_success():
    assert jh.is_terminal("Complete")
    assert jh.is_terminal("Stopped")
    assert jh.is_terminal("Deleted")
    assert not jh.is_terminal("Running")
    assert jh.is_success("complete")
    assert not jh.is_success("Stopped")


def test_extract_single_from_list():
    resp = {"jobs": [{"JobName": "a"}, {"JobName": "b"}]}
    assert jh._extract_single(resp, "b")["JobName"] == "b"
    # falls back to first when no name match
    assert jh._extract_single(resp, "zzz")["JobName"] == "a"


def test_extract_single_object():
    assert jh._extract_single({"JobName": "a", "JobStatus": "Running"}, "a")["JobName"] == "a"


def test_extract_single_indexed_shape():
    # The job API returns this shape for a single-jobName query.
    resp = {
        "0": {"JobName": "cli-e2e", "JobStatus": "In Queue", "Type": "boltz"},
        "statuses": {"In Queue": 1, "Complete": 0},
    }
    job = jh._extract_single(resp, "cli-e2e")
    assert job["JobName"] == "cli-e2e"
    assert jh.job_status(job) == "In Queue"


def test_extract_single_unknown_shape_returns_none():
    assert jh._extract_single({"statuses": {"Complete": 0}}, "x") is None


@respx.mock
def test_fetch_job_not_found():
    respx.get(f"{BASE}jobs").mock(return_value=httpx.Response(200, json={"jobs": []}))
    with pytest.raises(NotFoundError):
        jh.fetch_job(client(), "missing")


@respx.mock
def test_wait_polls_until_terminal():
    respx.get(f"{BASE}jobs").mock(
        side_effect=[
            httpx.Response(200, json={"JobName": "x", "JobStatus": "Running"}),
            httpx.Response(200, json={"JobName": "x", "JobStatus": "Running"}),
            httpx.Response(200, json={"JobName": "x", "JobStatus": "Complete"}),
        ]
    )
    seen = []
    final = jh.wait_for_job(
        client(), "x", poll_interval=0, on_poll=lambda j: seen.append(jh.job_status(j))
    )
    assert jh.job_status(final) == "Complete"
    assert seen == ["Running", "Running", "Complete"]
