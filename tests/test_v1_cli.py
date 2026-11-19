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

from tamarind import config
from tamarind.cli.main import app
from tamarind.cli.v1 import sdk
from tamarind.errors import JobTimeoutError, NotFoundError, UsageError

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

    def __getattr__(self, name: str) -> "_Path":
        return _Path(self, (name,))

    def paginate(self, method: "_Path", *args: Any, **params: Any):
        """Like ``tamarind.v1.Tamarind.paginate``: every item, following nextCursor."""
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
    monkeypatch.setenv("TAMARIND_API", "v1")
    recorder = Recorder({})
    monkeypatch.setattr(sdk, "make_client", lambda state, api_key=None: recorder)
    return recorder


def _json(result) -> Any:
    assert result.exit_code == 0, (result.output, result.exception)
    return json.loads(result.stdout)


# -- selection -------------------------------------------------------------


def test_classic_is_the_default(monkeypatch, tmp_path):
    monkeypatch.setenv("TAMARIND_CONFIG_DIR", str(tmp_path))
    monkeypatch.delenv("TAMARIND_API", raising=False)
    cfg = config.load_config()
    assert cfg.api == "classic" and not cfg.is_v1
    assert cfg.v1_api_base == "https://api.tamarind.bio/"


def test_v1_is_chosen_by_env_flag_or_profile(monkeypatch, tmp_path):
    monkeypatch.setenv("TAMARIND_CONFIG_DIR", str(tmp_path))
    monkeypatch.delenv("TAMARIND_API", raising=False)
    assert config.load_config(api="v1").is_v1
    monkeypatch.setenv("TAMARIND_API", "V1")
    assert config.load_config().is_v1
    assert config.load_config(api="classic").api == "classic"
    monkeypatch.delenv("TAMARIND_API")
    (tmp_path / "config.json").write_text(json.dumps({"profiles": {"default": {"api": "v1"}}}))
    assert config.load_config().is_v1


def test_unknown_api_value_is_a_usage_error(monkeypatch, tmp_path):
    monkeypatch.setenv("TAMARIND_CONFIG_DIR", str(tmp_path))
    monkeypatch.setenv("TAMARIND_API", "v2")
    with pytest.raises(UsageError):
        config.load_config()


def test_v1_base_never_falls_back_to_a_classic_base(monkeypatch, tmp_path):
    monkeypatch.setenv("TAMARIND_CONFIG_DIR", str(tmp_path))
    monkeypatch.setenv("TAMARIND_API_BASE", "https://classic.example/api")
    (tmp_path / "config.json").write_text(
        json.dumps({"profiles": {"default": {"api_base": "https://profile.example/api"}}})
    )
    cfg = config.load_config(api="v1")
    assert cfg.v1_api_base == "https://api.tamarind.bio/"
    assert cfg.api_base == "https://classic.example/api/"
    monkeypatch.setenv("TAMARIND_V1_API_BASE", "https://api-staging.example")
    assert config.load_config(api="v1").v1_api_base == "https://api-staging.example/"
    explicit = config.load_config(api="v1", v1_api_base="https://v1.example", api_base="https://c.example")
    assert explicit.v1_api_base == "https://v1.example/"
    # An explicit classic base is honored whichever API is selected (the classic
    # SDK's custom-tools resource is pointed at the v1 base this way).
    assert explicit.api_base == "https://c.example/"


def test_api_base_flag_names_the_selected_apis_base(monkeypatch, tmp_path):
    from tamarind.cli.main import State
    from tamarind.cli.output import OutputMode

    monkeypatch.setenv("TAMARIND_CONFIG_DIR", str(tmp_path))
    monkeypatch.delenv("TAMARIND_API_BASE", raising=False)
    monkeypatch.delenv("TAMARIND_V1_API_BASE", raising=False)
    kwargs = {"api_key": None, "api_base": "https://flag.example", "catalog_base": None, "profile": None}
    v1_state = State(output=OutputMode(json=True, quiet=False), _kwargs={**kwargs, "api": "v1"})
    cfg = v1_state.config()
    assert cfg.v1_api_base == "https://flag.example/" and cfg.api_base == "https://app.tamarind.bio/api/"
    classic_state = State(output=OutputMode(json=True, quiet=False), _kwargs={**kwargs, "api": None})
    cfg = classic_state.config()
    assert cfg.api_base == "https://flag.example/" and cfg.v1_api_base == "https://api.tamarind.bio/"


