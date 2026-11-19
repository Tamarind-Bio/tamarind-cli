"""Tamarind API v1 Python SDK (``https://api.tamarind.bio``).

``tamarind.v1._generated`` is the openapi-python-client output for
``openapi/api-v1.yaml``, the v1 contract vendored from tamarind-website, and
``tamarind.v1._contract`` holds what its request builders can't express (comma-joined
list parameters). Refresh both with ``scripts/sync_api_v1_contract.py``; CI fails when
either is stale.

The SDK uses only the generated request builders (each endpoint's ``_get_kwargs``) and
reads every answer itself. The generated ``sync``/``sync_detailed`` response parsers
are not a supported surface: they assume JSON, so they can't read file bytes
(``delivery=inline``) or CSV, and they pick the first ``oneOf`` model that parses.

This is a separate surface from the classic ``https://app.tamarind.bio/api`` client
(``tamarind.rest``, ``tamarind.Tamarind``), which is unchanged.
"""
