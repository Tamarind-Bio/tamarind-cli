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
