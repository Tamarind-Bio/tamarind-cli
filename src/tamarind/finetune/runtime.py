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
import shutil
import sys
import tempfile
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
    # The environment is the fallback whenever the file did not answer — not only when the variable
    # is unset. The platform also exports each submitted setting as an environment variable, so a
    # file that was exported but never delivered (a runtime that did not carry it into the
    # container) still trains with the submitted values instead of silently with the defaults.
    file_read = False
    if file_path:
        try:
            loaded = json.loads(Path(file_path).read_text())
        except (OSError, ValueError) as exc:  # a platform bug, not the user's: say so once
            print(
                f"[tamarind] could not read {ENV_HYPERPARAMETERS}={file_path}: {exc}; "
                "falling back to the environment",
                file=sys.stderr,
            )
            loaded = None
        if isinstance(loaded, dict):
            file_read = True
            for name, value in loaded.items():
                if not declared or name in declared:
                    values[name] = value
    recovered = []
    for name, spec in declared.items():
        raw = os.environ.get(name)
        if raw is not None and not file_read:
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
            recovered.append(name)
    if file_path and not file_read and recovered:
        # Names only: a `tm.Str` setting can carry a credential or a signed dataset URL, and this line
        # lands in the job's persisted log.
        print(
            "[tamarind] hyperparameters read from the environment: " + ", ".join(recovered),
            file=sys.stderr,
        )
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


def _append_line(path: Path, record: Mapping[str, Any]) -> bool:
    """Append one JSON line; True when it was written. Never raises."""
    try:
        line = json.dumps(_json_safe(record), separators=(",", ":")) + "\n"
    except Exception as exc:  # noqa: BLE001 - a cyclic or exotic value must not end a training run
        print(f"[tamarind] could not serialize a record for {path}: {exc}", file=sys.stderr)
        return False
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(line)
    except OSError as exc:
        print(f"[tamarind] could not write {path}: {exc}", file=sys.stderr)
        return False
    return True


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


#: Where ``tm.checkpoint()`` puts each checkpoint it names itself, under the run dir.
CHECKPOINTS_DIRNAME = "checkpoints"
#: The training run's objective as JSON, exported by the platform for every training run, so a
#: hand-written ``finetune`` block (no decorator to read it from) keeps the right checkpoints too.
ENV_OBJECTIVE = "TAMARIND_OBJECTIVE"

# The checkpoint directories this process created itself (no `path` given), oldest first, with
# their objective score: the only directories the SDK ever deletes.
_managed: list[tuple[Path, float | None]] = []
_next_index = 0


def _objective() -> tuple[str, str] | None:
    """``(metric, "max"|"min")``: the platform's export first, else the decorator's, else None."""
    objective: Any = None
    raw = os.environ.get(ENV_OBJECTIVE)
    if raw:
        try:
            objective = json.loads(raw)
        except ValueError:
            print(f"[tamarind] ignoring an unreadable {ENV_OBJECTIVE}", file=sys.stderr)
    if not isinstance(objective, Mapping):
        record = registered("training_run")
        objective = ((record or {}).get("block") or {}).get("objective")
    if not isinstance(objective, Mapping) or not isinstance(objective.get("metric"), str):
        return None
    return objective["metric"], "min" if objective.get("mode") == "min" else "max"


def _score(metrics: Mapping[str, Any] | None, objective: tuple[str, str] | None) -> float | None:
    if objective is None or not metrics:
        return None
    value = metrics.get(objective[0])
    if isinstance(value, bool):
        return None
    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError, OverflowError):
        return None
    return number if math.isfinite(number) else None


def _checkpoint_root() -> Path:
    return run_dir() / CHECKPOINTS_DIRNAME


def _default_checkpoint_dir(step: int | None) -> Path:
    """``checkpoints/step-00000412`` for a step, else the next free ``checkpoints/ckpt-0003``."""
    global _next_index
    root = _checkpoint_root()
    if isinstance(step, int) and not isinstance(step, bool) and step >= 0:
        return root / f"step-{step:08d}"
    while (root / f"ckpt-{_next_index:04d}").exists() or (
        root / f"ckpt-{_next_index:04d}"
    ).is_symlink():
        _next_index += 1
    path = root / f"ckpt-{_next_index:04d}"
    _next_index += 1
    return path


def _inside_root(path: Path) -> bool:
    """A real directory directly under the run's checkpoint root, reached through no symlink."""
    root = _checkpoint_root()
    if root.is_symlink() or path.is_symlink() or path.parent != root:
        return False
    return path.resolve().parent == root.resolve()


def _holds_a_file(path: Path) -> bool:
    """True when ``path`` is a real directory with at least one regular file under it (no symlinks)."""
    try:
        if path.is_symlink() or not path.is_dir():
            return False
        for root, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if not os.path.islink(os.path.join(root, d))]
            for name in files:
                full = os.path.join(root, name)
                if not os.path.islink(full) and os.path.isfile(full):
                    return True
    except OSError:
        return False
    return False


