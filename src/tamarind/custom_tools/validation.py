"""Archive-local Custom Tool checks; the server owns config semantics."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import NoReturn

from tamarind.custom_tools.packaging import SourceTree, inspect_source_tree
from tamarind.errors import CustomToolUploadError


_NETWORK_PATTERN = re.compile(
    r"\b(?:curl|wget)\b\s+https?://|\b(?:requests|httpx)\.(?:get|post)\s*\(|\burllib\.request\.urlopen\s*\(",
    re.IGNORECASE,
)
_MAX_NETWORK_SCAN_BYTES = 1024 * 1024
_MAX_CONFIG_BYTES = 8 * 1024 * 1024


def _reject_json_constant(value: str) -> NoReturn:
    raise ValueError(f"non-standard JSON constant {value!r}")


def _object_without_duplicate_members(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for name, member in pairs:
        if name in value:
            raise ValueError(f"duplicate JSON object member {name!r}")
        value[name] = member
    return value


def _load_strict_json(raw: str) -> object:
    return json.loads(
        raw,
        parse_constant=_reject_json_constant,
        object_pairs_hook=_object_without_duplicate_members,
    )


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
    if config_file is not None:
        if config_file.size > _MAX_CONFIG_BYTES:
            error(
                "config_too_large",
                "config.json",
                f"config.json exceeds the {_MAX_CONFIG_BYTES}-byte local validation limit",
            )
        else:
            try:
                value = _load_strict_json(config_file.read_text())
            except CustomToolUploadError as exc:
                error("invalid_source_tree", ".", str(exc))
                return ValidationReport(tuple(errors), tuple(warnings))
            except (OSError, UnicodeError, ValueError, RecursionError) as exc:
                error("invalid_json", "config.json", f"config.json is not valid JSON: {exc}")
            else:
                if not isinstance(value, dict):
                    error("invalid_config", "config.json", "config.json must contain a JSON object")

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
