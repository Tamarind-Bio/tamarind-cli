"""Prediction mode: the platform's environment turns a training script into a predictor."""

from __future__ import annotations

import csv
import json
from pathlib import Path
import textwrap

import pytest

import tamarind as tm
from tamarind.finetune import decorators, predict, runtime

PREDICTOR_SOURCE = textwrap.dedent(
    """
    import json
    import tamarind as tm

    @tm.predictor(gpu="None", inputs={"sequence": "sequence"}, outputs={"score": "number"})
    class Scorer:
        def load(self, weights_dir):
            self.scale = json.loads((weights_dir / "weights.json").read_text())["scale"]

        def predict(self, inputs):
            return {"score": self.scale * len(inputs["sequence"]), "note": "ok"}
    """
)


@pytest.fixture(autouse=True)
def _clean(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    decorators.reset_registry()
    for name in (
        predict.ENV_MODE,
        predict.ENV_WEIGHTS_DIR,
        predict.ENV_PREDICTOR,
        predict.ENV_PREDICTIONS_FILE,
        predict.ENV_INPUTS_FILE,
        runtime.ENV_RUN_DIR,
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.chdir(tmp_path)
    yield
    decorators.reset_registry()


def _weights(tmp_path: Path, scale: float = 2.0) -> Path:
    weights = tmp_path / "weights"
    weights.mkdir()
    (weights / "weights.json").write_text(json.dumps({"scale": scale}))
    return weights


def _platform_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, *, predictor: str) -> Path:
    inputs = tmp_path / "inputs.json"
    inputs.write_text(json.dumps({"sequence": "ACDE"}))
    out = tmp_path / "out" / "predictions.csv"
    monkeypatch.setenv(predict.ENV_MODE, "predict")
    monkeypatch.setenv(predict.ENV_WEIGHTS_DIR, str(_weights(tmp_path)))
    monkeypatch.setenv(predict.ENV_PREDICTOR, predictor)
    monkeypatch.setenv(predict.ENV_INPUTS_FILE, str(inputs))
    monkeypatch.setenv(predict.ENV_PREDICTIONS_FILE, str(out))
    return out


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def test_training_run_serves_the_predictor_in_prediction_mode(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    (tmp_path / "model.py").write_text(PREDICTOR_SOURCE)
    out = _platform_env(monkeypatch, tmp_path, predictor="model.py:Scorer")
    trained: list[str] = []

    @tm.training_run(hyperparameters={"lr": tm.Float(1e-3)})
    def main():
        trained.append("ran")
        return "trained"

    assert tm.is_predicting()
    assert main() is None  # the training body is not entered
    assert trained == []
    rows = _rows(out)
    assert rows == [{"score": "8.0", "note": "ok"}]  # declared column first, extras after


def test_off_platform_the_training_body_runs(tmp_path: Path) -> None:
    @tm.training_run()
    def main():
        return "trained"

    assert not tm.is_predicting()
    assert main() == "trained"
    assert main.__name__ == "main"
    assert decorators.registered("training_run")["target"] is main


def test_explicit_entry_runs_without_a_training_script(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    (tmp_path / "model.py").write_text(PREDICTOR_SOURCE)
    out = _platform_env(monkeypatch, tmp_path, predictor="model.py:Scorer")
    assert predict.main(["predict"]) == 0
    assert _rows(out)[0]["score"] == "8.0"


def test_local_command_takes_weights_and_inputs(tmp_path: Path) -> None:
    (tmp_path / "model.py").write_text(PREDICTOR_SOURCE)
    weights = _weights(tmp_path, scale=1.0)
    out = tmp_path / "preds.csv"
    code = predict.main(
        [
            "predict",
            "--predictor",
            "model.py:Scorer",
            "--weights",
            str(weights),
            "--input",
            "sequence=ACDEFG",
            "--out",
            str(out),
        ]
    )
    assert code == 0
    assert _rows(out) == [{"score": "6.0", "note": "ok"}]


def test_an_unset_weights_directory_is_refused_not_read_as_the_working_directory(
    tmp_path: Path,
) -> None:
    (tmp_path / "model.py").write_text(PREDICTOR_SOURCE)
    (tmp_path / "weights.json").write_text(json.dumps({"scale": 1.0}))  # a loadable cwd
    with pytest.raises(predict.PredictError, match="no weights directory"):
        predict.run("model.py:Scorer", inputs={"sequence": "AC"}, out=tmp_path / "p.csv")


def test_local_command_reports_a_missing_weights_directory(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "model.py").write_text(PREDICTOR_SOURCE)
    code = predict.main(
        ["predict", "--predictor", "model.py:Scorer", "--weights", str(tmp_path / "nope")]
    )
    assert code == 1
    assert "weights directory" in capsys.readouterr().err


def test_an_already_imported_predictor_is_not_imported_twice(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    loads: list[int] = []

    @tm.predictor(outputs={"score": "number"})
    class Scorer:
        def load(self, weights_dir):
            loads.append(1)

        def predict(self, inputs):
            return {"score": 1}

    (tmp_path / "model.py").write_text("raise AssertionError('must not be imported')\n")
    out = _platform_env(monkeypatch, tmp_path, predictor="model.py:Scorer")
    predict.run_from_environment()
    assert loads == [1]
    assert _rows(out) == [{"score": "1"}]


def test_a_same_named_class_from_another_file_is_not_reused(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    (tmp_path / "model.py").write_text(PREDICTOR_SOURCE)
    other = PREDICTOR_SOURCE.replace('self.scale * len(inputs["sequence"])', "-1.0")
    (tmp_path / "other.py").write_text(other)
    out = _platform_env(monkeypatch, tmp_path, predictor="other.py:Scorer")
    predict.run("model.py:Scorer", out=tmp_path / "first.csv")  # registers model.py's Scorer
    predict.run_from_environment()  # other.py:Scorer must be imported, not the registered one
    assert _rows(out) == [{"score": "-1.0", "note": "ok"}]


def test_a_bare_string_is_one_row_of_a_single_string_column(tmp_path: Path) -> None:
    @tm.predictor(outputs={"label": "string"})
    class Classifier:
        def load(self, weights_dir): ...

        def predict(self, inputs):
            return "active"

    out = predict.run(Classifier, weights_dir=_weights(tmp_path), inputs={}, out=tmp_path / "c.csv")
    assert _rows(out) == [{"label": "active"}]


def test_a_list_of_dicts_is_many_rows_and_a_bare_value_is_one(tmp_path: Path) -> None:
    @tm.predictor(outputs={"score": "number"})
    class Many:
        def load(self, weights_dir): ...

        def predict(self, inputs):
            return [{"score": 1}, {"score": 2}]

    weights = _weights(tmp_path)
    out = predict.run(Many, weights_dir=weights, inputs={}, out=tmp_path / "many.csv")
    assert [r["score"] for r in _rows(out)] == ["1", "2"]

    @tm.predictor(outputs={"score": "number"})
    class Bare:
        def load(self, weights_dir): ...

        def predict(self, inputs):
            return 0.5

    out = predict.run(Bare, weights_dir=weights, inputs={}, out=tmp_path / "bare.csv")
    assert _rows(out) == [{"score": "0.5"}]


def test_a_missing_declared_column_fails_the_prediction(tmp_path: Path) -> None:
    @tm.predictor(outputs={"score": "number", "label": "string"})
    class Partial:
        def load(self, weights_dir): ...

        def predict(self, inputs):
            return {"score": 1}

    with pytest.raises(predict.PredictError, match=r"\['label'\]"):
        predict.run(Partial, weights_dir=_weights(tmp_path), inputs={}, out=tmp_path / "p.csv")


def test_predictor_failures_name_the_step(tmp_path: Path) -> None:
    @tm.predictor(outputs={"score": "number"})
    class Broken:
        def load(self, weights_dir):
            raise ValueError("no weights here")

        def predict(self, inputs):
            return {"score": 1}

    with pytest.raises(predict.PredictError, match=r"Broken.load\(.*\) failed: no weights here"):
        predict.run(Broken, weights_dir=_weights(tmp_path), inputs={}, out=tmp_path / "b.csv")


def test_bad_predictor_references_are_refused(tmp_path: Path) -> None:
    with pytest.raises(predict.PredictError, match="model.py:ClassName"):
        predict.resolve_predictor_class("model.py")
    with pytest.raises(predict.PredictError, match="does not exist"):
        predict.resolve_predictor_class("missing.py:Thing")
    (tmp_path / "model.py").write_text(PREDICTOR_SOURCE)
    with pytest.raises(predict.PredictError, match="no class named Other"):
        predict.resolve_predictor_class("model.py:Other")


def test_serves_models_from_is_recorded_on_the_block() -> None:
    @tm.predictor(outputs={"score": "number"}, serves_models_from=["binder-train"])
    class Served:
        def load(self, weights_dir): ...

        def predict(self, inputs): ...

    block = getattr(Served, decorators.METADATA_ATTR)["block"]
    assert block["servesModelsFrom"] == ["binder-train"]
    with pytest.raises(tm.finetune.FinetuneSpecError, match="serves_models_from"):
        tm.finetune.spec.predictor_block(serves_models_from="binder-train")


def test_task_is_recorded_as_the_task_type() -> None:
    @tm.predictor(task="score", outputs={"score": "number"})
    class Scored:
        def load(self, weights_dir): ...

        def predict(self, inputs): ...

    assert getattr(Scored, decorators.METADATA_ATTR)["block"]["taskType"] == "score"
    with pytest.raises(tm.finetune.FinetuneSpecError, match="task must be"):
        tm.finetune.spec.predictor_block(task="  ")


def test_module_entry_point_is_runnable(tmp_path: Path) -> None:
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, "-m", "tamarind.finetune", "predict", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "--weights" in result.stdout
