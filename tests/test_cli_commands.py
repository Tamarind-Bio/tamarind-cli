"""Command-level tests (Typer runner + mocked HTTP) for parsing edge cases that
live testing against staging surfaced: the logs response shape and a non-list
folders response."""

import httpx
import respx
from typer.testing import CliRunner

from tamarind.cli.main import app

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
def test_logs_surfaces_error():
    respx.get(f"{CAT}catalog/jobs/job1/logs").mock(
        return_value=httpx.Response(200, json={"error": "Log file not found"})
    )
    res = runner.invoke(app, ["logs", "job1"], env=ENV)
    assert res.exit_code != 0


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
def test_upload_handles_non_dict_sentinel(tmp_path):
    # Staging /uploadFile can return a bare -1; the command must fail cleanly, not crash.
    f = tmp_path / "x.txt"
    f.write_text("hi")
    respx.post(f"{API}uploadFile").mock(return_value=httpx.Response(200, text="-1"))
    res = runner.invoke(app, ["files", "upload", str(f)], env=ENV)
    assert res.exit_code != 0
    assert not isinstance(res.exception, AttributeError)
