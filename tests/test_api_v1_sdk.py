"""Offline tests for the hand-written v1 SDK (tamarind.v1)."""

from __future__ import annotations

import base64
import json

import httpx
import pytest
import respx

from tamarind.errors import ExitCode, JobTimeoutError, TamarindError
from tamarind.v1 import ProblemError, Tamarind, paginate

BASE = "https://api.test.tamarind.bio"


def problem(status: int, code: str, **extra: object) -> dict[str, object]:
    return {
        "type": f"https://docs.tamarind.bio/errors/{code}",
        "title": "x",
        "status": status,
        "code": code,
        "requestId": "req_1",
        **extra,
    }


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Tamarind:
    monkeypatch.delenv("TAMARIND_API_BASE", raising=False)
    sdk = Tamarind("test-key", base_url=BASE)
    sdk.sleeps = []  # type: ignore[attr-defined]
    sdk._transport._sleep = sdk.sleeps.append  # type: ignore[attr-defined]
    return sdk


def test_base_url_and_key_from_the_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TAMARIND_API_BASE", raising=False)
    monkeypatch.setenv("TAMARIND_API_KEY", "env-key")
    assert Tamarind().base_url == "https://api.tamarind.bio"
    monkeypatch.setenv("TAMARIND_API_BASE", "https://api-staging.tamarind.bio/")
    sdk = Tamarind()
    assert sdk.base_url == "https://api-staging.tamarind.bio"
    assert sdk._transport._headers["x-api-key"] == "env-key"
    assert Tamarind(base_url="https://other.example").base_url == "https://other.example"


@respx.mock
def test_path_query_and_version_header(client: Tamarind) -> None:
    client._transport.version = "2026-12-01"
    route = respx.get(f"{BASE}/jobs").mock(
        return_value=httpx.Response(200, json={"items": [], "nextCursor": None})
    )
    assert client.jobs.list(status=["Running", "In Queue"], kind="batch", limit=5) == {
        "items": [],
        "nextCursor": None,
    }
    request = route.calls.last.request
    assert request.headers["x-api-key"] == "test-key"
    assert request.headers["Tamarind-Version"] == "2026-12-01"
    assert request.headers["X-Tamarind-Client-Channel"] in {"sdk", "cli"}
    # The contract's `explode: false`: one comma-joined value, not repeated keys.
    assert request.url.params.get_list("status") == ["Running,In Queue"]
    assert request.url.params["kind"] == "batch"
    assert request.url.params["limit"] == "5"

    files = respx.get(f"{BASE}/files").mock(
        return_value=httpx.Response(200, json={"items": [], "nextCursor": None})
    )
    client.files.list(extension=["pdb", "fasta"])
    assert files.calls.last.request.url.params.get_list("extension") == ["pdb,fasta"]

    respx.get(f"{BASE}/projects/proj_1/notes/entries/e%2F1").mock(
        return_value=httpx.Response(200, json={"id": "e/1"})
    )
    assert client.projects.notes.get_entry("proj_1", "e/1") == {"id": "e/1"}


def test_bad_arguments_fail_before_any_request(client: Tamarind) -> None:
    with pytest.raises(ValueError, match="not one of"):
        client.jobs.list(status="Done")
    with pytest.raises(TypeError, match="unexpected"):
        client.jobs.list(nope=1)
    with pytest.raises(TypeError, match="missing job_id"):
        client.jobs.get()
    with pytest.raises(TypeError, match="takes no request body"):
        client.me.get(body={"a": 1})


@respx.mock
def test_body_positional_or_keyword_and_idempotency_key(client: Tamarind) -> None:
    route = respx.post(f"{BASE}/jobs").mock(
        return_value=httpx.Response(201, json={"id": "job_1", "kind": "job"})
    )
    body = {"tool": "esmfold", "settings": {"sequence": "MKT"}}
    client.jobs.submit(body)
    client.jobs.submit(body=body, idempotency_key="mine")
    first, second = (call.request for call in route.calls)
    assert json.loads(first.content) == body
    assert len(first.headers["Idempotency-Key"]) == 36
    assert second.headers["Idempotency-Key"] == "mine"

    update = respx.patch(f"{BASE}/jobs/job_1").mock(return_value=httpx.Response(200, json={}))
    client.jobs.update("job_1", {"displayName": "x"})
    assert json.loads(update.calls.last.request.content) == {"displayName": "x"}
    assert "Idempotency-Key" not in update.calls.last.request.headers


