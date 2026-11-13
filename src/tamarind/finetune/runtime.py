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
                value = _coerce(spec["type"], raw)
            except ValueError:
                print(f"[tamarind] ignoring ${name}={raw!r}: not a {spec['type']}", file=sys.stderr)
                continue
            problem = _outside_declaration(spec, value)
            if problem:
                print(f"[tamarind] ignoring ${name}={raw!r}: {problem}", file=sys.stderr)
                continue
            values[name] = value
    return values


def _outside_declaration(spec: Mapping[str, Any], value: Any) -> str | None:
    """Why `value` is not one the declaration allows, or None: the same rule the submit form applies."""
    options = spec.get("options")
    if options is not None and value not in options:
        return f"not one of {list(options)}"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if spec.get("min") is not None and value < spec["min"]:
            return f"below the minimum {spec['min']}"
        if spec.get("max") is not None and value > spec["max"]:
            return f"above the maximum {spec['max']}"
    return None


def _json_safe(value: Any) -> Any:
    if isinstance(value, bool) or value is None or isinstance(value, str):
        return value
    if isinstance(value, int):
        return value  # exact at any size; math.isfinite would overflow converting 10**1000
    if isinstance(value, float):
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
        line = json.dumps(_json_safe(record), separators=(",", ":")) + "\n"
    except Exception as exc:  # noqa: BLE001 - a cyclic or exotic value must not end a training run
        print(f"[tamarind] could not serialize a record for {path}: {exc}", file=sys.stderr)
        return
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(line)
    except OSError as exc:
        print(f"[tamarind] could not write {path}: {exc}", file=sys.stderr)


def metrics_file() -> Path:
    return Path(os.environ.get(ENV_METRICS_FILE) or run_dir() / METRICS_FILENAME)


def log(metrics: Mapping[str, Any], step: int | None = None, **more: Any) -> None:
    """Record metrics at a step: ``tm.log({"train/loss": loss}, step=step)``.

    Appends one JSON line per call. Non-finite numbers become null. Never raises.
    """
    try:
        record: dict[str, Any] = {}
        record.update(metrics)
        record.update(more)
        # The SDK's own fields go last: a metric named "time" or "step" must not move the
        # observation to another time or step, which would misorder curves and checkpoints.
        record["time"] = time.time()
        if step is not None:
            record["step"] = step
        path = metrics_file()  # may create the local run dir, which can fail
    except Exception as exc:  # noqa: BLE001 - logging must never end a training run
        print(f"[tamarind] could not log metrics: {exc}", file=sys.stderr)
        return
    _append_line(path, record)


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
    # Never raises: a directory that cannot be created is reported, and the path is still
    # returned so the script's own save shows the real error where it happens.
    try:
        target = Path(path) if path is not None else artifact_dir()
        if path is not None and not target.is_absolute():
            target = run_dir() / target
        target = target.resolve()
    except Exception as exc:  # noqa: BLE001 - checkpoint recording must never end a training run
        print(f"[tamarind] could not resolve the checkpoint directory: {exc}", file=sys.stderr)
        target = (
            Path(path) if path is not None else Path(os.environ.get(ENV_ARTIFACT_DIR) or "model")
        )
        return target
    try:
        target.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        print(f"[tamarind] could not create checkpoint directory {target}: {exc}", file=sys.stderr)
    try:
        record: dict[str, Any] = {"time": time.time(), "path": str(target)}
        if step is not None:
            record["step"] = step
        if metrics:
            record["metrics"] = dict(metrics)
        records = run_dir() / CHECKPOINTS_FILENAME
    except Exception as exc:  # noqa: BLE001
        print(f"[tamarind] could not record the checkpoint: {exc}", file=sys.stderr)
        return target
    _append_line(records, record)
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
