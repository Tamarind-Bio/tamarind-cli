"""Prediction mode: serve a trained artifact with the ``@tm.predictor`` class.

A prediction job runs the SAME image and the same ``run.sh`` as a training job. The platform
cannot change the container's command, so it tells the SDK instead: before the script starts
the orchestrator stages the model's weights into the container and exports

- ``TAMARIND_MODE=predict``: this run serves a model instead of training one.
- ``TAMARIND_WEIGHTS_DIR``: the directory holding the trained artifact, read-only.
- ``TAMARIND_PREDICTOR``: the ``<file>.py:<Class>`` of the ``@tm.predictor`` class, relative to
  the working directory (``/app``), as the tool's pinned ``finetune`` block names it.
- ``TAMARIND_PREDICTIONS_FILE``: where the declared output columns go (``/app/out/predictions.csv``).
- ``TAMARIND_INPUTS_FILE``: the job's inputs as JSON (``/app/inputs/inputs.json``): each declared
  input by name, a file input as the path it was staged at.

``@tm.training_run`` sees the mode and runs :func:`run_from_environment` in place of the training
function, so ``python train.py`` serves predictions with no change to the script. A ``run.sh``
that prefers an explicit entry can call ``python -m tamarind.finetune predict`` instead; the same
command with ``--weights`` and ``--inputs`` runs a predictor on a laptop.

Unlike ``tm.log`` and ``tm.checkpoint``, everything here raises: a prediction that cannot be
produced must fail the job, not register an empty result.
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import inspect
import json
import os
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence

from tamarind.finetune.decorators import METADATA_ATTR, registered

ENV_MODE = "TAMARIND_MODE"
ENV_WEIGHTS_DIR = "TAMARIND_WEIGHTS_DIR"
ENV_PREDICTOR = "TAMARIND_PREDICTOR"
ENV_PREDICTIONS_FILE = "TAMARIND_PREDICTIONS_FILE"
ENV_INPUTS_FILE = "TAMARIND_INPUTS_FILE"

MODE_PREDICT = "predict"
PLATFORM_INPUTS_FILE = "/app/inputs/inputs.json"
PREDICTIONS_FILENAME = "predictions.csv"


class PredictError(RuntimeError):
    """The predictor could not be found, loaded or run. Fails the job."""


def is_predicting() -> bool:
    """True when the platform started this run to serve a model rather than train one."""
    return os.environ.get(ENV_MODE, "").strip().lower() == MODE_PREDICT


def _parse_class_ref(ref: str) -> tuple[Path, str]:
    file_part, sep, class_name = ref.partition(":")
    if not sep or not file_part.strip() or not class_name.strip():
        raise PredictError(f"predictor reference {ref!r} must look like model.py:ClassName")
    return Path(file_part.strip()), class_name.strip()


def _import_by_path(path: Path) -> Any:
    if not path.is_file():
        raise PredictError(f"predictor file {path} does not exist")
    module_name = f"_tamarind_predictor_{path.stem}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise PredictError(f"could not import {path}")
    module = importlib.util.module_from_spec(spec)
    # Sibling imports (``from utils import ...``) resolve as they do for ``python model.py``.
    parent = str(path.parent)
    if parent not in sys.path:
        sys.path.insert(0, parent)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception as exc:
        raise PredictError(f"importing {path} failed: {exc}") from exc
    return module


def _same_source(cls: type, path: Path) -> bool:
    """Is `cls` defined in the file `path` names? A same-named class from another file is not it."""
    try:
        source = inspect.getsourcefile(cls)
        if not source:
            return False
        return Path(source).resolve() == path.resolve()
    except (TypeError, OSError):
        return False


def resolve_predictor_class(ref: str | None = None) -> type:
    """The ``@tm.predictor`` class named by ``ref`` (``model.py:Class``), or the one already imported.

    A class the running script already imported is reused rather than re-executing its module,
    so a predictor that lives in ``train.py`` itself is not imported twice.
    """
    record = registered("predictor")
    if ref is None:
        if not record:
            raise PredictError(f"no @tm.predictor class is imported and {ENV_PREDICTOR} is not set")
        return record["target"]
    path, class_name = _parse_class_ref(ref)
    if record and record["target"].__name__ == class_name and _same_source(record["target"], path):
        return record["target"]
    module = _import_by_path(path.resolve())
    cls = getattr(module, class_name, None)
    if not isinstance(cls, type):
        raise PredictError(f"{path} has no class named {class_name}")
    if getattr(cls, METADATA_ATTR, {}).get("kind") != "predictor":
        print(
            f"[tamarind] {ref} is not decorated with @tm.predictor; serving it anyway",
            file=sys.stderr,
        )
    return cls


def declared_output_columns(cls: type | None = None) -> list[str]:
    """The output column names the predictor declared, in order; empty when it declared none."""
    record = getattr(cls, METADATA_ATTR, None) if cls is not None else registered("predictor")
    block = (record or {}).get("block") or {}
    columns: list[str] = []
    for produced in block.get("producedOutputs") or []:
        for column in produced.get("columns") or []:
            name = column.get("name")
            if isinstance(name, str) and name not in columns:
                columns.append(name)
    return columns


def read_inputs(path: str | os.PathLike[str] | None = None) -> dict[str, Any]:
    """The job's inputs: the file named by ``path`` or ``TAMARIND_INPUTS_FILE``, else the platform default."""
    chosen = Path(path or os.environ.get(ENV_INPUTS_FILE) or PLATFORM_INPUTS_FILE)
    if not chosen.is_file():
        if path is None and not os.environ.get(ENV_INPUTS_FILE):
            return {}
        raise PredictError(f"inputs file {chosen} does not exist")
    try:
        loaded = json.loads(chosen.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise PredictError(f"could not read inputs from {chosen}: {exc}") from exc
    if not isinstance(loaded, dict):
        raise PredictError(f"inputs file {chosen} must hold a JSON object")
    return loaded


def rows_from(result: Any, columns: Sequence[str]) -> list[dict[str, Any]]:
    """Normalize what ``predict`` returned into CSV rows.

    A dict is one row; a list of dicts is many; a bare value is one row of the single declared
    column. Anything else is refused with what was expected.
    """
    if isinstance(result, Mapping):
        return [dict(result)]
    if isinstance(result, (list, tuple)):
        if not result:
            raise PredictError(
                "predict() returned no rows; a prediction job must produce at least one"
            )
        rows: list[dict[str, Any]] = []
        for index, item in enumerate(result):
            if not isinstance(item, Mapping):
                raise PredictError(
                    f"predict() returned a list whose item {index} is {type(item).__name__}, "
                    "not a dict of column -> value"
                )
            rows.append(dict(item))
        return rows
    if len(columns) == 1 and result is not None and not isinstance(result, bytes):
        return [{columns[0]: result}]
    raise PredictError(
        "predict() must return a dict of column -> value, or a list of them"
        + (
            f"; a bare value is only accepted for a single declared output ({list(columns)})"
            if columns
            else ""
        )
    )


def _cell(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    item = getattr(value, "item", None)  # numpy / torch scalars
    if callable(item):
        try:
            return item()
        except Exception:  # noqa: BLE001 - fall through to the generic rendering
            pass
    return json.dumps(value, default=str) if isinstance(value, (list, dict)) else str(value)


def write_predictions(
    rows: Sequence[Mapping[str, Any]],
    columns: Sequence[str],
    path: str | os.PathLike[str],
) -> Path:
    """Write ``rows`` as CSV: the declared columns first, then any extra keys the predictor returned."""
    header = list(columns)
    for row in rows:
        for key in row:
            if key not in header:
                header.append(str(key))
    missing = [c for c in columns if any(c not in row for row in rows)]
    if missing:
        raise PredictError(
            f"predict() did not return the declared output column(s) {missing} for every row"
        )
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _cell(row.get(key)) for key in header})
    return target