def test_custom_tools_on_v1_use_the_v1_base(monkeypatch, tmp_path):
    from tamarind.cli.main import State
    from tamarind.cli.output import OutputMode

    monkeypatch.setenv("TAMARIND_CONFIG_DIR", str(tmp_path))
    monkeypatch.setenv("TAMARIND_API", "v1")
    monkeypatch.setenv("TAMARIND_V1_API_BASE", "https://api-staging.example")
    state = State(
        output=OutputMode(json=True, quiet=False),
        _kwargs={"api_key": "k", "api_base": None, "catalog_base": None, "profile": None, "api": None},
    )
    client = state.sdk_client()
    try:
        assert str(client._http.base_url) == "https://api-staging.example/"
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
    assert "TAMARIND_API=v1" in str(res.exception)


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


# -- today's commands on v1 ---------------------------------------------------


def test_submit_sends_kind_tool_settings_and_name(v1, tmp_path):
    v1.answers["jobs.submit"] = {"kind": "job", "id": "job_00000000-0000-0000-0000-000000000001", "name": "fold-1", "status": "In Queue"}
    settings = tmp_path / "s.yaml"
    settings.write_text("sequence: MKT\n")
    res = runner.invoke(app, ["--json", "submit", "esmfold", "-i", str(settings), "-n", "fold-1", "--low-priority"])
    assert _json(res)["id"] == "job_00000000-0000-0000-0000-000000000001"
    assert [c[0] for c in v1.calls] == ["jobs.submit"]  # no separate validate call on v1
    assert v1.calls[0][2].pop("idempotency_key")  # the CLI picks one, so a retry can reuse it
    assert v1.calls[0][2] == {
        "body": {
            "kind": "job",
            "tool": "esmfold",
            "settings": {"sequence": "MKT"},
            "name": "fold-1",
            "lowPriority": True,
        }
    }


def test_jobs_submit_is_the_same_command(v1):
    v1.answers["jobs.submit"] = {"kind": "job", "id": "job_00000000-0000-0000-0000-000000000002", "name": "n", "status": "In Queue"}
    res = runner.invoke(app, ["--json", "jobs", "submit", "esmfold", "--set", "sequence=MKT"])
    assert _json(res)["id"] == "job_00000000-0000-0000-0000-000000000002"
    assert "name" not in v1.calls[0][2]["body"]  # the server names it


def test_submit_wait_and_failed_exit_code(v1):
    v1.answers["jobs.submit"] = {"kind": "job", "id": "job_00000000-0000-0000-0000-000000000003", "name": "n", "status": "In Queue"}
    v1.answers["jobs.wait"] = {"id": "job_00000000-0000-0000-0000-000000000003", "name": "n", "status": "Failed", "stopReason": {"kind": "error"}}
    res = runner.invoke(app, ["--json", "submit", "esmfold", "--set", "sequence=MKT", "--wait"])
    assert res.exit_code == 9
    out = json.loads(res.stdout)
    assert out["submit"]["id"] == "job_00000000-0000-0000-0000-000000000003" and out["final"]["status"] == "Failed"
    assert v1.calls[-1][0] == "jobs.wait" and v1.calls[-1][1] == ("job_00000000-0000-0000-0000-000000000003",)


def test_wait_timeout_keeps_exit_code(v1):
    v1.answers["jobs.wait"] = JobTimeoutError("still running")
    res = runner.invoke(app, ["--json", "wait", "job_00000000-0000-0000-0000-000000000004", "--timeout", "1"])
    assert isinstance(res.exception, JobTimeoutError)


