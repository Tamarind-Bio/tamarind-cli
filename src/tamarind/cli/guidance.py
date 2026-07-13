"""Rewrite server-authored transport guidance for CLI users."""

from __future__ import annotations

import re


_REPLACEMENTS = (
    (r"\bgetJobSchema\s*\([^)]*\)", "`tamarind --json schema NAME`"),
    (r"\blistJobFiles\s*\([^)]*\)", "the downloaded result bundle"),
    (r"\bvalidateJob\b", "`tamarind --json validate`"),
    (r"\bsubmitJob\b", "`tamarind --json submit`"),
    (
        r"\buploadFile(?:\s*\([^)]*\))?",
        "`tamarind --json files upload PATH`",
    ),
    (
        r"(?:please\s+)?upload your file using the /upload endpoint",
        "Upload the file with `tamarind --json files upload PATH`",
    ),
)

_UPLOAD_ENDPOINT = re.compile(
    r"(?:please\s+)?upload your file using the /upload endpoint",
    flags=re.IGNORECASE,
)


def rewrite_legacy_guidance(text: object) -> object:
    """Translate known MCP/REST instructions while preserving scientific text."""
    if not isinstance(text, str):
        return text
    rewritten = text
    for pattern, replacement in _REPLACEMENTS:
        rewritten = re.sub(pattern, replacement, rewritten, flags=re.IGNORECASE)
    return rewritten


def rewrite_validation_guidance(text: object) -> object:
    """Rewrite only the server's known upload instruction.

    Validation errors may echo user field names or values such as
    ``submitJob``. Broad MCP-token replacement would corrupt that diagnostic,
    so validation uses this deliberately narrow translation.
    """
    if not isinstance(text, str):
        return text
    return _UPLOAD_ENDPOINT.sub(
        "Upload the file with `tamarind --json files upload PATH`",
        text,
    )
