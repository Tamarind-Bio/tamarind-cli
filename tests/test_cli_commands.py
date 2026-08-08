"""Command-level tests (Typer runner + mocked HTTP) for parsing edge cases that
live testing against staging surfaced: the logs response shape and a non-list
folders response."""

import json
from io import BytesIO

import httpx
import pytest
import respx
from typer.testing import CliRunner

from tamarind.cli.main import app
from tamarind.upload import UPLOAD_CHUNK_SIZE as _UPLOAD_CHUNK_SIZE
from tamarind.upload import iter_file_chunks as _iter_file_chunks
from tamarind.errors import NotFoundError, TamarindError

runner = CliRunner()

API = "https://api.test/"
CAT = "https://cat.test/"
ENV = {
    "TAMARIND_API_KEY": "k",
    "TAMARIND_API_BASE": API,
    "TAMARIND_CATALOG_BASE": CAT,
}


class _NoUnboundedRead(BytesIO):
    def read(self, size=-1):
        assert size == _UPLOAD_CHUNK_SIZE
        return super().read(size)


def test_upload_chunk_iterator_never_reads_the_whole_file_at_once():
    payload = b"x" * (_UPLOAD_CHUNK_SIZE + 1)
    assert b"".join(_iter_file_chunks(_NoUnboundedRead(payload))) == payload


@respx.mock
def test_logs_renders_log_field():
    respx.get(f"{CAT}catalog/jobs/job1/logs").mock(
        return_value=httpx.Response(200, json={"jobName": "job1", "log": "hello\nworld"})
    )
    res = runner.invoke(app, ["logs", "job1"], env=ENV)
    assert res.exit_code == 0
    assert "hello" in res.stdout and "world" in res.stdout


@respx.mock
def test_logs_not_found_maps_to_not_found_error():
    # getJobLogs returns {"error": "...not found..."} for a missing job; that must
    # raise NotFoundError (exit 4 via the entry point), not a generic error (exit 1).
    # CliRunner bypasses the run() exit-code mapping, so assert the exception type.
    respx.get(f"{CAT}catalog/jobs/job1/logs").mock(
        return_value=httpx.Response(200, json={"error": "Log file not found at s3://..."})
    )
    res = runner.invoke(app, ["logs", "job1"], env=ENV)
    assert isinstance(res.exception, NotFoundError)
    assert res.exception.exit_code == 4


@respx.mock
def test_logs_other_error_is_generic():
    respx.get(f"{CAT}catalog/jobs/job1/logs").mock(
        return_value=httpx.Response(200, json={"error": "internal boom"})
    )
    res = runner.invoke(app, ["logs", "job1"], env=ENV)
    assert isinstance(res.exception, TamarindError)
    assert not isinstance(res.exception, NotFoundError)


@respx.mock
def test_folders_survives_non_list_response():
    # The staging preview redirects /getFolders to an HTML "Redirecting..." body;
    # the command must not crash on a non-list payload.
    respx.get(f"{API}getFolders").mock(return_value=httpx.Response(200, text="Redirecting..."))
    res = runner.invoke(app, ["files", "folders"], env=ENV)
    assert res.exit_code == 0
    assert res.exception is None


@respx.mock
def test_files_list_survives_non_list_response():
    respx.get(f"{API}files").mock(return_value=httpx.Response(200, text="Redirecting..."))
    res = runner.invoke(app, ["files", "list"], env=ENV)
    assert res.exit_code == 0
    assert res.exception is None


@respx.mock
def test_schema_unknown_tool_exits_nonzero():
    # The catalog returns 200 + {"error": ...} for an unknown tool; must not be exit 0.
    respx.get(f"{CAT}catalog/tools/notarealtool/schema").mock(
        return_value=httpx.Response(200, json={"error": "Tool 'notarealtool' not found"})
    )
    res = runner.invoke(app, ["schema", "notarealtool"], env=ENV)
    assert res.exit_code != 0


@respx.mock
def test_tools_replaces_mcp_only_server_hint_with_cli_guidance():
    respx.get(f"{CAT}catalog/tools").mock(
        return_value=httpx.Response(
            200,
            json={
                "totalTools": 1,
                "tools": [{"name": "boltz", "displayName": "Boltz", "categories": []}],
                "hint": "Use getJobSchema(jobType='<name>') next",
            },
        )
    )

    res = runner.invoke(app, ["--json", "tools"], env=ENV)

    assert res.exit_code == 0, res.stdout
    payload = json.loads(res.stdout)
    assert "tamarind --json schema NAME" in payload["hint"]
    assert "tamarind --json schema NAME" in payload["cliHint"]
    assert "getJobSchema" not in payload["hint"]


