"""Strip credential-bearing URLs out of API payloads.

Promoted out of `cli/commands/jobs.py`. It was never a display concern: a result
payload carrying a presigned S3 URL is just as dangerous written to a log by a
script as printed to a terminal, and a library consumer had no way to reach this.
One implementation, so a new caller inherits the protection instead of
reimplementing it — or forgetting to.

Pure: no I/O, no network. Safe to import from anywhere.
"""

from __future__ import annotations

import re
from urllib.parse import parse_qsl, urlsplit

# Keys whose value is a transfer URL regardless of what the query string looks like.
# Kept byte-identical to the set this was promoted from — this move is behaviour-
# preserving, so widening the set (e.g. adding "signedurl") belongs in its own change
# where the effect can be reviewed on its own merits.
SENSITIVE_URL_KEYS = {
    "resulturl",
    "downloadurl",
    "presignedurl",
    "uploadurl",
    "headurl",
}

# Query-parameter names that mark a URL as carrying its own authorization.
SENSITIVE_QUERY_NAMES = {
    "awsaccesskeyid",
    "googleaccessid",
    "policy",
    "sig",
    "signature",
    "token",
}


def normalized_key(key: object) -> str:
    """Fold a payload key to bare lowercase alphanumerics for matching."""
    return re.sub(r"[^a-z0-9]", "", str(key).lower())


def is_credential_url(value: object) -> bool:
    """Whether a string is an HTTP(S) URL carrying auth query data."""
    if not isinstance(value, str):
        return False
    try:
        parsed = urlsplit(value.strip())
    except ValueError:
        return False
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc:
        return False
    names = {name.lower() for name, _ in parse_qsl(parsed.query, keep_blank_values=True)}
    return any(
        name in SENSITIVE_QUERY_NAMES
        or name.startswith(("x-amz-", "x-goog-", "x-ms-"))
        or name.endswith(("signature", "credential", "security-token"))
        for name in names
    )


def with_redactions(cleaned: dict, removed: list[str]) -> dict:
    """Record what was stripped, without clobbering an upstream field of the same name."""
    if not removed:
        return cleaned
    existing = cleaned.get("redactedFields")
    if existing is None or (
        isinstance(existing, list) and all(isinstance(item, str) for item in existing)
    ):
        cleaned["redactedFields"] = sorted(set((existing or []) + removed))
    else:
        # Never overwrite an upstream field that happens to use our metadata
        # name. Keep our redaction audit under a collision-safe key.
        cleaned["tamarindRedactedFields"] = sorted(set(removed))
    return cleaned


def sanitize(value: object) -> object:
    """Remove credential-bearing transfer URLs from an API payload, recursively."""
    if isinstance(value, list):
        return [sanitize(item) for item in value]
    if is_credential_url(value):
        return "<redacted credential URL>"
    if not isinstance(value, dict):
        return value
    sanitized = {}
    removed = []
    for key, item in value.items():
        normalized = normalized_key(key)
        if normalized in SENSITIVE_URL_KEYS or (
            is_credential_url(item)
            and (normalized.endswith(("url", "uri", "link", "location")) or "signed" in normalized)
        ):
            removed.append(str(key))
            continue
        sanitized[key] = sanitize(item)
    return with_redactions(sanitized, removed)
