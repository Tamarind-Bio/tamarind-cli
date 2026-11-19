"""The CLI on the v1 API, against a fake SDK client.

The CLI calls v1 only through ``tamarind.cli.v1.sdk``; these tests replace the
SDK client with a recorder, so they check what each command asks the SDK for
and what it prints, and that classic stays the default.
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from typer.testing import CliRunner

from tamarind.cli.main import app
from tamarind.cli.v1 import sdk  # noqa: F401

from conftest import remember_v1, turn_v1_on
from tamarind.errors import NotFoundError, UsageError

runner = CliRunner()


class Recorder:
    """Stands in for the v1 SDK client: records calls, answers from a table."""

    def __init__(self, answers: dict[str, Any]) -> None:
        self.answers = answers
        self.calls: list[tuple[str, tuple, dict]] = []

    def __enter__(self) -> "Recorder":
        return self

    def __exit__(self, *exc: object) -> None:
        return None

    def close(self) -> None:
        return None

    def __getattr__(self, name: str) -> "_Path":
        return _Path(self, (name,))

    def paginate(self, method: "_Path", *args: Any, **params: Any):
        """Like ``tamarind._v1.Tamarind.paginate``: every item, following nextCursor
        (in the body when the call has one, as for molecules.search)."""
        if "body" in params:
            body = dict(params.pop("body") or {})
            while True:
                page = method(*args, body=body, **params)
                yield from page.get("items") or []
                if not page.get("nextCursor"):
                    return
                body = {**body, "cursor": page["nextCursor"]}
        cursor = params.pop("cursor", None)
        while True:
            page = method(*args, cursor=cursor, **params)
            yield from page.get("items") or []
            cursor = page.get("nextCursor")
            if not cursor:
                return


class _Path:
    def __init__(self, root: Recorder, path: tuple[str, ...]) -> None:
        self.root = root
        self.path = path

    def __getattr__(self, name: str) -> "_Path":
        return _Path(self.root, self.path + (name,))

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        name = ".".join(self.path)
        self.root.calls.append((name, args, kwargs))
        answer = self.root.answers.get(name)
        if isinstance(answer, BaseException):
            raise answer
        if callable(answer):
            return answer(*args, **kwargs)
        return answer


@pytest.fixture
def v1(monkeypatch, tmp_path):
    monkeypatch.setenv("TAMARIND_CONFIG_DIR", str(tmp_path))
    monkeypatch.setenv("TAMARIND_API_KEY", "test-key")
    monkeypatch.delenv("TAMARIND_API", raising=False)
    recorder = Recorder({})
    turn_v1_on(monkeypatch, client=recorder)
    remember_v1(tmp_path, "test-key")  # what --help lists v1 commands by
    return recorder


def _json(result) -> Any:
    assert result.exit_code == 0, (result.output, result.exception)
    return json.loads(result.stdout)


# -- selection -------------------------------------------------------------


def test_custom_tools_on_v1_go_to_the_v1_base(monkeypatch, tmp_path):
    from tamarind.cli.main import State
    from tamarind.cli.output import OutputMode

    monkeypatch.setenv("TAMARIND_CONFIG_DIR", str(tmp_path))
    monkeypatch.setenv("TAMARIND_V1_API_BASE", "https://api-staging.example")
    turn_v1_on(monkeypatch)
    state = State(
        output=OutputMode(json=True, quiet=False),
        _kwargs={"api_key": "k", "api_base": None, "catalog_base": None, "profile": None},
    )
    client = state.sdk_client()
    try:
        # The classic base stays the client's; a custom-tools request is sent to v1's.
        assert str(client._http.base_url) == "https://app.tamarind.bio/api/"
        assert client._http._raw_client("custom-tools").base_url == "https://api-staging.example"
        assert client._http._raw_client("submit-job") is client._http
    finally:
        client.close()


def test_v1_only_commands_are_hidden_and_refused_in_classic(monkeypatch, tmp_path):
    monkeypatch.setenv("TAMARIND_CONFIG_DIR", str(tmp_path))
    monkeypatch.delenv("TAMARIND_API", raising=False)
    monkeypatch.setenv("TAMARIND_API_KEY", "k")
    help_text = runner.invoke(app, ["--help"]).stdout
    assert "projects" not in help_text and "molecules" not in help_text
    assert "download" not in runner.invoke(app, ["files", "--help"]).stdout
    res = runner.invoke(app, ["projects", "list"])
    assert isinstance(res.exception, UsageError)
    assert "isn't enabled for this account yet" in str(res.exception)


def test_v1_commands_show_in_help_when_selected(v1):
    help_text = runner.invoke(app, ["--help"]).stdout
    for group in ("projects", "molecules", "pipelines", "assays", "keys", "org", "usage", "models"):
        assert group in help_text
    assert "download" in runner.invoke(app, ["files", "--help"]).stdout


# -- generic commands ------------------------------------------------------


def test_generic_command_maps_path_query_and_body(v1, tmp_path):
    v1.answers["projects.notes.create_entry"] = {"id": "ent_1", "title": "x"}
    body = tmp_path / "entry.yaml"
    body.write_text("title: Round 1\nkind: note\n")
    res = runner.invoke(
        app,
        ["--json", "projects", "notes", "add", "prj_1", "--input", str(body), "--set", "meta.count=3"],
    )
    assert _json(res) == {"id": "ent_1", "title": "x"}
    name, args, kwargs = v1.calls[-1]
    assert name == "projects.notes.create_entry"
    assert args == ("prj_1",)
    assert kwargs == {"body": {"title": "Round 1", "kind": "note", "meta": {"count": 3}}}


def test_generic_list_sends_only_given_options_and_splits_lists(v1):
    v1.answers["molecules.list"] = {"items": [{"id": "mol_1"}], "nextCursor": None}
    res = runner.invoke(app, ["--json", "molecules", "list", "--limit", "5"])
    assert _json(res)["items"] == [{"id": "mol_1"}]
    assert v1.calls[-1] == ("molecules.list", (), {"limit": 5})
    v1.answers["usage.get"] = {"items": [], "nextCursor": None}
    runner.invoke(app, ["--json", "usage", "--group-by", "tool,month", "--group-by", "user"])
    assert v1.calls[-1][2]["group_by"] == ["tool", "month", "user"]


def test_generic_all_follows_next_cursor(v1):
    pages = iter(
        [
            {"items": [{"id": "a"}], "nextCursor": "c1"},
            {"items": [{"id": "b"}], "nextCursor": None},
        ]
    )
    v1.answers["projects.list"] = lambda **kw: next(pages)
    res = runner.invoke(app, ["--json", "projects", "list", "--all"])
    assert _json(res) == {"items": [{"id": "a"}, {"id": "b"}], "nextCursor": None}
    assert [c[2].get("cursor") for c in v1.calls] == [None, "c1"]


def test_group_that_is_also_a_command_runs_its_operation(v1):
    v1.answers["projects.notes.get"] = {"entries": []}
    v1.answers["projects.notes.update"] = {"entries": [], "version": 2}
    assert _json(runner.invoke(app, ["--json", "projects", "notes", "prj_9"])) == {"entries": []}
    assert v1.calls[-1] == ("projects.notes.get", ("prj_9",), {})
    res = runner.invoke(app, ["--json", "projects", "notes", "update", "prj_9", "--set", "title=T"])
    assert _json(res)["version"] == 2
    assert v1.calls[-1] == ("projects.notes.update", ("prj_9",), {"body": {"title": "T"}})
    v1.answers["usage.get"] = {"items": [], "nextCursor": None}
    assert _json(runner.invoke(app, ["--json", "usage"]))["items"] == []


def test_idempotency_key_and_if_match_are_passed_through(v1):
    v1.answers["custom_tools.validate_config"] = {"valid": True}
    res = runner.invoke(app, ["--json", "custom-tools", "validate-config", "--set", "name=t"])
    assert _json(res) == {"valid": True}
    v1.answers["assays.submit"] = {"id": "asy_1"}
    res = runner.invoke(app, ["--json", "assays", "submit", "--set", "x=1", "--idempotency-key", "k-1", "--yes"])
    assert _json(res) == {"id": "asy_1"}
    assert v1.calls[-1][2]["idempotency_key"] == "k-1"


def test_required_body_missing_lets_the_server_answer(v1):
    v1.answers["projects.create"] = {"id": "prj_1"}
    runner.invoke(app, ["--json", "projects", "create"])
    assert v1.calls[-1] == ("projects.create", (), {"body": {}})


def test_errors_keep_exit_codes(v1):
    v1.answers["models.get"] = NotFoundError("Model not found.", detail={"code": "model_not_found"})
    res = runner.invoke(app, ["--json", "models", "get", "mdl_x"])
    assert isinstance(res.exception, NotFoundError)


# -- more v1 commands ------------------------------------------------------------


def test_files_download_saves_without_printing_the_link(v1, tmp_path, monkeypatch):
    from tamarind.cli.commands import jobs as jobs_cmds

    v1.answers["files.get"] = {"url": "https://s3.example/a.pdb?X-Amz-Signature=s", "expiresAt": "t", "sizeBytes": 4}
    monkeypatch.setattr(jobs_cmds, "_download", lambda url, dest: 4)
    res = runner.invoke(app, ["--json", "files", "download", "dir/a.pdb", "-o", str(tmp_path)])
    out = _json(res)
    assert out == {"path": str(tmp_path / "a.pdb"), "bytes": 4}
    assert v1.calls[-1] == ("files.get", (), {"path": "dir/a.pdb", "delivery": "url"})


def test_only_comma_joined_arrays_are_split(v1):
    v1.answers["molecules.list"] = {"items": [], "nextCursor": None}
    runner.invoke(app, ["--json", "molecules", "list", "--filter", "label:eq:a,b", "--filter", "x:eq:1"])
    assert v1.calls[-1][2]["filter_"] == ["label:eq:a,b", "x:eq:1"]
    v1.answers["files.list"] = {"items": [], "nextCursor": None}
    v1.answers["usage.get"] = {"items": [], "nextCursor": None}
    runner.invoke(app, ["--json", "usage", "--group-by", "tool,month"])
    assert v1.calls[-1][2]["group_by"] == ["tool", "month"]


def test_help_honors_an_explicit_profile(monkeypatch, tmp_path):
    import sys

    monkeypatch.setenv("TAMARIND_CONFIG_DIR", str(tmp_path))
    monkeypatch.delenv("TAMARIND_API", raising=False)
    monkeypatch.delenv("TAMARIND_PROFILE", raising=False)
    monkeypatch.delenv("TAMARIND_API_KEY", raising=False)
    (tmp_path / "config.json").write_text(
        json.dumps({"current_profile": "default", "profiles": {"default": {"api_key": "k1"}, "next": {"api_key": "k2"}}})
    )
    remember_v1(tmp_path, "k2")  # v1 is on for the next profile's key, not the default's
    monkeypatch.setattr(sys, "argv", ["tamarind", "--profile", "next", "--help"])
    assert "projects" in runner.invoke(app, ["--profile", "next", "--help"]).stdout
    monkeypatch.setattr(sys, "argv", ["tamarind", "--help"])
    assert "projects" not in runner.invoke(app, ["--help"]).stdout


def test_help_never_asks_the_server(monkeypatch, tmp_path):
    monkeypatch.setenv("TAMARIND_CONFIG_DIR", str(tmp_path))
    monkeypatch.setenv("TAMARIND_API_KEY", "k")
    monkeypatch.delenv("TAMARIND_API", raising=False)
    from tamarind._v1 import switch

    monkeypatch.setattr(switch, "probe", lambda *a, **k: pytest.fail("--help asked /me"))
    for args in (["--help"], ["jobs", "--help"], ["files", "--help"], ["--version"]):
        assert runner.invoke(app, args).exit_code == 0
    assert "projects" not in runner.invoke(app, ["--help"]).stdout


def test_generated_destructive_commands_need_yes(v1):
    v1.answers["api_keys.revoke"] = None
    res = runner.invoke(app, ["--json", "keys", "revoke", "key_1"])
    assert res.exit_code == 2 and v1.calls == []
    res = runner.invoke(app, ["--json", "keys", "revoke", "key_1", "--yes"])
    assert _json(res) == {"ok": True}
    assert v1.calls == [("api_keys.revoke", ("key_1",), {})]


def test_signed_links_are_redacted_unless_asked_for(v1):
    signed = "https://bucket.s3.amazonaws.com/m.pdb?X-Amz-Signature=abc&X-Amz-Credential=k"
    v1.answers["molecules.get"] = {"id": "mol_1", "files": {"boltz": [{"path": "m.pdb", "downloadUrl": signed}]}}
    out = _json(runner.invoke(app, ["--json", "molecules", "get", "mol_1"]))
    assert signed not in json.dumps(out)
    out = _json(runner.invoke(app, ["--json", "molecules", "get", "mol_1", "--show-urls"]))
    assert out["files"]["boltz"][0]["downloadUrl"] == signed


def test_values_outside_a_contract_enum_are_usage_errors(v1):
    res = runner.invoke(app, ["--json", "usage", "--metric", "bogus"])
    assert isinstance(res.exception, UsageError) and v1.calls == []
    res = runner.invoke(app, ["--json", "jobs", "list", "--status", "Running,Bogus"])
    assert isinstance(res.exception, UsageError) and v1.calls == []


def test_login_refuses_a_blank_key_on_v1(v1):
    res = runner.invoke(app, ["--json", "auth", "login", "--api-key", "   "])
    assert res.exception is not None and res.exception.exit_code == 3
    assert v1.calls == []


def test_an_assay_order_and_its_cancel_need_yes(v1):
    v1.answers["assays.submit"] = {"id": "asy_1"}
    res = runner.invoke(app, ["--json", "assays", "submit", "--set", "x=1"])
    assert res.exit_code == 2 and v1.calls == []
    v1.answers["assays.cancel"] = {"id": "asy_1", "status": "cancelled"}
    res = runner.invoke(app, ["--json", "assays", "cancel", "asy_1"])
    assert res.exit_code == 2 and v1.calls == []
    assert _json(runner.invoke(app, ["--json", "assays", "cancel", "asy_1", "--yes"]))["status"] == "cancelled"


def test_confirm_first_comes_from_the_contract():
    from tamarind.cli.v1 import manifest

    assert {o["operationId"] for o in manifest.operations() if o["confirmFirst"]} == {"submitAssay", "cancelAssay"}


def test_bad_date_times_are_usage_errors(v1):
    res = runner.invoke(app, ["--json", "usage", "--from", "bogus"])
    assert isinstance(res.exception, UsageError) and v1.calls == []
    v1.answers["usage.get"] = {"items": [], "nextCursor": None}
    _json(runner.invoke(app, ["--json", "usage", "--from", "2026-10-01T00:00:00Z"]))
    assert v1.calls[-1][2]["from_"] == "2026-10-01T00:00:00Z"


def test_all_pages_keep_the_pages_other_fields(v1):
    pages = iter(
        [
            {"items": [{"tool": "boltz"}], "nextCursor": "c1", "total": 7, "metric": "jobs", "asOf": "t"},
            {"items": [{"tool": "esmfold"}], "nextCursor": None, "total": 7, "metric": "jobs", "asOf": "t"},
        ]
    )
    v1.answers["usage.get"] = lambda **kw: next(pages)
    out = _json(runner.invoke(app, ["--json", "usage", "--metric", "jobs", "--all"]))
    assert out == {"items": [{"tool": "boltz"}, {"tool": "esmfold"}], "nextCursor": None, "total": 7, "metric": "jobs", "asOf": "t"}


def test_jobs_download_of_a_pipeline_run_is_refused(v1):
    res = runner.invoke(app, ["--json", "jobs", "download", "run_0f8fad5b-d9cb-469f-a165-70867728950e", "--path", "x.pdb"])
    assert isinstance(res.exception, UsageError) and v1.calls == []


def test_default_operation_groups_show_its_options_in_help(v1):
    text = runner.invoke(app, ["usage", "--help"]).stdout
    assert "--metric" in text and "refresh" in text
    text = runner.invoke(app, ["projects", "notes", "--help"]).stdout
    assert "PROJECT_ID" in text and "add" in text


def test_generated_writes_with_an_idempotency_key_say_how_to_retry(v1):
    from tamarind.errors import APIError

    v1.answers["pipelines.submit"] = APIError("503 service_unavailable", status_code=503)
    res = runner.invoke(app, ["--json", "pipelines", "submit", "--set", "name=p"])
    key = v1.calls[-1][2]["idempotency_key"]
    assert res.exception.detail["idempotencyKey"] == key
    assert f"--idempotency-key {key}" in str(res.exception)


def test_show_urls_shows_them_in_human_output_too(v1):
    signed = "https://bucket.s3.amazonaws.com/a.pdb?X-Amz-Signature=abc"
    v1.answers["jobs.list_files"] = {"items": [{"path": "a.pdb", "downloadUrl": signed}], "nextCursor": None}
    res = runner.invoke(app, ["--no-json", "jobs", "files", "job_0f8fad5b-d9cb-469f-a165-70867728950e", "--include-download-urls", "--show-urls"])
    assert signed in res.stdout


def test_all_follows_a_body_cursor(v1):
    pages = {None: {"items": [{"id": "mol_1"}], "nextCursor": "c1"}, "c1": {"items": [{"id": "mol_2"}], "nextCursor": None}}
    v1.answers["molecules.search"] = lambda body=None, **kw: pages[(body or {}).get("cursor")]
    out = _json(runner.invoke(app, ["--json", "molecules", "search", "--set", "text=abc", "--all"]))
    assert [m["id"] for m in out["items"]] == ["mol_1", "mol_2"] and out["nextCursor"] is None
    assert [c[2]["body"] for c in v1.calls] == [{"text": "abc"}, {"text": "abc", "cursor": "c1"}]


def test_an_error_on_an_answer_is_not_called_unclear(v1):
    from tamarind.errors import TamarindError

    v1.answers["api_keys.create"] = TamarindError(
        "Key key_1 was made by an earlier attempt with this Idempotency-Key, and its secret can't be shown again."
    )
    res = runner.invoke(app, ["--json", "keys", "create", "--set", "name=k"])
    assert "--idempotency-key" not in str(res.exception)
    assert str(res.exception).startswith("Key key_1 was made by an earlier attempt")


def test_an_assay_order_its_key_cant_read_back_is_an_unclear_outcome(v1):
    """409 idempotency_order_unavailable: the key's order was placed, so the key is shown
    for the retry rather than read as a refusal (a new key would order again)."""
    from tamarind._v1.errors import ProblemError

    v1.answers["assays.submit"] = ProblemError(
        status=409, code="idempotency_order_unavailable", title="Conflict",
        detail="This key's order can't be read back.",
    )
    res = runner.invoke(app, ["--json", "assays", "submit", "--set", "x=1", "--yes"])
    assert res.exception.detail["outcomeMayBeAmbiguous"] is True
    assert "--idempotency-key" in str(res.exception)


def test_no_answer_is_an_unclear_outcome(v1):
    import httpx

    from tamarind.errors import TamarindError

    def lost(**kwargs):
        raise TamarindError("Network error: connection reset") from httpx.ConnectError("reset")

    v1.answers["api_keys.create"] = lost
    res = runner.invoke(app, ["--json", "keys", "create", "--set", "name=k"])
    assert res.exception.detail["outcomeMayBeAmbiguous"] is True
    assert "--idempotency-key" in str(res.exception)



def test_all_only_on_operations_that_answer_pages(v1):
    assert "--all" in runner.invoke(app, ["jobs", "list", "--help"]).stdout
    assert "--all" in runner.invoke(app, ["molecules", "search", "--help"]).stdout
    # a log chunk has a cursor but isn't a page of items
    assert "--all" not in runner.invoke(app, ["jobs", "logs", "--help"]).stdout


def test_all_reports_the_last_pages_scan_state(v1, monkeypatch):
    import time

    slept: list[float] = []
    monkeypatch.setattr(time, "sleep", slept.append)
    pages = {
        None: {"items": [{"id": "mol_1"}], "nextCursor": "c1", "waiting": True, "retryAfterMs": 250, "scanProgress": 0.4},
        "c1": {"items": [{"id": "mol_2"}], "nextCursor": None, "waiting": False, "retryAfterMs": None, "scanProgress": 1.0},
    }
    v1.answers["molecules.list"] = lambda **kw: pages[kw.get("cursor")]
    out = _json(runner.invoke(app, ["--json", "molecules", "list", "--all"]))
    assert [m["id"] for m in out["items"]] == ["mol_1", "mol_2"]
    assert out["waiting"] is False and out["scanProgress"] == 1.0 and out["nextCursor"] is None
    assert slept == [0.25]


def test_download_to_a_new_directory_keeps_its_separator(v1, tmp_path, monkeypatch):
    import os

    from tamarind.cli.commands import jobs as jobs_cmds

    saved: list[str] = []
    v1.answers["files.get"] = {"url": "https://s3.example/a.pdb?X-Amz-Signature=s", "sizeBytes": 4}
    monkeypatch.setattr(jobs_cmds, "_download", lambda url, dest: saved.append(str(dest)) or 4)
    target = str(tmp_path / "newdir") + os.sep  # doesn't exist yet
    _json(runner.invoke(app, ["--json", "files", "download", "dir/a.pdb", "-o", target]))
    assert saved == [str(tmp_path / "newdir" / "a.pdb")]


def test_all_keeps_polling_a_waiting_cursor(v1, monkeypatch):
    import time

    monkeypatch.setattr(time, "sleep", lambda seconds: None)
    answers = iter(
        [
            {"items": [{"id": "mol_1"}], "nextCursor": "c1", "waiting": True, "retryAfterMs": 10},
            {"items": [], "nextCursor": "c1", "waiting": True, "retryAfterMs": 10, "waitReason": "stuck"},
            {"items": [{"id": "mol_2"}], "nextCursor": None, "waiting": False},
        ]
    )
    v1.answers["molecules.list"] = lambda **kw: next(answers)
    out = _json(runner.invoke(app, ["--json", "molecules", "list", "--all"]))
    assert [m["id"] for m in out["items"]] == ["mol_1", "mol_2"] and out["nextCursor"] is None


def test_all_sends_if_match_on_every_page():
    from tamarind.cli.v1 import manifest

    pages = {None: {"items": [1], "nextCursor": "c1"}, "c1": {"items": [2], "nextCursor": None}}
    recorder = Recorder({"custom_tools.list_versions": lambda *a, cursor=None, **kw: pages[cursor]})
    out = sdk.collect(recorder, manifest.operation("listCustomToolVersions"), "tool-a", if_match="etag-1")
    assert out["items"] == [1, 2]
    assert [c[2].get("if_match") for c in recorder.calls] == ["etag-1", "etag-1"]
