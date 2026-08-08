"""The `.tamarind` project file: which tool a folder belongs to.

`tamarind deploy` with no arguments has to answer "deploy what?". Every comparable
tool keeps a small project file for this — fly.toml, wrangler.toml, .vercel/ — and the
alternative here is guessing from the directory name, which is wrong the moment someone
renames a folder or runs from a checkout with a different name.

It deliberately does NOT live in config.json. That file is the tool manifest and the web
editor rewrites it from a template on save, so an extra key there would be silently
dropped — the kind of data loss that is invisible until someone's deploy targets the
wrong tool.

Never holds credentials. The tool id is not a secret, so this file is safe to commit;
it is excluded from the source archive because the server has no use for it.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from ..errors import TamarindError

PROJECT_FILENAME = ".tamarind"


@dataclass(frozen=True)
class Project:
    """What a folder knows about itself."""

    name: str
    path: Path


def read(folder: Path | str) -> Project | None:
    """The project recorded in ``folder``, or None if there is none.

    A malformed file raises rather than being ignored: silently falling back to the
    directory name would deploy to a *different* tool than the one recorded, which is
    the one failure this file exists to prevent.
    """
    path = Path(folder) / PROJECT_FILENAME
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text())
    except (OSError, ValueError) as exc:
        raise TamarindError(
            f"{path} is not readable as JSON ({exc}). Delete it, or fix the tool name, "
            f"rather than letting the folder name decide which tool gets deployed."
        ) from exc
    name = data.get("name") if isinstance(data, dict) else None
    if not isinstance(name, str) or not name:
        raise TamarindError(f'{path} has no tool name. Expected {{"name": "<tool-id>"}}.')
    return Project(name=name, path=path)


def write(folder: Path | str, *, name: str) -> Path:
    """Record ``name`` as the folder's tool. Returns the file written.

    Writes through :func:`write_without_following_links`, because this is the FOURTH
    place a symlink could redirect a write outside the folder we were asked to touch.
    The marker is not an archive member, so `clone --force`'s extraction guard never
    sees it — a `.tamarind` symlink in the destination survives extraction and then
    catches this write.
    """
    path = Path(folder) / PROJECT_FILENAME
    write_without_following_links(path, json.dumps({"name": name}, indent=2) + "\n")
    return path


def write_without_following_links(path: Path, text: str) -> None:
    """Write ``text`` to ``path``, replacing a symlink rather than writing through it.

    THE one write primitive for user-controlled destinations. Four separate symlink
    escapes have now been fixed in this package one call site at a time (the archive
    walk, extraction, the preflight checks, and this marker); the pattern is that each
    new write is written with `write_text` and only later noticed. Routing every one
    through here — and enforcing that in `tests/test_layering.py` — is what makes the
    fifth instance fail a test instead of shipping.
    """
    if path.is_symlink():
        path.unlink()
    try:
        path.write_text(text)
    except OSError as exc:
        raise TamarindError(f"Could not write {path}: {exc}") from exc


def resolve_name(folder: Path | str, explicit: str | None = None) -> str:
    """Which tool a command should act on.

    Precedence: an explicit ``--name`` wins, then the project file, then the folder's
    own name as a last resort. The fallback is what makes the very first `deploy
    --create` work in a folder that has no project file yet.
    """
    if explicit:
        return explicit
    project = read(folder)
    if project is not None:
        return project.name
    return Path(folder).resolve().name