def test_batch_sends_kind_batch_with_names(v1, tmp_path):
    rows = tmp_path / "rows.yaml"
    rows.write_text(
        "batchName: b1\nsettings:\n  - {sequence: MKT}\n  - {sequence: MKV}\njobNames: [a, b]\n"
    )
    v1.answers["jobs.validate"] = {"valid": True, "count": 2, "validCount": 2, "errors": [], "results": []}
    v1.answers["jobs.submit"] = {"kind": "batch", "id": "batch_00000000-0000-0000-0000-000000000001", "name": "b1", "status": "In Queue"}
    res = runner.invoke(app, ["--json", "batch", "esmfold", "-i", str(rows), "--prevalidate"])
    assert _json(res)["id"] == "batch_00000000-0000-0000-0000-000000000001"
    assert [c[0] for c in v1.calls] == ["jobs.validate", "jobs.submit"]
    assert v1.calls[1][2]["body"] == {
        "kind": "batch",
        "tool": "esmfold",
        "settings": [{"sequence": "MKT"}, {"sequence": "MKV"}],
        "name": "b1",
        "names": ["a", "b"],
    }


def test_validate_invalid_exits_5(v1):
    v1.answers["jobs.validate"] = {
        "valid": False,
        "checks": {"settings": "failed"},
        "errors": [{"pointer": "/settings/sequence", "detail": "required"}],
        "warnings": [],
    }
    res = runner.invoke(app, ["--json", "validate", "esmfold"])
    assert res.exit_code == 5
    assert json.loads(res.stdout)["valid"] is False


def test_status_by_name_resolves_through_list_jobs(v1):
    v1.answers["jobs.list"] = {"items": [{"id": "job_00000000-0000-0000-0000-000000000009", "name": "fold-1"}], "nextCursor": None}
    v1.answers["jobs.get"] = {"id": "job_00000000-0000-0000-0000-000000000009", "name": "fold-1", "status": "Running"}
    res = runner.invoke(app, ["--json", "status", "fold-1"])
    assert _json(res)["id"] == "job_00000000-0000-0000-0000-000000000009"
    assert v1.calls == [
        ("jobs.list", (), {"name": "fold-1"}),
        ("jobs.get", ("job_00000000-0000-0000-0000-000000000009",), {}),
    ]


def test_status_by_id_skips_the_lookup(v1):
    v1.answers["jobs.get"] = {"id": "batch_00000000-0000-0000-0000-000000000001", "status": "Complete", "kind": "batch"}
    runner.invoke(app, ["--json", "jobs", "get", "batch_00000000-0000-0000-0000-000000000001"])
    assert v1.calls == [("jobs.get", ("batch_00000000-0000-0000-0000-000000000001",), {})]


def test_unknown_name_is_not_found(v1):
    v1.answers["jobs.list"] = {"items": [], "nextCursor": None}
    res = runner.invoke(app, ["--json", "status", "nope"])
    assert isinstance(res.exception, NotFoundError)


def test_jobs_list_maps_today_flags(v1):
    v1.answers["jobs.list"] = lambda **kw: (
        {"items": [{"id": "batch_00000000-0000-0000-0000-000000000007", "name": "b"}], "nextCursor": None}
        if kw.get("name")
        else {"items": [{"id": "job_00000000-0000-0000-0000-000000000001", "status": "Running"}], "nextCursor": "cur"}
    )
    res = runner.invoke(
        app,
        ["--json", "jobs", "--status", "Running,In Queue", "--batch", "b", "--limit", "10", "--start-key", "s0"],
    )
    out = _json(res)
    assert out["nextCursor"] == "cur"
    assert v1.calls[0] == ("jobs.list", (), {"name": "b", "kind": "batch"})
    assert v1.calls[1][2] == {
        "limit": 10,
        "status": ["Running", "In Queue"],
        "batch_id": "batch_00000000-0000-0000-0000-000000000007",
        "cursor": "s0",
    }
    res = runner.invoke(app, ["--json", "jobs", "--include-subjobs"])
    assert isinstance(res.exception, UsageError)


