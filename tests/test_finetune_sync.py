"""`sync-finetune`: the server compiles the decorators; the SDK writes back what it says."""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest
import respx

from tamarind import Tamarind
from tamarind.finetune import FinetuneCompileError, sync_config_json

BASE = "https://api.test/"
URL = f"{BASE}custom-tools/validate-config"
TRAIN = "import tamarind as tm\n@tm.training_run(gpu='L4', hyperparameters={'epochs': tm.Int(3)})\ndef main(): ...\n"
BLOCK = {
    "entrypoint": "train.py:main",
    "hyperparameters": {"epochs": {"type": "int", "default": 3}},
}
CORRECTED = (
    json.dumps({"displayName": "t", "inputs": [], "finetune": BLOCK, "gpuType": "L4"}, indent=2)
    + "\n"
)


def _folder(tmp_path: Path, *, config: dict | None, train: str = TRAIN) -> Path:
    (tmp_path / "train.py").write_text(train)
    if config is not None:
        (tmp_path / "config.json").write_text(json.dumps(config))
    return tmp_path


def _client() -> Tamarind:
    return Tamarind(api_key="key", api_base=BASE)


def _derived(
    config: str | None,
    *,
    valid: bool = True,
    errors: list | None = None,
    warnings: list | None = None,
):
    return httpx.Response(
        200,
        json={
            "valid": valid,
            "errors": errors or [],
            "warnings": warnings or [],
            "finetune": {
                "block": BLOCK,
                "resources": {"gpuType": "L4"},
                "sources": ["train.py"],
                "config": config,
            },
        },
    )


@respx.mock
def test_derives_and_writes_what_the_server_returns(tmp_path: Path) -> None:
    folder = _folder(tmp_path, config={"displayName": "t", "inputs": []})
    route = respx.post(URL).mock(
        return_value=_derived(
            CORRECTED, warnings=[{"code": "finetune_no_predictor", "message": "m"}]
        )
    )

    result = _client().custom_tools.sync_finetune(folder, write=True)

    sent = json.loads(route.calls[0].request.content)
    assert sent["sources"] == [{"path": "train.py", "content": TRAIN}]
    assert json.loads(sent["config"]) == {"displayName": "t", "inputs": []}
    assert result.changed is True
    assert result.compiled is not None
    assert result.compiled.block == BLOCK
    assert result.compiled.resources == {"gpuType": "L4"}
    assert result.warnings == (("finetune_no_predictor", "m"),)
    assert (folder / "config.json").read_text() == CORRECTED


@respx.mock
def test_check_reports_without_writing(tmp_path: Path) -> None:
    folder = _folder(tmp_path, config={"displayName": "t", "inputs": []})
    respx.post(URL).mock(return_value=_derived(CORRECTED))
    result = _client().custom_tools.sync_finetune(folder, write=False)
    assert result.changed is True
    assert json.loads((folder / "config.json").read_text()) == {"displayName": "t", "inputs": []}


@respx.mock
def test_a_matching_block_is_up_to_date(tmp_path: Path) -> None:
    folder = _folder(
        tmp_path, config={"displayName": "t", "inputs": [], "finetune": BLOCK, "gpuType": "L4"}
    )
    respx.post(URL).mock(return_value=_derived(None))
    result = _client().custom_tools.sync_finetune(folder, write=True)
    assert result.changed is False
    assert result.compiled is not None


@respx.mock
def test_a_stale_block_is_rewritten_from_the_servers_correction(tmp_path: Path) -> None:
    folder = _folder(
        tmp_path,
        config={"displayName": "t", "inputs": [], "finetune": {**BLOCK, "artifact": "old"}},
    )
    respx.post(URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "valid": False,
                "errors": [
                    {
                        "code": "invalid_custom_tool_config",
                        "message": "does not match the @tm decorators in train.py",
                    }
                ],
                "warnings": [],
                "finetune": {
                    "block": None,
                    "resources": {},
                    "sources": ["train.py"],
                    "config": CORRECTED,
                },
            },
        )
    )
    result = _client().custom_tools.sync_finetune(folder, write=True)
    assert result.changed is True
    assert (folder / "config.json").read_text() == CORRECTED


