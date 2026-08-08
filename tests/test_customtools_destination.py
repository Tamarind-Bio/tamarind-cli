"""The write capability.

These are the tests that used to be spread across five call sites — the archive walk,
extraction, preflight, the marker write, and the destination root — each with its own
version of "is this safe". They are here now because the answer is here now.

What is worth testing is the CONSTRUCTION rule (what `prepare` refuses) and that the
operations cannot be reached around it.
"""

from __future__ import annotations

import os
import stat
import zipfile
from pathlib import Path

import pytest

from tamarind.customtools import destination as destination_module
from tamarind.customtools.destination import Destination
from tamarind.errors import TamarindError, ValidationError


def _zip(path: Path, members: dict[str, str], *, executable: tuple[str, ...] = ()) -> Path:
    with zipfile.ZipFile(path, "w") as zf:
        for name, body in members.items():
            info = zipfile.ZipInfo(name)
            if name in executable:
                info.external_attr = (0o755 & 0xFFFF) << 16
            zf.writestr(info, body)
    return path


class TestPrepare:
    """Four cases, distinguished because collapsing any two produced a real bug."""

    def test_a_missing_path_is_fine(self, tmp_path: Path) -> None:
        target = tmp_path / "new"
        assert Destination.prepare(target).path == target

    def test_an_empty_folder_is_fine(self, tmp_path: Path) -> None:
        (tmp_path / "empty").mkdir()
        assert Destination.prepare(tmp_path / "empty")

    def test_an_existing_file_is_a_typed_error_not_a_traceback(self, tmp_path: Path) -> None:
        """`any(iterdir())` on a file raises NotADirectoryError, which the CLI boundary
        does not catch — so ordinary user input produced a stack trace."""
        target = tmp_path / "notafolder"
        target.write_text("i am a file\n")
        with pytest.raises(ValidationError):
            Destination.prepare(target)

    def test_a_non_empty_folder_is_refused_by_default(self, tmp_path: Path) -> None:
        busy = tmp_path / "busy"
        busy.mkdir()
        (busy / "work.py").write_text("mine\n")
        with pytest.raises(ValidationError):
            Destination.prepare(busy)

    def test_a_non_empty_folder_is_allowed_when_asked(self, tmp_path: Path) -> None:
        busy = tmp_path / "busy"
        busy.mkdir()
        (busy / "work.py").write_text("mine\n")
        assert Destination.prepare(busy, allow_nonempty=True).path == busy

    @pytest.mark.parametrize("force", [False, True])
    def test_a_symlinked_root_is_always_refused(self, tmp_path: Path, force: bool) -> None:
        """The outermost escape: `exists()` and `is_dir()` both follow the link, so a
        linked root makes every per-member protection below it irrelevant. `--force`
        permits overwriting THIS folder, not redirecting to another one — which is why
        it is checked before anything else and why force does not relax it."""
        real = tmp_path / "elsewhere"
        real.mkdir()
        link = tmp_path / "dest"
        link.symlink_to(real, target_is_directory=True)
        with pytest.raises(ValidationError):
            Destination.prepare(link, allow_nonempty=force)


class TestWriteFile:
    def test_a_symlinked_target_is_replaced_not_written_through(self, tmp_path: Path) -> None:
        """`.tamarind` is not an archive member, so extraction's guard never sees it —
        this was the fourth escape and needed its own answer until the capability
        collapsed them into one."""
        outside = tmp_path / "outside.txt"
        outside.write_text("ORIGINAL\n")
        folder = tmp_path / "dest"
        folder.mkdir()
        (folder / ".tamarind").symlink_to(outside)

        dest = Destination.prepare(folder, allow_nonempty=True)
        dest.write_file(".tamarind", "replaced\n")

        assert (folder / ".tamarind").read_text() == "replaced\n"
        assert outside.read_text() == "ORIGINAL\n", "wrote through the link"
        assert not (folder / ".tamarind").is_symlink()

    def test_it_creates_the_folder_if_needed(self, tmp_path: Path) -> None:
        dest = Destination.prepare(tmp_path / "new")
        dest.write_file("a.txt", "x\n")
        assert (tmp_path / "new" / "a.txt").read_text() == "x\n"