@respx.mock
def test_schema_replaces_mcp_only_server_hints_with_cli_guidance():
    respx.get(f"{CAT}catalog/tools/boltz/schema").mock(
        return_value=httpx.Response(
            200,
            json={
                "displayName": "Boltz",
                "parameters": [],
                "hint": "Use listJobFiles()",
                "exampleJobNote": (
                    "Scientific caveat: replace placeholder files. "
                    "Use uploadFile('input.pdb'), validateJob, then submitJob"
                ),
            },
        )
    )

    res = runner.invoke(app, ["--json", "schema", "boltz"], env=ENV)

    assert res.exit_code == 0, res.stdout
    payload = json.loads(res.stdout)
    combined = payload["hint"] + payload["exampleJobNote"] + payload["cliHint"]
    assert "tamarind --json validate boltz" in combined
    assert "tamarind --json results JOB" in combined
    assert "Scientific caveat: replace placeholder files." in combined
    for legacy in ("listJobFiles", "uploadFile", "validateJob", "submitJob"):
        assert legacy not in combined


@respx.mock
def test_auth_status_never_emits_even_a_masked_key_fragment():
    secret = "codex-super-secret-key"
    endpoint_secret = "endpoint-secret"
    respx.get(f"{API}jobs").mock(return_value=httpx.Response(200, json={"jobs": []}))
    env = {
        **ENV,
        "TAMARIND_API_KEY": secret,
        "TAMARIND_CATALOG_BASE": (f"https://catalog.test/?X-Amz-Signature={endpoint_secret}"),
    }

    machine = runner.invoke(app, ["--json", "auth", "status"], env=env)
    human = runner.invoke(app, ["--no-json", "auth", "status"], env=env)

    assert machine.exit_code == 0, machine.stdout
    payload = json.loads(machine.stdout)
    assert "apiKey" not in payload
    assert "apiBase" not in payload
    assert "catalogBase" not in payload
    assert payload["hasKey"] is True
    assert secret not in machine.stdout + human.stdout
    assert endpoint_secret not in machine.stdout + human.stdout
    assert "X-Amz" not in machine.stdout + human.stdout
    assert "code" not in machine.stdout + human.stdout
    assert "-key" not in machine.stdout + human.stdout
    assert "configured (verified)" in human.stdout


@respx.mock
def test_upload_gets_presigned_url_then_puts_to_s3(tmp_path):
    # `files upload` is a two-step presigned PUT: POST /getPresignedUploadUrl to
    # get a PUT-able uploadUrl, then PUT the bytes straight to S3 (not multipart
    # through the API). The Content-Type on the PUT must match what was signed.
    import json

    f = tmp_path / "target.pdb"
    f.write_bytes(b"ATOM      1  N   MET A   1\n")
    upload_url = "https://s3.amazonaws.com/alphafold-dbs-tamarind/user%40x.com/target.pdb"

    post_route = respx.post(f"{API}getPresignedUploadUrl").mock(
        return_value=httpx.Response(
            200,
            json={
                "uploadUrl": upload_url,
                "headUrl": "https://h",
                "key": "user@x.com/target.pdb",
                "bucket": "b",
            },
        )
    )
    put_route = respx.put(upload_url).mock(return_value=httpx.Response(200))

    res = runner.invoke(app, ["files", "upload", str(f)], env=ENV)

    assert res.exit_code == 0, res.stdout
    assert post_route.called and put_route.called
    # POST carried the filename + contentType the URL is signed with
    body = json.loads(post_route.calls.last.request.content)
    assert body == {"filename": "target.pdb", "contentType": "application/octet-stream"}
    # PUT streamed the exact bytes with the matching Content-Type
    put_req = put_route.calls.last.request
    assert put_req.content == b"ATOM      1  N   MET A   1\n"
    assert put_req.headers["content-type"] == "application/octet-stream"
    assert put_req.headers["content-length"] == str(f.stat().st_size)


