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

from typing import TYPE_CHECKING

from ..errors import TamarindError

from .destination import read_text_here

if TYPE_CHECKING:
    from .destination import Destination

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
    text = read_text_here(folder, PROJECT_FILENAME)
    if text is None:
        return None
    try:
        data = json.loads(text)
    except ValueError as exc:
        raise TamarindError(
            f"{path} is not readable as JSON ({exc}). Delete it, or fix the tool name, "
            f"rather than letting the folder name decide which tool gets deployed."
        ) from exc
    name = data.get("name") if isinstance(data, dict) else None
    if not isinstance(name, str) or not name:
        raise TamarindError(f'{path} has no tool name. Expected {{"name": "<tool-id>"}}.')
    return Project(name=name, path=path)


def write(destination: "Destination", *, name: str) -> Path:
    """Record ``name`` as the folder's tool. Returns the file written.

    Takes a :class:`~tamarind.customtools.destination.Destination` rather than a path,
    so the marker cannot be written somewhere unchecked. That is not hypothetical: the
    marker write was the FOURTH symlink escape in this package — `.tamarind` is not an
    archive member, so extraction's per-member guard never sees it, and a link left in
    the destination caught this write and redirected it out of the folder.
    """
    return destination.write_file(PROJECT_FILENAME, json.dumps({"name": name}, indent=2) + "\n")


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
