from __future__ import annotations

from io import BytesIO
import json
import os
from pathlib import Path
import subprocess
import zipfile

import pytest

from tamarind.custom_tools import packaging
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


@pytest.mark.parametrize("metadata_name", [".git", ".hg", ".svn"])
def test_archive_excludes_file_form_vcs_metadata(tmp_path: Path, metadata_name: str) -> None:
    _valid_source(tmp_path)
    (tmp_path / metadata_name).write_text("gitdir: ../metadata\n")

    with zipfile.ZipFile(BytesIO(build_archive(tmp_path).data)) as archive:
        assert metadata_name not in archive.namelist()


def test_archive_preserves_explicit_build_inputs_and_empty_directories(tmp_path: Path) -> None:
    _valid_source(tmp_path)
    (tmp_path / "dist").mkdir()
    (tmp_path / "dist" / "model.whl").write_bytes(b"wheel")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "runtime.js").write_text("export {}\n")
    (tmp_path / "empty-cache").mkdir()

    with zipfile.ZipFile(BytesIO(build_archive(tmp_path).data)) as archive:
        names = archive.namelist()

    assert "dist/model.whl" in names
    assert "node_modules/runtime.js" in names
    assert "empty-cache/" in names
    assert "empty-cache/.gitkeep" in names


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