@respx.mock
def test_problem_error_carries_the_problem(client: Tamarind) -> None:
    errors = [
        {"code": "unknown_field", "pointer": "/settings/x", "detail": "no", "suggestion": "y"}
    ]
    respx.post(f"{BASE}/jobs").mock(
        return_value=httpx.Response(
            422,
            json=problem(422, "validation_failed", detail="1 problem", errors=errors),
            headers={"content-type": "application/problem+json"},
        )
    )
    with pytest.raises(ProblemError) as raised:
        client.jobs.submit({"tool": "esmfold", "settings": {"x": 1}})
    error = raised.value
    assert (error.status, error.code, error.detail, error.errors) == (
        422,
        "validation_failed",
        "1 problem",
        errors,
    )
    assert error.type == "https://docs.tamarind.bio/errors/validation_failed"
    assert error.request_id == "req_1"
    assert error.exit_code == ExitCode.VALIDATION
    assert "/settings/x" in str(error) and "'y'" in str(error)


@respx.mock
def test_problem_error_from_a_non_problem_answer(client: Tamarind) -> None:
    client._transport.max_retries = 0
    respx.get(f"{BASE}/me").mock(return_value=httpx.Response(502, text="<html>bad gateway</html>"))
    with pytest.raises(ProblemError) as raised:
        client.me.get()
    assert raised.value.status == 502 and raised.value.code == "bad_gateway"
    respx.get(f"{BASE}/jobs/job_1").mock(
        return_value=httpx.Response(401, json=problem(401, "invalid_api_key"))
    )
    with pytest.raises(ProblemError) as raised:
        client.jobs.get("job_1")
    assert raised.value.exit_code == ExitCode.AUTH


@respx.mock
def test_retries_429_honoring_retry_after(client: Tamarind) -> None:
    route = respx.get(f"{BASE}/me").mock(
        side_effect=[
            httpx.Response(429, json=problem(429, "rate_limited"), headers={"Retry-After": "7"}),
            httpx.Response(200, json={"user": {}}),
        ]
    )
    assert client.me.get() == {"user": {}}
    assert route.call_count == 2
    assert client.sleeps == [7.0]  # type: ignore[attr-defined]


@respx.mock
def test_5xx_retries_only_requests_that_are_safe_to_repeat(client: Tamarind) -> None:
    # A POST without an Idempotency-Key may have done its work: never repeated on a 500.
    create = respx.post(f"{BASE}/projects").mock(
        return_value=httpx.Response(500, json=problem(500, "internal_error"))
    )
    with pytest.raises(ProblemError):
        client.projects.create({"name": "p"})
    assert create.call_count == 1

    # A submit carries its Idempotency-Key, so the retry is the same request.
    submit = respx.post(f"{BASE}/jobs").mock(
        side_effect=[
            httpx.Response(502, text="bad gateway"),
            httpx.Response(201, json={"id": "job_1"}),
        ]
    )
    assert client.jobs.submit({"tool": "t", "settings": {}}) == {"id": "job_1"}
    keys = {call.request.headers["Idempotency-Key"] for call in submit.calls}
    assert len(keys) == 1

    # A GET is repeated until max_retries, then the last error is raised.
    get = respx.get(f"{BASE}/jobs/job_1").mock(
        return_value=httpx.Response(503, json=problem(503, "service_unavailable"))
    )
    with pytest.raises(ProblemError) as raised:
        client.jobs.get("job_1")
    assert raised.value.code == "service_unavailable"
    assert get.call_count == client._transport.max_retries + 1


@respx.mock
def test_no_retry_when_the_server_says_it_would_not_help(client: Tamarind) -> None:
    route = respx.get(f"{BASE}/me").mock(
        return_value=httpx.Response(503, json=problem(503, "service_unavailable", retryable=False))
    )
    with pytest.raises(ProblemError):
        client.me.get()
    assert route.call_count == 1

    replayed = respx.post(f"{BASE}/jobs").mock(
        return_value=httpx.Response(
            500, json=problem(500, "internal_error"), headers={"Idempotent-Replayed": "true"}
        )
    )
    with pytest.raises(ProblemError):
        client.jobs.submit({"tool": "t", "settings": {}})
    assert replayed.call_count == 1

    far = respx.get(f"{BASE}/tools").mock(
        return_value=httpx.Response(
            429, json=problem(429, "rate_limited"), headers={"Retry-After": "900"}
        )
    )
    with pytest.raises(ProblemError):
        client.tools.list()
    assert far.call_count == 1


