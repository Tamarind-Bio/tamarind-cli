"""Fast local validation for Custom Tool source folders."""

from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path
import re
from typing import Any


GPU_TYPES = frozenset({"None", "T4", "L4", "L40S", "A10", "A100"})
MEMORY_OPTIONS = frozenset({"8Gi", "12Gi", "24Gi", "32Gi", "48Gi", "64Gi", "90Gi", "96Gi", "180Gi"})
INPUT_TYPES = frozenset(
    {"file", "pdb", "sdf", "smiles", "dropdown", "text", "number", "sequence", "boolean"}
)
_INPUT_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")
_NETWORK_PATTERN = re.compile(
    r"\b(?:curl|wget)\b\s+https?://|\b(?:requests|httpx)\.(?:get|post)\s*\(|\burllib\.request\.urlopen\s*\(",
    re.IGNORECASE,
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
    root = Path(folder).expanduser()
    errors: list[ValidationProblem] = []
    warnings: list[ValidationProblem] = []

    def error(code: str, path: str, message: str) -> None:
        errors.append(ValidationProblem(code=code, path=path, message=message))

    def warning(code: str, path: str, message: str) -> None:
        warnings.append(ValidationProblem(code=code, path=path, message=message))

    if not root.is_dir():
        error("folder_not_found", ".", f"Source folder does not exist: {root}")
        return ValidationReport(tuple(errors), tuple(warnings))

    for required in ("config.json", "Dockerfile"):
        if not (root / required).is_file():
            error("required_file_missing", required, f"{required} is required")

    if not (root / "run.sh").is_file():
        warning(
            "run_script_missing",
            "run.sh",
            "run.sh is recommended because the Custom Tool runtime invokes it directly",
        )

    config_path = root / "config.json"
    if config_path.is_file():
        try:
            value = json.loads(config_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            error("invalid_json", "config.json", f"config.json is not valid JSON: {exc}")
        else:
            if not isinstance(value, dict):
                error("invalid_config", "config.json", "config.json must contain a JSON object")
            else:
                _validate_config(value, error)

    for candidate in (root / "run.sh", *sorted(root.glob("*.py"))):
        if not candidate.is_file() or candidate.is_symlink():
            continue
        try:
            text = candidate.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
        if _NETWORK_PATTERN.search(text):
            warning(
                "runtime_network_access",
                candidate.relative_to(root).as_posix(),
                "Runtime network access is blocked; bake dependencies into the image or use platform inputs",
            )

    return ValidationReport(tuple(errors), tuple(warnings))


def _validate_config(value: dict[str, Any], error: Any) -> None:
    display_name = value.get("displayName")
    if not isinstance(display_name, str) or not display_name.strip():
        error(
            "invalid_display_name",
            "config.json.displayName",
            "displayName must be a non-empty string",
        )

    gpu_type = value.get("gpuType", "None")
    if not isinstance(gpu_type, str) or gpu_type not in GPU_TYPES:
        error(
            "invalid_gpu_type", "config.json.gpuType", f"gpuType must be one of {sorted(GPU_TYPES)}"
        )

    memory = value.get("memory", "8Gi")
    if not isinstance(memory, str) or memory not in MEMORY_OPTIONS:
        error(
            "invalid_memory",
            "config.json.memory",
            f"memory must be one of {sorted(MEMORY_OPTIONS)}",
        )

    cpu = value.get("cpu", 1)
    if isinstance(cpu, bool) or not isinstance(cpu, int) or not 1 <= cpu <= 8:
        error("invalid_cpu", "config.json.cpu", "cpu must be an integer from 1 through 8")

    inputs = value.get("inputs")
    if not isinstance(inputs, list):
        error("invalid_inputs", "config.json.inputs", "inputs must be an array")
        return

    names: set[str] = set()
    batching: list[str] = []
    for index, item in enumerate(inputs):
        path = f"config.json.inputs[{index}]"
        if not isinstance(item, dict):
            error("invalid_input", path, "each input must be an object")
            continue
        name = item.get("name")
        if not isinstance(name, str) or not _INPUT_NAME.fullmatch(name):
            error("invalid_input_name", f"{path}.name", "input name must be a valid identifier")
        elif name in names:
            error("duplicate_input_name", f"{path}.name", f"input name {name!r} is duplicated")
        else:
            names.add(name)

        kind = item.get("type")
        if not isinstance(kind, str) or kind not in INPUT_TYPES:
            error(
                "invalid_input_type",
                f"{path}.type",
                f"input type must be one of {sorted(INPUT_TYPES)}",
            )
            continue
        if kind == "dropdown":
            options = item.get("options")
            if (
                not isinstance(options, list)
                or not options
                or not all(isinstance(option, str) for option in options)
            ):
                error(
                    "invalid_dropdown_options",
                    f"{path}.options",
                    "dropdown options must be a non-empty string array",
                )
            elif "default" in item and item["default"] not in options:
                error(
                    "invalid_default",
                    f"{path}.default",
                    "dropdown default must be one of its options",
                )
        if kind == "number":
            _validate_number_input(item, path, error)
        elif "default" in item:
            expected = bool if kind == "boolean" else str
            default = item["default"]
            if default is not None and not isinstance(default, expected):
                error("invalid_default", f"{path}.default", f"{kind} default has the wrong type")

        design_batching = item.get("designBatching", False)
        if not isinstance(design_batching, bool):
            error(
                "invalid_design_batching",
                f"{path}.designBatching",
                "designBatching must be a boolean",
            )
        elif design_batching:
            batching.append(str(name))
            if kind != "number":
                error(
                    "invalid_design_batching",
                    f"{path}.designBatching",
                    "designBatching is only valid on a number input",
                )
            designs_per_batch = item.get("designsPerBatch")
            if (
                isinstance(designs_per_batch, bool)
                or not isinstance(designs_per_batch, int)
                or designs_per_batch < 1
            ):
                error(
                    "invalid_design_batching",
                    f"{path}.designsPerBatch",
                    "designsPerBatch must be an integer of at least 1",
                )

    if len(batching) > 1:
        error(
            "invalid_design_batching",
            "config.json.inputs",
            "at most one input may enable designBatching",
        )

    outputs = value.get("producedOutputs", [])
    if not isinstance(outputs, list):
        error("invalid_outputs", "config.json.producedOutputs", "producedOutputs must be an array")
    else:
        primary: list[dict[str, Any]] = []
        for index, item in enumerate(outputs):
            if not isinstance(item, dict):
                error(
                    "invalid_output",
                    f"config.json.producedOutputs[{index}]",
                    "each produced output must be an object",
                )
                continue
            flag = item.get("primary", False)
            if not isinstance(flag, bool):
                error(
                    "invalid_output_primary",
                    f"config.json.producedOutputs[{index}].primary",
                    "primary must be a boolean",
                )
            elif item.get("type") == "csv" and flag:
                primary.append(item)
        if len(primary) > 1:
            error(
                "multiple_primary_outputs",
                "config.json.producedOutputs",
                "at most one CSV output may be primary",
            )


def _validate_number_input(item: dict[str, Any], path: str, error: Any) -> None:
    values: dict[str, int | float] = {}
    for field in ("lowerBound", "upperBound", "default"):
        if field not in item:
            continue
        value = item[field]
        normalized = _finite_number(value)
        if normalized is None:
            error("invalid_number", f"{path}.{field}", f"{field} must be a finite number")
        else:
            values[field] = normalized
    lower = values.get("lowerBound")
    upper = values.get("upperBound")
    default = values.get("default")
    if lower is not None and upper is not None and lower > upper:
        error("invalid_number_bounds", path, "lowerBound cannot exceed upperBound")
    if default is not None and lower is not None and default < lower:
        error("invalid_default", f"{path}.default", "default is below lowerBound")
    if default is not None and upper is not None and default > upper:
        error("invalid_default", f"{path}.default", "default is above upperBound")


def _finite_number(value: object) -> int | float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    try:
        normalized = float(value)
    except (OverflowError, ValueError):
        return None
    return value if math.isfinite(normalized) else None
