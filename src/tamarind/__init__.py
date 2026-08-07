"""Tamarind Bio CLI and Python client.

A thin client over the Tamarind platform. One resource per package, each with the
same internal shape, so a caller who learns one knows the others:

- ``api``  — one function per endpoint. Client in, payload out, no branching.
- ``plan`` — pure decisions. No network, no clock; testable as a table of
             inputs and outputs. May not import ``api``/``flow``/``http``.
- ``flow`` — orchestration that owns the clock, for genuinely multi-step work.
             Reports progress through callbacks, never by printing.

The resources:

- :mod:`tamarind.jobs`    — submit, inspect, wait (``api`` / ``plan`` / ``flow``)
- :mod:`tamarind.files`   — workspace files (``api`` / ``plan``)
- :mod:`tamarind.catalog` — discovery: tools, schemas, modalities (``api`` / ``plan``)

Shared infrastructure: :mod:`tamarind.http` (transport), :mod:`tamarind.config`
(credentials and profiles), :mod:`tamarind.errors` (one exception hierarchy, each
carrying a stable exit code), :mod:`tamarind.upload` (streaming PUT to a presigned
URL), :mod:`tamarind.redact` (stripping credential-bearing URLs out of payloads).

The command layer lives under ``tamarind.cli`` and is deliberately thin: it parses
arguments and renders results. Nothing below it imports typer or writes to stdout,
which is what makes every one of these functions usable from a script or a notebook
— ``tests/test_layering.py`` enforces that rather than trusting it.

The request/response contract is the same OpenAPI spec the Tamarind MCP server is
built from, so the CLI and the MCP cannot drift on it. Discovery goes through the
server-side ``/catalog/*`` routes rather than reimplementing per-org visibility.

:mod:`tamarind.rest` is the pre-split job/file namespace, kept as a deprecated shim.
"""

from importlib.metadata import PackageNotFoundError, version as _pkg_version

try:
    # Single source of truth: the installed package version (pyproject.toml),
    # so `tamarind --version` can never drift from the released version.
    __version__ = _pkg_version("tamarind-cli")
except PackageNotFoundError:  # running from a source tree with no install metadata
    __version__ = "0.0.0+dev"
