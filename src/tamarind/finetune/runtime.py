"""What a training script calls while it runs: config, log, checkpoint, evaluate.

On the platform the orchestrator sets three environment variables before the script starts:

- ``TAMARIND_RUN_DIR``: the run's output directory (``/app/out``). Everything durable goes here.
- ``TAMARIND_HYPERPARAMETERS``: a JSON file holding the chosen value of every declared
  hyperparameter, already typed. ``tm.hyperparameters()`` reads it.
- ``TAMARIND_METRICS_FILE``: where ``tm.log`` appends JSON lines. A sidecar ships them.

Off the platform none of these are set: ``tm.hyperparameters()`` returns the decorator's defaults with
environment-variable overrides, and files land under ``./tamarind_run`` so the same script
runs on a laptop. Nothing here makes a network call, and ``log`` / ``checkpoint`` never raise.
"""

from __future__ import annotations

import json
import math
import os
from pathlib import Path
import sys
import time
from typing import Any, Mapping

from tamarind.finetune.decorators import registered

ENV_RUN_DIR = "TAMARIND_RUN_DIR"
ENV_HYPERPARAMETERS = "TAMARIND_HYPERPARAMETERS"
ENV_METRICS_FILE = "TAMARIND_METRICS_FILE"
ENV_ARTIFACT_DIR = "TAMARIND_ARTIFACT_DIR"

LOCAL_RUN_DIR = "tamarind_run"
METRICS_FILENAME = "metrics.jsonl"
CHECKPOINTS_FILENAME = "checkpoints.jsonl"


def is_platform() -> bool:
    """True inside a Tamarind training run."""
    return bool(os.environ.get(ENV_RUN_DIR))


def run_dir() -> Path:
    """Where this run writes. Created on first use."""
    path = Path(os.environ.get(ENV_RUN_DIR) or LOCAL_RUN_DIR).resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def _declared() -> dict[str, dict[str, Any]]:
    record = registered("training_run")
    if not record:
        return {}
    return dict(record["block"].get("hyperparameters") or {})


def _coerce(hp_type: str, raw: str) -> Any:
    if hp_type == "int":
        return int(raw)
    if hp_type == "float":
        return float(raw)
    if hp_type == "boolean":
        text = raw.strip().lower()
        if text in ("1", "true", "yes", "on"):
            return True
        if text in ("0", "false", "no", "off"):
            return False
        raise ValueError(f"not a boolean: {raw!r}")  # "treu" must not quietly flip the setting
    return raw


def hyperparameters() -> dict[str, Any]:
    """The hyperparameter values for this run.

    Precedence: the platform's typed file, then an environment variable named after the
    hyperparameter (how the platform and a local shell both pass overrides), then the
    decorator's default. Only declared names are returned.
    """
    declared = _declared()
    values: dict[str, Any] = {
        name: spec["default"] for name, spec in declared.items() if "default" in spec
    }
    file_path = os.environ.get(ENV_HYPERPARAMETERS)
    if file_path:
        try:
            loaded = json.loads(Path(file_path).read_text())
        except (OSError, ValueError) as exc:  # a platform bug, not the user's: say so once
            print(
                f"[tamarind] could not read {ENV_HYPERPARAMETERS}={file_path}: {exc}",
                file=sys.stderr,
            )
            loaded = {}
        if isinstance(loaded, dict):
            for name, value in loaded.items():
                if not declared or name in declared:
                    values[name] = value
    for name, spec in declared.items():
        raw = os.environ.get(name)
        if raw is not None and not file_path:
            try:
                values[name] = _coerce(spec["type"], raw)
            except ValueError:
                print(f"[tamarind] ignoring ${name}={raw!r}: not a {spec['type']}", file=sys.stderr)
    return values


def _json_safe(value: Any) -> Any:
    if isinstance(value, bool) or value is None or isinstance(value, str):
        return value
    if isinstance(value, (int, float)):
        return value if math.isfinite(value) else None
    if isinstance(value, Mapping):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    item = getattr(value, "item", None)  # numpy / torch scalars
    if callable(item):
        try:
            return _json_safe(item())
        except Exception:  # noqa: BLE001 - best effort, the fallback below is fine
            pass
    return str(value)


def _append_line(path: Path, record: Mapping[str, Any]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(_json_safe(record), separators=(",", ":")) + "\n")
    except OSError as exc:
        print(f"[tamarind] could not write {path}: {exc}", file=sys.stderr)


def metrics_file() -> Path:
    return Path(os.environ.get(ENV_METRICS_FILE) or run_dir() / METRICS_FILENAME)


def log(metrics: Mapping[str, Any], step: int | None = None, **more: Any) -> None:
    """Record metrics at a step: ``tm.log({"train/loss": loss}, step=step)``.

    Appends one JSON line per call. Non-finite numbers become null. Never raises.
    """
    record: dict[str, Any] = {"time": time.time()}
    if step is not None:
        record["step"] = step
    record.update(metrics)
    record.update(more)
    _append_line(metrics_file(), record)


def artifact_dir() -> Path:
    """The directory the trained model must be saved to. Created on first use.

    On the platform this is the directory the run's pinned `finetune` block names, which the
    platform exports as TAMARIND_ARTIFACT_DIR: the same place registration looks, whether the
    block came from decorators or was written by hand. Locally it is the decorator's
    `artifact` under the run dir.
    """
    pinned = os.environ.get(ENV_ARTIFACT_DIR)
    if pinned:
        path = Path(pinned)
        path.mkdir(parents=True, exist_ok=True)
        return path
    record = registered("training_run")
    name = (record or {}).get("block", {}).get("artifact") or "model"
    path = run_dir() / name
    path.mkdir(parents=True, exist_ok=True)
    return path


def checkpoint(
    path: str | os.PathLike[str] | None = None,
    *,
    step: int | None = None,
    metrics: Mapping[str, Any] | None = None,
) -> Path:
    """Record that a checkpoint was saved, tying it to its step and metrics.

    Returns the directory to save into (``path``, or the artifact dir). The platform uses the
    records to pick the best checkpoint by the declared objective.
    """
    target = Path(path) if path is not None else artifact_dir()
    if path is not None and not target.is_absolute():
        target = run_dir() / target
    target = target.resolve()
    target.mkdir(parents=True, exist_ok=True)
    record: dict[str, Any] = {"time": time.time(), "path": str(target)}
    if step is not None:
        record["step"] = step
    if metrics:
        record["metrics"] = dict(metrics)
    _append_line(run_dir() / CHECKPOINTS_FILENAME, record)
    return target


def evaluate(predictions: Any, truths: Any = None) -> dict[str, Any]:
    """Call the ``@tm.evaluator`` with these predictions and truths."""
    record = registered("evaluator")
    if not record:
        raise RuntimeError("no @tm.evaluator is defined in this script")
    result = record["target"](predictions, truths)
    if not isinstance(result, Mapping):
        raise TypeError("the evaluator must return a dict of metric name -> value")
    return dict(result)
