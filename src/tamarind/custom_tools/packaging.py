"""Deterministic Custom Tool source archives."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from hashlib import sha256
import os
from pathlib import Path
import stat
from tempfile import SpooledTemporaryFile
from typing import BinaryIO, cast
import zipfile

from typing_extensions import Buffer

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
_EXCLUDED_DIRECTORY_NAMES = frozenset(name.casefold() for name in EXCLUDED_DIRECTORIES)
_EXCLUDED_FILE_NAMES = frozenset(name.casefold() for name in EXCLUDED_FILES)
_EXCLUDED_FILE_SUFFIXES = frozenset(suffix.casefold() for suffix in EXCLUDED_SUFFIXES)
_ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
_REGULAR_FILE_MODE = 0o100644
_EXECUTABLE_FILE_MODE = 0o100755
_DIRECTORY_MODE = 0o040755
_MAX_SOURCE_ENTRIES = 25_000
MAX_TOOL_SOURCE_BYTES = 5 * 1024 * 1024 * 1024
_ARCHIVE_MEMORY_BYTES = 8 * 1024 * 1024


class _CappedArchive:
    """A seekable ZIP target whose retained content cannot exceed the service cap."""

    def __init__(self, max_bytes: int | None) -> None:
        self._stream = SpooledTemporaryFile(max_size=_ARCHIVE_MEMORY_BYTES, mode="w+b")
        self._max_bytes = max_bytes

    def write(self, data: Buffer) -> int:
        data_size = memoryview(data).nbytes
        if self._max_bytes is not None and self.tell() + data_size > self._max_bytes:
            raise CustomToolUploadError(
                f"Source archive exceeds the {self._max_bytes}-byte upload limit"
            )
        return self._stream.write(data)

    def read(self, size: int = -1) -> bytes:
        return self._stream.read(size)

    def __iter__(self) -> "_CappedArchive":
        return self

    def __next__(self) -> bytes:
        chunk = self.read(1024 * 1024)
        if not chunk:
            raise StopIteration
        return chunk

    def seek(self, offset: int, whence: int = 0) -> int:
        return self._stream.seek(offset, whence)

    def tell(self) -> int:
        return self._stream.tell()

    def flush(self) -> None:
        self._stream.flush()

    def close(self) -> None:
        self._stream.close()


@dataclass(frozen=True)
class SourceArchive:
    digest: str
    size: int
    _stream: _CappedArchive = field(repr=False, compare=False)

    @property
    def data(self) -> bytes:
        position = self._stream.tell()
        try:
            self._stream.seek(0)
            return self._stream.read()
        finally:
            self._stream.seek(position)

    def content(self) -> BinaryIO:
        self._stream.seek(0)
        return cast(BinaryIO, self._stream)

    def close(self) -> None:
        self._stream.close()


class _ContentReader:
    def __init__(self, source: BinaryIO, path: Path) -> None:
        self._source = source
        self._path = path
        self._digest = sha256()
        self.bytes_read = 0

    def read(self, size: int = -1) -> bytes:
        try:
            data = self._source.read(size)
        except OSError as exc:
            raise CustomToolUploadError(f"Source file cannot be read: {self._path}") from exc
        self._digest.update(data)
        self.bytes_read += len(data)
        return data

    @property
    def hexdigest(self) -> str:
        return self._digest.hexdigest()


@dataclass(frozen=True)
class SourceFile:
    relative: str
    path: Path
    root: Path
    device: int
    inode: int
    size: int
    modified_ns: int
    mode: int
    content_sha256: str

    @classmethod
    def inspect(cls, relative: str, path: Path, root: Path) -> SourceFile:
        _validate_archive_name(relative, path)
        metadata = _file_metadata(path)
        _assert_contained(root, path)
        confirmed = _file_metadata(path)
        if _identity(metadata) != _identity(confirmed):
            raise CustomToolUploadError(f"Source file changed during inspection: {path}")
        if not stat.S_ISREG(metadata.st_mode):
            raise CustomToolUploadError(f"Source archives can contain only regular files: {path}")
        content_sha256 = _content_digest(path, metadata)
        confirmed = _file_metadata(path)
        if _identity(metadata) != _identity(confirmed):
            raise CustomToolUploadError(f"Source file changed during inspection: {path}")
        inspected = cls(
            relative=relative,
            path=path,
            root=root,
            device=metadata.st_dev,
            inode=metadata.st_ino,
            size=metadata.st_size,
            modified_ns=metadata.st_mtime_ns,
            mode=metadata.st_mode,
            content_sha256=content_sha256,
        )
        return inspected

    @contextmanager
    def open_verified(self) -> Iterator[BinaryIO]:
        """Open the inspected file without following a replacement symlink."""
        self._verify_path()
        flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
        try:
            descriptor = os.open(self.path, flags)
        except OSError as exc:
            raise CustomToolUploadError(
                f"Source file cannot be read or changed after inspection: {self.path}"
            ) from exc

        with os.fdopen(descriptor, "rb") as source:
            self._verify(os.fstat(source.fileno()))
            reader = _ContentReader(source, self.path)
            completed = False
            try:
                yield cast(BinaryIO, reader)
                completed = True
            finally:
                if completed and (
                    reader.bytes_read != self.size or reader.hexdigest != self.content_sha256
                ):
                    raise CustomToolUploadError(
                        f"Source file contents changed after inspection: {self.path}"
                    )
                self._verify(os.fstat(source.fileno()))
                self._verify_path()

    def read_text(self, encoding: str = "utf-8") -> str:
        with self.open_verified() as source:
            return source.read().decode(encoding)

    def _verify(self, metadata: os.stat_result) -> None:
        identity = _identity(metadata)
        expected = (self.device, self.inode, self.size, self.modified_ns, self.mode)
        if identity != expected or not stat.S_ISREG(metadata.st_mode):
            raise CustomToolUploadError(f"Source file changed after inspection: {self.path}")

    def _verify_path(self) -> None:
        _assert_contained(self.root, self.path)
        self._verify(_file_metadata(self.path))


@dataclass(frozen=True)
class SourceTree:
    files: tuple[SourceFile, ...]
    empty_directories: tuple[str, ...]


def inspect_source_tree(folder: str | Path) -> SourceTree:
    """Collect the exact retained tree while enforcing archive link policy."""
    try:
        root = Path(folder).expanduser()
    except (OSError, RuntimeError) as exc:
        raise CustomToolUploadError(f"Cannot resolve Custom Tool source folder: {folder}") from exc
    try:
        root_metadata = root.lstat()
    except OSError as exc:
        raise CustomToolUploadError(f"Custom Tool source folder does not exist: {root}") from exc
    if not stat.S_ISDIR(root_metadata.st_mode):
        raise CustomToolUploadError(f"Custom Tool source folder does not exist: {root}")
    if _metadata_is_link_like(root_metadata):
        raise CustomToolUploadError(f"Source archives cannot contain symlinks or junctions: {root}")
    try:
        resolved_root = root.resolve(strict=True)
    except OSError as exc:
        raise CustomToolUploadError(f"Cannot resolve Custom Tool source folder: {root}") from exc

    files: list[SourceFile] = []
    empty_directories: list[str] = []
    retained_entries = 0
    pending = [root]
    while pending:
        current_path = pending.pop()
        _verify_directory(resolved_root, current_path)
        kept_directories, kept_files = _scan_directory(
            current_path,
            max_entries=_MAX_SOURCE_ENTRIES - retained_entries,
        )
        retained_entries += len(kept_directories) + len(kept_files)
        pending.extend(reversed(kept_directories))
        files.extend(
            SourceFile.inspect(path.relative_to(root).as_posix(), path, resolved_root)
            for path in kept_files
        )
        if current_path != root and not kept_directories and not kept_files:
            relative = current_path.relative_to(root).as_posix()
            _validate_archive_name(relative, current_path)
            empty_directories.append(relative)

    return SourceTree(
        files=tuple(files),
        empty_directories=tuple(empty_directories),
    )


def build_archive(folder: str | Path, *, max_bytes: int | None = None) -> SourceArchive:
    """Package a folder into byte-for-byte reproducible ZIP content."""
    return build_source_tree_archive(inspect_source_tree(folder), max_bytes=max_bytes)


def build_source_tree_archive(
    tree: SourceTree,
    *,
    max_bytes: int | None = None,
) -> SourceArchive:
    """Package one previously inspected source snapshot."""
    _enforce_source_entry_limit(len(tree.files) + len(tree.empty_directories))
    output = _CappedArchive(max_bytes)
    try:
        with zipfile.ZipFile(
            output,
            mode="w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=9,
            strict_timestamps=True,
        ) as archive:
            entries: list[tuple[str, SourceFile | None, int]] = []
            for relative in tree.empty_directories:
                entries.append((f"{relative}/", None, _DIRECTORY_MODE))
                # Git cannot persist an empty tree. The marker keeps the directory
                # present when the backend commits the uploaded archive to Gitea.
                entries.append((f"{relative}/.gitkeep", None, _REGULAR_FILE_MODE))
            for source_file in tree.files:
                executable = source_file.relative == "run.sh" or bool(source_file.mode & 0o111)
                mode = _EXECUTABLE_FILE_MODE if executable else _REGULAR_FILE_MODE
                entries.append((source_file.relative, source_file, mode))

            for relative, entry_path, mode in sorted(entries, key=lambda item: item[0]):
                info = zipfile.ZipInfo(relative, date_time=_ZIP_TIMESTAMP)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.create_system = 3
                info.external_attr = mode << 16
                if entry_path is None:
                    archive.writestr(info, b"", compresslevel=9)
                    continue
                with entry_path.open_verified() as source:
                    with archive.open(info, "w", force_zip64=True) as destination:
                        while chunk := source.read(1024 * 1024):
                            destination.write(chunk)

        output.seek(0)
        digest = sha256()
        size = 0
        while chunk := output.read(1024 * 1024):
            digest.update(chunk)
            size += len(chunk)
        output.seek(0)
        return SourceArchive(digest=f"sha256:{digest.hexdigest()}", size=size, _stream=output)
    except BaseException:
        output.close()
        raise


def is_link_like(path: Path) -> bool:
    """Reject POSIX links and Windows reparse points such as junctions."""
    return _metadata_is_link_like(_file_metadata(path))


def _scan_directory(path: Path, *, max_entries: int) -> tuple[list[Path], list[Path]]:
    directories: list[Path] = []
    files: list[Path] = []
    try:
        entries = os.scandir(path)
        with entries:
            for entry in entries:
                child = path / entry.name
                metadata = _file_metadata(child)
                is_directory = stat.S_ISDIR(metadata.st_mode)
                if _is_excluded_entry(entry.name, is_directory=is_directory):
                    continue
                if is_directory:
                    if _metadata_is_link_like(metadata):
                        raise CustomToolUploadError(
                            f"Source archives cannot contain symlinks or junctions: {child}"
                        )
                    directories.append(child)
                else:
                    if _metadata_is_link_like(metadata):
                        raise CustomToolUploadError(
                            f"Source archives cannot contain symlinks or junctions: {child}"
                        )
                    files.append(child)
                _enforce_source_entry_limit(len(directories) + len(files), maximum=max_entries)
    except CustomToolUploadError:
        raise
    except (OSError, RecursionError) as exc:
        raise CustomToolUploadError(f"Cannot traverse Custom Tool source folder: {exc}") from exc
    return sorted(directories, key=lambda child: child.name), sorted(
        files, key=lambda child: child.name
    )


def _is_excluded_entry(name: str, *, is_directory: bool) -> bool:
    """Apply archive exclusions with filesystem-independent name semantics."""
    normalized = name.casefold()
    if normalized in _EXCLUDED_DIRECTORY_NAMES:
        return True
    if is_directory:
        return False
    return normalized in _EXCLUDED_FILE_NAMES or Path(normalized).suffix in _EXCLUDED_FILE_SUFFIXES


def _enforce_source_entry_limit(
    count: int,
    *,
    maximum: int | None = None,
) -> None:
    if maximum is None:
        maximum = _MAX_SOURCE_ENTRIES
    if count > maximum:
        raise CustomToolUploadError(
            f"Source tree exceeds the {_MAX_SOURCE_ENTRIES}-entry inspection limit"
        )


def _validate_archive_name(relative: str, path: Path) -> None:
    try:
        relative.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise CustomToolUploadError(f"Source archive path is not valid UTF-8: {path}") from exc


def _metadata_is_link_like(metadata: os.stat_result) -> bool:
    if stat.S_ISLNK(metadata.st_mode):
        return True
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    file_attributes = getattr(metadata, "st_file_attributes", 0)
    return bool(reparse_flag and file_attributes & reparse_flag)


def _verify_directory(root: Path, path: Path) -> None:
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise CustomToolUploadError(f"Source directory changed during inspection: {path}") from exc
    if not stat.S_ISDIR(metadata.st_mode) or _metadata_is_link_like(metadata):
        raise CustomToolUploadError(f"Source archives cannot contain symlinks or junctions: {path}")
    _assert_contained(root, path)


def _assert_contained(root: Path, path: Path) -> None:
    try:
        resolved = path.resolve(strict=True)
        resolved.relative_to(root)
    except (OSError, ValueError) as exc:
        raise CustomToolUploadError(f"Source path escapes the source folder: {path}") from exc


def _file_metadata(path: Path) -> os.stat_result:
    try:
        return path.lstat()
    except OSError as exc:
        raise CustomToolUploadError(f"Source file changed during inspection: {path}") from exc


def _content_digest(path: Path, expected: os.stat_result) -> str:
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise CustomToolUploadError(
            f"Source file cannot be read during inspection: {path}"
        ) from exc
    digest = sha256()
    with os.fdopen(descriptor, "rb") as source:
        if _identity(os.fstat(source.fileno())) != _identity(expected):
            raise CustomToolUploadError(f"Source file changed during inspection: {path}")
        try:
            while chunk := source.read(1024 * 1024):
                digest.update(chunk)
        except OSError as exc:
            raise CustomToolUploadError(
                f"Source file cannot be read during inspection: {path}"
            ) from exc
        if _identity(os.fstat(source.fileno())) != _identity(expected):
            raise CustomToolUploadError(f"Source file changed during inspection: {path}")
    return digest.hexdigest()


def _identity(metadata: os.stat_result) -> tuple[int, int, int, int, int]:
    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_size,
        metadata.st_mtime_ns,
        metadata.st_mode,
    )
