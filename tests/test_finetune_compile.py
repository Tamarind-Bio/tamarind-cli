from __future__ import annotations

import json
from pathlib import Path

import pytest

from tamarind.finetune import (
    FinetuneCompileError,
    compile_folder,
    compile_sources,
    sync_config_json,
)
from tamarind.finetune.compile import SourceText, apply_to_config

TRAIN = """
import os
import tamarind as tm

@tm.training_run(
    gpu="H100",
    memory="32Gi",
    timeout_hours=12,
    hyperparameters={
        "lr": tm.Float(1e-4, 1e-6, 1e-2, description="Learning rate"),
        "epochs": tm.Int(10),
        "rank": tm.Choice(8, [4, 8, 16, 32]),
        "loss": tm.Choice("mse", ["mse", "ranking"]),
        "freeze": tm.Bool(True),
        "note": tm.Str("baseline"),
        "dropout": {"type": "float", "default": 0.1},
    },
    objective=("val/spearman", "max"),
    artifact="checkpoints/best",
)
def main():
    cfg = tm.hyperparameters()
    tm.log({"train/loss": 0.1}, step=1)


@tm.evaluator(metrics={"spearman": "max", "mae": "min"})
def score(predictions, truths):
    return {"spearman": 0.5, "mae": 0.1}


@tm.splitter
def split(dataset):
    return [], []
"""

MODEL = """
from tamarind import predictor

@predictor(gpu="L4", inputs={"sequence": "sequence"}, outputs={"affinity": "number"})
class BindingModel:
    def load(self, artifact_dir): ...
    def predict(self, inputs): ...
"""


def _write(folder: Path, files: dict[str, str]) -> Path:
    for name, text in files.items():
        path = folder / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    return folder


def test_compiles_every_decorator_into_the_block(tmp_path: Path) -> None:
    _write(tmp_path, {"train.py": TRAIN, "models/model.py": MODEL})
    compiled = compile_folder(tmp_path)
    assert compiled is not None
    assert compiled.resources == {"gpuType": "H100", "memory": "32Gi"}
    assert compiled.sources == ("models/model.py", "train.py")
    assert compiled.block == {
        "entrypoint": "train.py:main",
        "timeoutHours": 12,
        "hyperparameters": {
            "lr": {
                "type": "float",
                "default": 1e-4,
                "min": 1e-6,
                "max": 1e-2,
                "description": "Learning rate",
            },
            "epochs": {"type": "int", "default": 10},
            "rank": {"type": "int", "default": 8, "options": [4, 8, 16, 32]},
            "loss": {"type": "string", "default": "mse", "options": ["mse", "ranking"]},
            "freeze": {"type": "boolean", "default": True},
            "note": {"type": "string", "default": "baseline"},
            "dropout": {"type": "float", "default": 0.1},
        },
        "objective": {"metric": "val/spearman", "mode": "max"},
        "artifact": "checkpoints/best",
        "predictor": {
            "class": "models/model.py:BindingModel",
            "gpuType": "L4",
            "inputs": [{"name": "sequence", "type": "sequence", "required": True}],
            "producedOutputs": [
                {
                    "type": "csv",
                    "name": "predictions",
                    "path": "predictions.csv",
                    "primary": True,
                    "columns": [{"name": "affinity", "type": "number"}],
                }
            ],
        },
        "evaluator": "train.py:score",
        "splitter": "train.py:split",
    }


def test_no_decorators_means_none(tmp_path: Path) -> None:
    _write(tmp_path, {"main.py": "print('hi')\n"})
    assert compile_folder(tmp_path) is None


def test_a_decorator_named_the_same_in_another_library_is_ignored() -> None:
    source = "from ray import training_run\n@training_run(gpu='x')\ndef main(): ...\n"
    assert compile_sources([SourceText("main.py", source)]) is None


def test_skips_environments_and_caches(tmp_path: Path) -> None:
    _write(
        tmp_path,
        {
            "train.py": TRAIN,
            ".venv/lib/site.py": "import tamarind as tm\n@tm.training_run()\ndef other(): ...\n",
            "__pycache__/x.py": "import tamarind as tm\n@tm.training_run()\ndef other(): ...\n",
        },
    )
    compiled = compile_folder(tmp_path)
    assert compiled is not None
    assert compiled.block["entrypoint"] == "train.py:main"


