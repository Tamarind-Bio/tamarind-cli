"""Hyperparameter specs and the `finetune` block shape.

Specs are plain dicts so that the same expression works in three places: as a decorator
argument at runtime, as a literal the platform's build can evaluate from source without importing the
user's script, and as JSON in config.json. The backend (tamarind-website
`custom_tool_finetune.py`) is the strict validator; this module keeps the shape and names.
"""

from __future__ import annotations

from typing import Any, Callable, Mapping, Sequence

SCALAR_TYPES = ("float", "int", "string", "boolean")


class FinetuneSpecError(ValueError):
    """A decorator argument that cannot become a finetune block."""


def _spec(
    hp_type: str,
    default: Any,
    *,
    min: float | None = None,  # noqa: A002 - mirrors the config.json key
    max: float | None = None,  # noqa: A002
    options: Sequence[Any] | None = None,
    description: str | None = None,
    display_name: str | None = None,
) -> dict[str, Any]:
    out: dict[str, Any] = {"type": hp_type}
    if default is not None:
        out["default"] = default
    if min is not None:
        out["min"] = min
    if max is not None:
        out["max"] = max
    if options is not None:
        out["options"] = list(options)
    if description is not None:
        out["description"] = description
    if display_name is not None:
        out["displayName"] = display_name
    return out


def Float(  # noqa: N802 - a constructor-like helper, read as a type
    default: float | None = None,
    min: float | None = None,  # noqa: A002
    max: float | None = None,  # noqa: A002
    *,
    description: str | None = None,
    display_name: str | None = None,
) -> dict[str, Any]:
    """A float hyperparameter. `tm.Float(1e-4, 1e-6, 1e-2)` is default, min, max."""
    return _spec(
        "float", default, min=min, max=max, description=description, display_name=display_name
    )


def Int(  # noqa: N802
    default: int | None = None,
    min: int | None = None,  # noqa: A002
    max: int | None = None,  # noqa: A002
    *,
    description: str | None = None,
    display_name: str | None = None,
) -> dict[str, Any]:
    """An integer hyperparameter."""
    return _spec(
        "int", default, min=min, max=max, description=description, display_name=display_name
    )


def Str(  # noqa: N802
    default: str | None = None,
    *,
    description: str | None = None,
    display_name: str | None = None,
) -> dict[str, Any]:
    """A free-text hyperparameter."""
    return _spec("string", default, description=description, display_name=display_name)


def Bool(  # noqa: N802
    default: bool | None = None,
    *,
    description: str | None = None,
    display_name: str | None = None,
) -> dict[str, Any]:
    """An on/off hyperparameter."""
    return _spec("boolean", default, description=description, display_name=display_name)


def Choice(  # noqa: N802
    default: Any,
    options: Sequence[Any],
    *,
    description: str | None = None,
    display_name: str | None = None,
) -> dict[str, Any]:
    """One of a fixed set. The type is read off the options: all ints, all numbers, or all strings."""
    values = list(options)
    if not values:
        raise FinetuneSpecError("Choice needs at least one option")
    if all(isinstance(v, bool) for v in values):
        raise FinetuneSpecError("use tm.Bool for an on/off hyperparameter")
    if all(isinstance(v, int) and not isinstance(v, bool) for v in values):
        hp_type = "int"
    elif all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in values):
        hp_type = "float"
    elif all(isinstance(v, str) for v in values):
        hp_type = "string"
    else:
        raise FinetuneSpecError("Choice options must be all ints, all numbers, or all strings")
    return _spec(
        hp_type, default, options=values, description=description, display_name=display_name
    )


SPEC_HELPERS: dict[str, Callable[..., dict[str, Any]]] = {
    "Float": Float,
    "Int": Int,
    "Str": Str,
    "Bool": Bool,
    "Choice": Choice,
}