@respx.mock
def test_409_with_retry_after_is_retried(client: Tamarind) -> None:
    route = respx.post(f"{BASE}/jobs").mock(
        side_effect=[
            httpx.Response(
                409, json=problem(409, "idempotency_in_progress"), headers={"Retry-After": "1"}
            ),
            httpx.Response(201, json={"id": "job_1"}),
        ]
    )
    assert client.jobs.submit({"tool": "t", "settings": {}})["id"] == "job_1"
    assert route.call_count == 2
    conflict = respx.post(f"{BASE}/jobs/job_1/cancel").mock(
        return_value=httpx.Response(409, json=problem(409, "job_already_finished"))
    )
    with pytest.raises(ProblemError):
        client.jobs.cancel("job_1")
    assert conflict.call_count == 1


@respx.mock
def test_paginate_follows_next_cursor(client: Tamarind) -> None:
    pages = {
        None: {"items": [1, 2], "nextCursor": "c2"},
        "c2": {"items": [3], "nextCursor": "c3"},
        "c3": {"items": [4], "nextCursor": None},
    }

    def answer(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=pages[request.url.params.get("cursor")])

    route = respx.get(f"{BASE}/tools").mock(side_effect=answer)
    assert list(client.paginate(client.tools.list, limit=2)) == [1, 2, 3, 4]
    assert route.call_count == 3
    assert all(call.request.url.params["limit"] == "2" for call in route.calls)
    respx.get(f"{BASE}/jobs/job_1/files").mock(
        return_value=httpx.Response(200, json={"items": ["a"], "nextCursor": None})
    )
    assert list(paginate(client.jobs.list_files, "job_1")) == ["a"]
    with pytest.raises(TypeError):
        list(client.paginate(client.me.get))


@respx.mock
def test_wait_polls_until_a_terminal_status(client: Tamarind) -> None:
    respx.get(f"{BASE}/jobs/job_1").mock(
        side_effect=[
            httpx.Response(200, json={"id": "job_1", "status": "In Queue", "pollAfterSeconds": 30}),
            httpx.Response(200, json={"id": "job_1", "status": "Running", "pollAfterSeconds": 15}),
            httpx.Response(
                200, json={"id": "job_1", "status": "Complete", "pollAfterSeconds": None}
            ),
        ]
    )
    seen: list[str] = []
    done = client.jobs.wait("job_1", on_update=lambda item: seen.append(item["status"]))
    assert done["status"] == "Complete"
    assert seen == ["In Queue", "Running", "Complete"]
    assert client.sleeps == [30.0, 15.0]  # type: ignore[attr-defined]


@respx.mock
def test_wait_times_out_without_reading_after_the_deadline(
    client: Tamarind, monkeypatch: pytest.MonkeyPatch
) -> None:
    clock = iter([0.0, 0.0, 5.0, 5.0, 11.0])
    monkeypatch.setattr("tamarind.v1.client.time.monotonic", lambda: next(clock))
    route = respx.get(f"{BASE}/jobs/batch_1").mock(
        return_value=httpx.Response(
            200, json={"id": "batch_1", "status": "Running", "pollAfterSeconds": 15}
        )
    )
    with pytest.raises(JobTimeoutError):
        client.jobs.wait("batch_1", timeout=10)
    assert client.sleeps == [10.0, 5.0]  # type: ignore[attr-defined]
    assert route.call_count == 2


@respx.mock
def test_extra_headers_reach_the_request(client: Tamarind) -> None:
    route = respx.get(f"{BASE}/usage").mock(
        return_value=httpx.Response(200, text="month,value\n", headers={"content-type": "text/csv"})
    )
    assert client.usage.get(extra_headers={"accept": "text/csv"}) == b"month,value\n"
    assert route.calls.last.request.headers.get_list("accept") == ["text/csv"]


@respx.mock
def test_paginate_a_cursor_in_the_request_body(client: Tamarind) -> None:
    def answer(request: httpx.Request) -> httpx.Response:
        sent = json.loads(request.content)
        assert sent["query"] == "x"
        if sent.get("cursor") is None:
            return httpx.Response(200, json={"items": [1], "nextCursor": "c2"})
        return httpx.Response(200, json={"items": [2], "nextCursor": None})

    respx.post(f"{BASE}/molecules/search").mock(side_effect=answer)
    assert list(client.paginate(client.molecules.search, {"query": "x"})) == [1, 2]
    respx.post(f"{BASE}/molecules/groups/grp_1/score-observations").mock(
        return_value=httpx.Response(200, json={"items": ["o"], "nextCursor": None})
    )
    assert list(client.paginate(client.molecules.list_score_observations, "grp_1", {})) == ["o"]


