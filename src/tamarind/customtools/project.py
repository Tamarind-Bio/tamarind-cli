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
    """Record ``name`` as the folder's tool. Returns the file written."""
    path = Path(folder) / PROJECT_FILENAME
    try:
        path.write_text(json.dumps({"name": name}, indent=2) + "\n")
    except OSError as exc:
        raise TamarindError(f"Could not write {path}: {exc}") from exc
    return path


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
