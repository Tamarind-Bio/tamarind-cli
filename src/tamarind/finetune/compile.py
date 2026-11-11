"""Read the decorators out of a source folder and write the `finetune` block of config.json.

The source is parsed, never imported: the user's dependencies only exist inside the image, and
the block is needed before the image is built. So every decorator argument has to be a literal.
A computed value (`gpu=os.environ["GPU"]`) is refused with the file and line.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any, Iterable

from tamarind.finetune import spec as _spec

DECORATOR_KINDS = ("training_run", "predictor", "evaluator", "splitter")
SKIPPED_DIRS = {"__pycache__", "node_modules", "venv", ".venv", "site-packages", "build", "dist"}
MAX_SOURCE_BYTES = 2 * 1024 * 1024


class FinetuneCompileError(ValueError):
    def __init__(self, path: str, lineno: int | None, message: str) -> None:
        where = f"{path}:{lineno}" if lineno else path
        super().__init__(f"{where}: {message}")
        self.path = path
        self.lineno = lineno
        self.reason = message


@dataclass
class _Found:
    kind: str
    path: str
    name: str
    lineno: int
    kwargs: dict[str, Any] = field(default_factory=dict)

    @property
    def reference(self) -> str:
        return f"{self.path}:{self.name}"


@dataclass(frozen=True)
class CompiledFinetune:
    """What the decorators say. `block` is config.json's `finetune`; `resources` are top-level keys."""

    block: dict[str, Any]
    resources: dict[str, Any]
    sources: tuple[str, ...]


@dataclass(frozen=True)
class SourceText:
    relative: str
    text: str


def _is_tamarind_module(tree: ast.Module) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import) and any(
            a.name.split(".")[0] == "tamarind" for a in node.names
        ):
            return True
        if isinstance(node, ast.ImportFrom) and (node.module or "").split(".")[0] == "tamarind":
            return True
    return False