@respx.mock
def test_a_replayed_key_creation_without_its_secret_raises(client: Tamarind) -> None:
    respx.post(f"{BASE}/api-keys").mock(
        side_effect=[
            httpx.Response(201, json={"id": "key_1", "secret": "s"}),
            httpx.Response(200, json={"id": "key_1"}, headers={"Idempotent-Replayed": "true"}),
        ]
    )
    assert client.api_keys.create({"serviceAccountId": "u_1"})["secret"] == "s"
    with pytest.raises(TamarindError, match="key_1.*Revoke it"):
        client.api_keys.create({"serviceAccountId": "u_1"}, idempotency_key="again")


@respx.mock
def test_upload_small_files_inline(client: Tamarind, tmp_path) -> None:  # type: ignore[no-untyped-def]
    local = tmp_path / "x.fasta"
    local.write_bytes(b">a\nMKT\n")
    route = respx.post(f"{BASE}/files").mock(
        return_value=httpx.Response(201, json={"file": {"path": "x.fasta"}, "upload": None})
    )
    assert client.files.upload(local) == {"path": "x.fasta"}
    sent = json.loads(route.calls.last.request.content)
    assert sent == {"path": "x.fasta", "contentBase64": base64.b64encode(b">a\nMKT\n").decode()}
    client.files.upload(b"abc", "dir/y.txt", content_type="text/plain")
    assert json.loads(route.calls.last.request.content)["contentType"] == "text/plain"
    with pytest.raises(TypeError, match="path="):
        client.files.upload(b"abc")


@respx.mock
def test_upload_large_files_through_a_signed_put(client: Tamarind) -> None:
    data = b"z" * (3 * 1024 * 1024 + 1)
    respx.post(f"{BASE}/files").mock(
        return_value=httpx.Response(
            201,
            json={
                "file": {"path": "big.bin"},
                "upload": {
                    "method": "PUT",
                    "url": "https://storage.test/put?sig=1",
                    "headers": {"Content-Type": "application/octet-stream"},
                    "expiresAt": "2026-11-19T00:00:00Z",
                },
            },
        )
    )
    put = respx.put("https://storage.test/put?sig=1").mock(return_value=httpx.Response(200))
    assert client.files.upload(data, "big.bin") == {"path": "big.bin"}
    request = put.calls.last.request
    assert "x-api-key" not in request.headers
    assert request.headers["Content-Length"] == str(len(data))
    assert request.headers["Content-Type"] == "application/octet-stream"
    assert request.content == data


@respx.mock
def test_upload_multipart(client: Tamarind) -> None:
    data = b"0123456789"
    start = respx.post(f"{BASE}/files").mock(
        return_value=httpx.Response(
            201,
            json={
                "file": {"path": "m.bin"},
                "upload": {
                    "id": "up_1",
                    "method": "PUT",
                    "partSizeBytes": 4,
                    "parts": [
                        {"partNumber": n, "url": f"https://storage.test/p{n}"} for n in (1, 2, 3)
                    ],
                    "expiresAt": "2026-11-19T00:00:00Z",
                },
            },
        )
    )
    bodies = {}
    for n in (1, 2, 3):
        respx.put(f"https://storage.test/p{n}").mock(
            side_effect=lambda request, n=n: (
                bodies.__setitem__(n, request.content)
                or httpx.Response(200, headers={"ETag": f'"e{n}"'})
            )
        )
    complete = respx.post(f"{BASE}/files/complete").mock(
        return_value=httpx.Response(200, json={"path": "m.bin", "sizeBytes": 10})
    )
    assert client.files.upload(data, "m.bin", multipart=True) == {"path": "m.bin", "sizeBytes": 10}
    assert json.loads(start.calls.last.request.content) == {
        "path": "m.bin",
        "sizeBytes": 10,
        "multipart": True,
    }
    assert bodies == {1: b"0123", 2: b"4567", 3: b"89"}
    assert json.loads(complete.calls.last.request.content) == {
        "uploadId": "up_1",
        "parts": [{"partNumber": n, "etag": f'"e{n}"'} for n in (1, 2, 3)],
    }


@respx.mock
def test_file_content_comes_back_as_bytes(client: Tamarind) -> None:
    respx.get(f"{BASE}/files/content").mock(
        return_value=httpx.Response(
            200, content=b"ATOM", headers={"content-type": "application/octet-stream"}
        )
    )
    assert client.files.get(path="a.pdb", delivery="inline") == b"ATOM"
    respx.delete(f"{BASE}/files").mock(return_value=httpx.Response(204))
    assert client.files.delete(path="a.pdb") is None