@pytest.mark.parametrize(
    ("source", "message"),
    [
        (
            'import tamarind as tm\n@tm.training_run(gpu=os.environ["GPU"])\ndef main(): ...\n',
            "main.py:2: decorator arguments must be literals",
        ),
        (
            "import tamarind as tm\n@tm.training_run(timeout_hours=2 * 3)\ndef main(): ...\n",
            "must be literals",
        ),
        (
            'import tamarind as tm\n@tm.training_run("H100")\ndef main(): ...\n',
            "keyword arguments only",
        ),
        (
            'import tamarind as tm\n@tm.training_run(gpus="H100")\ndef main(): ...\n',
            "unknown arguments ['gpus']",
        ),
        (
            'import tamarind as tm\n@tm.training_run(hyperparameters={"lr": 0.1})\ndef main(): ...\n',
            "use tm.Float",
        ),
        (
            'import tamarind as tm\n@tm.training_run(hyperparameters={"r": tm.Choice(1, [])})\ndef main(): ...\n',
            "at least one option",
        ),
        (
            'import tamarind as tm\n@tm.training_run(objective=("loss", "best"))\ndef main(): ...\n',
            'must be "max" or "min"',
        ),
        (
            "import tamarind as tm\n@tm.training_run()\ndef a(): ...\n@tm.training_run()\ndef b(): ...\n",
            "more than one @tm.training_run",
        ),
        (
            "import tamarind as tm\n@tm.evaluator\ndef score(p, t): ...\n",
            "needs a @tm.training_run",
        ),
        (
            "import tamarind as tm\n@tm.training_run()\ndef main(): ...\n@tm.predictor()\ndef not_a_class(): ...\n",
            "goes on a class",
        ),
        ("import tamarind as tm\n@tm.training_run()\nclass Main: ...\n", "goes on a function"),
        (
            "import tamarind as tm\n@tm.training_run()\ndef main(): ...\n@tm.splitter(seed=1)\ndef s(d): ...\n",
            "takes no arguments",
        ),
        ("import tamarind as tm\n@tm.training_run(\ndef main(): ...\n", "syntax error"),
    ],
)
def test_refusals_name_the_file_and_line(source: str, message: str) -> None:
    with pytest.raises(FinetuneCompileError, match=__import__("re").escape(message)):
        compile_sources([SourceText("main.py", source)])


def test_sync_writes_the_block_and_resources_and_keeps_the_rest(tmp_path: Path) -> None:
    config = {
        "displayName": "trainer",
        "gpuType": "L4",
        "maxRuntimeSeconds": 3600,
        "inputs": [],
        "tags": ["x"],
    }
    _write(tmp_path, {"train.py": TRAIN, "config.json": json.dumps(config)})

    checked = sync_config_json(tmp_path, write=False)
    assert checked.changed is True
    assert json.loads((tmp_path / "config.json").read_text()) == config  # --check never writes

    result = sync_config_json(tmp_path, write=True)
    assert result.changed is True
    written = json.loads((tmp_path / "config.json").read_text())
    assert written["finetune"]["entrypoint"] == "train.py:main"
    assert written["gpuType"] == "H100"
    assert written["memory"] == "32Gi"
    assert written["tags"] == ["x"]
    assert "maxRuntimeSeconds" not in written  # timeoutHours is the block's spelling of it

    again = sync_config_json(tmp_path, write=True)
    assert again.changed is False


def test_sync_without_decorators_leaves_config_alone(tmp_path: Path) -> None:
    _write(tmp_path, {"main.py": "print(1)\n", "config.json": '{"displayName": "x"}\n'})
    result = sync_config_json(tmp_path, write=True)
    assert result.compiled is None
    assert result.changed is False
    assert (tmp_path / "config.json").read_text() == '{"displayName": "x"}\n'


def test_sync_needs_a_config_json_when_decorators_exist(tmp_path: Path) -> None:
    _write(tmp_path, {"train.py": TRAIN})
    with pytest.raises(FinetuneCompileError, match="config.json is required"):
        sync_config_json(tmp_path, write=True)


def test_apply_keeps_max_runtime_when_the_block_sets_no_timeout() -> None:
    compiled = compile_sources(
        [SourceText("t.py", "import tamarind as tm\n@tm.training_run()\ndef main(): ...\n")]
    )
    updated = apply_to_config({"maxRuntimeSeconds": 60}, compiled)
    assert updated["maxRuntimeSeconds"] == 60
    assert updated["finetune"] == {"entrypoint": "t.py:main", "hyperparameters": {}}
