from __future__ import annotations

from io import BytesIO
import json
import os
from pathlib import Path
import subprocess
import zipfile

import pytest

from tamarind.custom_tools import packaging, validation
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


@pytest.mark.parametrize("metadata_name", [".git", ".GIT", ".Hg", ".sVn"])
@pytest.mark.parametrize("is_directory", [False, True])
def test_archive_excludes_vcs_metadata_independent_of_case_and_form(
    tmp_path: Path,
    metadata_name: str,
    is_directory: bool,
) -> None:
    _valid_source(tmp_path)
    metadata = tmp_path / metadata_name
    if is_directory:
        metadata.mkdir()
        (metadata / "config").write_text("secret")
    else:
        metadata.write_text("gitdir: ../metadata\n")

    with zipfile.ZipFile(BytesIO(build_archive(tmp_path).data)) as archive:
        assert not any(
            name.casefold().startswith(metadata_name.casefold()) for name in archive.namelist()
        )


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


def test_archive_rejects_same_metadata_content_rewrite(tmp_path: Path) -> None:
    _valid_source(tmp_path)
    tree = packaging.inspect_source_tree(tmp_path)
    main = tmp_path / "main.py"
    metadata = main.stat()
    main.write_text("print('no')\n")
    os.utime(main, ns=(metadata.st_atime_ns, metadata.st_mtime_ns))

    with pytest.raises(CustomToolUploadError, match="contents changed"):
        packaging.build_source_tree_archive(tree)


def test_source_inspection_translates_unresolvable_home_paths(monkeypatch) -> None:
    def fail_expansion(_path: Path) -> Path:
        raise RuntimeError("cannot determine home")

    monkeypatch.setattr(Path, "expanduser", fail_expansion)

    with pytest.raises(CustomToolUploadError, match="Cannot resolve"):
        packaging.inspect_source_tree("~missing-tamarind-user/source")


def test_content_reader_translates_midstream_source_read_failures(tmp_path: Path) -> None:
    class FailingSource:
        def read(self, size: int = -1) -> bytes:
            raise OSError("simulated I/O failure")

    reader = packaging._ContentReader(FailingSource(), tmp_path / "source.py")  # type: ignore[arg-type]
    with pytest.raises(CustomToolUploadError, match="cannot be read"):
        reader.read()


def test_inspection_rejects_directory_traversal_errors(tmp_path: Path, monkeypatch) -> None:
    _valid_source(tmp_path)

    def failing_scan(_root):
        raise PermissionError("directory is unreadable")

    monkeypatch.setattr(packaging.os, "scandir", failing_scan)

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

    real_scan = packaging._scan_directory

    def replaced_scan(path: Path, *, max_entries: int):
        result = real_scan(path, max_entries=max_entries)
        if path == tmp_path:
            nested.rmdir()
            nested.symlink_to(outside, target_is_directory=True)
        return result

    monkeypatch.setattr(packaging, "_scan_directory", replaced_scan)

    with pytest.raises(CustomToolUploadError, match="symlinks or junctions"):
        packaging.inspect_source_tree(tmp_path)


def test_inspection_bounds_retained_manifest_entries(tmp_path: Path, monkeypatch) -> None:
    _valid_source(tmp_path)
    monkeypatch.setattr(packaging, "_MAX_SOURCE_ENTRIES", 3)

    with pytest.raises(CustomToolUploadError, match="3-entry inspection limit"):
        packaging.inspect_source_tree(tmp_path)


def test_archive_rechecks_manifest_entry_budget(tmp_path: Path, monkeypatch) -> None:
    _valid_source(tmp_path)
    tree = packaging.inspect_source_tree(tmp_path)
    monkeypatch.setattr(packaging, "_MAX_SOURCE_ENTRIES", 3)

    with pytest.raises(CustomToolUploadError, match="3-entry inspection limit"):
        packaging.build_source_tree_archive(tree)