@respx.mock
def test_upload_surfaces_clean_error_on_non_dict_response(tmp_path):
    # An auth/sentinel failure (e.g. bare -1) must not crash on .get — it should
    # raise a clean TamarindError and never attempt the PUT.
    f = tmp_path / "target.pdb"
    f.write_bytes(b"x")
    respx.post(f"{API}getPresignedUploadUrl").mock(return_value=httpx.Response(200, json=-1))
    res = runner.invoke(app, ["files", "upload", str(f)], env=ENV)
    assert res.exit_code != 0
    # A clean, typed error (the isinstance(dict) guard worked) — NOT an
    # AttributeError from calling .get on an int.
    assert isinstance(res.exception, TamarindError)


@respx.mock
def test_upload_missing_url_error_detail_does_not_leak_sibling_presigned_url(tmp_path):
    f = tmp_path / "target.pdb"
    f.write_bytes(b"ATOM")
    secret = "https://storage.test/head?signature=do-not-leak"
    respx.post(f"{API}getPresignedUploadUrl").mock(
        return_value=httpx.Response(200, json={"headUrl": secret, "bucket": "workspace"})
    )

    res = runner.invoke(app, ["files", "upload", str(f)], env=ENV)

    assert res.exit_code != 0
    assert isinstance(res.exception, TamarindError)
    assert "do-not-leak" not in res.exception.message
    assert "do-not-leak" not in str(res.exception.detail)
    assert res.exception.detail == {
        "responseType": "dict",
        "fields": ["bucket", "headUrl"],
    }


@respx.mock
def test_upload_maps_presigned_put_http_failure_without_leaking_url(tmp_path):
    f = tmp_path / "target.pdb"
    f.write_bytes(b"ATOM")
    upload_url = "https://s3.amazonaws.com/bucket/target.pdb?X-Amz-Signature=secret"
    respx.post(f"{API}getPresignedUploadUrl").mock(
        return_value=httpx.Response(200, json={"uploadUrl": upload_url})
    )
    respx.put(upload_url).mock(return_value=httpx.Response(403, text="SignatureDoesNotMatch"))

    res = runner.invoke(app, ["files", "upload", str(f)], env=ENV)

    assert res.exit_code != 0
    assert isinstance(res.exception, TamarindError)
    assert "HTTP 403" in res.exception.message
    assert "secret" not in res.exception.message


@respx.mock
def test_upload_maps_presigned_put_network_failure_without_leaking_url(tmp_path):
    f = tmp_path / "target.pdb"
    f.write_bytes(b"ATOM")
    upload_url = "https://s3.amazonaws.com/bucket/target.pdb?X-Amz-Signature=secret"
    respx.post(f"{API}getPresignedUploadUrl").mock(
        return_value=httpx.Response(200, json={"uploadUrl": upload_url})
    )
    request = httpx.Request("PUT", upload_url)
    respx.put(upload_url).mock(side_effect=httpx.ConnectError("boom", request=request))

    res = runner.invoke(app, ["files", "upload", str(f)], env=ENV)

    assert res.exit_code != 0
    assert isinstance(res.exception, TamarindError)
    assert "ConnectError" in res.exception.message
    assert "secret" not in res.exception.message


@respx.mock
def test_upload_maps_invalid_presigned_url_without_traceback_or_leak(tmp_path, monkeypatch):
    from tamarind import upload as upload_mod

    f = tmp_path / "target.pdb"
    f.write_bytes(b"ATOM")
    respx.post(f"{API}getPresignedUploadUrl").mock(
        return_value=httpx.Response(200, json={"uploadUrl": "not-a-valid-secret-url"})
    )

    def invalid_put(*args, **kwargs):
        raise httpx.InvalidURL("not-a-valid-secret-url")

    monkeypatch.setattr(upload_mod.httpx, "put", invalid_put)

    res = runner.invoke(app, ["files", "upload", str(f)], env=ENV)

    assert res.exit_code != 0
    assert isinstance(res.exception, TamarindError)
    assert "InvalidURL" in res.exception.message
    assert "not-a-valid-secret-url" not in res.exception.message


@respx.mock
def test_upload_maps_stream_protocol_failure_without_leaking_url(tmp_path, monkeypatch):
    from tamarind import upload as upload_mod

    f = tmp_path / "target.pdb"
    f.write_bytes(b"ATOM")
    upload_url = "https://storage.test/object?X-Amz-Signature=do-not-leak"
    respx.post(f"{API}getPresignedUploadUrl").mock(
        return_value=httpx.Response(200, json={"uploadUrl": upload_url})
    )

    def broken_put(*args, **kwargs):
        raise httpx.StreamError("stream consumed")

    monkeypatch.setattr(upload_mod.httpx, "put", broken_put)
    result = runner.invoke(app, ["files", "upload", str(f)], env=ENV)

    assert result.exit_code != 0
    assert isinstance(result.exception, TamarindError)
    assert "StreamError" in result.exception.message
    assert "do-not-leak" not in result.exception.message