def normalize_hyperparameters(value: Mapping[str, Any] | None) -> dict[str, dict[str, Any]]:
    """Each value a spec dict (from the helpers above) or a plain dict with a `type`."""
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise FinetuneSpecError(
            "hyperparameters must be a dict of name -> tm.Float(...) / tm.Int(...) / ..."
        )
    out: dict[str, dict[str, Any]] = {}
    for name, spec in value.items():
        if not isinstance(name, str):
            raise FinetuneSpecError(f"hyperparameter names must be strings, got {name!r}")
        if not isinstance(spec, Mapping) or spec.get("type") not in SCALAR_TYPES:
            raise FinetuneSpecError(
                f"hyperparameter {name!r}: use tm.Float(...), tm.Int(...), tm.Str(...), tm.Bool(...) "
                f"or tm.Choice(...), or a dict with a type in {list(SCALAR_TYPES)}"
            )
        out[name] = dict(spec)
    return out


def normalize_objective(value: Any) -> dict[str, str] | None:
    """`("val/loss", "min")`, `"val/spearman"` (max), or `{"metric": ..., "mode": ...}`."""
    if value is None:
        return None
    if isinstance(value, str):
        return {"metric": value, "mode": "max"}
    if isinstance(value, (tuple, list)) and len(value) in (1, 2) and isinstance(value[0], str):
        mode = value[1] if len(value) == 2 else "max"
        if mode not in ("max", "min"):
            raise FinetuneSpecError('objective mode must be "max" or "min"')
        return {"metric": value[0], "mode": mode}
    if isinstance(value, Mapping) and isinstance(value.get("metric"), str):
        mode = value.get("mode", "max")
        if mode not in ("max", "min"):
            raise FinetuneSpecError('objective mode must be "max" or "min"')
        return {"metric": value["metric"], "mode": mode}
    raise FinetuneSpecError('objective must be ("<metric>", "max"|"min") or a metric name')


def training_run_block(
    *,
    timeout_hours: float | None = None,
    hyperparameters: Mapping[str, Any] | None = None,
    objective: Any = None,
    artifact: str | None = None,
) -> dict[str, Any]:
    """The `finetune` keys a @training_run contributes, minus the entrypoint the caller adds."""
    block: dict[str, Any] = {"hyperparameters": normalize_hyperparameters(hyperparameters)}
    if timeout_hours is not None:
        if isinstance(timeout_hours, bool) or not isinstance(timeout_hours, (int, float)):
            raise FinetuneSpecError("timeout_hours must be a number")
        block["timeoutHours"] = timeout_hours
    normalized_objective = normalize_objective(objective)
    if normalized_objective is not None:
        block["objective"] = normalized_objective
    if artifact is not None:
        if not isinstance(artifact, str) or not artifact.strip():
            raise FinetuneSpecError("artifact must be a relative directory under the run's output")
        block["artifact"] = artifact.strip().strip("/")
    return block


def predictor_block(
    *,
    gpu: str | None = None,
    memory: str | None = None,
    inputs: Mapping[str, str] | Sequence[Mapping[str, Any]] | None = None,
    outputs: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """The `finetune.predictor` keys a @predictor contributes, minus the class the caller adds.

    `inputs={"sequence": "sequence"}` is shorthand for one input per entry; a list of full input
    dicts is passed through. `outputs={"affinity": "number"}` becomes the primary predictions CSV.
    """
    block: dict[str, Any] = {}
    if gpu is not None:
        block["gpuType"] = gpu
    if memory is not None:
        block["memory"] = memory
    if inputs is not None:
        if isinstance(inputs, Mapping):
            block["inputs"] = [
                {"name": name, "type": kind, "required": True} for name, kind in inputs.items()
            ]
        else:
            block["inputs"] = [dict(entry) for entry in inputs]
    if outputs is not None:
        if not isinstance(outputs, Mapping) or not outputs:
            raise FinetuneSpecError("outputs must be a dict of column name -> column type")
        block["producedOutputs"] = [
            {
                "type": "csv",
                "name": "predictions",
                "path": "predictions.csv",
                "primary": True,
                "columns": [{"name": name, "type": kind} for name, kind in outputs.items()],
            }
        ]
    return block


def evaluator_block(
    *, metrics: Mapping[str, str] | None = None, aggregate: str = "mean"
) -> dict[str, Any]:
    """Runtime-only metadata for @evaluator; the block stores just the reference."""
    out: dict[str, Any] = {"aggregate": aggregate}
    if metrics is not None:
        for name, better in metrics.items():
            if better not in ("max", "min"):
                raise FinetuneSpecError(f'metric {name!r}: direction must be "max" or "min"')
        out["metrics"] = dict(metrics)
    return out
