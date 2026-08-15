"""Deterministic Custom Tool source archives."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO
import os
from pathlib import Path
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
        ".tox",
        ".venv",
        "__pycache__",
        "build",
        "dist",
        "node_modules",
    }
)
EXCLUDED_FILES = frozenset({".DS_Store"})
EXCLUDED_SUFFIXES = frozenset({".pyc", ".pyo"})
_ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
_REGULAR_FILE_MODE = 0o100644


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

    files: list[tuple[str, Path]] = []
    for current, directories, filenames in os.walk(root, followlinks=False):
        current_path = Path(current)
        kept_directories: list[str] = []
        for name in sorted(directories):
            path = current_path / name
            if name in EXCLUDED_DIRECTORIES:
                continue
            if path.is_symlink():
                raise CustomToolUploadError(f"Source archives cannot contain symlinks: {path}")
            kept_directories.append(name)
        directories[:] = kept_directories

        for name in sorted(filenames):
            path = current_path / name
            if name in EXCLUDED_FILES or path.suffix in EXCLUDED_SUFFIXES:
                continue
            if path.is_symlink():
                raise CustomToolUploadError(f"Source archives cannot contain symlinks: {path}")
            relative = path.relative_to(root).as_posix()
            files.append((relative, path))

    output = BytesIO()
    with zipfile.ZipFile(
        output,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
        strict_timestamps=True,
    ) as archive:
        for relative, path in sorted(files):
            info = zipfile.ZipInfo(relative, date_time=_ZIP_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = _REGULAR_FILE_MODE << 16
            archive.writestr(info, path.read_bytes(), compresslevel=9)

    data = output.getvalue()
    return SourceArchive(data=data, digest=f"sha256:{sha256(data).hexdigest()}")
