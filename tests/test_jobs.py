import time

import httpx
import pytest
import respx

from tamarind import jobs as jh
from tamarind.errors import (
    APIError,
    AuthError,
    BudgetError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)
from tamarind.http import HTTPClient

BASE = "https://api.test/"


def client():
    return HTTPClient(BASE, "k")


def test_status_normalization():
    assert jh.job_status({"JobStatus": "Running"}) == "Running"
    assert jh.job_status({"status": "completed"}) == "completed"
    assert jh.job_status({"batchStatus": "AggregationFailed"}) == "AggregationFailed"
    # Batch lifecycle is authoritative if a parent also carries JobStatus.
    assert jh.job_status({
        "Type": "batch", "batchStatus": "Complete", "JobStatus": "Running"
    }) == "Complete"
    assert jh.job_status({
        "Type": "boltz",
        "JobName": "batch-1-subjob-1",
        "batchName": "batch-1",
        "batchStatus": "Complete",
        "JobStatus": "Running",
    }) == "Running"
    assert jh.job_status({}) is None


def test_terminal_and_success():
    assert jh.is_terminal("Complete")
    assert jh.is_terminal("Stopped")
    assert jh.is_terminal("Deleted")
    assert jh.is_terminal("AggregationFailed")
    assert not jh.is_terminal("Running")
    assert jh.is_success("complete")
    assert not jh.is_success("Stopped")
    assert not jh.is_success("AggregationFailed")


def test_extract_single_from_list():
    resp = {"jobs": [{"JobName": "a"}, {"JobName": "b"}]}
    assert jh._extract_single(resp, "b")["JobName"] == "b"
    # falls back to first when no name match
    assert jh._extract_single(resp, "zzz")["JobName"] == "a"


def test_extract_single_object():
    assert jh._extract_single({"JobName": "a", "JobStatus": "Running"}, "a")["JobName"] == "a"


def test_extract_single_batch_parent_object():
    parent = {"batchName": "batch-1", "batchStatus": "Complete"}
    assert jh._extract_single(parent, "batch-1") == parent
    assert jh.job_name(parent) == "batch-1"


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


@respx.mock
def test_wait_polls_batch_parent_until_batch_status_terminal():
    respx.get(f"{BASE}jobs").mock(
        side_effect=[
            httpx.Response(200, json={"batchName": "batch-1", "batchStatus": "Aggregating"}),
            httpx.Response(200, json={"batchName": "batch-1", "batchStatus": "Complete"}),
        ]
    )
    final = jh.wait_for_job(client(), "batch-1", poll_interval=0)
    assert jh.job_status(final) == "Complete"
    assert jh.is_success(jh.job_status(final))


@respx.mock
def test_wait_returns_failed_batch_aggregation_without_polling_forever():
    route = respx.get(f"{BASE}jobs").mock(
        return_value=httpx.Response(
            200, json={"batchName": "batch-1", "batchStatus": "AggregationFailed"}
        )
    )
    final = jh.wait_for_job(client(), "batch-1", poll_interval=0)
    assert route.call_count == 1
    assert jh.job_status(final) == "AggregationFailed"
    assert not jh.is_success(jh.job_status(final))


@respx.mock
def test_wait_timeout_caps_sleep_to_remaining_deadline():
    respx.get(f"{BASE}jobs").mock(
        return_value=httpx.Response(200, json={"JobName": "x", "JobStatus": "Running"})
    )
    started = time.monotonic()
    with pytest.raises(jh.JobTimeoutError):
        jh.wait_for_job(client(), "x", poll_interval=10, timeout=0.01)
    assert time.monotonic() - started < 0.5


@pytest.mark.parametrize(
    "kwargs",
    [
        {"poll_interval": -1},
        {"poll_interval": float("nan")},
        {"poll_interval": float("inf")},
        {"poll_interval": -0.0},
        {"timeout": -1},
        {"timeout": float("nan")},
        {"timeout": float("inf")},
        {"timeout": -0.0},
    ],
)
@respx.mock
def test_wait_rejects_invalid_timing_values_before_polling(kwargs):
    route = respx.get(f"{BASE}jobs").mock(
        return_value=httpx.Response(200, json={"JobName": "x", "JobStatus": "Running"})
    )

    with pytest.raises(ValidationError):
        jh.wait_for_job(client(), "x", **kwargs)

    assert not route.called


@pytest.mark.parametrize(
    "exc",
    [
        AuthError("bad key"),
        BudgetError("budget exhausted"),
        NotFoundError("missing"),
        RateLimitError("slow down"),
        APIError("forbidden", status_code=403),
    ],
)
def test_wait_preserves_typed_error_when_deadline_crosses(monkeypatch, exc):
    ticks = iter([0.0, 0.1, 2.0])
    monkeypatch.setattr(jh.time, "monotonic", lambda: next(ticks))
    monkeypatch.setattr(jh, "fetch_job", lambda *args, **kwargs: (_ for _ in ()).throw(exc))

    with pytest.raises(type(exc)) as raised:
        jh.wait_for_job(client(), "x", timeout=1.0)

    assert raised.value is exc
