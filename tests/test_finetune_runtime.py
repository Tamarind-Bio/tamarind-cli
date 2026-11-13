from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

import tamarind as tm
from tamarind.finetune import decorators, runtime


@pytest.fixture(autouse=True)
def _clean(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    decorators.reset_registry()
    for name in (
        runtime.ENV_RUN_DIR,
        runtime.ENV_HYPERPARAMETERS,
        runtime.ENV_METRICS_FILE,
        runtime.ENV_ARTIFACT_DIR,
        "lr",
        "epochs",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.chdir(tmp_path)
    yield
    decorators.reset_registry()


def _declare():
    @tm.training_run(
        hyperparameters={
            "lr": tm.Float(1e-3),
            "epochs": tm.Int(5),
            "on": tm.Bool(False),
            "tag": tm.Str("a"),
        },
        artifact="ckpt",
    )
    def main():
        return "ran"

    return main


def test_decorators_return_the_object_unchanged_and_record_metadata() -> None:
    main = _declare()
    assert main() == "ran"
    record = getattr(main, decorators.METADATA_ATTR)
    assert record["kind"] == "training_run"
    assert record["block"]["artifact"] == "ckpt"
    assert decorators.registered("training_run")["target"] is main


def test_predictor_requires_load_and_predict() -> None:
    with pytest.raises(tm.finetune.FinetuneSpecError, match="needs a callable predict"):

        @tm.predictor()
        class Half:
            def load(self, d): ...


def test_config_off_platform_is_defaults_then_env(monkeypatch: pytest.MonkeyPatch) -> None:
    _declare()
    assert tm.hyperparameters() == {"lr": 1e-3, "epochs": 5, "on": False, "tag": "a"}
    monkeypatch.setenv("epochs", "7")
    monkeypatch.setenv("lr", "0.5")
    assert tm.hyperparameters() == {"lr": 0.5, "epochs": 7, "on": False, "tag": "a"}
    monkeypatch.setenv("on", "yes")
    assert tm.hyperparameters()["on"] is True
    monkeypatch.setenv("on", "treu")  # a typo is ignored like a malformed int, never read as False
    assert tm.hyperparameters()["on"] is False
    monkeypatch.setenv("on", "off")
    assert tm.hyperparameters()["on"] is False
    assert not tm.is_platform()


def test_config_on_platform_reads_the_typed_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _declare()
    run = tmp_path / "out"
    hp = tmp_path / "hp.json"
    hp.write_text(json.dumps({"lr": 2e-4, "epochs": 3, "undeclared": 1}))
    monkeypatch.setenv(runtime.ENV_RUN_DIR, str(run))
    monkeypatch.setenv(runtime.ENV_HYPERPARAMETERS, str(hp))
    monkeypatch.setenv("epochs", "99")  # the file wins over the env var on the platform
    assert tm.is_platform()
    assert tm.hyperparameters() == {"lr": 2e-4, "epochs": 3, "on": False, "tag": "a"}


def test_config_without_declaration_returns_the_whole_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    hp = tmp_path / "hp.json"
    hp.write_text(json.dumps({"anything": 1}))
    monkeypatch.setenv(runtime.ENV_HYPERPARAMETERS, str(hp))
    assert tm.hyperparameters() == {"anything": 1}


def test_log_appends_json_lines_and_nulls_non_finite(tmp_path: Path) -> None:
    tm.log({"train/loss": 0.5}, step=1)
    tm.log({"train/loss": math.nan, "val/spearman": float("inf")}, step=2, lr=1e-3)
    lines = [
        json.loads(line)
        for line in (tmp_path / "tamarind_run" / "metrics.jsonl").read_text().splitlines()
    ]
    assert lines[0]["step"] == 1
    assert lines[0]["train/loss"] == 0.5
    assert "time" in lines[0]
    assert lines[1] == {**lines[1], "train/loss": None, "val/spearman": None, "lr": 1e-3, "step": 2}


def test_log_honours_the_platform_metrics_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    target = tmp_path / "deep" / "m.jsonl"
    monkeypatch.setenv(runtime.ENV_METRICS_FILE, str(target))
    tm.log({"a": 1})
    assert json.loads(target.read_text())["a"] == 1


def test_artifact_dir_follows_the_platform_for_a_hand_written_block(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # No decorators at all: the block was written by hand in config.json.
    run = tmp_path / "out"
    monkeypatch.setenv(runtime.ENV_RUN_DIR, str(run))
    monkeypatch.setenv(runtime.ENV_ARTIFACT_DIR, str(run / "checkpoints" / "best"))
    assert tm.artifact_dir() == run / "checkpoints" / "best"
    assert tm.artifact_dir().is_dir()
    assert tm.checkpoint(step=1) == run / "checkpoints" / "best"
    # The platform's pin wins over a decorator default that disagrees.
    _declare()
    assert tm.artifact_dir() == run / "checkpoints" / "best"


def test_log_never_raises(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    blocker = tmp_path / "file"
    blocker.write_text("x")
    monkeypatch.setenv(runtime.ENV_METRICS_FILE, str(blocker / "cannot" / "nest"))
    tm.log({"a": 1})  # a path under a regular file cannot be created


def test_checkpoint_records_path_step_and_metrics(tmp_path: Path) -> None:
    _declare()
    target = tm.checkpoint(step=3, metrics={"val/loss": 0.2})
    assert target == tmp_path / "tamarind_run" / "ckpt"
    assert target.is_dir()
    assert tm.artifact_dir() == target
    other = tm.checkpoint("epoch_2", step=2)
    assert other == tmp_path / "tamarind_run" / "epoch_2"
    records = [
        json.loads(line)
        for line in (tmp_path / "tamarind_run" / "checkpoints.jsonl").read_text().splitlines()
    ]
    assert records[0]["step"] == 3
    assert records[0]["metrics"] == {"val/loss": 0.2}
    assert records[0]["path"] == str(target)
    assert records[1]["path"] == str(other)


def test_evaluate_calls_the_registered_evaluator() -> None:
    @tm.evaluator(metrics={"mae": "min"})
    def score(predictions, truths):
        return {"mae": sum(abs(p - t) for p, t in zip(predictions, truths)) / len(truths)}

    assert tm.evaluate([1.0, 2.0], [1.5, 2.5]) == {"mae": 0.5}


def test_evaluate_without_an_evaluator_is_an_error() -> None:
    with pytest.raises(RuntimeError, match="no @tm.evaluator"):
        tm.evaluate([], [])


def test_evaluator_direction_is_checked() -> None:
    with pytest.raises(tm.finetune.FinetuneSpecError, match='direction must be "max" or "min"'):
        tm.evaluator(metrics={"x": "up"})


def test_top_level_exports_resolve_lazily() -> None:
    assert "training_run" in dir(tm)
    with pytest.raises(AttributeError):
        tm.not_a_thing  # noqa: B018