def run(
    predictor: type | str | None = None,
    *,
    weights_dir: str | os.PathLike[str] | None = None,
    inputs: Mapping[str, Any] | None = None,
    out: str | os.PathLike[str] | None = None,
) -> Path:
    """Load the predictor on ``weights_dir``, run it on ``inputs``, write the predictions CSV.

    Each argument defaults to the platform's environment variable. Returns the file written.
    """
    cls = (
        predictor
        if isinstance(predictor, type)
        else resolve_predictor_class(
            predictor if predictor is not None else os.environ.get(ENV_PREDICTOR)
        )
    )
    chosen = weights_dir or os.environ.get(ENV_WEIGHTS_DIR)
    if not chosen:
        # Checked before Path(): Path("") is the working directory, which exists, and load()
        # would then read whatever happens to be there instead of the trained artifact.
        raise PredictError(
            f"no weights directory: the platform sets {ENV_WEIGHTS_DIR}, locally pass --weights"
        )
    weights = Path(chosen)
    if not weights.is_dir():
        raise PredictError(f"weights directory {weights} does not exist")
    for required in ("load", "predict"):
        if not callable(getattr(cls, required, None)):
            raise PredictError(f"predictor {cls.__name__} needs a callable {required}()")
    columns = declared_output_columns(cls)
    values = dict(inputs) if inputs is not None else read_inputs()
    try:
        model = cls()
        model.load(weights)
    except Exception as exc:
        raise PredictError(f"{cls.__name__}.load({weights}) failed: {exc}") from exc
    try:
        result = model.predict(values)
    except Exception as exc:
        raise PredictError(f"{cls.__name__}.predict() failed: {exc}") from exc
    rows = rows_from(result, columns)
    target = out or os.environ.get(ENV_PREDICTIONS_FILE)
    if not target:
        from tamarind.finetune.runtime import run_dir

        target = run_dir() / PREDICTIONS_FILENAME
    written = write_predictions(rows, columns, target)
    print(f"[tamarind] wrote {len(rows)} prediction row(s) to {written}", file=sys.stderr)
    return written


