"""The decorators meet the custom-tools surfaces: validate, build, and the sync-finetune command."""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import respx
from typer.testing import CliRunner

from tamarind.cli.main import app
from tamarind.custom_tools.validation import validate_folder

runner = CliRunner()
ENV = {"TAMARIND_API_KEY": "key", "TAMARIND_API_BASE": "https://api.test/"}
URL = "https://api.test/custom-tools/validate-config"


def _derived(
    corrected: str | None, *, errors: list | None = None, block: dict | None = None
) -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "valid": not errors,
            "errors": errors or [],
            "warnings": [],
            "finetune": {
                "block": block,
                "resources": {"gpuType": "L4"} if block else {},
                "sources": ["train.py"],
                "config": corrected,
            },
        },
    )


TRAIN = """
import tamarind as tm

@tm.training_run(gpu="L4", hyperparameters={"epochs": tm.Int(3)})
def main():
    print(tm.hyperparameters())
"""

BLOCK = {
    "entrypoint": "train.py:main",
    "hyperparameters": {"epochs": {"type": "int", "default": 3}},
}


def _tool_folder(tmp_path: Path, *, config: dict, train: str = TRAIN) -> Path:
    (tmp_path / "Dockerfile").write_text("FROM python:3.12-slim\n")
    (tmp_path / "run.sh").write_text("python train.py\n")
    (tmp_path / "train.py").write_text(train)
    (tmp_path / "config.json").write_text(json.dumps(config))
    return tmp_path


def test_validate_says_the_server_compiles_the_decorators(tmp_path: Path) -> None:
    folder = _tool_folder(tmp_path, config={"displayName": "t", "inputs": []})
    report = validate_folder(folder)
    assert report.valid
    assert [w.code for w in report.warnings] == ["finetune_not_checked_offline"]
    assert "sync-finetune" in report.warnings[0].message


def test_validate_is_quiet_when_the_block_matches(tmp_path: Path) -> None:
    folder = _tool_folder(
        tmp_path, config={"displayName": "t", "gpuType": "L4", "inputs": [], "finetune": BLOCK}
    )
    report = validate_folder(folder)
    assert report.valid
    assert report.warnings == ()


def test_validate_offline_does_not_judge_the_decorators(tmp_path: Path) -> None:
    """A non-literal argument is the server's call; offline validation only says decorators are present."""
    folder = _tool_folder(
        tmp_path,
        config={"displayName": "t", "inputs": []},
        train='import os\nimport tamarind as tm\n@tm.training_run(gpu=os.environ["G"])\ndef main(): ...\n',
    )
    report = validate_folder(folder)
    assert report.valid
    assert [w.code for w in report.warnings] == ["finetune_not_checked_offline"]


@respx.mock
def test_sync_finetune_command_writes_and_check_only_reports(tmp_path: Path) -> None:
    folder = _tool_folder(tmp_path, config={"displayName": "t", "inputs": []})
    corrected = (
        json.dumps({"displayName": "t", "inputs": [], "finetune": BLOCK, "gpuType": "L4"}, indent=2)
        + "\n"
    )
    route = respx.post(URL).mock(return_value=_derived(corrected, block=BLOCK))

    checked = runner.invoke(
        app, ["--json", "custom-tools", "sync-finetune", str(folder), "--check"], env=ENV
    )
    assert checked.exit_code == 5, checked.stdout
    assert json.loads(checked.stdout)["changed"] is True
    assert "finetune" not in json.loads((folder / "config.json").read_text())

    written = runner.invoke(app, ["--json", "custom-tools", "sync-finetune", str(folder)], env=ENV)
    assert written.exit_code == 0, written.stdout
    payload = json.loads(written.stdout)
    assert payload["written"] is True
    assert payload["finetune"] == BLOCK
    assert payload["resources"] == {"gpuType": "L4"}
    config = json.loads((folder / "config.json").read_text())
    assert config["finetune"] == BLOCK
    assert config["gpuType"] == "L4"

    route.mock(return_value=_derived(None, block=BLOCK))
    again = runner.invoke(
        app, ["--json", "custom-tools", "sync-finetune", str(folder), "--check"], env=ENV
    )
    assert again.exit_code == 0, again.stdout


@respx.mock
def test_sync_finetune_command_without_decorators(tmp_path: Path) -> None:
    folder = _tool_folder(tmp_path, config={"displayName": "t", "inputs": []}, train="print(1)\n")
    respx.post(URL).mock(
        return_value=httpx.Response(
            200, json={"valid": True, "errors": [], "warnings": [], "finetune": None}
        )
    )
    result = runner.invoke(app, ["--json", "custom-tools", "sync-finetune", str(folder)], env=ENV)
    assert result.exit_code == 0, result.stdout
    assert json.loads(result.stdout) == {"finetune": None, "changed": False}


@respx.mock
def test_sync_finetune_command_reports_a_bad_decorator(tmp_path: Path) -> None:
    folder = _tool_folder(
        tmp_path,
        config={"displayName": "t", "inputs": []},
        train='import tamarind as tm\n@tm.training_run("A100")\ndef main(): ...\n',
    )
    respx.post(URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "valid": False,
                "errors": [
                    {
                        "code": "invalid_custom_tool_config",
                        "message": "the @tm decorators cannot be compiled: train.py:3: @tm.training_run takes keyword arguments only",
                    }
                ],
                "warnings": [],
                "finetune": None,
            },
        )
    )
    result = runner.invoke(app, ["custom-tools", "sync-finetune", str(folder)], env=ENV)
    assert result.exit_code == 5
    assert "keyword arguments only" in result.output


def test_build_syncs_the_block_before_packaging(monkeypatch, tmp_path: Path) -> None:
    from tamarind.custom_tools import resources

    folder = _tool_folder(tmp_path, config={"displayName": "t", "inputs": []})
    seen: dict[str, object] = {}

    class FakeCollection:
        def sync_finetune(self, folder, *, write=True):
            (Path(folder) / "config.json").write_text(
                json.dumps({"displayName": "t", "inputs": [], "finetune": BLOCK})
            )

        def _build(self, tool, tree, *, idempotency_key, source_timeout):
            files = {f.relative: f for f in tree.files}
            seen["config"] = json.loads(files["config.json"].read_text())
            return "built"

    tool = resources.CustomTool.__new__(resources.CustomTool)
    object.__setattr__(tool, "_collection", FakeCollection())
    assert tool.build(folder) == "built"
    assert seen["config"]["finetune"] == BLOCK  # the archive carries the synced block
    assert json.loads((folder / "config.json").read_text())["finetune"] == BLOCK


def test_build_with_sync_off_ships_the_folder_as_is(monkeypatch, tmp_path: Path) -> None:
    from tamarind.custom_tools import resources

    folder = _tool_folder(tmp_path, config={"displayName": "t", "inputs": []})
    seen: dict[str, object] = {}

    class FakeCollection:
        def sync_finetune(self, folder, *, write=True):
            raise AssertionError("not called with sync_finetune=False")

        def _build(self, tool, tree, *, idempotency_key, source_timeout):
            files = {f.relative: f for f in tree.files}
            seen["config"] = json.loads(files["config.json"].read_text())
            return "built"

    tool = resources.CustomTool.__new__(resources.CustomTool)
    object.__setattr__(tool, "_collection", FakeCollection())
    tool.build(folder, sync_finetune=False)
    assert "finetune" not in seen["config"]
