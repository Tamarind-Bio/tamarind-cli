"""Deciding what goes into a tool's source archive. Pure — no filesystem access.

The exclude list is a **security control**, not housekeeping. This archive becomes a
Docker image layer, and anyone with read access to the tool's source can pull it — so a
credential swept in here is published, and stays in the layer even after it is deleted
from the folder. The classification therefore lives in `plan`-style pure code with its
own tests, rather than as a convenience filter next to the zip writer.

Writing the archive is in :mod:`tamarind.customtools.archive`; this module only decides.
"""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass
from enum import Enum

# Refused outright. Every one of these is a credential or a private key; none has any
# business in a container image, and the platform has an env-var mechanism for the case
# people reach for `.env` to solve.
SECRET_PATTERNS = (
    ".env",
    ".env.*",
    "*.pem",
    "*.key",
    "*.p12",
    "*.pfx",
    "*.keytab",
    "id_rsa*",
    "id_dsa*",
    "id_ecdsa*",
    "id_ed25519*",
    ".netrc",
    ".npmrc",
    ".pypirc",
    ".git-credentials",
    "credentials",
    "credentials.json",
    "service-account*.json",
)

# Directories whose contents are always credentials or local machine state.
SECRET_DIRS = (".ssh", ".aws", ".gcloud", ".azure", ".config/gcloud")

# Dropped as noise: build detritus and VCS internals. Harmless but large, and shipping
# them slows every build.
NOISE_PATTERNS = (
    "*.pyc",
    "*.pyo",
    "*.egg-info",
    ".DS_Store",
    "Thumbs.db",
    "*.swp",
    ".tamarind",
)
NOISE_DIRS = (
    ".git",
    ".hg",
    ".svn",
    "__pycache__",
    ".venv",
    "venv",
    "node_modules",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".ipynb_checkpoints",
    ".tox",
)

# Included, but worth saying out loud. Model weights belong in the image, downloaded by
# the Dockerfile at build time — the runtime container has no network, so a tool that
# expects to fetch them at run time fails in a way that is hard to read from the logs.
WEIGHT_PATTERNS = ("*.pt", "*.pth", "*.ckpt", "*.safetensors", "*.h5", "*.pkl", "*.onnx")


class Disposition(Enum):
    INCLUDE = "include"
    SECRET = "secret"
    NOISE = "noise"


@dataclass(frozen=True)
class Decision:
    disposition: Disposition
    # Why, in the user's terms. Silence about a dropped file is how someone spends an
    # afternoon wondering where their config went.
    reason: str = ""

    @property
    def included(self) -> bool:
        return self.disposition is Disposition.INCLUDE


def _matches(name: str, patterns: tuple[str, ...]) -> bool:
    """Case-INSENSITIVELY, because these patterns are a security control.

    `fnmatch.fnmatch` normalizes case only on case-insensitive filesystems, so on
    Linux — where CI runs — `server.PEM`, `PRIVATE.KEY` and `.AWS/credentials` all
    sail past a lowercase pattern list and into the image layer. A filter that a
    capital letter defeats is not a filter.

    `fnmatchcase` on a lowered name rather than `fnmatch`, so the behaviour does not
    depend on the host filesystem.
    """
    lowered = name.lower()
    return any(fnmatch.fnmatchcase(lowered, pattern.lower()) for pattern in patterns)


def classify(relative_path: str) -> Decision:
    """Decide one path's fate. ``relative_path`` is POSIX-style, relative to the folder.

    Secrets are checked before noise so a file matching both is reported as the secret
    it is — the message is the point, not just the exclusion.
    """
    parts = [p for p in relative_path.replace("\\", "/").split("/") if p not in ("", ".")]
    if not parts:
        return Decision(Disposition.NOISE, "empty path")
    name = parts[-1]
    directories = parts[:-1]

    for directory in directories:
        if directory in SECRET_DIRS:
            return Decision(Disposition.SECRET, f"{directory}/ holds credentials")
    # Nested spellings like `.config/gcloud` are matched on the joined path.
    joined = "/".join(directories)
    for secret_dir in SECRET_DIRS:
        if "/" in secret_dir and (joined == secret_dir or joined.endswith("/" + secret_dir)):
            return Decision(Disposition.SECRET, f"{secret_dir}/ holds credentials")

    if _matches(name, SECRET_PATTERNS):
        return Decision(Disposition.SECRET, f"{name} looks like a credential")

    for directory in directories:
        if directory in NOISE_DIRS:
            return Decision(Disposition.NOISE, f"{directory}/ is not source")
    if _matches(name, NOISE_PATTERNS):
        return Decision(Disposition.NOISE, f"{name} is build output")

    return Decision(Disposition.INCLUDE)


def is_weight_file(relative_path: str) -> bool:
    """Whether a path looks like model weights — included, but warned about."""
    name = relative_path.replace("\\", "/").rsplit("/", 1)[-1]
    return _matches(name, WEIGHT_PATTERNS)


def env_var_advice(dropped_secrets: tuple[str, ...]) -> str | None:
    """What to tell someone whose `.env` was dropped.

    Naming the platform's own mechanism, because otherwise the next step is to work
    around the exclusion rather than use the thing that exists.
    """
    if not dropped_secrets:
        return None
    return (
        f"Excluded {len(dropped_secrets)} credential-like file(s) from the upload: "
        f"{', '.join(sorted(dropped_secrets)[:5])}"
        f"{' …' if len(dropped_secrets) > 5 else ''}. "
        "This archive becomes an image layer, so anything in it is readable by anyone "
        "who can read the tool's source. Use `tamarind ct config --env KEY=VALUE` for "
        "secrets the tool needs at run time."
    )