def run_from_environment() -> Path:
    """What ``@tm.training_run`` calls in prediction mode: everything from the environment."""
    return run()


def _parse_inputs_argument(text: str | None, pairs: Sequence[str]) -> dict[str, Any] | None:
    values: dict[str, Any] | None = None
    if text is not None:
        candidate = Path(text)
        if candidate.is_file():
            values = read_inputs(candidate)
        else:
            try:
                loaded = json.loads(text)
            except ValueError as exc:
                raise PredictError(
                    f"--inputs must be a JSON object or the path of a JSON file: {exc}"
                ) from exc
            if not isinstance(loaded, dict):
                raise PredictError("--inputs must be a JSON object")
            values = loaded
    if pairs:
        values = dict(values or {})
        for pair in pairs:
            name, sep, value = pair.partition("=")
            if not sep or not name:
                raise PredictError(f"--input expects name=value, got {pair!r}")
            values[name] = value
    return values


def main(argv: Sequence[str] | None = None) -> int:
    """``python -m tamarind.finetune predict [--predictor model.py:Class] [--weights DIR] ...``."""
    parser = argparse.ArgumentParser(
        prog="python -m tamarind.finetune",
        description="Run a @tm.predictor class on a trained artifact and write predictions.csv.",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    predict = sub.add_parser("predict", help="serve a trained artifact once")
    predict.add_argument("--predictor", help="<file>.py:<Class>; default: $TAMARIND_PREDICTOR")
    predict.add_argument("--weights", help="artifact directory; default: $TAMARIND_WEIGHTS_DIR")
    predict.add_argument(
        "--inputs", help="JSON object or path to one; default: $TAMARIND_INPUTS_FILE"
    )
    predict.add_argument(
        "--input", action="append", default=[], metavar="NAME=VALUE", help="one input; repeatable"
    )
    predict.add_argument("--out", help="predictions CSV; default: $TAMARIND_PREDICTIONS_FILE")
    args = parser.parse_args(argv)
    try:
        values = _parse_inputs_argument(args.inputs, args.input)
        run(args.predictor, weights_dir=args.weights, inputs=values, out=args.out)
    except PredictError as exc:
        print(f"[tamarind] {exc}", file=sys.stderr)
        return 1
    return 0
