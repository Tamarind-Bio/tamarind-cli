"""Writing a tool folder into a zip, applying the packaging decisions.

Separate from :mod:`tamarind.customtools.packaging` because that module decides and
this one touches the disk — keeping the decision pure is what lets the security-
relevant part be tested as a table.

The library takes a FOLDER and never an archive. That is deliberate: if a caller could
hand in a pre-built zip, the exclusion rules would be bypassable, and they are the only
thing standing between a stray `.env` and a published image layer.
"""

from __future__ import annotations

import zipfile
from dataclasses import dataclass, field
from pathlib import Path

from ..errors import TamarindError, ValidationError
from . import packaging

# The backend refuses a larger upload at finalize. Checked here so a doomed 5 GiB
# transfer is refused before it starts rather than after.
MAX_SOURCE_BYTES = 5 * 1024 * 1024 * 1024


@dataclass(frozen=True)
class ArchivePlan:
    """What a folder would upload, decided before anything is written."""

    included: tuple[Path, ...] = ()
    secrets: tuple[str, ...] = ()
    # Symlinks, which are never uploaded. Reported because dropping one silently is
    # how a tool builds without a file its author believed was there.
    links: tuple[str, ...] = ()
    noise_count: int = 0
    weights: tuple[str, ...] = ()
    total_bytes: int = 0
    root: Path = field(default_factory=Path)


def plan_archive(folder: Path) -> ArchivePlan:
    """Walk ``folder`` and classify everything, without writing anything.

    Separated from the write so `check` and `--dry-run` can report exactly what a
    deploy would send without producing a file.
    """
    root = Path(folder).resolve()
    if not root.is_dir():
        raise ValidationError(f"'{folder}' is not a directory.")

    included: list[Path] = []
    secrets: list[str] = []
    links: list[str] = []
    weights: list[str] = []
    noise = 0
    total = 0

    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            # NEVER followed. Every filter in `packaging` works on the pathname, and a
            # symlink's name says nothing about what it points at: `config.txt ->
            # ~/.ssh/id_rsa` classifies as an ordinary file, and `ZipFile.write` would
            # then archive the KEY's bytes under that harmless name. That single case
            # defeats the entire exclusion list, so links are reported and dropped
            # rather than resolved-then-classified — resolving first would still let a
            # link to an unnamed-but-sensitive file through.
            links.append(path.relative_to(root).as_posix())
            continue
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        decision = packaging.classify(relative)
        if decision.disposition is packaging.Disposition.SECRET:
            secrets.append(relative)
            continue
        if decision.disposition is packaging.Disposition.NOISE:
            noise += 1
            continue
        included.append(path)
        total += path.stat().st_size
        if packaging.is_weight_file(relative):
            weights.append(relative)

    return ArchivePlan(
        included=tuple(included),
        secrets=tuple(secrets),
        links=tuple(links),
        noise_count=noise,
        weights=tuple(weights),
        total_bytes=total,
        root=root,
    )


def write_archive(plan: ArchivePlan, destination: Path) -> int:
    """Write the planned files to ``destination``. Returns the archive's byte size.

    Refuses to write past the server's ceiling: failing here costs nothing, while
    failing at finalize costs however long the upload took.
    """
    if plan.total_bytes > MAX_SOURCE_BYTES:
        raise ValidationError(
            f"Source is {plan.total_bytes / 1024**3:.1f} GiB, over the "
            f"{MAX_SOURCE_BYTES / 1024**3:.0f} GiB limit. Model weights belong in the "
            f"image (downloaded by the Dockerfile), not the source upload."
        )
    if not plan.included:
        raise ValidationError(
            "Nothing to upload — every file in the folder was excluded as build "
            "output or credentials."
        )
    try:
        with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as zf:
            for path in plan.included:
                zf.write(path, path.relative_to(plan.root).as_posix())
    except OSError as exc:
        raise TamarindError(f"Could not write the source archive: {exc}") from exc
    return destination.stat().st_size
