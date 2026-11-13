"""The four decorators. They attach metadata and return the object as it was, except that the
training function learns one thing: in prediction mode (``TAMARIND_MODE=predict``, set by the
platform when a job serves a trained model) calling it runs the ``@tm.predictor`` class instead.

The platform never calls through a decorator: at build time it reads the decorator arguments
out of the uploaded source (without importing it) and stores the `finetune` block they describe
on the tool's version, leaving the source as it was; at run time it invokes the entrypoint the
block names. So a decorated
script runs identically on a laptop, where the decorators only register defaults for
`tm.hyperparameters()` and the evaluator for `tm.evaluate()`.

Every argument must be a literal: a number, string, bool, tuple, list or dict of those, or one
of the `tm.Float` / `tm.Int` / `tm.Str` / `tm.Bool` / `tm.Choice` helpers with literal
arguments. The build refuses anything else with the file and line, because the config is
needed before the image that holds the script's dependencies exists.
"""

from __future__ import annotations

import functools
import sys
from typing import Any, Callable, Mapping, Sequence, TypeVar

from tamarind.finetune import spec as _spec

F = TypeVar("F", bound=Callable[..., Any])
C = TypeVar("C", bound=type)

METADATA_ATTR = "__tamarind_finetune__"

# What the most recent decorators declared, for the runtime helpers. Keyed by kind so a script
# with one of each (the normal case) resolves without the caller naming anything.
_registry: dict[str, Any] = {}


def _attach(obj: Any, kind: str, metadata: dict[str, Any]) -> None:
    record = {"kind": kind, **metadata}
    setattr(obj, METADATA_ATTR, record)
    _registry[kind] = {"target": obj, **record}


def registered(kind: str) -> dict[str, Any] | None:
    """The most recently decorated object of `kind`, with its metadata, or None."""
    return _registry.get(kind)


def reset_registry() -> None:
    _registry.clear()


def training_run(
    *,
    gpu: str | None = None,
    memory: str | None = None,
    cpu: int | None = None,
    timeout_hours: float | None = None,
    hyperparameters: Mapping[str, Any] | None = None,
    objective: Any = None,
    artifact: str | None = None,
) -> Callable[[F], F]:
    """Mark the function the platform invokes to train.

        @tm.training_run(gpu="A100", timeout_hours=12,
                         hyperparameters={"lr": tm.Float(1e-4, 1e-6, 1e-2), "epochs": tm.Int(10)},
                         objective=("val/spearman", "max"), artifact="checkpoints/best")
        def main():
            cfg = tm.hyperparameters()
            ...

    `gpu`, `memory` and `cpu` set the tool's resources (config.json `gpuType`, `memory`, `cpu`).
    `hyperparameters` become submit-form settings and the sweep axes; the script reads the
    chosen values with `tm.hyperparameters()`. `objective` names the logged metric that ranks runs and
    picks the best checkpoint. `artifact` is the directory under the run's output that holds
    the trained model (default "model").
    """
    block = _spec.training_run_block(
        timeout_hours=timeout_hours,
        hyperparameters=hyperparameters,
        objective=objective,
        artifact=artifact,
    )
    resources = {
        k: v for k, v in (("gpuType", gpu), ("memory", memory), ("cpu", cpu)) if v is not None
    }

    def decorate(fn: F) -> F:
        @functools.wraps(fn)
        def entry(*args: Any, **kwargs: Any) -> Any:
            # A prediction job runs the same image and the same `run.sh`, so the switch lives
            # here: the platform sets the mode and the predictor class, and the training body
            # is not entered. Imported lazily so a laptop run never pays for it.
            from tamarind.finetune import predict as _predict

            if _predict.is_predicting():
                print(
                    "[tamarind] prediction mode: serving the @tm.predictor class instead of "
                    f"training with {fn.__name__}()",
                    file=sys.stderr,
                )
                _predict.run_from_environment()
                return None
            return fn(*args, **kwargs)

        _attach(entry, "training_run", {"block": block, "resources": resources})
        return entry  # type: ignore[return-value]

    return decorate


def predictor(
    *,
    gpu: str | None = None,
    memory: str | None = None,
    inputs: Mapping[str, str] | Sequence[Mapping[str, Any]] | None = None,
    outputs: Mapping[str, str] | None = None,
    serves_models_from: Sequence[str] | None = None,
) -> Callable[[C], C]:
    """Mark the class that serves the trained artifact.

        @tm.predictor(gpu="L4", inputs={"sequence": "sequence"}, outputs={"affinity": "number"})
        class BindingModel:
            def load(self, artifact_dir): ...
            def predict(self, inputs): ...   # -> {"affinity": 0.42} or a list of such dicts
            def embed(self, inputs): ...     # optional

    `load` and `predict` are required; `embed` turns on feature extraction. With `inputs` and
    `outputs` the trained model becomes a custom tool endpoint the API, pipelines and benchmarks
    can call: a prediction job stages the model's weights, calls `load(weights_dir)` then
    `predict(inputs)` with each declared input by name, and writes the returned columns to
    `predictions.csv`. `serves_models_from` lists the training tools whose models this class may
    serve when it is deployed as a separate tool; by default it serves its own tool's models.
    """
    block = _spec.predictor_block(
        gpu=gpu,
        memory=memory,
        inputs=inputs,
        outputs=outputs,
        serves_models_from=serves_models_from,
    )

    def decorate(cls: C) -> C:
        for required in ("load", "predict"):
            if not callable(getattr(cls, required, None)):
                raise _spec.FinetuneSpecError(
                    f"@tm.predictor class {cls.__name__} needs a callable {required}()"
                )
        _attach(cls, "predictor", {"block": block})
        return cls

    return decorate


def evaluator(
    fn: F | None = None,
    *,
    metrics: Mapping[str, str] | None = None,
    aggregate: str = "mean",
) -> Any:
    """Mark the scoring function: `score(predictions, truths) -> {metric: value}`.

    `metrics` names each returned metric's direction ({"spearman": "max", "mae": "min"}). The
    same function validates during training (`tm.evaluate`) and scores a benchmark.
    """
    metadata = _spec.evaluator_block(metrics=metrics, aggregate=aggregate)

    def decorate(target: F) -> F:
        _attach(target, "evaluator", metadata)
        return target

    return decorate(fn) if fn is not None else decorate


def splitter(fn: F | None = None) -> Any:
    """Mark a custom train/validation split: `split(dataset) -> (train_index, val_index)`."""

    def decorate(target: F) -> F:
        _attach(target, "splitter", {})
        return target

    return decorate(fn) if fn is not None else decorate
