"""httpx logs every request URL at INFO; a presigned URL's query is the credential."""

from __future__ import annotations

import logging

import httpx
import pytest
import respx

from tamarind._logging import SignedUrlRedactor, redact_signed_urls
from tamarind.agent.resources import save_url
from tamarind.uploads import put_presigned_upload

SIGNED = "https://s3.test/u/file_9f2?X-Amz-Credential=AKIAEXAMPLE&X-Amz-Signature=topsecretsig&X-Amz-Expires=900"


@pytest.fixture
def httpx_logger():
    """The httpx logger without our filter, so the helper under test has to install it."""
    logger = logging.getLogger("httpx")
    before = list(logger.filters)
    logger.filters[:] = [f for f in before if not isinstance(f, SignedUrlRedactor)]
    yield logger
    logger.filters[:] = before


@respx.mock
def test_an_upload_never_logs_the_signature(httpx_logger, caplog, tmp_path):
    caplog.set_level(logging.INFO, logger="httpx")
    target = tmp_path / "a.pdb"
    target.write_bytes(b"ATOM\n")
    respx.put("https://s3.test/u/file_9f2").mock(return_value=httpx.Response(200))

    put_presigned_upload(SIGNED, target, content_type="chemical/x-pdb", remote="a.pdb")

    assert "HTTP Request: PUT https://s3.test/u/file_9f2" in caplog.text  # still logged
    assert "topsecretsig" not in caplog.text and "AKIAEXAMPLE" not in caplog.text


@respx.mock
def test_a_download_never_logs_the_signature(httpx_logger, caplog, tmp_path):
    caplog.set_level(logging.INFO, logger="httpx")
    respx.get("https://s3.test/u/file_9f2").mock(return_value=httpx.Response(200, content=b"data"))

    save_url(SIGNED, tmp_path / "out.cif")

    assert "HTTP Request: GET https://s3.test/u/file_9f2" in caplog.text
    assert "topsecretsig" not in caplog.text and "AKIAEXAMPLE" not in caplog.text


@pytest.mark.parametrize(("name", "redacted"), [
    ("X-Amz-Signature", True), ("Signature", True), ("X-Goog-Signature", True), ("sig", True),
    ("X-Amz-Security-Token", True), ("expires", False), ("page", False),
])
def test_only_urls_carrying_a_credential_parameter_are_rewritten(name, redacted, httpx_logger):
    redact_signed_urls()
    record = logging.LogRecord("httpx", logging.INFO, __file__, 1,
                               'HTTP Request: %s %s "HTTP/1.1 200 OK"', ("GET", f"https://h.test/p?{name}=v1&a=b"), None)
    assert httpx_logger.filters and all(f.filter(record) for f in httpx_logger.filters)
    text = record.getMessage()
    assert ("<redacted>" in text) is redacted
    assert ("v1" in text) is not redacted


def test_installing_twice_adds_one_filter_and_changes_no_level(httpx_logger):
    level = httpx_logger.level
    redact_signed_urls()
    redact_signed_urls()
    assert sum(isinstance(f, SignedUrlRedactor) for f in httpx_logger.filters) == 1
    assert httpx_logger.level == level
