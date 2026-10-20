"""Multipart upload: chunking, retries, resume, abort, lost-complete recovery and the
fallback to a single PUT on servers without the multipart endpoint. The server and the
storage endpoint are both faked with respx."""

import json
import os
import re
from pathlib import Path

import httpx
import pytest
import respx
from typer.testing import CliRunner

from tamarind import uploads
from tamarind.cli.main import app
from tamarind.errors import TamarindError
from tamarind.http import HTTPClient

API = "https://api.test/"
STORAGE = "https://storage.test/"
PART_URL = re.compile(r"https://storage\.test/(?P<upload>[^/]+)/(?P<part>\d+)")


@pytest.fixture(autouse=True)
def _small_parts(monkeypatch):
    monkeypatch.setattr(uploads, "MULTIPART_THRESHOLD_BYTES", 16)
    monkeypatch.setattr(uploads, "_BACKOFF_BASE_SECONDS", 0)


class FakeServer:
    """The multipart endpoint plus the storage it signs URLs for."""

    def __init__(self, part_size=10, max_bytes=None):
        self.part_size = part_size
        self.max_bytes = max_bytes
        self.uploads = {}
        self.objects = {}
        self.tokens = {}
        self.status_fails = False
        self.calls = []
        self.put_failures = {}  # part number -> list of status codes to return first
        self.complete_override = None
        self.next_id = 0
        self.part_count_override = None

    def install(self, router):
        router.post(f"{API}uploads/multipart").mock(side_effect=self._api)
        router.put(PART_URL).mock(side_effect=self._put)

    def actions(self, name=None):
        return [c for c in self.calls if name is None or c["action"] == name]

    def _api(self, request):
        body = json.loads(request.content)
        self.calls.append(body)
        action = body["action"]
        name = body["filename"]
        if action == "create":
            if self.max_bytes is not None and body["size"] > self.max_bytes:
                return httpx.Response(413, json={"error": "File exceeds the maximum upload size"})
            self.next_id += 1
            upload_id = f"up{self.next_id}"
            self.uploads[upload_id] = {"name": name, "parts": {}, "token": f"tok-{upload_id}"}
            count = -(-body["size"] // self.part_size)
            return httpx.Response(200, json={
                "uploadId": upload_id, "uploadToken": f"tok-{upload_id}", "key": f"u/{name}", "partSize": self.part_size,
                "partCount": self.part_count_override or count,
            })
        if action == "sign":
            return httpx.Response(200, json={"parts": [
                {"partNumber": n, "url": f"{STORAGE}{body['uploadId']}/{n}"} for n in body["partNumbers"]
            ], "expiresIn": 3600})
        if action == "complete":
            if self.complete_override is not None:
                response = self.complete_override(body)
                if response is not None:
                    return response
            upload = self.uploads.pop(body["uploadId"], None)
            if upload is None:
                return httpx.Response(404, json={"error": "Upload not found"})
            parts = upload["parts"]
            data = b"".join(parts[p["partNumber"]][0] for p in body["parts"])
            assert [p["etag"] for p in body["parts"]] == [parts[p["partNumber"]][1] for p in body["parts"]]
            self.objects[name] = data
            self.tokens[name] = upload["token"]
            return httpx.Response(200, json={"key": f"u/{name}", "size": len(data)})
        if action == "abort":
            self.uploads.pop(body["uploadId"], None)
            return httpx.Response(200, json={"aborted": True})
        if action == "status":
            if self.status_fails:
                return httpx.Response(503, json={"error": "unavailable"})
            data = self.objects.get(name)
            if data is None:
                return httpx.Response(200, json={"key": f"u/{name}", "exists": False})
            return httpx.Response(200, json={
                "key": f"u/{name}", "exists": True, "size": len(data),
                "matchesUpload": body.get("uploadToken") is not None and self.tokens.get(name) == body.get("uploadToken"),
            })
        return httpx.Response(400, json={"error": "bad action"})

    def _put(self, request, upload, part):
        n = int(part)
        queued = self.put_failures.get(n)
        if queued:
            status = queued.pop(0) if isinstance(queued, list) else queued
            return httpx.Response(status)
        if upload not in self.uploads:
            return httpx.Response(404, text="NoSuchUpload")
        data = request.read()
        assert int(request.headers["content-length"]) == len(data)
        etag = f'"etag-{upload}-{n}"'
        self.uploads[upload]["parts"][n] = (data, etag)
        return httpx.Response(200, headers={"ETag": etag})


def _client():
    return HTTPClient(API, "test-key")


def _file(tmp_path: Path, size: int, name="reads.fastq.gz") -> Path:
    p = tmp_path / name
    p.write_bytes(os.urandom(size))
    return p


def _upload(path, state_dir, **kw):
    with _client() as c:
        return uploads.upload_file(c, path, state_dir=state_dir, **kw)


def _state_files(state_dir: Path):
    return list(state_dir.glob("*.json")) if state_dir.exists() else []


@pytest.mark.parametrize("size,expected_parts", [(30, 3), (31, 4), (17, 2)])
def test_parts_cover_the_file_exactly(tmp_path, size, expected_parts):
    server = FakeServer(part_size=10)
    f = _file(tmp_path, size)
    with respx.mock(assert_all_called=False) as router:
        server.install(router)
        result = _upload(f, tmp_path / "state", concurrency=3)
    assert result == {
        "ok": True, "filename": f.name, "bytes": size, "multipart": True,
        "parts": expected_parts, "resumed": False,
    }
    assert server.objects[f.name] == f.read_bytes()
    complete = server.actions("complete")[0]
    assert [p["partNumber"] for p in complete["parts"]] == list(range(1, expected_parts + 1))
    # The size the server reports from complete is trusted; no status call, no state left.
    assert server.actions()[-1]["action"] == "complete"
    assert complete["uploadToken"] == "tok-up1"
    assert _state_files(tmp_path / "state") == []


def test_threshold_boundary_keeps_single_put_for_small_files(tmp_path):
    f = _file(tmp_path, 16)
    with respx.mock(assert_all_called=False) as router:
        presign = router.post(f"{API}getPresignedUploadUrl").mock(
            return_value=httpx.Response(200, json={"uploadUrl": f"{STORAGE}single"})
        )
        put = router.put(f"{STORAGE}single").mock(return_value=httpx.Response(200))
        multipart = router.post(f"{API}uploads/multipart")
        result = _upload(f, tmp_path / "state")
    assert presign.called and put.called and not multipart.called
    assert result == {"ok": True, "filename": f.name, "bytes": 16}


def test_part_count_disagreement_aborts(tmp_path):
    server = FakeServer(part_size=10)
    server.part_count_override = 7
    f = _file(tmp_path, 30)
    with respx.mock(assert_all_called=False) as router:
        server.install(router)
        with pytest.raises(TamarindError, match="disagree"):
            _upload(f, tmp_path / "state")
    assert [c["action"] for c in server.calls] == ["create", "abort"]
    assert _state_files(tmp_path / "state") == []


def test_failed_part_is_retried_with_a_fresh_url(tmp_path):
    server = FakeServer(part_size=10)
    server.put_failures[2] = [500, 503]
    f = _file(tmp_path, 30)
    with respx.mock(assert_all_called=False) as router:
        server.install(router)
        _upload(f, tmp_path / "state", concurrency=1)
    assert server.objects[f.name] == f.read_bytes()
    signs = [c["partNumbers"] for c in server.actions("sign")]
    assert signs.count([2]) == 2  # one fresh signature per retry


def test_exhausted_retries_keep_state_for_resume_and_do_not_abort(tmp_path):
    server = FakeServer(part_size=10)
    server.put_failures[3] = 500  # every attempt
    f = _file(tmp_path, 30)
    state_dir = tmp_path / "state"
    with respx.mock(assert_all_called=False) as router:
        server.install(router)
        with pytest.raises(TamarindError, match="rerun the same command to resume"):
            _upload(f, state_dir, concurrency=1)
    assert server.actions("abort") == []
    [state_file] = _state_files(state_dir)
    saved = json.loads(state_file.read_text())
    assert saved["uploadId"] == "up1"
    assert sorted(saved["parts"]) == ["1", "2"]
    assert "test-key" not in state_file.read_text()


def test_rerun_resumes_and_skips_finished_parts(tmp_path):
    server = FakeServer(part_size=10)
    server.put_failures[3] = 500
    f = _file(tmp_path, 30)
    state_dir = tmp_path / "state"
    with respx.mock(assert_all_called=False) as router:
        server.install(router)
        with pytest.raises(TamarindError):
            _upload(f, state_dir, concurrency=1)
        del server.put_failures[3]
        server.calls.clear()
        result = _upload(f, state_dir, concurrency=1)
        puts = [c.request.url.path for c in router.calls if c.request.method == "PUT"]
    assert result["resumed"] is True
    assert server.actions("create") == []
    assert [c["partNumbers"] for c in server.actions("sign")] == [[3]]
    assert puts[-1] == "/up1/3"
    assert server.objects[f.name] == f.read_bytes()
    assert _state_files(state_dir) == []


def test_changed_file_aborts_the_saved_upload_and_starts_over(tmp_path):
    server = FakeServer(part_size=10)
    server.put_failures[3] = 500
    f = _file(tmp_path, 30)
    state_dir = tmp_path / "state"
    with respx.mock(assert_all_called=False) as router:
        server.install(router)
        with pytest.raises(TamarindError):
            _upload(f, state_dir, concurrency=1)
        del server.put_failures[3]
        f.write_bytes(os.urandom(35))
        server.calls.clear()
        result = _upload(f, state_dir, concurrency=1)
    assert result["resumed"] is False and result["parts"] == 4
    assert server.calls[0] == {"action": "abort", "filename": f.name, "uploadId": "up1"}
    assert server.actions("create")[0]["size"] == 35
    assert server.objects[f.name] == f.read_bytes()


def test_no_resume_discards_the_saved_upload(tmp_path):
    server = FakeServer(part_size=10)
    server.put_failures[3] = 500
    f = _file(tmp_path, 30)
    state_dir = tmp_path / "state"
    with respx.mock(assert_all_called=False) as router:
        server.install(router)
        with pytest.raises(TamarindError):
            _upload(f, state_dir, concurrency=1)
        del server.put_failures[3]
        server.calls.clear()
        result = _upload(f, state_dir, concurrency=1, resume=False)
    assert result["resumed"] is False
    assert server.calls[0]["action"] == "abort"
    assert len(server.actions("create")) == 1


def test_expired_saved_upload_restarts_from_scratch(tmp_path):
    server = FakeServer(part_size=10)
    server.put_failures[3] = 500
    f = _file(tmp_path, 30)
    state_dir = tmp_path / "state"
    with respx.mock(assert_all_called=False) as router:
        server.install(router)
        with pytest.raises(TamarindError):
            _upload(f, state_dir, concurrency=1)
        del server.put_failures[3]
        server.uploads.clear()  # storage forgot the upload id
        result = _upload(f, state_dir, concurrency=1)
    assert result["resumed"] is False
    assert len(server.actions("create")) == 2
    assert server.objects[f.name] == f.read_bytes()


def test_server_rejection_aborts_and_clears_state(tmp_path):
    server = FakeServer(part_size=10)
    server.complete_override = lambda body: httpx.Response(
        400, json={"error": "Multipart upload could not be completed: InvalidPart"}
    )
    f = _file(tmp_path, 30)
    state_dir = tmp_path / "state"
    with respx.mock(assert_all_called=False) as router:
        server.install(router)
        with pytest.raises(TamarindError, match="InvalidPart"):
            _upload(f, state_dir)
    assert len(server.actions("abort")) == 1
    assert _state_files(state_dir) == []


def test_oversize_file_is_refused_with_the_server_message(tmp_path):
    server = FakeServer(part_size=10, max_bytes=20)
    f = _file(tmp_path, 30)
    with respx.mock(assert_all_called=False) as router:
        server.install(router)
        with pytest.raises(TamarindError, match="maximum upload size"):
            _upload(f, tmp_path / "state")
    assert _state_files(tmp_path / "state") == []


def test_interrupt_keeps_the_upload_for_resume(tmp_path):
    server = FakeServer(part_size=10)
    f = _file(tmp_path, 30)
    state_dir = tmp_path / "state"
    seen = []

    def interrupt_after_first_part(sent, total):
        seen.append(sent)
        if sent >= 15:
            raise KeyboardInterrupt

    with respx.mock(assert_all_called=False) as router:
        server.install(router)
        with pytest.raises(KeyboardInterrupt):
            _upload(f, state_dir, concurrency=1, progress=interrupt_after_first_part)
        assert server.actions("abort") == []
        [state_file] = _state_files(state_dir)
        assert list(json.loads(state_file.read_text())["parts"]) == ["1"]
        result = _upload(f, state_dir, concurrency=1)
    assert result["resumed"] is True
    assert server.objects[f.name] == f.read_bytes()


def test_lost_complete_response_is_recovered_through_status(tmp_path):
    server = FakeServer(part_size=10)
    real_complete = []

    def complete_then_drop(body):
        # Assemble the object, then lose the response.
        upload = server.uploads.pop(body["uploadId"])
        server.objects[body["filename"]] = b"".join(
            upload["parts"][p["partNumber"]][0] for p in body["parts"]
        )
        server.tokens[body["filename"]] = upload["token"]
        real_complete.append(body)
        return httpx.Response(504, text="Gateway Timeout")

    server.complete_override = complete_then_drop
    f = _file(tmp_path, 30)
    with respx.mock(assert_all_called=False) as router:
        server.install(router)
        result = _upload(f, tmp_path / "state")
    assert result["ok"] is True and real_complete
    assert server.actions("abort") == []
    assert _state_files(tmp_path / "state") == []


def test_lost_complete_is_not_confirmed_by_an_older_same_sized_object(tmp_path):
    server = FakeServer(part_size=10)
    f = _file(tmp_path, 30)
    server.objects[f.name] = b"x" * 30
    server.tokens[f.name] = "tok-from-an-earlier-upload"
    server.complete_override = lambda body: httpx.Response(502, text="Bad Gateway")
    state_dir = tmp_path / "state"
    with respx.mock(assert_all_called=False) as router:
        server.install(router)
        with pytest.raises(TamarindError, match="rerun the same command to resume"):
            _upload(f, state_dir)
    [status] = server.actions("status")
    assert status["uploadToken"] == "tok-up1"
    assert len(_state_files(state_dir)) == 1


def test_status_failure_after_a_successful_complete_does_not_fail_the_upload(tmp_path):
    server = FakeServer(part_size=10)
    f = _file(tmp_path, 30)
    server.status_fails = True
    with respx.mock(assert_all_called=False) as router:
        server.install(router)
        result = _upload(f, tmp_path / "state")
    assert result["ok"] is True
    assert server.objects[f.name] == f.read_bytes()


@pytest.mark.parametrize("code", [400, 413])
def test_permanent_part_rejection_aborts_without_retrying(tmp_path, code):
    server = FakeServer(part_size=10)
    server.put_failures[2] = [code] * 10
    f = _file(tmp_path, 30)
    state_dir = tmp_path / "state"
    with respx.mock(assert_all_called=False) as router:
        server.install(router)
        with pytest.raises(TamarindError, match=f"HTTP {code}") as info:
            _upload(f, state_dir, concurrency=1)
    assert "resume" not in str(info.value)
    assert server.put_failures[2] == [code] * 9
    assert len(server.actions("abort")) == 1
    assert _state_files(state_dir) == []


def test_persistent_403_is_retried_with_fresh_urls_then_aborted(tmp_path):
    server = FakeServer(part_size=10)
    server.put_failures[1] = [403] * 10
    f = _file(tmp_path, 30)
    state_dir = tmp_path / "state"
    with respx.mock(assert_all_called=False) as router:
        server.install(router)
        with pytest.raises(TamarindError, match="HTTP 403"):
            _upload(f, state_dir, concurrency=1)
    assert server.put_failures[1] == [403] * (10 - uploads.MAX_PART_ATTEMPTS)
    assert len(server.actions("abort")) == 1
    assert _state_files(state_dir) == []


def test_one_403_then_success_is_retried(tmp_path):
    server = FakeServer(part_size=10)
    server.put_failures[1] = [403]
    f = _file(tmp_path, 30)
    with respx.mock(assert_all_called=False) as router:
        server.install(router)
        result = _upload(f, tmp_path / "state", concurrency=1)
    assert result["ok"] is True


def test_lost_complete_without_an_object_keeps_state(tmp_path):
    server = FakeServer(part_size=10)
    server.complete_override = lambda body: httpx.Response(502, text="Bad Gateway")
    f = _file(tmp_path, 30)
    state_dir = tmp_path / "state"
    with respx.mock(assert_all_called=False) as router:
        server.install(router)
        with pytest.raises(TamarindError, match="rerun the same command to resume"):
            _upload(f, state_dir)
    assert server.actions("abort") == []
    assert len(_state_files(state_dir)) == 1


def test_size_mismatch_after_complete_is_an_error(tmp_path):
    server = FakeServer(part_size=10)

    def complete_short(body):
        server.uploads.pop(body["uploadId"])
        server.objects[body["filename"]] = b"short"
        return httpx.Response(200, json={"key": "k", "size": 5})

    server.complete_override = complete_short
    f = _file(tmp_path, 30)
    with respx.mock(assert_all_called=False) as router:
        server.install(router)
        with pytest.raises(TamarindError, match="does not match"):
            _upload(f, tmp_path / "state")


def test_missing_endpoint_falls_back_to_single_put(tmp_path):
    f = _file(tmp_path, 30)
    with respx.mock(assert_all_called=False) as router:
        router.post(f"{API}uploads/multipart").mock(return_value=httpx.Response(404, text="Not Found"))
        router.post(f"{API}getPresignedUploadUrl").mock(
            return_value=httpx.Response(200, json={"uploadUrl": f"{STORAGE}single"})
        )
        put = router.put(f"{STORAGE}single").mock(return_value=httpx.Response(200))
        result = _upload(f, tmp_path / "state")
    assert put.calls.last.request.content == f.read_bytes()
    assert result == {"ok": True, "filename": f.name, "bytes": 30}
    assert _state_files(tmp_path / "state") == []


def test_missing_endpoint_above_single_put_limit_is_a_clear_error(tmp_path, monkeypatch):
    monkeypatch.setattr(uploads, "SINGLE_PUT_MAX_BYTES", 20)
    f = _file(tmp_path, 30)
    with respx.mock(assert_all_called=False) as router:
        router.post(f"{API}uploads/multipart").mock(return_value=httpx.Response(404, text="Not Found"))
        presign = router.post(f"{API}getPresignedUploadUrl")
        with pytest.raises(TamarindError, match="does not support multipart"):
            _upload(f, tmp_path / "state")
    assert not presign.called


def test_cli_upload_uses_multipart_and_reports_json(tmp_path):
    server = FakeServer(part_size=10)
    f = _file(tmp_path, 45)
    env = {
        "TAMARIND_API_KEY": "k",
        "TAMARIND_API_BASE": API,
        "TAMARIND_CATALOG_BASE": "https://cat.test/",
        "TAMARIND_CONFIG_DIR": str(tmp_path / "cfg"),
    }
    with respx.mock(assert_all_called=False) as router:
        server.install(router)
        res = CliRunner().invoke(
            app, ["--json", "files", "upload", str(f), "--name", "run1/reads.bam", "--concurrency", "2"],
            env=env,
        )
    assert res.exit_code == 0, res.output
    out = json.loads(res.stdout)
    assert out["multipart"] is True and out["parts"] == 5 and out["filename"] == "run1/reads.bam"
    assert server.objects["run1/reads.bam"] == f.read_bytes()
    assert not (tmp_path / "cfg" / "uploads").exists() or _state_files(tmp_path / "cfg" / "uploads") == []


def test_cli_interrupt_exits_130_with_one_error_document(tmp_path, monkeypatch, capsys):
    f = _file(tmp_path, 45)
    env = {
        "TAMARIND_API_KEY": "k",
        "TAMARIND_API_BASE": API,
        "TAMARIND_CATALOG_BASE": "https://cat.test/",
        "TAMARIND_CONFIG_DIR": str(tmp_path / "cfg"),
    }

    def interrupted(*_args, **_kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr(uploads, "upload_file", interrupted)
    monkeypatch.setattr("sys.argv", ["tamarind", "--json", "files", "upload", str(f)])
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    from tamarind.cli.main import run

    with pytest.raises(SystemExit) as info:
        run()
    assert info.value.code == 130
    err = capsys.readouterr().err
    assert err.count('"error"') == 1 and '"Interrupted"' in err


def test_file_changed_mid_upload_aborts(tmp_path):
    server = FakeServer(part_size=10)
    f = _file(tmp_path, 30)

    def touch_on_last_part(sent, total):
        if sent == total:
            os.utime(f, ns=(1, 1))

    with respx.mock(assert_all_called=False) as router:
        server.install(router)
        with pytest.raises(TamarindError, match="changed while it was uploading"):
            _upload(f, tmp_path / "state", concurrency=1, progress=touch_on_last_part)
    assert server.actions("complete") == []
    assert len(server.actions("abort")) == 1
    assert _state_files(tmp_path / "state") == []
