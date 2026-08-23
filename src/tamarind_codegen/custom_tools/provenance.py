"""Canonical provenance constraints for the vendored Custom Tools contract."""

from __future__ import annotations

from pathlib import Path
import re
import subprocess

SOURCE_REPOSITORY = "Tamarind-Bio/tamarind-website"
SOURCE_ARTIFACT_PATH = "backend/app/public_api/openapi/public-v1.generated.json"
SOURCE_PATH = f"{SOURCE_ARTIFACT_PATH}#tag=custom-tools"
COMMIT_PATTERN = re.compile(r"[0-9a-f]{40}\Z")


def validate_source_provenance(repository: object, commit: object, path: object) -> None:
    """Reject provenance that the repository freshness check cannot verify."""
    if repository != SOURCE_REPOSITORY:
        raise ValueError(f"source repository must be {SOURCE_REPOSITORY!r}")
    if path != SOURCE_PATH:
        raise ValueError(f"source path must be {SOURCE_PATH!r}")
    if not isinstance(commit, str) or COMMIT_PATTERN.fullmatch(commit) is None:
        raise ValueError("source commit must be a full lowercase hexadecimal Git commit SHA")


def verify_source_checkout(checkout: Path, commit: str, source: bytes) -> None:
    """Prove that the checked-out producer contains the supplied artifact at the recorded commit."""
    try:
        remote = subprocess.run(
            ["git", "-C", str(checkout), "remote", "get-url", "origin"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        resolved_commit = subprocess.run(
            ["git", "-C", str(checkout), "rev-parse", f"{commit}^{{commit}}"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        committed_source = subprocess.run(
            ["git", "-C", str(checkout), "show", f"{commit}:{SOURCE_ARTIFACT_PATH}"],
            check=True,
            capture_output=True,
        ).stdout
    except subprocess.CalledProcessError as exc:
        raise ValueError("source checkout cannot verify the recorded backend commit") from exc
    normalized_remote = remote.removesuffix(".git").replace(
        "git@github.com:", "https://github.com/"
    )
    if normalized_remote != f"https://github.com/{SOURCE_REPOSITORY}":
        raise ValueError(f"source checkout origin must be {SOURCE_REPOSITORY!r}")
    if resolved_commit != commit:
        raise ValueError("source commit must identify the exact checked-out backend revision")
    if committed_source != source:
        raise ValueError("source artifact must match the recorded backend commit")