class TestExtract:
    def test_a_destination_symlink_is_replaced(self, tmp_path: Path) -> None:
        outside = tmp_path / "outside.json"
        outside.write_text("ORIGINAL\n")
        folder = tmp_path / "dest"
        folder.mkdir()
        (folder / "config.json").symlink_to(outside)

        dest = Destination.prepare(folder, allow_nonempty=True)
        dest.extract(_zip(tmp_path / "a.zip", {"config.json": "FROM ARCHIVE\n"}))

        assert (folder / "config.json").read_text() == "FROM ARCHIVE\n"
        assert outside.read_text() == "ORIGINAL\n"

    def test_a_symlinked_parent_is_replaced(self, tmp_path: Path) -> None:
        """`a/b.txt` writes through `a` when `a` is a link, so every component is
        checked and not just the leaf."""
        outside = tmp_path / "outside"
        outside.mkdir()
        (outside / "b.txt").write_text("ORIGINAL\n")
        folder = tmp_path / "dest"
        folder.mkdir()
        (folder / "a").symlink_to(outside, target_is_directory=True)

        dest = Destination.prepare(folder, allow_nonempty=True)
        dest.extract(_zip(tmp_path / "a.zip", {"a/b.txt": "FROM ARCHIVE\n"}))
        assert (outside / "b.txt").read_text() == "ORIGINAL\n"

    def test_lfs_pointers_are_reported(self, tmp_path: Path) -> None:
        pointer = "version https://git-lfs.github.com/spec/v1\noid sha256:abc\nsize 1\n"
        dest = Destination.prepare(tmp_path / "out")
        found = dest.extract(_zip(tmp_path / "a.zip", {"m.py": "x\n", "w.pt": pointer}))
        assert found == ("w.pt",)

    @pytest.mark.skipif(
        os.name == "nt",
        reason="Windows has no executable bit — chmod there only toggles read-only.",
    )
    def test_the_executable_bit_survives(self, tmp_path: Path) -> None:
        dest = Destination.prepare(tmp_path / "out")
        dest.extract(
            _zip(
                tmp_path / "a.zip",
                {"install.sh": "#!/bin/sh\n", "notes.md": "plain\n"},
                executable=("install.sh",),
            )
        )
        assert (tmp_path / "out" / "install.sh").stat().st_mode & stat.S_IXUSR
        assert not (tmp_path / "out" / "notes.md").stat().st_mode & stat.S_IXUSR

    def test_a_corrupt_archive_is_a_typed_error(self, tmp_path: Path) -> None:
        bad = tmp_path / "bad.zip"
        bad.write_bytes(b"not a zip")
        with pytest.raises(TamarindError):
            Destination.prepare(tmp_path / "out").extract(bad)


class TestClear:
    def test_it_empties_the_folder(self, tmp_path: Path) -> None:
        folder = tmp_path / "dest"
        folder.mkdir()
        (folder / "a.py").write_text("x\n")
        (folder / "sub").mkdir()
        (folder / "sub" / "b.py").write_text("y\n")

        Destination.prepare(folder, allow_nonempty=True).clear()
        assert list(folder.iterdir()) == []

    def test_a_symlinked_entry_loses_the_link_not_the_target(self, tmp_path: Path) -> None:
        outside = tmp_path / "keep.txt"
        outside.write_text("KEEP\n")
        folder = tmp_path / "dest"
        folder.mkdir()
        (folder / "link").symlink_to(outside)

        Destination.prepare(folder, allow_nonempty=True).clear()
        assert list(folder.iterdir()) == []
        assert outside.read_text() == "KEEP\n", "clear() deleted through a link"


class TestReadTextHere:
    def test_it_reads_an_ordinary_file(self, tmp_path: Path) -> None:
        (tmp_path / "config.json").write_text("{}\n")
        assert destination_module.read_text_here(tmp_path, "config.json") == "{}\n"

    def test_a_missing_file_is_none(self, tmp_path: Path) -> None:
        assert destination_module.read_text_here(tmp_path, "config.json") is None

    def test_a_symlink_is_none_rather_than_followed(self, tmp_path: Path) -> None:
        """Reading through a link answers a question about a file that will NOT ship.
        That mismatch is the defect, whichever direction it runs in: parsing a linked
        config.json reported a JSON error about a file the server never sees."""
        real = tmp_path / "real.json"
        real.write_text('{"displayName": "sneaky"}\n')
        (tmp_path / "config.json").symlink_to(real)
        assert destination_module.read_text_here(tmp_path, "config.json") is None