def _terminal_name(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _decorator_kind(decorator: ast.expr) -> tuple[str, ast.Call | None] | None:
    target = decorator.func if isinstance(decorator, ast.Call) else decorator
    name = _terminal_name(target)
    if name in DECORATOR_KINDS:
        return name, decorator if isinstance(decorator, ast.Call) else None
    return None


class _Literal:
    """Evaluate a decorator argument: literals plus the spec helpers with literal arguments."""

    def __init__(self, path: str) -> None:
        self.path = path

    def fail(self, node: ast.AST, message: str) -> FinetuneCompileError:
        return FinetuneCompileError(self.path, getattr(node, "lineno", None), message)

    def value(self, node: ast.expr) -> Any:
        if isinstance(node, ast.Call):
            helper = _spec.SPEC_HELPERS.get(_terminal_name(node.func) or "")
            if helper is None:
                raise self.fail(
                    node, "decorator arguments must be literals or tm.Float/Int/Str/Bool/Choice"
                )
            args = [self.value(a) for a in node.args]
            kwargs = {k.arg: self.value(k.value) for k in node.keywords if k.arg}
            if any(k.arg is None for k in node.keywords):
                raise self.fail(node, "**kwargs is not a literal")
            try:
                return helper(*args, **kwargs)
            except (TypeError, _spec.FinetuneSpecError) as exc:
                raise self.fail(node, str(exc)) from None
        if isinstance(node, ast.Dict):
            out: dict[Any, Any] = {}
            for key, val in zip(node.keys, node.values):
                if key is None:
                    raise self.fail(node, "**mapping is not a literal")
                out[self.value(key)] = self.value(val)
            return out
        if isinstance(node, (ast.List, ast.Tuple)):
            items = [self.value(e) for e in node.elts]
            return tuple(items) if isinstance(node, ast.Tuple) else items
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            inner = self.value(node.operand)
            if isinstance(inner, (int, float)) and not isinstance(inner, bool):
                return -inner
            raise self.fail(node, "decorator arguments must be literals")
        if isinstance(node, ast.Constant):
            return node.value
        raise self.fail(
            node,
            "decorator arguments must be literals (the source is read without importing it, "
            "because the config is needed before the image exists)",
        )


def _collect(sources: Iterable[SourceText]) -> list[_Found]:
    found: list[_Found] = []
    for source in sources:
        try:
            tree = ast.parse(source.text, filename=source.relative)
        except SyntaxError as exc:
            raise FinetuneCompileError(
                source.relative, exc.lineno, f"syntax error: {exc.msg}"
            ) from None
        if not _is_tamarind_module(tree):
            continue
        literal = _Literal(source.relative)
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            for decorator in node.decorator_list:
                matched = _decorator_kind(decorator)
                if matched is None:
                    continue
                kind, call = matched
                kwargs: dict[str, Any] = {}
                if call is not None:
                    if call.args:
                        raise literal.fail(call, f"@tm.{kind} takes keyword arguments only")
                    for keyword in call.keywords:
                        if keyword.arg is None:
                            raise literal.fail(call, "**kwargs is not a literal")
                        kwargs[keyword.arg] = literal.value(keyword.value)
                if kind == "predictor" and not isinstance(node, ast.ClassDef):
                    raise literal.fail(
                        node, "@tm.predictor goes on a class with load() and predict()"
                    )
                if kind != "predictor" and isinstance(node, ast.ClassDef):
                    raise literal.fail(node, f"@tm.{kind} goes on a function")
                found.append(_Found(kind, source.relative, node.name, node.lineno, kwargs))
    return found


def compile_sources(sources: Iterable[SourceText]) -> CompiledFinetune | None:
    """The finetune block the decorators in `sources` describe, or None when there are none."""
    found = _collect(sources)
    if not found:
        return None
    by_kind: dict[str, list[_Found]] = {}
    for item in found:
        by_kind.setdefault(item.kind, []).append(item)
    for kind, items in by_kind.items():
        if len(items) > 1:
            places = ", ".join(f"{i.path}:{i.lineno}" for i in items)
            raise FinetuneCompileError(
                items[1].path, items[1].lineno, f"more than one @tm.{kind}: {places}"
            )
    run = by_kind.get("training_run")
    if not run:
        other = found[0]
        raise FinetuneCompileError(
            other.path,
            other.lineno,
            f"@tm.{other.kind} needs a @tm.training_run in the same source folder",
        )
    entry = run[0]
    try:
        block = {
            "entrypoint": entry.reference,
            **_spec.training_run_block(**_kw(entry, _TRAINING_RUN_KEYS)),
        }
        resources = {
            key: entry.kwargs[arg]
            for arg, key in (("gpu", "gpuType"), ("memory", "memory"), ("cpu", "cpu"))
            if arg in entry.kwargs
        }
        if pred := by_kind.get("predictor"):
            block["predictor"] = {
                "class": pred[0].reference,
                **_spec.predictor_block(**_kw(pred[0], _PREDICTOR_KEYS)),
            }
        if ev := by_kind.get("evaluator"):
            _spec.evaluator_block(**_kw(ev[0], _EVALUATOR_KEYS))  # shape check only
            block["evaluator"] = ev[0].reference
        if sp := by_kind.get("splitter"):
            if sp[0].kwargs:
                raise FinetuneCompileError(
                    sp[0].path, sp[0].lineno, "@tm.splitter takes no arguments"
                )
            block["splitter"] = sp[0].reference
    except (TypeError, _spec.FinetuneSpecError) as exc:
        raise FinetuneCompileError(entry.path, entry.lineno, str(exc)) from None
    return CompiledFinetune(
        block=block, resources=resources, sources=tuple(sorted({f.path for f in found}))
    )


_TRAINING_RUN_KEYS = ("timeout_hours", "hyperparameters", "objective", "artifact")
_PREDICTOR_KEYS = ("gpu", "memory", "inputs", "outputs")
_EVALUATOR_KEYS = ("metrics", "aggregate")


def _kw(item: _Found, allowed: tuple[str, ...]) -> dict[str, Any]:
    extra = (
        set(item.kwargs) - set(allowed) - {"gpu", "memory", "cpu"}
        if item.kind == "training_run"
        else set(item.kwargs) - set(allowed)
    )
    if extra:
        raise FinetuneCompileError(
            item.path, item.lineno, f"@tm.{item.kind} got unknown arguments {sorted(extra)}"
        )
    return {k: v for k, v in item.kwargs.items() if k in allowed}


def iter_python_sources(folder: str | Path) -> list[SourceText]:
    """Every .py file under `folder`, as (relative path, text), skipping environments and caches."""
    root = Path(folder)
    out: list[SourceText] = []
    for path in sorted(root.rglob("*.py")):
        parts = path.relative_to(root).parts
        if any(p.startswith(".") or p in SKIPPED_DIRS for p in parts[:-1]) or path.is_symlink():
            continue
        if path.stat().st_size > MAX_SOURCE_BYTES:
            continue
        out.append(SourceText(path.relative_to(root).as_posix(), path.read_text(encoding="utf-8")))
    return out


def compile_folder(folder: str | Path) -> CompiledFinetune | None:
    return compile_sources(iter_python_sources(folder))


def apply_to_config(config: dict[str, Any], compiled: CompiledFinetune | None) -> dict[str, Any]:
    """`config` with the compiled block written in. Resources set by the decorator win; others stay."""
    updated = dict(config)
    if compiled is None:
        return updated
    updated["finetune"] = compiled.block
    updated.update(compiled.resources)
    if "timeoutHours" in compiled.block:
        # The block's spelling; a disagreeing maxRuntimeSeconds would be refused by the backend.
        updated.pop("maxRuntimeSeconds", None)
    return updated


@dataclass(frozen=True)
class SyncResult:
    compiled: CompiledFinetune | None
    changed: bool
    config_text: str


def sync_config_json(folder: str | Path, *, write: bool) -> SyncResult:
    """Compile the decorators and merge the block into `<folder>/config.json`.

    With `write`, the file is rewritten only when the block changed, keeping the rest of the
    document as it was.
    """
    root = Path(folder)
    config_path = root / "config.json"
    compiled = compile_folder(root)
    if not config_path.is_file():
        if compiled is None:
            return SyncResult(None, False, "")
        raise FinetuneCompileError(
            "config.json",
            None,
            "config.json is required; the decorators only fill its finetune block",
        )
    text = config_path.read_text(encoding="utf-8")
    try:
        config = json.loads(text)
    except ValueError as exc:
        raise FinetuneCompileError("config.json", None, f"not valid JSON: {exc}") from None
    if not isinstance(config, dict):
        raise FinetuneCompileError("config.json", None, "must contain a JSON object")
    if compiled is None:
        return SyncResult(None, False, text)
    updated = apply_to_config(config, compiled)
    changed = updated != config
    new_text = json.dumps(updated, indent=2) + "\n" if changed else text
    if changed and write:
        config_path.write_text(new_text, encoding="utf-8")
    return SyncResult(compiled, changed, new_text)
