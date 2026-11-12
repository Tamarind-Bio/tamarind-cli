"""The decorators meet the custom-tools surfaces: a decorated folder validates and builds as it is."""

from __future__ import annotations

import json
from pathlib import Path

from tamarind.custom_tools.validation import validate_folder

TRAIN = """
import tamarind as tm

@tm.training_run(gpu="L4", hyperparameters={"epochs": tm.Int(3)})
def main():
    print(tm.hyperparameters())
"""


def _tool_folder(tmp_path: Path, *, config: dict, train: str = TRAIN) -> Path:
    (tmp_path / "Dockerfile").write_text("FROM python:3.12-slim\n")
    (tmp_path / "run.sh").write_text("python train.py\n")
    (tmp_path / "train.py").write_text(train)
    (tmp_path / "config.json").write_text(json.dumps(config))
    return tmp_path


def test_a_decorated_folder_needs_no_finetune_block_to_validate(tmp_path: Path) -> None:
    report = validate_folder(_tool_folder(tmp_path, config={"displayName": "t", "inputs": []}))
    assert report.valid
    assert report.warnings == ()


def test_build_ships_the_folder_exactly_as_it_is(tmp_path: Path) -> None:
    """The platform derives the block at build; the SDK never writes it into the folder."""
    from tamarind.custom_tools import resources

    config = {"displayName": "t", "inputs": []}
    folder = _tool_folder(tmp_path, config=config)
    seen: dict[str, object] = {}

    class FakeCollection:
        def _build(self, tool, tree, *, idempotency_key, source_timeout):
            files = {f.relative: f for f in tree.files}
            seen["config"] = json.loads(files["config.json"].read_text())
            seen["train"] = files["train.py"].read_text()
            return "built"

    tool = resources.CustomTool.__new__(resources.CustomTool)
    object.__setattr__(tool, "_collection", FakeCollection())
    assert tool.build(folder) == "built"
    assert seen["config"] == config
    assert seen["train"] == (folder / "train.py").read_bytes().decode()  # byte-for-byte, any OS
    assert json.loads((folder / "config.json").read_text()) == config