@respx.mock
def test_a_refusal_without_a_correction_is_reported_not_rewritten(tmp_path: Path) -> None:
    original = {"displayName": "t", "inputs": []}
    folder = _folder(
        tmp_path,
        config=original,
        train="import tamarind as tm\n@tm.training_run\ndef main(): ...\n",
    )
    respx.post(URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "valid": False,
                "errors": [
                    {
                        "code": "invalid_custom_tool_config",
                        "message": "the @tm decorators cannot be compiled: train.py:3: needs parentheses",
                    }
                ],
                "warnings": [],
                "finetune": None,
            },
        )
    )
    with pytest.raises(FinetuneCompileError, match="train.py:3: needs parentheses"):
        _client().custom_tools.sync_finetune(folder, write=True)
    assert json.loads((folder / "config.json").read_text()) == original


@respx.mock
def test_no_decorators_means_no_change(tmp_path: Path) -> None:
    folder = _folder(tmp_path, config={"displayName": "t"}, train="print(1)\n")
    respx.post(URL).mock(
        return_value=httpx.Response(
            200, json={"valid": True, "errors": [], "warnings": [], "finetune": None}
        )
    )
    result = _client().custom_tools.sync_finetune(folder, write=True)
    assert result.compiled is None
    assert result.changed is False


def test_no_python_files_never_calls_the_server(tmp_path: Path) -> None:
    (tmp_path / "config.json").write_text('{"displayName": "t"}')

    class Never:
        def validate_config(self, **_: object) -> dict:
            raise AssertionError("not called")

    result = sync_config_json(tmp_path, write=True, validator=Never())
    assert result.compiled is None


def test_sync_needs_a_config_json_when_decorators_exist(tmp_path: Path) -> None:
    folder = _folder(tmp_path, config=None)
    with pytest.raises(FinetuneCompileError, match="config.json is required"):
        _client().custom_tools.sync_finetune(folder, write=True)


def test_sync_refuses_a_symlinked_config_json_and_folder(tmp_path: Path) -> None:
    outside = tmp_path / "outside.json"
    outside.write_text('{"displayName": "victim"}')
    folder = tmp_path / "tool"
    folder.mkdir()
    (folder / "train.py").write_text(TRAIN)
    (folder / "config.json").symlink_to(outside)
    with pytest.raises(FinetuneCompileError, match="symlink"):
        _client().custom_tools.sync_finetune(folder, write=True)
    assert outside.read_text() == '{"displayName": "victim"}'
    linked = tmp_path / "linked"
    linked.symlink_to(folder)
    with pytest.raises(FinetuneCompileError, match="real directory"):
        _client().custom_tools.sync_finetune(linked, write=True)


def test_sources_skip_environments_and_caches_and_honour_declared_encodings(tmp_path: Path) -> None:
    from tamarind.finetune.compile import iter_python_sources

    (tmp_path / "train.py").write_text(TRAIN)
    (tmp_path / ".venv" / "lib").mkdir(parents=True)
    (tmp_path / ".venv" / "lib" / "x.py").write_text("x")
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__" / "y.py").write_text("y")
    (tmp_path / "legacy.py").write_bytes(
        "# -*- coding: latin-1 -*-\nNAME = 'caf\xe9'\n".encode("latin-1")
    )
    (tmp_path / "binary.py").write_bytes(b"\xff\xfe not text")
    (tmp_path / "crlf.py").write_bytes(b"import tamarind\r\nx = 1\r\n")
    sources = {s.relative: s.text for s in iter_python_sources(tmp_path)}
    assert sorted(sources) == ["binary.py", "crlf.py", "legacy.py", "train.py"]
    assert (
        sources["crlf.py"] == "import tamarind\nx = 1\n"
    )  # a Windows checkout sends the same text
    assert "caf\xe9" in sources["legacy.py"]  # decoded as Python would, not as UTF-8
    assert "\ufffd" in sources["binary.py"]  # undecodable bytes replaced, never an exception


def test_sources_refuse_links_before_anything_is_sent(tmp_path: Path) -> None:
    from tamarind.finetune.compile import iter_python_sources

    (tmp_path / "train.py").write_text(TRAIN)
    (tmp_path / "link.py").symlink_to(tmp_path / "train.py")
    with pytest.raises(FinetuneCompileError, match="symlinks or junctions"):
        iter_python_sources(tmp_path)