def test_results_downloads_the_archive(v1, tmp_path, monkeypatch):
    from tamarind.cli.commands import jobs as jobs_cmds

    v1.answers["jobs.archive"] = {"status": "ready", "downloadUrl": "https://s3.example/x.zip", "expiresAt": "t", "sizeBytes": 3, "fileCount": 1, "truncated": False}
    fetched = []

    def fake_download(url, dest):
        fetched.append((url, dest))
        return 3

    monkeypatch.setattr(jobs_cmds, "_download", fake_download)
    res = runner.invoke(app, ["--json", "results", "job_00000000-0000-0000-0000-000000000005", "--download", str(tmp_path), "--pdbs-only"])
    out = _json(res)
    assert out["download"]["bytes"] == 3
    assert v1.calls[-1] == ("jobs.archive", ("job_00000000-0000-0000-0000-000000000005",), {"body": {"glob": "*.pdb"}})
    assert fetched[0][0] == "https://s3.example/x.zip"
    assert "url" not in out  # the signed link stays out of the output unless --show-url


def test_results_preparing_without_wait_says_so(v1, tmp_path):
    v1.answers["jobs.archive"] = {"status": "preparing", "retryAfterSeconds": 30}
    res = runner.invoke(app, ["--json", "results", "job_00000000-0000-0000-0000-000000000005", "--download", str(tmp_path)])
    assert res.exit_code != 0
    assert "--wait" in str(res.exception)


def test_logs_tails_lines(v1):
    v1.answers["jobs.logs"] = {"content": "a\nb\nc\n", "nextCursor": None, "complete": True}
    res = runner.invoke(app, ["--no-json", "logs", "job_00000000-0000-0000-0000-000000000001", "--max-lines", "2"])
    assert res.exit_code == 0
    assert res.stdout.strip() == "b\nc"


def test_cancel_batch_by_name(v1):
    v1.answers["jobs.list"] = {"items": [{"id": "batch_00000000-0000-0000-0000-000000000002", "kind": "batch"}], "nextCursor": None}
    v1.answers["jobs.cancel"] = {"id": "batch_00000000-0000-0000-0000-000000000002", "status": "Stopped"}
    res = runner.invoke(app, ["--json", "cancel", "--batch", "b2"])
    assert _json(res)["status"] == "Stopped"
    assert v1.calls[-1] == ("jobs.cancel", ("batch_00000000-0000-0000-0000-000000000002",), {"body": {}})


def test_delete_confirms_then_deletes_by_id(v1):
    v1.answers["jobs.delete"] = None
    res = runner.invoke(app, ["--json", "delete", "job_00000000-0000-0000-0000-000000000001"])
    assert res.exit_code == 2  # still needs --yes in non-interactive mode
    res = runner.invoke(app, ["--json", "delete", "job_00000000-0000-0000-0000-000000000001", "--yes"])
    assert _json(res) == {"id": "job_00000000-0000-0000-0000-000000000001", "deleted": True}


def test_tools_lists_the_whole_catalog(v1):
    pages = iter(
        [
            {"items": [{"name": "boltz"}], "nextCursor": "c"},
            {"items": [{"name": "esmfold"}], "nextCursor": None},
        ]
    )
    v1.answers["tools.list"] = lambda **kw: next(pages)
    res = runner.invoke(app, ["--json", "tools", "--modality", "protein"])
    assert [t["name"] for t in _json(res)["items"]] == ["boltz", "esmfold"]
    assert v1.calls[0][2] == {"modality": "protein", "cursor": None}