def test_archive_rejects_file_replaced_by_symlink_after_inspection(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _valid_source(tmp_path)
    inspected = packaging.inspect_source_tree(tmp_path)
    main = tmp_path / "main.py"
    main.unlink()
    main.symlink_to(tmp_path / "run.sh")
    monkeypatch.setattr(packaging, "inspect_source_tree", lambda _folder: inspected)

    with pytest.raises(CustomToolUploadError, match="changed after inspection"):
        build_archive(tmp_path)


def test_inspection_rejects_directory_traversal_errors(tmp_path: Path, monkeypatch) -> None:
    _valid_source(tmp_path)

    def failing_walk(_root, *, followlinks, onerror):
        assert followlinks is False
        onerror(PermissionError("directory is unreadable"))
        return ()

    monkeypatch.setattr(packaging.os, "walk", failing_walk)

    with pytest.raises(CustomToolUploadError, match="Cannot traverse"):
        packaging.inspect_source_tree(tmp_path)


def test_inspection_rejects_directory_replaced_by_link_during_descent(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _valid_source(tmp_path)
    nested = tmp_path / "nested"
    nested.mkdir()
    outside = tmp_path.parent / "outside"
    outside.mkdir()
    (outside / "secret.txt").write_text("secret")

    def replaced_walk(root, *, followlinks, onerror):
        assert followlinks is False
        assert onerror is not None
        filenames = [path.name for path in Path(root).iterdir() if path.is_file()]
        yield str(root), ["nested"], filenames
        nested.rmdir()
        nested.symlink_to(outside, target_is_directory=True)
        yield str(nested), [], ["secret.txt"]

    monkeypatch.setattr(packaging.os, "walk", replaced_walk)

    with pytest.raises(CustomToolUploadError, match="symlinks or junctions"):
        packaging.inspect_source_tree(tmp_path)


def test_validation_rejects_symlinked_source_root(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    _valid_source(source)
    linked_source = tmp_path / "linked-source"
    linked_source.symlink_to(source, target_is_directory=True)

    report = validate_folder(linked_source)

    assert not report.valid
    assert [(problem.code, problem.path) for problem in report.errors] == [
        ("invalid_source_tree", ".")
    ]


def test_validation_rejects_linked_descendants(tmp_path: Path) -> None:
    _valid_source(tmp_path)
    (tmp_path / "linked.py").symlink_to(tmp_path / "main.py")

    report = validate_folder(tmp_path)

    assert not report.valid
    assert [(problem.code, problem.path) for problem in report.errors] == [
        ("invalid_source_tree", ".")
    ]


def test_validation_requires_exact_runtime_filename_casing(tmp_path: Path) -> None:
    _valid_source(tmp_path)
    for exact, alternate in (
        ("config.json", "CONFIG.JSON"),
        ("Dockerfile", "dockerfile"),
        ("run.sh", "RUN.SH"),
    ):
        contents = (tmp_path / exact).read_bytes()
        (tmp_path / exact).unlink()
        (tmp_path / alternate).write_bytes(contents)

    report = validate_folder(tmp_path)

    assert [(problem.code, problem.path) for problem in report.errors] == [
        ("required_file_missing", "config.json"),
        ("required_file_missing", "Dockerfile"),
    ]
    assert ("run_script_missing", "run.sh") in [
        (problem.code, problem.path) for problem in report.warnings
    ]


def test_archive_streams_files_without_reading_each_one_into_memory(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _valid_source(tmp_path)

    def fail_read_bytes(_path: Path) -> bytes:
        raise AssertionError("archive construction must stream source files")

    monkeypatch.setattr(Path, "read_bytes", fail_read_bytes)

    archive = build_archive(tmp_path)

    assert archive.size > 0


def test_archive_aborts_while_compressed_output_crosses_upload_limit(tmp_path: Path) -> None:
    _valid_source(tmp_path)
    (tmp_path / "weights.bin").write_bytes(os.urandom(64 * 1024))

    with pytest.raises(CustomToolUploadError, match="1024-byte upload limit"):
        build_archive(tmp_path, max_bytes=1024)


@pytest.mark.skipif(os.name != "nt", reason="NTFS junctions are Windows-specific")
def test_archive_rejects_windows_junctions(tmp_path: Path) -> None:
    _valid_source(tmp_path)
    outside = tmp_path.parent / f"{tmp_path.name}-outside"
    outside.mkdir()
    (outside / "secret.txt").write_text("secret")
    subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(tmp_path / "junction"), str(outside)],
        check=True,
        capture_output=True,
    )

    with pytest.raises(CustomToolUploadError, match="junctions"):
        build_archive(tmp_path)
    (tmp_path / "junction").rmdir()


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


def test_validation_preserves_integer_precision_for_numeric_bounds(tmp_path: Path) -> None:
    _valid_source(tmp_path)
    (tmp_path / "config.json").write_text(
        json.dumps(
            {
                "displayName": "Example",
                "inputs": [
                    {
                        "name": "count",
                        "type": "number",
                        "lowerBound": 9_007_199_254_740_993,
                        "upperBound": 9_007_199_254_740_992,
                    }
                ],
            }
        )
    )

    report = validate_folder(tmp_path)

    assert "invalid_number_bounds" in {problem.code for problem in report.errors}


@pytest.mark.parametrize("constant", ["NaN", "Infinity", "-Infinity"])
def test_validation_rejects_non_standard_json_constants(tmp_path: Path, constant: str) -> None:
    _valid_source(tmp_path)
    (tmp_path / "config.json").write_text(
        '{"displayName":"Example","inputs":[],"extension":' + constant + "}"
    )

    report = validate_folder(tmp_path)

    assert [(problem.code, problem.path) for problem in report.errors] == [
        ("invalid_json", "config.json")
    ]


def test_validation_rejects_duplicate_json_members_recursively(tmp_path: Path) -> None:
    _valid_source(tmp_path)
    (tmp_path / "config.json").write_text(
        '{"displayName":"Example","inputs":[{"name":"x","name":"y","type":"text"}]}'
    )

    report = validate_folder(tmp_path)

    assert [(problem.code, problem.path) for problem in report.errors] == [
        ("invalid_json", "config.json")
    ]


def test_validation_skips_warning_only_network_scan_for_large_runtime_file(tmp_path: Path) -> None:
    _valid_source(tmp_path)
    (tmp_path / "run.sh").write_text(
        "#!/bin/sh\n" + ("# padding\n" * 120_000) + "curl https://example.com/model.bin\n"
    )

    report = validate_folder(tmp_path)

    assert report.valid
    assert report.warnings == ()


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


@pytest.mark.parametrize("value", ["false", 0, 1, None])
def test_validation_rejects_non_boolean_output_primary(tmp_path: Path, value: object) -> None:
    _valid_source(tmp_path)
    (tmp_path / "config.json").write_text(
        json.dumps(
            {
                "displayName": "Example",
                "inputs": [],
                "producedOutputs": [{"type": "csv", "primary": value}],
            }
        )
    )

    report = validate_folder(tmp_path)

    assert not report.valid
    assert any(
        problem.path == "config.json.producedOutputs[0].primary"
        and problem.code == "invalid_output_primary"
        for problem in report.errors
    )


def test_validation_rejects_non_object_produced_outputs(tmp_path: Path) -> None:
    _valid_source(tmp_path)
    (tmp_path / "config.json").write_text(
        json.dumps({"displayName": "Example", "inputs": [], "producedOutputs": [42]})
    )

    report = validate_folder(tmp_path)

    assert not report.valid
    assert any(
        problem.path == "config.json.producedOutputs[0]" and problem.code == "invalid_output"
        for problem in report.errors
    )


@pytest.mark.parametrize("output", [{}, {"type": []}, {"type": "unsupported"}])
def test_validation_rejects_missing_or_unsupported_output_types(
    tmp_path: Path,
    output: object,
) -> None:
    _valid_source(tmp_path)
    (tmp_path / "config.json").write_text(
        json.dumps({"displayName": "Example", "inputs": [], "producedOutputs": [output]})
    )

    report = validate_folder(tmp_path)

    assert not report.valid
    assert any(
        problem.path == "config.json.producedOutputs[0].type"
        and problem.code == "invalid_output_type"
        for problem in report.errors
    )
