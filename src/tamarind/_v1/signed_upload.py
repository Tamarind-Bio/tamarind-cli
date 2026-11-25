"""Classic's presigned upload link (``POST /getPresignedUploadUrl``, ``rest.upload_file_url``),
answered by v1's uploadFile when the server says a key uses v1.

v1 signs the same object in the same account bucket: ``uploadUrl`` is v1's signed PUT link
(``Content-Type`` is signed, so it is always sent, as classic always signs it), and ``key``
is classic's ``{email}/{path}``, with the email from ``GET /me``. v1 has no ``headUrl`` or
``bucket`` (storage internals), so they are left out. Nothing is stored until the bytes are
PUT, as with classic.
"""

from __future__ import annotations

from typing import Any, NoReturn

from ..errors import TamarindError
from .classic import classic_error, plain


def _raise_classic(exc: TamarindError) -> NoReturn:
    converted = classic_error(exc)
    if converted is exc:
        raise exc
    raise converted from exc


def upload_url(http: Any, filename: str, content_type: str) -> dict[str, Any] | None:
    """Classic's ``{uploadUrl, key}`` from v1, or None when v1 isn't on for this key."""
    if not http.has_credentials or not http.uses_v1():
        return None
    try:
        v1 = http.v1()
        answer = plain(v1.files.sign_upload(filename, content_type=content_type))
        email = (plain(v1.me.get()).get("user") or {}).get("email")
    except TamarindError as exc:
        _raise_classic(exc)
    path = (answer.get("file") or {}).get("path") or filename
    out: dict[str, Any] = {"uploadUrl": (answer.get("upload") or {}).get("url")}
    if email:
        out["key"] = f"{email}/{path}"
    return out
