"""Tamarind Bio CLI and Python client.

This package is a thin client over the Tamarind platform. Two surfaces:

- REST passthrough (``tamarind.rest``): submit/validate/batch, jobs, result,
  files, cancel, delete — these hit the Tamarind API directly with an API key.
  The request/response contract is the same OpenAPI spec the Tamarind MCP server
  is built from, so the CLI and the MCP cannot drift on this surface.

- Discovery (``tamarind.catalog``): tools, schema, modalities, functions. The
  catalog lives behind per-org visibility logic that runs server-side, so the
  CLI consumes it over HTTP (the ``/catalog/*`` routes) rather than reading the
  database directly.
"""

from importlib.metadata import PackageNotFoundError, version as _pkg_version

try:
    # Single source of truth: the installed package version (pyproject.toml),
    # so `tamarind --version` can never drift from the released version.
    __version__ = _pkg_version("tamarind-cli")
except PackageNotFoundError:  # running from a source tree with no install metadata
    __version__ = "0.0.0+dev"