# --- files list filtering (the /files endpoint ignores query filters; the CLI
#     applies them client-side, mirroring the MCP getFiles tool) ---------------

_WORKSPACE_FILES = ["a.pdb", "b.PDB", "c.cif", "notes.txt", "run.log", "seqs.fasta"]


@respx.mock
def test_files_list_filters_by_type_client_side():
    # The endpoint returns the FULL list regardless of ?types=; the CLI must still
    # narrow it (this is the bug: the filter used to be silently ignored).
    respx.get(f"{API}files").mock(return_value=httpx.Response(200, json=_WORKSPACE_FILES))
    res = runner.invoke(app, ["--json", "files", "list", "--types", "pdb"], env=ENV)
    assert res.exit_code == 0, res.stdout
    out = json.loads(res.stdout)
    assert set(out["files"]) == {"a.pdb", "b.PDB"}  # case-insensitive extension match
    assert out["count"] == 2
    assert out["total"] == 2
    assert out["totalUnfiltered"] == 6


@respx.mock
def test_files_list_filters_by_multiple_types():
    respx.get(f"{API}files").mock(return_value=httpx.Response(200, json=_WORKSPACE_FILES))
    res = runner.invoke(app, ["--json", "files", "list", "--types", "pdb,cif"], env=ENV)
    out = json.loads(res.stdout)
    assert set(out["files"]) == {"a.pdb", "b.PDB", "c.cif"}


@respx.mock
def test_files_list_filters_by_search():
    respx.get(f"{API}files").mock(return_value=httpx.Response(200, json=_WORKSPACE_FILES))
    res = runner.invoke(app, ["--json", "files", "list", "--search", "SEQ"], env=ENV)
    out = json.loads(res.stdout)
    assert out["files"] == ["seqs.fasta"]  # substring, case-insensitive
    assert out["total"] == 1


@respx.mock
def test_files_list_paginates_client_side():
    respx.get(f"{API}files").mock(return_value=httpx.Response(200, json=_WORKSPACE_FILES))
    page1 = json.loads(
        runner.invoke(
            app, ["--json", "files", "list", "--limit", "2", "--offset", "0"], env=ENV
        ).stdout
    )
    assert page1["count"] == 2 and page1["total"] == 6 and page1["hasMore"] is True
    page3 = json.loads(
        runner.invoke(
            app, ["--json", "files", "list", "--limit", "2", "--offset", "4"], env=ENV
        ).stdout
    )
    assert page3["count"] == 2 and page3["hasMore"] is False


# --- jobs pagination cursor --------------------------------------------------


@respx.mock
def test_jobs_forwards_and_surfaces_start_key():
    route = respx.get(f"{API}jobs").mock(
        return_value=httpx.Response(
            200,
            json={
                "jobs": [{"JobName": "j1", "JobStatus": "Complete"}],
                "startKey": "CURSOR123",
                "statuses": {"Complete": 1},
            },
        )
    )
    res = runner.invoke(app, ["--json", "jobs", "--limit", "1", "--start-key", "PREV"], env=ENV)
    assert res.exit_code == 0, res.stdout
    out = json.loads(res.stdout)
    assert out["startKey"] == "CURSOR123"  # next-page cursor surfaced
    url = str(route.calls.last.request.url)
    assert "startKey=PREV" in url and "limit=1" in url  # our cursor was forwarded


@respx.mock
def test_jobs_omits_start_key_when_backend_has_none():
    respx.get(f"{API}jobs").mock(
        return_value=httpx.Response(200, json={"jobs": [], "statuses": {}})
    )
    out = json.loads(runner.invoke(app, ["--json", "jobs"], env=ENV).stdout)
    assert "startKey" not in out


