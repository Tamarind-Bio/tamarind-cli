"""Archive-local Custom Tool checks; the server owns config semantics."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from tamarind.custom_tools.packaging import (
    SourceTree,
    inspect_source_tree,
    validate_source_tree_manifest,
)
from tamarind.custom_tools.strict_json import load_strict_json
from tamarind.errors import CustomToolUploadError
from tamarind.finetune.compile import (
    FinetuneCompileError,
    SKIPPED_DIRS,
    MAX_SOURCE_BYTES,
    SourceText,
    compile_sources,
)


_NETWORK_PATTERN = re.compile(
    r"\b(?:curl|wget)\b[^\r\n;&|]*\bhttps?://|"
    r"\b(?:requests|httpx)\.(?:get|post)\s*\(|"
    r"\burllib\.request\.urlopen\s*\(",
    re.IGNORECASE,
)
_MAX_NETWORK_SCAN_BYTES = 1024 * 1024
_MAX_CONFIG_BYTES = 8 * 1024 * 1024


@dataclass(frozen=True)
class ValidationProblem:
    code: str
    path: str
    message: str


@dataclass(frozen=True)
class ValidationReport:
    errors: tuple[ValidationProblem, ...] = ()
    warnings: tuple[ValidationProblem, ...] = ()

    @property
    def valid(self) -> bool:
        return not self.errors


def validate_folder(folder: str | Path) -> ValidationReport:
    try:
        tree = inspect_source_tree(folder)
    except CustomToolUploadError as exc:
        return ValidationReport(
            errors=(ValidationProblem(code="invalid_source_tree", path=".", message=str(exc)),)
        )
    return validate_source_tree(tree)


def validate_source_tree(tree: SourceTree) -> ValidationReport:
    """Check only facts available from the exact archive snapshot."""
    try:
        validate_source_tree_manifest(tree)
    except CustomToolUploadError as exc:
        return ValidationReport(
            errors=(ValidationProblem(code="invalid_source_tree", path=".", message=str(exc)),)
        )
    errors: list[ValidationProblem] = []
    warnings: list[ValidationProblem] = []

    def error(code: str, path: str, message: str) -> None:
        errors.append(ValidationProblem(code=code, path=path, message=message))

    def warning(code: str, path: str, message: str) -> None:
        warnings.append(ValidationProblem(code=code, path=path, message=message))

    files = {source_file.relative: source_file for source_file in tree.files}
    if "Dockerfile" not in files:
        error("required_file_missing", "Dockerfile", "Dockerfile is required")

    if "run.sh" not in files:
        warning(
            "run_script_missing",
            "run.sh",
            "run.sh is recommended because the Custom Tool runtime invokes it directly",
        )

    config_file = files.get("config.json")
    if config_file is None:
        error(
            "required_file_missing", "config.json", "config.json is required to build a Custom Tool"
        )
    else:
        if config_file.size > _MAX_CONFIG_BYTES:
            error(
                "config_too_large",
                "config.json",
                f"config.json exceeds the {_MAX_CONFIG_BYTES}-byte local validation limit",
            )
        else:
            try:
                value = load_strict_json(config_file.read_text())
            except CustomToolUploadError as exc:
                error("invalid_source_tree", ".", str(exc))
                return ValidationReport(tuple(errors), tuple(warnings))
            except (OSError, UnicodeError, ValueError, RecursionError) as exc:
                error("invalid_json", "config.json", f"config.json is not valid JSON: {exc}")
            else:
                if not isinstance(value, dict):
                    error("invalid_config", "config.json", "config.json must contain a JSON object")
                else:
                    _check_finetune(tree, value, error, warning)

    runtime_files = [
        source_file
        for source_file in tree.files
        if source_file.relative == "run.sh"
        or ("/" not in source_file.relative and source_file.path.suffix == ".py")
    ]
    for candidate in runtime_files:
        if candidate.size > _MAX_NETWORK_SCAN_BYTES:
            continue
        try:
            text = candidate.read_text()
        except CustomToolUploadError as exc:
            error("invalid_source_tree", ".", str(exc))
            return ValidationReport(tuple(errors), tuple(warnings))
        except (OSError, UnicodeError):
            continue
        if _NETWORK_PATTERN.search(text):
            warning(
                "runtime_network_access",
                candidate.relative,
                "Runtime network access is blocked; bake dependencies into the image or use platform inputs",
            )

    return ValidationReport(tuple(errors), tuple(warnings))


def finetune_sources(tree: SourceTree) -> list[SourceText]:
    """The .py files of the archive the finetune compiler reads, in archive order."""
    out: list[SourceText] = []
    for source_file in tree.files:
        parts = source_file.relative.split("/")
        if not source_file.relative.endswith(".py") or source_file.size > MAX_SOURCE_BYTES:
            continue
        if any(part.startswith(".") or part in SKIPPED_DIRS for part in parts[:-1]):
            continue
        try:
            out.append(SourceText(source_file.relative, source_file.read_text()))
        except (CustomToolUploadError, OSError, UnicodeError):
            continue
    return out


def _check_finetune(tree: SourceTree, config: dict[str, object], error, warning) -> None:  # type: ignore[no-untyped-def]
    """The decorators in the source and the `finetune` block in config.json must agree."""
    try:
        compiled = compile_sources(finetune_sources(tree))
    except FinetuneCompileError as exc:
        error("finetune_decorator_invalid", exc.path, str(exc))
        return
    if compiled is None:
        return
    if config.get("finetune") != compiled.block:
        warning(
            "finetune_block_stale",
            "config.json",
            "config.json's finetune block does not match the @tm decorators in "
            + ", ".join(compiled.sources)
            + ". `tamarind custom-tools sync-finetune <folder>` rewrites it; build does so automatically.",
        )