def test_inspection_traverses_deep_trees_iteratively(tmp_path: Path, monkeypatch) -> None:
    depth = 1_500

    def simulated_scan(path: Path, *, max_entries: int):
        assert max_entries > 0
        current_depth = len(path.parts) - len(tmp_path.parts)
        return ([path / "d"], []) if current_depth < depth else ([], [])

    monkeypatch.setattr(packaging, "_scan_directory", simulated_scan)
    monkeypatch.setattr(packaging, "_verify_directory", lambda _root, _path: None)

    tree = packaging.inspect_source_tree(tmp_path)

    assert len(tree.empty_directories[0].split("/")) == depth


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


def test_validation_rejects_unreadable_retained_files(tmp_path: Path, monkeypatch) -> None:
    _valid_source(tmp_path)
    unreadable = tmp_path / "weights.bin"
    unreadable.write_bytes(b"weights")
    real_open = packaging.os.open

    def guarded_open(path, flags, *args):
        if Path(path) == unreadable:
            raise PermissionError("unreadable")
        return real_open(path, flags, *args)

    monkeypatch.setattr(packaging.os, "open", guarded_open)

    report = validate_folder(tmp_path)

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


def test_validation_leaves_config_semantics_to_the_server(tmp_path: Path) -> None:
    (tmp_path / "Dockerfile").write_text("FROM python:3.12-slim\n")
    (tmp_path / "run.sh").write_text("#!/bin/sh\ncurl https://example.com/model.bin\n")
    (tmp_path / "config.json").write_text(
        json.dumps(
            {
                "gpuType": "quantum",
                "inputs": "the server owns this evolving contract",
                "usesMsa": {"future": "shape"},
            }
        )
    )

    report = validate_folder(tmp_path)

    assert report.valid
    assert {problem.code for problem in report.warnings} == {"runtime_network_access"}


def test_validation_accepts_an_absent_config_file(tmp_path: Path) -> None:
    _valid_source(tmp_path)
    (tmp_path / "config.json").unlink()

    report = validate_folder(tmp_path)

    assert report.valid


def test_validation_rejects_malformed_config_json(tmp_path: Path) -> None:
    _valid_source(tmp_path)
    (tmp_path / "config.json").write_text("{")

    report = validate_folder(tmp_path)

    assert [(problem.code, problem.path) for problem in report.errors] == [
        ("invalid_json", "config.json")
    ]


@pytest.mark.parametrize("constant", ["NaN", "Infinity", "-Infinity"])
def test_validation_rejects_non_standard_json_constants(
    tmp_path: Path,
    constant: str,
) -> None:
    _valid_source(tmp_path)
    (tmp_path / "config.json").write_text('{"value":' + constant + "}")

    report = validate_folder(tmp_path)

    assert [(problem.code, problem.path) for problem in report.errors] == [
        ("invalid_json", "config.json")
    ]


def test_validation_rejects_duplicate_json_object_members(tmp_path: Path) -> None:
    _valid_source(tmp_path)
    (tmp_path / "config.json").write_text(
        '{"inputs": [], "nested": {"value": "first", "value": "second"}}'
    )

    report = validate_folder(tmp_path)

    assert [(problem.code, problem.path) for problem in report.errors] == [
        ("invalid_json", "config.json")
    ]


def test_validation_rejects_non_object_config_json(tmp_path: Path) -> None:
    _valid_source(tmp_path)
    (tmp_path / "config.json").write_text("[]")

    report = validate_folder(tmp_path)

    assert [(problem.code, problem.path) for problem in report.errors] == [
        ("invalid_config", "config.json")
    ]


def test_validation_bounds_config_json_before_parsing(tmp_path: Path, monkeypatch) -> None:
    _valid_source(tmp_path)
    monkeypatch.setattr(validation, "_MAX_CONFIG_BYTES", 16)

    report = validate_folder(tmp_path)

    assert [(problem.code, problem.path) for problem in report.errors] == [
        ("config_too_large", "config.json")
    ]


def test_validation_translates_parser_recursion(tmp_path: Path, monkeypatch) -> None:
    _valid_source(tmp_path)

    def raise_recursion(_raw: str, **_kwargs: object) -> object:
        raise RecursionError("excessive nesting")

    monkeypatch.setattr(validation.json, "loads", raise_recursion)

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
