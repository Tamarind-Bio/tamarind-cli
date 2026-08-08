"""A directory this process has verified it may write into.

Five separate symlink escapes shipped in this package before this module existed —
the archive walk followed links into secrets, `clone --force` extracted through them,
preflight blessed a linked Dockerfile, the `.tamarind` marker write followed a link
out of the folder, and a linked destination ROOT redirected all of the above. Each was
fixed on its own, and the next one was written the same way.

They shared a cause, not a coincidence: every one took a bare :class:`~pathlib.Path`
and re-derived "is this safe to write to" at the point of use. Five call sites, five
independent answers, and the ones that were wrong looked exactly like the ones that
were right.

So the check does not return a validated path. It returns a **capability**, and the
write operations are methods on it:

    dest = Destination.prepare(folder)      # the checks live here, once
    dest.extract(archive)                   # there is no module-level extract()
    dest.write_file(".tamarind", text)

A validated value can be ignored — nothing stops a caller using the original variable
they passed in, which is precisely what kept happening. A capability cannot, because
the operation is not reachable without one.

`tests/test_layering.py` enforces the other half: no other library module may call the
raw filesystem primitives this one is built from.
"""

from __future__ import annotations

import os
import shutil
import stat
import zipfile
from dataclasses import dataclass
from pathlib import Path

from ..errors import TamarindError, ValidationError


@dataclass(frozen=True)
class Destination:
    """A directory that has been checked and may be written to.

    Construct with :meth:`prepare`. The constructor is not private — Python has no way
    to make it so — but every write in this package goes through the methods here, and
    the layering test is what keeps it that way.
    """

    path: Path

    # ------------------------------------------------------------------ construct ----

    @classmethod
    def prepare(cls, path: Path | str, *, allow_nonempty: bool = False) -> "Destination":
        """Verify ``path`` is a directory we may write into. Returns the capability.

        Four distinct cases, distinguished on purpose because collapsing any two of
        them produced a real bug:

          * a SYMLINK          -> refused, always. Checked first, because `exists()`
                                  and `is_dir()` both follow the link — a linked root
                                  makes every per-member protection below irrelevant,
                                  since the writes land somewhere the caller never
                                  named. `--force` does not relax this: it permits
                                  overwriting THIS folder, not redirecting to another.
          * missing            -> fine; the caller creates it
          * an existing FILE   -> refused. `any(iterdir())` on a file raises
                                  NotADirectoryError, which reached users as a
                                  traceback rather than a typed error.
          * a non-empty folder -> refused unless the caller opts in, since writing
                                  here overwrites whatever is already there
        """
        target = Path(path)
        if target.is_symlink():
            raise ValidationError(
                f"'{target}' is a symlink. Point this at a real directory — writing "
                f"through a link would modify somewhere other than the path you named."
            )
        if target.exists():
            if not target.is_dir():
                raise ValidationError(
                    f"'{target}' is a file, not a folder. Point this at a directory, or remove it."
                )
            if not allow_nonempty and any(target.iterdir()):
                raise ValidationError(
                    f"'{target}' is not empty. Writing here overwrites whatever is "
                    f"already there, so local edits would be lost. Choose an empty "
                    f"folder."
                )
        return cls(path=target)

    # --------------------------------------------------------------------- writes ----

    def write_file(self, name: str, text: str) -> Path:
        """Write ``text`` to ``name`` inside this directory, replacing any symlink.

        Replacing rather than refusing: the caller already holds a capability for this
        folder, so the file being replaced is the link itself and nothing beyond it.
        """
        target = self.path / name
        self.path.mkdir(parents=True, exist_ok=True)
        if target.is_symlink():
            target.unlink()
        try:
            target.write_text(text)
        except OSError as exc:
            raise TamarindError(f"Could not write {target}: {exc}") from exc
        return target

    def clear(self) -> None:
        """Empty this directory.

        `clone --force` needs it: extraction only overwrites paths the archive
        contains, so without this a forced clone was a MERGE — files the requested
        version had deleted survived, and a later deploy repackaged them under that
        version's name.

        Entries are removed without following links, so unlinking a symlinked
        directory removes the link and never what it points at.
        """
        if not self.path.is_dir():
            return
        for entry in self.path.iterdir():
            try:
                if entry.is_symlink() or entry.is_file():
                    entry.unlink()
                elif entry.is_dir():
                    shutil.rmtree(entry)
            except OSError as exc:
                raise TamarindError(f"Could not clear '{entry}': {exc}") from exc

    def extract(self, archive_path: Path) -> tuple[str, ...]:
        """Unpack a zip into this directory. Returns any Git-LFS pointer paths.

        Never writes THROUGH a symlink. `extractall` opens each output path for
        writing and `open()` follows a link already sitting there, so a destination
        holding `config.json -> /etc/thing` let an archive member write outside the
        folder entirely. Every path component is checked, not just the leaf: `a/b.txt`
        writes through `a` when `a` is a link.
        """
        self.path.mkdir(parents=True, exist_ok=True)
        try:
            with zipfile.ZipFile(archive_path) as zf:
                for member in zf.infolist():
                    parts = _sanitized_parts(member.filename)
                    if not parts:
                        continue
                    current = self.path
                    for part in parts:
                        current = current / part
                        if current.is_symlink():
                            current.unlink()
                    extracted = Path(zf.extract(member, self.path))
                    _restore_mode(member, extracted)
        except (zipfile.BadZipFile, OSError) as exc:
            raise TamarindError(f"Could not unpack the tool's source: {exc}") from exc
        return self._lfs_pointers()

    # ---------------------------------------------------------------------- reads ----

    def _lfs_pointers(self) -> tuple[str, ...]:
        """Files that came down as Git-LFS pointers rather than content.

        Archives serve LFS-tracked files as pointers, matching GitHub and GitLab, so a
        cloned tool with large assets is not immediately redeployable. Worth saying
        rather than letting the next build fail confusingly.
        """
        found = []
        for candidate in sorted(self.path.rglob("*")):
            if candidate.is_symlink() or not candidate.is_file():
                continue
            try:
                with candidate.open("rb") as handle:
                    header = handle.read(45)
            except OSError:
                continue
            if header.startswith(b"version https://git-lfs.github.com/spec"):
                found.append(candidate.relative_to(self.path).as_posix())
        return tuple(found)