def test_modalities_and_schema_example(v1):
    v1.answers["tools.facets"] = {"modalities": [{"value": "protein", "count": 3}], "functions": []}
    assert _json(runner.invoke(app, ["--json", "modalities"]))["modalities"][0]["value"] == "protein"
    v1.answers["tools.schema"] = {"tool": "esmfold", "version": "1", "schema": {}, "example": {"sequence": "MKT"}}
    res = runner.invoke(app, ["--json", "schema", "esmfold", "--example"])
    assert _json(res) == {"tool": "esmfold", "settings": {"sequence": "MKT"}}
    assert _json(runner.invoke(app, ["--json", "tools", "schema", "esmfold"]))["tool"] == "esmfold"


def test_files_commands(v1, tmp_path):
    v1.answers["files.list"] = {"items": [{"path": "a.pdb", "type": "file"}, {"path": "dir", "type": "folder"}], "nextCursor": None}
    res = runner.invoke(app, ["--json", "files", "list", "--types", "pdb,cif", "--all", "--folder", "x"])
    assert _json(res)["items"][0]["path"] == "a.pdb"
    assert v1.calls[-1][2] == {"limit": 50, "extension": ["pdb", "cif"], "folder": "x", "recursive": True}
    res = runner.invoke(app, ["--json", "files", "list", "--offset", "10"])
    assert isinstance(res.exception, UsageError)
    assert _json(runner.invoke(app, ["--json", "files", "folders"]))["items"] == [{"path": "dir", "type": "folder"}]
    v1.answers["files.stats"] = {"fileCount": 2, "totalBytes": 5, "byExtension": {"pdb": 2}}
    assert _json(runner.invoke(app, ["--json", "files", "stats", "--folder", "x"]))["fileCount"] == 2
    assert v1.calls[-1] == ("files.stats", (), {"folder": "x"})
    local = tmp_path / "t.pdb"
    local.write_text("ATOM")
    v1.answers["files.upload"] = {"path": "t.pdb", "type": "file", "sizeBytes": 4, "modifiedAt": None}
    assert _json(runner.invoke(app, ["--json", "files", "upload", str(local)]))["path"] == "t.pdb"
    assert v1.calls[-1][0] == "files.upload" and v1.calls[-1][2] == {"path": "t.pdb"}
    v1.answers["files.delete"] = None
    assert _json(runner.invoke(app, ["--json", "files", "delete", "t.pdb", "-y"])) == {"deleted": "t.pdb"}
    assert v1.calls[-1] == ("files.delete", (), {"path": "t.pdb"})


def test_files_download_saves_without_printing_the_link(v1, tmp_path, monkeypatch):
    from tamarind.cli.commands import jobs as jobs_cmds

    v1.answers["files.get"] = {"url": "https://s3.example/a.pdb?X-Amz-Signature=s", "expiresAt": "t", "sizeBytes": 4}
    monkeypatch.setattr(jobs_cmds, "_download", lambda url, dest: 4)
    res = runner.invoke(app, ["--json", "files", "download", "dir/a.pdb", "-o", str(tmp_path)])
    out = _json(res)
    assert out == {"path": str(tmp_path / "a.pdb"), "bytes": 4}
    assert v1.calls[-1] == ("files.get", (), {"path": "dir/a.pdb", "delivery": "url"})


def test_auth_status_reports_me(v1):
    v1.answers["me.get"] = {"user": {"email": "u@example.com"}, "tier": "Premium", "organization": None}
    out = _json(runner.invoke(app, ["--json", "auth", "status"]))
    assert out["verified"] is True and out["api"] == "v1"
    assert out["me"]["tier"] == "Premium"