@respx.mock
def test_jobs_all_follows_cursor_to_exhaustion():
    page1 = {
        "jobs": [
            {"JobName": "a", "JobStatus": "Complete"},
            {"JobName": "b", "JobStatus": "Running"},
        ],
        "startKey": "K1",
        "statuses": {"Complete": 1, "Running": 1},
    }
    page2 = {"jobs": [{"JobName": "c", "JobStatus": "Complete"}], "statuses": {"Complete": 1}}
    respx.get(f"{API}jobs").mock(
        side_effect=[httpx.Response(200, json=page1), httpx.Response(200, json=page2)]
    )
    out = json.loads(runner.invoke(app, ["--json", "jobs", "--all"], env=ENV).stdout)
    assert [j["JobName"] for j in out["jobs"]] == ["a", "b", "c"]  # both pages accumulated
    assert out["count"] == 3
    assert out["statuses"] == {"Complete": 2, "Running": 1}  # recomputed across pages
    assert "startKey" not in out  # cursor exhausted


@respx.mock
def test_jobs_all_respects_page_cap(monkeypatch):
    from tamarind.cli.commands import jobs as jobs_cmd

    monkeypatch.setattr(jobs_cmd, "_MAX_AUTO_PAGES", 2)
    # Every page returns a startKey — without the cap this would loop forever.
    respx.get(f"{API}jobs").mock(
        return_value=httpx.Response(
            200, json={"jobs": [{"JobName": "x", "JobStatus": "Complete"}], "startKey": "NEXT"}
        )
    )
    out = json.loads(runner.invoke(app, ["--json", "jobs", "--all"], env=ENV).stdout)
    assert out["count"] == 2  # 2 pages * 1 job, stopped by the cap
    assert out["startKey"] == "NEXT"  # resume cursor surfaced


@respx.mock
def test_files_stats_counts_by_type():
    files = ["a.pdb", "b.pdb", "c.cif", "readme", "notes.txt"]
    respx.get(f"{API}files").mock(return_value=httpx.Response(200, json=files))
    out = json.loads(runner.invoke(app, ["--json", "files", "stats"], env=ENV).stdout)
    assert out["totalFiles"] == 5
    assert out["fileTypes"] == {"pdb": 2, "cif": 1, "no_extension": 1, "txt": 1}


# ── Custom tools: guards that cost nothing to check and a lot to get wrong ────────


def test_deploy_rejects_publish_without_waiting(tmp_path):
    """`--publish` requires a COMPLETE version and `--no-wait` returns while the build
    is still Running, so the pair can never succeed for a build that actually builds.

    The check is before the upload deliberately: without it, deploy packages the folder,
    uploads it, starts a build, and only then raises from `publish`.

    Asserting on stderr rather than the exit code because CliRunner bypasses the exit
    mapping; the point is that it refused, and named both flags.
    """
    (tmp_path / "Dockerfile").write_text("FROM scratch\n")
    (tmp_path / "run.sh").write_text("true\n")
    (tmp_path / "config.json").write_text("{}\n")
    res = runner.invoke(app, ["deploy", str(tmp_path), "--no-wait", "--publish"], env=ENV)
    assert res.exit_code != 0
    combined = res.output + str(res.exception or "")
    assert "--publish" in combined and "--no-wait" in combined


def test_clone_refuses_a_non_empty_destination(tmp_path):
    """Extraction overwrites without asking, so re-cloning into a folder you have been
    editing destroys that work — and `clone name .` asks for exactly that.

    No HTTP is mocked here on purpose: the guard has to fire BEFORE the download, so a
    request reaching the network would fail this test by erroring differently.
    """
    dest = tmp_path / "work"
    dest.mkdir()
    (dest / "main.py").write_text("my unsaved edits\n")
    res = runner.invoke(app, ["ct", "clone", "some-tool", str(dest)], env=ENV)
    assert res.exit_code != 0
    combined = res.output + str(res.exception or "")
    assert "not empty" in combined or "--force" in combined
    assert (dest / "main.py").read_text() == "my unsaved edits\n", "the guard did not protect"


@respx.mock
def test_ct_config_never_prints_environment_values():
    """THE credential leak. `--env` exists precisely so an API key stays OUT of the
    source archive; echoing it back on the next `ct config` puts it in CI logs instead,
    since JSON is the default whenever stdout is piped.

    Without the redaction the payload contains `envVars` with the literal secret and
    the `SUPER_SECRET_VALUE` assertion fails.
    """
    respx.get(f"{API}v2/custom-tools/mytool").mock(
        return_value=httpx.Response(
            200,
            json={
                "latest": {
                    "name": "mytool",
                    "gpuType": "A100",
                    "envVars": {"OPENAI_API_KEY": "SUPER_SECRET_VALUE"},
                }
            },
        )
    )
    res = runner.invoke(app, ["--json", "ct", "config", "mytool"], env=ENV)
    assert res.exit_code == 0, res.output
    assert "SUPER_SECRET_VALUE" not in res.output, "an env value was printed"
    payload = json.loads(res.output)
    # The NAME is still reported — that is what confirms the write landed.
    assert payload["envVarNames"] == ["OPENAI_API_KEY"]
    assert "envVars" not in payload


