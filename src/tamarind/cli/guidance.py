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


def rewrite_legacy_guidance(text: object) -> object:
    """Translate known MCP/REST instructions while preserving scientific text."""
    if not isinstance(text, str):
        return text
    rewritten = text
    for pattern, replacement in _REPLACEMENTS:
        rewritten = re.sub(pattern, replacement, rewritten, flags=re.IGNORECASE)
    return rewritten