def test_v1_request_flags_on_todays_commands(v1):
    v1.answers["jobs.submit"] = {"kind": "job", "id": "job_00000000-0000-0000-0000-000000000001", "name": "n", "status": "In Queue"}
    runner.invoke(
        app,
        ["--json", "submit", "esmfold", "--set", "sequence=M", "--project", "prj_1", "--model", "mdl_1",
         "--tool-version", "v2", "--max-runtime", "600"],
    )
    body = v1.calls[-1][2]["body"]
    assert body["projectId"] == "prj_1" and body["modelId"] == "mdl_1"
    assert body["toolVersion"] == "v2" and body["maxRuntimeSeconds"] == 600
    v1.answers["jobs.list"] = {"items": [], "nextCursor": None}
    runner.invoke(app, ["--json", "jobs", "list", "--kind", "batch", "--tool", "boltz", "--order", "asc",
                        "--pipeline-run", "run_1", "--search", "x", "--source", "cli"])
    assert v1.calls[-1][2] == {"limit": 50, "kind": "batch", "tool": "boltz", "search": "x", "source": "cli",
                               "order": "asc", "pipeline_run_id": "run_1"}
    v1.answers["jobs.logs"] = {"content": "", "nextCursor": None, "complete": True}
    runner.invoke(app, ["--json", "logs", "job_00000000-0000-0000-0000-000000000001", "--max-bytes", "100", "--cursor", "c"])
    assert v1.calls[-1] == ("jobs.logs", ("job_00000000-0000-0000-0000-000000000001",), {"max_bytes": 100, "cursor": "c"})
    v1.answers["jobs.cancel"] = {"id": "job_00000000-0000-0000-0000-000000000001", "status": "Stopped"}
    runner.invoke(app, ["--json", "cancel", "job_00000000-0000-0000-0000-000000000001", "--reason", "wrong input"])
    assert v1.calls[-1] == ("jobs.cancel", ("job_00000000-0000-0000-0000-000000000001",), {"body": {"reason": "wrong input"}})


def test_v1_request_flags_are_refused_in_classic(monkeypatch, tmp_path):
    monkeypatch.setenv("TAMARIND_CONFIG_DIR", str(tmp_path))
    monkeypatch.delenv("TAMARIND_API", raising=False)
    monkeypatch.setenv("TAMARIND_API_KEY", "k")
    for args in (
        ["submit", "esmfold", "--set", "sequence=M", "--project", "prj_1"],
        ["jobs", "--kind", "batch"],
        ["logs", "j", "--cursor", "c"],
        ["cancel", "j", "--reason", "r"],
    ):
        res = runner.invoke(app, ["--json", *args])
        assert res.exit_code == 2, (args, res.output)


def test_a_name_that_starts_with_job_is_still_a_name(v1):
    v1.answers["jobs.list"] = {"items": [{"id": "job_0f8fad5b-d9cb-469f-a165-70867728950e"}], "nextCursor": None}
    v1.answers["jobs.get"] = {"id": "job_0f8fad5b-d9cb-469f-a165-70867728950e", "status": "Running"}
    runner.invoke(app, ["--json", "status", "job_test"])
    assert v1.calls[0] == ("jobs.list", (), {"name": "job_test"})
    v1.calls.clear()
    runner.invoke(app, ["--json", "status", "job_0f8fad5bd9cb469fa16570867728950e"])
    assert v1.calls == [("jobs.get", ("job_0f8fad5bd9cb469fa16570867728950e",), {})]


def test_only_comma_joined_arrays_are_split(v1):
    v1.answers["molecules.list"] = {"items": [], "nextCursor": None}
    runner.invoke(app, ["--json", "molecules", "list", "--filter", "label:eq:a,b", "--filter", "x:eq:1"])
    assert v1.calls[-1][2]["filter_"] == ["label:eq:a,b", "x:eq:1"]
    v1.answers["files.list"] = {"items": [], "nextCursor": None}
    v1.answers["usage.get"] = {"items": [], "nextCursor": None}
    runner.invoke(app, ["--json", "usage", "--group-by", "tool,month"])
    assert v1.calls[-1][2]["group_by"] == ["tool", "month"]


