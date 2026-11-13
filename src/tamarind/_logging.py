"""Keep presigned-URL credentials out of httpx's request log.

httpx logs every request at INFO as ``HTTP Request: GET https://host/path?query ...``. For a
presigned upload or download the query IS the credential (``X-Amz-Signature``, ...), so an
application with httpx INFO logging would write usable, if short-lived, credentials to its
logs (``from None`` on our errors only protects tracebacks).

:func:`redact_signed_urls` installs one narrow filter on the ``httpx`` logger: a URL whose
query carries a signature parameter has its query replaced; every other record, and every
log level, is untouched. The SDK's transfer helpers call it before they send, so ``tamarind
files upload`` and the Agent API's file transfers are both covered.
"""

from __future__ import annotations

import logging
import re
from urllib.parse import parse_qsl, urlsplit

_URL = re.compile(r"https?://[^\s\"'<>]+")
_SENSITIVE_NAMES = frozenset({"sig", "x-amz-security-token", "x-amz-credential", "awsaccesskeyid"})


def _is_credential(name: str) -> bool:
    lowered = name.lower()
    return "signature" in lowered or lowered in _SENSITIVE_NAMES


def _redact(match: re.Match[str]) -> str:
    url = match.group(0)
    query = urlsplit(url).query
    if query and any(_is_credential(name) for name, _ in parse_qsl(query, keep_blank_values=True)):
        return url.split("?", 1)[0] + "?<redacted>"
    return url


class SignedUrlRedactor(logging.Filter):
    """Rewrites a log record whose message holds a URL with a signature in its query."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            message = record.getMessage()
        except Exception:  # noqa: BLE001 - a malformed record is not ours to break
            return True
        redacted = _URL.sub(_redact, message)
        if redacted != message:
            record.msg, record.args = redacted, ()
        return True


def redact_signed_urls() -> None:
    """Install the filter on the ``httpx`` logger, once (calling again is a no-op)."""
    logger = logging.getLogger("httpx")
    if not any(isinstance(existing, SignedUrlRedactor) for existing in logger.filters):
        logger.addFilter(SignedUrlRedactor())
