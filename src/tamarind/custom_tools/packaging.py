"""Deterministic Custom Tool source archives."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO
import os
from pathlib import Path
import shutil
import stat
import zipfile

from tamarind.errors import CustomToolUploadError


EXCLUDED_DIRECTORIES = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        "__pycache__",
    }
)
EXCLUDED_FILES = frozenset({".DS_Store"})
EXCLUDED_SUFFIXES = frozenset({".pyc", ".pyo"})
_ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
_REGULAR_FILE_MODE = 0o100644
_EXECUTABLE_FILE_MODE = 0o100755
_DIRECTORY_MODE = 0o040755


@dataclass(frozen=True)
class SourceArchive:
    data: bytes
    digest: str

    @property
    def size(self) -> int:
        return len(self.data)


def build_archive(folder: str | Path) -> SourceArchive:
    """Package a folder into byte-for-byte reproducible ZIP content."""
    root = Path(folder).expanduser()
    if not root.is_dir():
        raise CustomToolUploadError(f"Custom Tool source folder does not exist: {root}")
    if _is_link_like(root):
        raise CustomToolUploadError(f"Source archives cannot contain symlinks or junctions: {root}")

    files: list[tuple[str, Path]] = []
    empty_directories: list[str] = []
    for current, directories, filenames in os.walk(root, followlinks=False):
        current_path = Path(current)
        kept_directories: list[str] = []
        for name in sorted(directories):
            path = current_path / name
            if name in EXCLUDED_DIRECTORIES:
                continue
            if _is_link_like(path):
                raise CustomToolUploadError(
                    f"Source archives cannot contain symlinks or junctions: {path}"
                )
            kept_directories.append(name)
        directories[:] = kept_directories

        kept_files: list[tuple[str, Path]] = []
        for name in sorted(filenames):
            path = current_path / name
            if name in EXCLUDED_FILES or path.suffix in EXCLUDED_SUFFIXES:
                continue
            if _is_link_like(path):
                raise CustomToolUploadError(
                    f"Source archives cannot contain symlinks or junctions: {path}"
                )
            relative = path.relative_to(root).as_posix()
            kept_files.append((relative, path))
        files.extend(kept_files)
        if current_path != root and not kept_directories and not kept_files:
            empty_directories.append(current_path.relative_to(root).as_posix())

    output = BytesIO()
    with zipfile.ZipFile(
        output,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
        strict_timestamps=True,
    ) as archive:
        entries: list[tuple[str, Path | None, int]] = []
        for relative in empty_directories:
            entries.append((f"{relative}/", None, _DIRECTORY_MODE))
            # Git cannot persist an empty tree. The marker keeps the directory
            # present when the backend commits the uploaded archive to Gitea.
            entries.append((f"{relative}/.gitkeep", None, _REGULAR_FILE_MODE))
        for relative, path in files:
            executable = relative == "run.sh" or bool(path.stat().st_mode & 0o111)
            mode = _EXECUTABLE_FILE_MODE if executable else _REGULAR_FILE_MODE
            entries.append((relative, path, mode))

        for relative, entry_path, mode in sorted(entries, key=lambda item: item[0]):
            info = zipfile.ZipInfo(relative, date_time=_ZIP_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = mode << 16
            if entry_path is None:
                archive.writestr(info, b"", compresslevel=9)
                continue
            with (
                entry_path.open("rb") as source,
                archive.open(info, "w", force_zip64=True) as destination,
            ):
                shutil.copyfileobj(source, destination, length=1024 * 1024)

    data = output.getvalue()
    return SourceArchive(data=data, digest=f"sha256:{sha256(data).hexdigest()}")


def _is_link_like(path: Path) -> bool:
    """Reject POSIX links and Windows reparse points such as junctions."""
    if path.is_symlink():
        return True
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    file_attributes = getattr(path.lstat(), "st_file_attributes", 0)
    return bool(reparse_flag and file_attributes & reparse_flag)
