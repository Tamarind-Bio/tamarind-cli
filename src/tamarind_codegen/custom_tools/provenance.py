"""Canonical provenance constraints for the vendored Custom Tools contract."""

from __future__ import annotations

import re

SOURCE_REPOSITORY = "Tamarind-Bio/tamarind-website"
SOURCE_PATH = "backend/app/public_api/openapi/public-v1.generated.json#tag=custom-tools"
COMMIT_PATTERN = re.compile(r"[0-9a-f]{40}\Z")


def validate_source_provenance(repository: object, commit: object, path: object) -> None:
    """Reject provenance that the repository freshness check cannot verify."""
    if repository != SOURCE_REPOSITORY:
        raise ValueError(f"source repository must be {SOURCE_REPOSITORY!r}")
    if path != SOURCE_PATH:
        raise ValueError(f"source path must be {SOURCE_PATH!r}")
    if not isinstance(commit, str) or COMMIT_PATTERN.fullmatch(commit) is None:
        raise ValueError("source commit must be a full lowercase hexadecimal Git commit SHA")