def test_files_folders_reads_past_a_page_of_root_files(v1):
    pages = iter(
        [
            {"items": [{"path": f"f{i}.pdb", "type": "file"} for i in range(3)], "nextCursor": "c1"},
            {"items": [{"path": "a", "type": "folder"}, {"path": "b", "type": "folder"}], "nextCursor": "c2"},
            {"items": [{"path": "c", "type": "folder"}], "nextCursor": None},
        ]
    )
    v1.answers["files.list"] = lambda **kw: next(pages)
    out = _json(runner.invoke(app, ["--json", "files", "folders", "--limit", "2"]))
    assert [f["path"] for f in out["items"]] == ["a", "b"]
    assert len(v1.calls) == 2  # stops once it has enough


def test_results_wait_checks_its_timing_options_first(v1, tmp_path):
    res = runner.invoke(app, ["--json", "results", "job_0f8fad5bd9cb469fa16570867728950e", "--download", str(tmp_path), "--wait", "--poll-interval", "-1"])
    assert res.exit_code != 0
    assert v1.calls == []


def test_help_honors_an_explicit_profile(monkeypatch, tmp_path):
    import sys

    monkeypatch.setenv("TAMARIND_CONFIG_DIR", str(tmp_path))
    monkeypatch.delenv("TAMARIND_API", raising=False)
    monkeypatch.delenv("TAMARIND_PROFILE", raising=False)
    (tmp_path / "config.json").write_text(
        json.dumps({"current_profile": "default", "profiles": {"default": {}, "next": {"api": "v1"}}})
    )
    monkeypatch.setattr(sys, "argv", ["tamarind", "--profile", "next", "--help"])
    assert "projects" in runner.invoke(app, ["--profile", "next", "--help"]).stdout
    monkeypatch.setattr(sys, "argv", ["tamarind", "--help"])
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


def test_a_pipeline_runs_archive_comes_from_archive_pipeline_run(v1, tmp_path, monkeypatch):
    from tamarind.cli.commands import jobs as jobs_cmds

    run = "run_0f8fad5b-d9cb-469f-a165-70867728950e"
    v1.answers["pipelines.archive_run"] = {"status": "ready", "downloadUrl": "https://s3.example/r.zip", "expiresAt": "t", "sizeBytes": 1, "fileCount": None, "truncated": None}
    monkeypatch.setattr(jobs_cmds, "_download", lambda url, dest: 1)
    out = _json(runner.invoke(app, ["--json", "results", run, "--download", str(tmp_path)]))
    assert out["download"]["bytes"] == 1
    assert v1.calls[-1] == ("pipelines.archive_run", (run,), {"body": {}})


def test_an_empty_example_is_a_runnable_example(v1):
    v1.answers["tools.schema"] = {"tool": "noargs", "version": "1", "schema": {}, "example": {}}
    assert _json(runner.invoke(app, ["--json", "schema", "noargs", "--example"])) == {"tool": "noargs", "settings": {}}


def test_cancel_batch_takes_a_pipeline_run_name_too(v1):
    run = "run_0f8fad5b-d9cb-469f-a165-70867728950e"
    v1.answers["jobs.list"] = {"items": [{"id": run, "kind": "pipeline"}], "nextCursor": None}
    v1.answers["jobs.cancel"] = {"id": run, "status": "Stopped"}
    _json(runner.invoke(app, ["--json", "cancel", "--batch", "my-run"]))
    assert v1.calls[0] == ("jobs.list", (), {"name": "my-run"})
    assert v1.calls[-1][1] == (run,)
    v1.answers["jobs.list"] = {"items": [{"id": "job_0f8fad5b-d9cb-469f-a165-70867728950e", "kind": "job"}], "nextCursor": None}
    res = runner.invoke(app, ["--json", "cancel", "--batch", "a-single-job"])
    assert isinstance(res.exception, NotFoundError)