def read_text_here(folder: Path | str, name: str) -> str | None:
    """Read ``name`` from ``folder``. None when it is absent OR a symlink.

    A read is less dangerous than a write, but not harmless: following a link means
    answering a question about a file that is NOT the one the folder will ship, and
    that mismatch is the whole defect this module exists to prevent. `inspect_manifest`
    parsing a symlinked config.json reported a JSON error about a file the server would
    never see; `project.read` following a linked marker would take a tool id from
    outside the folder entirely.

    None rather than an exception: "there is no config.json here" is an ordinary state
    for every caller of this, and a link is indistinguishable from absence as far as
    what actually ships.
    """
    target = Path(folder) / name
    if target.is_symlink() or not target.is_file():
        return None
    try:
        return target.read_text()
    except OSError as exc:
        raise TamarindError(f"Could not read {target}: {exc}") from exc


def _sanitized_parts(filename: str) -> list[str]:
    """The path components `ZipFile.extract` will actually use for a member.

    Mirrors CPython's `_extract_member`: drive letters are dropped and empty, `.` and
    `..` components are removed. Computing the same path is what makes the symlink
    check land on the file that gets written rather than on a name that never exists.
    """
    name = filename.replace("/", os.path.sep)
    if os.path.altsep:
        name = name.replace(os.path.altsep, os.path.sep)
    name = os.path.splitdrive(name)[1]
    invalid = ("", os.path.curdir, os.path.pardir)
    return [part for part in name.split(os.path.sep) if part not in invalid]


def _restore_mode(member: zipfile.ZipInfo, path: Path) -> None:
    """Put back the executable bit the archive recorded.

    `ZipFile.extract` creates files with the process default (usually 0644) and drops
    the Unix mode in `external_attr`, so a cloned `run.sh` came back non-executable and
    `RUN ./install.sh` failed on a tree that built fine before.

    Only the executable bits, and only where the archive already grants read:
    setuid/setgid/sticky and world-writable bits out of an untrusted archive are not
    something a clone should be able to set.
    """
    mode = member.external_attr >> 16
    if not mode or stat.S_ISDIR(mode) or stat.S_ISLNK(mode):
        return
    if not mode & 0o111:
        return
    try:
        current = path.stat().st_mode
        # Grant execute exactly where read is already granted — the umask-respecting
        # idiom. 0644 becomes 0755; a file the extractor made group-unreadable does not
        # silently become group-executable.
        path.chmod(current | ((current & 0o444) >> 2))
    except OSError:
        # A filesystem without executable bits (or a read-only one) is not a reason to
        # fail a clone that has already written every file.
        pass
