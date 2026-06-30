"""Command-level tests (Typer runner + mocked HTTP) for parsing edge cases that
live testing against staging surfaced: the logs response shape and a non-list
folders response."""

import httpx
import respx
from typer.testing import CliRunner

from tamarind.cli.main import app
from tamarind.errors import NotFoundError, TamarindError

runner = CliRunner()

API = "https://api.test/"
CAT = "https://cat.test/"
ENV = {
    "TAMARIND_API_KEY": "k",
    "TAMARIND_API_BASE": API,
    "TAMARIND_CATALOG_BASE": CAT,
}


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
            json={"uploadUrl": upload_url, "headUrl": "https://h", "key": "user@x.com/target.pdb", "bucket": "b"},
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