def _prune(new: Path, objective: tuple[str, str] | None) -> None:
    """Delete the SDK's own earlier checkpoint directories, keeping three.

    Kept: the best of the earlier checkpoints that hold a file, by the objective (scored on the
    metrics each one recorded), the previous such one, and the new one. The previous one stays because this call runs
    BEFORE the script saves into ``new``: if that save fails, the run still has its last complete
    checkpoint. With no objective, no earlier checkpoint is "best". A directory the script named
    itself (``path=``) is never in this list, so never touched. Never raises.
    """
    global _managed
    earlier = [(path, score) for path, score in _managed if path != new]
    # Only a directory holding a file counts as a checkpoint, as at registration: a save that failed
    # (and that the script caught) or a directory that was never created must not stand in for the
    # previous or the best one and push out a directory that holds real weights.
    complete = [(path, score) for path, score in earlier if _holds_a_file(path)]
    keep = {new}
    if complete:
        keep.add(complete[-1][0])
        scored = [(path, score) for path, score in complete if score is not None]
        if objective is not None and scored:
            pick = min if objective[1] == "min" else max
            keep.add(pick(scored, key=lambda item: item[1])[0])
    remaining = []
    for path, score in earlier:
        if path in keep:
            remaining.append((path, score))
            continue
        if not _inside_root(path):
            print(
                f"[tamarind] not removing {path}: not a directory under {_checkpoint_root()}",
                file=sys.stderr,
            )
            continue
        try:
            shutil.rmtree(path)
        except FileNotFoundError:
            pass
        except OSError as exc:
            print(f"[tamarind] could not remove old checkpoint {path}: {exc}", file=sys.stderr)
            remaining.append((path, score))
    _managed = remaining


def checkpoint(
    path: str | os.PathLike[str] | None = None,
    *,
    step: int | None = None,
    metrics: Mapping[str, Any] | None = None,
) -> Path:
    """Start a checkpoint: returns the directory to save the model into, and records it.

        model.save(tm.checkpoint(step=step, metrics={"val/spearman": rho}))

    With no ``path`` each checkpoint gets its own directory (``checkpoints/step-00000412``), and
    the SDK deletes its earlier ones except the best so far by the training run's ``objective``
    (scored on the ``metrics`` passed here) and the previous one, which stays until the next
    checkpoint starts in case this save fails. The platform registers the best recorded checkpoint
    as the model, with the metrics logged at its step; with no objective, the latest one. A
    ``path`` you pass is used as given and never deleted.
    """
    global _managed
    # Never raises: a directory that cannot be created is reported, and the path is still
    # returned so the script's own save shows the real error where it happens.
    managed = path is None
    try:
        if managed:
            target = _default_checkpoint_dir(step)
            if _checkpoint_root().is_symlink() or target.is_symlink():
                # Never hand back a destination that leads outside the run: save into a fresh
                # directory of the run instead, never enrolled for deletion.
                print(
                    f"[tamarind] {target} or its parent is a symlink; saving this checkpoint elsewhere in the run",
                    file=sys.stderr,
                )
                target = Path(tempfile.mkdtemp(prefix="checkpoint-", dir=run_dir()))
                enroll = False
            elif target.exists() and not any(p == target for p, _ in _managed):
                # Left by an earlier process (a second local run, a restarted job): saving into it
                # would mix its files with the new weights, and it is not ours to delete. Use a
                # fresh directory beside it, which this run owns.
                target = Path(tempfile.mkdtemp(prefix=f"{target.name}-", dir=_checkpoint_root()))
                enroll = True
            else:
                enroll = True
        else:
            target = Path(path)  # type: ignore[arg-type]
            if not target.is_absolute():
                target = run_dir() / target
            target = target.resolve()
            enroll = False
    except Exception as exc:  # noqa: BLE001 - checkpoint recording must never end a training run
        print(f"[tamarind] could not resolve the checkpoint directory: {exc}", file=sys.stderr)
        return Path(path) if path is not None else Path(CHECKPOINTS_DIRNAME)
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
    recorded = _append_line(records, record)
    # Pruning only follows what the platform will see: a checkpoint whose record was not written
    # cannot be chosen at registration, so it must not count as the best and push a recorded one out.
    if managed and recorded:
        try:
            objective = _objective()
            if enroll and target.is_dir() and _inside_root(target):
                _prune(target, objective)
                _managed = [(p, sc) for p, sc in _managed if p != target]
                _managed.append((target, _score(metrics, objective)))
        except Exception as exc:  # noqa: BLE001
            print(f"[tamarind] could not tidy old checkpoints: {exc}", file=sys.stderr)
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