@respx.mock
def test_ct_logs_puts_the_lines_in_the_json_payload():
    """`output.info` is suppressed in JSON mode, so a status-only payload meant
    `tamarind --json ct logs` returned no logs at all — having just fetched them.

    Without accumulating into the payload, `payload["logs"]` is absent and this fails.
    """
    respx.get(f"{API}v2/custom-tools/mytool/logs").mock(
        return_value=httpx.Response(
            200,
            json={
                "buildStatus": "FAILED",
                "logs": [{"message": "step 1"}, {"message": "the real error"}],
            },
        )
    )
    res = runner.invoke(app, ["--json", "ct", "logs", "mytool", "--build-id", "b-1"], env=ENV)
    assert res.exit_code == 0, res.output
    payload = json.loads(res.output)
    assert [entry["message"] for entry in payload["logs"]] == ["step 1", "the real error"]
    assert payload["buildStatus"] == "FAILED"


@respx.mock
def test_clone_refuses_a_version_with_no_source_ref():
    """A null ref falls through to "no ref parameter", which fetches the tool's CURRENT
    source — a different tree, reported as the version that was asked for."""
    respx.get(f"{API}v2/custom-tools/mytool/versions").mock(
        return_value=httpx.Response(200, json=[{"versionName": "v1", "status": "Complete"}])
    )
    res = runner.invoke(
        app, ["ct", "clone", "mytool", "/tmp/ct-clone-noref", "--version", "v1"], env=ENV
    )
    assert res.exit_code != 0
    combined = res.output + str(res.exception or "")
    assert "source ref" in combined


@respx.mock
def test_clone_records_the_project_marker():
    """A clone into a differently-named folder left no `.tamarind`, so the next bare
    `deploy` fell back to the folder name and targeted a different tool. Third write
    site for the marker and the one that was missing.
    """
    import io
    import zipfile
    from pathlib import Path
    from tempfile import mkdtemp

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("Dockerfile", "FROM scratch\n")
    respx.get(f"{API}v2/custom-tools/mytool/archive").mock(
        return_value=httpx.Response(200, content=buf.getvalue())
    )
    dest = Path(mkdtemp()) / "differently-named"
    res = runner.invoke(app, ["ct", "clone", "mytool", str(dest)], env=ENV)
    assert res.exit_code == 0, res.output + str(res.exception or "")
    assert (dest / ".tamarind").is_file(), "no marker written; a bare deploy would guess"
    assert json.loads((dest / ".tamarind").read_text())["name"] == "mytool"


def test_config_apply_refuses_flags_it_would_discard(tmp_path):
    """`--apply` pushes config.json only. Accepting `--env` alongside it and reporting
    success claimed a credential had been stored when it was never sent."""
    (tmp_path / "config.json").write_text("{}\n")
    res = runner.invoke(
        app,
        ["ct", "config", "mytool", "--apply", str(tmp_path), "--env", "KEY=value"],
        env=ENV,
    )
    assert res.exit_code != 0
    combined = res.output + str(res.exception or "")
    assert "--env" in combined and "ignored" in combined


@pytest.mark.parametrize("bad", ["-1", "nan"])
def test_deploy_validates_the_timeout_before_uploading(tmp_path, bad):
    """`--timeout -1` expired only after a remote build had started; `--timeout nan`
    produced a deadline no comparison ever satisfies, so the bound did nothing.

    No HTTP is mocked: the check must fire before any request, so a call reaching the
    network fails this differently.
    """
    (tmp_path / "Dockerfile").write_text("FROM scratch\n")
    (tmp_path / "run.sh").write_text("true\n")
    (tmp_path / "config.json").write_text("{}\n")
    res = runner.invoke(app, ["deploy", str(tmp_path), "--timeout", bad], env=ENV)
    assert res.exit_code != 0
    combined = res.output + str(res.exception or "")
    assert "finite" in combined or "non-negative" in combined