def _multipart_session(parts: list[int], part_size: int, url: str = "https://storage.test") -> dict:
    return {
        "file": {"path": "m.bin"},
        "upload": {
            "id": "up_1",
            "method": "PUT",
            "partSizeBytes": part_size,
            "parts": [{"partNumber": n, "url": f"{url}/p{n}"} for n in parts],
            "expiresAt": "2026-11-19T00:00:00Z",
        },
    }


@respx.mock
def test_a_malformed_upload_session_sends_nothing(client: Tamarind) -> None:
    import io

    stream = io.BytesIO(b"SECRET-PREFIX|0123456789")
    stream.seek(len(b"SECRET-PREFIX|"))
    puts = respx.put(url__startswith="https://storage.test/").mock(return_value=httpx.Response(200))
    plain = respx.put(url__startswith="http://storage.test/").mock(return_value=httpx.Response(200))
    for session, message in [
        (_multipart_session([0, 1, 2], 4), "number 1 to N"),
        (_multipart_session([1, 2], 4), "cover the file"),
        (_multipart_session([1, 2, 3, 4], 4), "cover the file"),
        (_multipart_session([1, 2, 3], 4, url="http://storage.test"), "isn't HTTPS"),
    ]:
        respx.post(f"{BASE}/files").mock(return_value=httpx.Response(201, json=session))
        with pytest.raises(TamarindError, match=message):
            client.files.upload(stream, "m.bin", multipart=True)
    assert puts.call_count == 0 and plain.call_count == 0


@respx.mock
def test_deletes_are_not_repeated_after_an_ambiguous_failure(client: Tamarind) -> None:
    gone = respx.delete(f"{BASE}/files").mock(return_value=httpx.Response(502, text="bad gateway"))
    with pytest.raises(ProblemError):
        client.files.delete(path="a.pdb")
    assert gone.call_count == 1
    busy = respx.delete(f"{BASE}/custom-tools/t").mock(
        side_effect=[
            httpx.Response(503, json=problem(503, "service_unavailable")),
            httpx.Response(204),
        ]
    )
    assert client.custom_tools.delete("t") is None
    assert busy.call_count == 2


@respx.mock
def test_requests_that_never_left_are_retried(client: Tamarind) -> None:
    route = respx.post(f"{BASE}/projects").mock(
        side_effect=[httpx.PoolTimeout("pool"), httpx.Response(201, json={"id": "proj_1"})]
    )
    assert client.projects.create({"name": "p"}) == {"id": "proj_1"}
    assert route.call_count == 2
    lost = respx.post(f"{BASE}/projects/proj_1/notes/entries").mock(
        side_effect=httpx.ReadTimeout("lost")
    )
    with pytest.raises(TamarindError):
        client.projects.notes.create_entry("proj_1", {"title": "t"})
    assert lost.call_count == 1


@respx.mock
def test_an_inconclusive_submit_names_its_idempotency_key(client: Tamarind) -> None:
    route = respx.post(f"{BASE}/jobs").mock(side_effect=httpx.ReadTimeout("lost"))
    with pytest.raises(TamarindError) as raised:
        client.jobs.submit({"tool": "t", "settings": {}})
    key = raised.value.idempotency_key  # type: ignore[attr-defined]
    assert route.call_count == client._transport.max_retries + 1
    assert {call.request.headers["Idempotency-Key"] for call in route.calls} == {key}


@respx.mock
def test_multipart_completion_is_repeated_after_a_lost_answer(client: Tamarind) -> None:
    respx.post(f"{BASE}/files").mock(
        return_value=httpx.Response(201, json=_multipart_session([1], 8))
    )
    respx.put("https://storage.test/p1").mock(
        return_value=httpx.Response(200, headers={"ETag": '"e1"'})
    )
    complete = respx.post(f"{BASE}/files/complete").mock(
        side_effect=[httpx.ReadTimeout("lost"), httpx.Response(200, json={"path": "m.bin"})]
    )
    assert client.files.upload(b"abc", "m.bin", multipart=True) == {"path": "m.bin"}
    assert complete.call_count == 2


def test_logs_are_not_an_item_page(client: Tamarind) -> None:
    with pytest.raises(TypeError):
        list(client.paginate(client.jobs.logs, "job_1"))
