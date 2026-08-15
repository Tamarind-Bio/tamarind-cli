from __future__ import annotations

from io import BytesIO
import json
from pathlib import Path
import zipfile

import pytest

from tamarind.custom_tools.packaging import build_archive
from tamarind.custom_tools.validation import validate_folder
from tamarind.errors import CustomToolUploadError


def _valid_source(root: Path) -> None:
    (root / "config.json").write_text(
        json.dumps(
            {
                "displayName": "Example",
                "inputs": [{"name": "count", "type": "number", "default": 2}],
                "producedOutputs": [{"type": "csv", "primary": True}],
            }
        )
    )
    (root / "Dockerfile").write_text("FROM python:3.12-slim\n")
    (root / "run.sh").write_text("#!/bin/sh\npython main.py\n")
    (root / "main.py").write_text("print('ok')\n")


def test_archive_is_deterministic_and_excludes_local_artifacts(tmp_path: Path) -> None:
    _valid_source(tmp_path)
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text("secret")
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__" / "main.pyc").write_bytes(b"cache")
    (tmp_path / ".DS_Store").write_bytes(b"metadata")

    first = build_archive(tmp_path)
    second = build_archive(tmp_path)

    assert first == second
    assert first.digest.startswith("sha256:")
    with zipfile.ZipFile(BytesIO(first.data)) as archive:
        assert archive.namelist() == ["Dockerfile", "config.json", "main.py", "run.sh"]
        assert all(info.date_time == (1980, 1, 1, 0, 0, 0) for info in archive.infolist())


def test_archive_makes_runtime_entrypoint_executable_on_every_platform(tmp_path: Path) -> None:
    _valid_source(tmp_path)

    with zipfile.ZipFile(BytesIO(build_archive(tmp_path).data)) as archive:
        modes = {info.filename: info.external_attr >> 16 for info in archive.infolist()}

    assert modes["run.sh"] == 0o100755
    assert modes["main.py"] == 0o100644


def test_archive_rejects_symlinks(tmp_path: Path) -> None:
    _valid_source(tmp_path)
    (tmp_path / "linked.py").symlink_to(tmp_path / "main.py")

    with pytest.raises(CustomToolUploadError, match="symlinks"):
        build_archive(tmp_path)


def test_validation_reports_config_errors_and_runtime_network_warning(tmp_path: Path) -> None:
    (tmp_path / "Dockerfile").write_text("FROM python:3.12-slim\n")
    (tmp_path / "run.sh").write_text("#!/bin/sh\ncurl https://example.com/model.bin\n")
    (tmp_path / "config.json").write_text(
        json.dumps(
            {
                "displayName": "Example",
                "gpuType": "quantum",
                "inputs": [
                    {"name": "mode", "type": "dropdown", "options": [], "default": "x"},
                    {"name": "count", "type": "number", "lowerBound": 5, "upperBound": 1},
                ],
            }
        )
    )

    report = validate_folder(tmp_path)

    assert not report.valid
    assert {problem.code for problem in report.errors} >= {
        "invalid_gpu_type",
        "invalid_dropdown_options",
        "invalid_number_bounds",
    }
    assert {problem.code for problem in report.warnings} == {"runtime_network_access"}


def test_validation_warns_when_run_script_is_missing(tmp_path: Path) -> None:
    _valid_source(tmp_path)
    (tmp_path / "run.sh").unlink()

    report = validate_folder(tmp_path)

    assert report.valid
    assert [problem.code for problem in report.warnings] == ["run_script_missing"]


def test_validation_contains_malformed_enum_and_oversized_number_values(tmp_path: Path) -> None:
    _valid_source(tmp_path)
    (tmp_path / "config.json").write_text(
        json.dumps(
            {
                "displayName": "Example",
                "gpuType": [],
                "memory": {},
                "inputs": [
                    {"name": "bad_type", "type": []},
                    {"name": "huge", "type": "number", "default": 10**1000},
                ],
            }
        )
    )

    report = validate_folder(tmp_path)

    assert {problem.code for problem in report.errors} >= {
        "invalid_gpu_type",
        "invalid_memory",
        "invalid_input_type",
        "invalid_number",
    }


@pytest.mark.parametrize("value", ["false", 0, 1, None])
def test_validation_rejects_non_boolean_design_batching(tmp_path: Path, value: object) -> None:
    _valid_source(tmp_path)
    (tmp_path / "config.json").write_text(
        json.dumps(
            {
                "displayName": "Example",
                "inputs": [
                    {
                        "name": "count",
                        "type": "number",
                        "designBatching": value,
                        "designsPerBatch": 2,
                    }
                ],
            }
        )
    )

    report = validate_folder(tmp_path)

    assert not report.valid
    assert any(
        problem.path == "config.json.inputs[0].designBatching"
        and problem.code == "invalid_design_batching"
        for problem in report.errors
    )