def test_an_unclear_submit_outcome_says_how_to_retry_safely(v1):
    from tamarind.errors import APIError

    v1.answers["jobs.submit"] = APIError("502 bad_gateway", status_code=502)
    res = runner.invoke(app, ["--json", "submit", "esmfold", "--set", "sequence=M"])
    key = v1.calls[-1][2]["idempotency_key"]
    assert res.exception.detail["idempotencyKey"] == key
    assert f"--idempotency-key {key}" in str(res.exception)
    v1.answers["jobs.submit"] = APIError("422 validation_failed", status_code=422)
    v1.answers["jobs.submit"].status = 422
    res = runner.invoke(app, ["--json", "submit", "esmfold", "--set", "sequence=M", "--idempotency-key", "mine"])
    assert "idempotency" not in str(res.exception)  # refused, so nothing to retry
    assert v1.calls[-1][2]["idempotency_key"] == "mine"


def test_values_outside_a_contract_enum_are_usage_errors(v1):
    res = runner.invoke(app, ["--json", "usage", "--metric", "bogus"])
    assert isinstance(res.exception, UsageError) and v1.calls == []
    res = runner.invoke(app, ["--json", "jobs", "--status", "Running,Bogus"])
    assert isinstance(res.exception, UsageError) and v1.calls == []


def test_login_refuses_a_blank_key_on_v1(v1):
    res = runner.invoke(app, ["--json", "auth", "login", "--api-key", "   "])
    assert res.exception is not None and res.exception.exit_code == 3
    assert v1.calls == []


def test_submit_wait_download_shares_one_timeout(v1, tmp_path, monkeypatch):
    from tamarind.cli.v1 import commands as v1cmds

    v1.answers["jobs.submit"] = {"kind": "job", "id": "job_0f8fad5b-d9cb-469f-a165-70867728950e", "name": "n", "status": "In Queue"}
    clock = [1000.0]
    monkeypatch.setattr(v1cmds.time, "monotonic", lambda: clock[0])

    def waited(*args, **kwargs):
        clock[0] += 60  # the job took 60 of the 100 seconds
        return {"id": "job_0f8fad5b-d9cb-469f-a165-70867728950e", "name": "n", "status": "Complete"}

    v1.answers["jobs.wait"] = waited
    seen = {}

    def fake_archive(client, job_id, *, body, wait, timeout):
        seen["timeout"] = timeout
        return {"downloadUrl": "https://s3.example/x.zip"}

    monkeypatch.setattr(v1cmds, "_archive", fake_archive)
    monkeypatch.setattr("tamarind.cli.commands.jobs._download", lambda url, dest: 1)
    runner.invoke(app, ["--json", "submit", "esmfold", "--set", "sequence=M", "--wait", "--timeout", "100", "--download", str(tmp_path)])
    assert seen["timeout"] == 40


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


def test_results_file_of_a_pipeline_run_is_refused(v1, tmp_path):
    res = runner.invoke(app, ["--json", "results", "run_0f8fad5b-d9cb-469f-a165-70867728950e", "--file", "x.pdb", "--download", str(tmp_path)])
    assert isinstance(res.exception, UsageError) and v1.calls == []


def test_files_folders_limit_must_be_positive(v1):
    res = runner.invoke(app, ["--json", "files", "folders", "--limit", "0"])
    assert isinstance(res.exception, UsageError) and v1.calls == []


def test_results_wait_download_output_is_redacted(v1, tmp_path, monkeypatch):
    signed = "https://bucket.s3.amazonaws.com/in.pdb?X-Amz-Signature=abc&X-Amz-Credential=k"
    job = "job_0f8fad5b-d9cb-469f-a165-70867728950e"
    v1.answers["jobs.wait"] = {"id": job, "status": "Complete", "settings": {"target": signed}}
    v1.answers["jobs.archive"] = {"status": "ready", "downloadUrl": "https://s3.example/x.zip?X-Amz-Signature=z"}
    monkeypatch.setattr("tamarind.cli.commands.jobs._download", lambda url, dest: 1)
    res = runner.invoke(app, ["--json", "results", job, "--wait", "--download", str(tmp_path)])
    assert signed not in res.stdout and "X-Amz-Signature" not in res.stdout
