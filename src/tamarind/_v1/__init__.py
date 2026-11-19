"""The v1 API client, private to this package (``https://api.tamarind.bio``).

The public entry point is :class:`tamarind.Tamarind`. When the server turns v1 on for
a key (``tamarind._v1.switch``), today's methods are answered from v1
(``tamarind._v1.classic``), and the operations only v1 has are reached through the
same client (``tamarind._v1.public``). Nothing outside this package imports it except
the CLI, which builds its v1-only commands on it.

One method per operation, named from the contract's ``x-clients.sdk``; see
:mod:`tamarind._v1.client`.

``tamarind._v1._generated`` is the openapi-python-client output for
``openapi/api-v1.yaml``, the v1 contract vendored from tamarind-website, and
``tamarind._v1._contract`` holds what its request builders can't express (comma-joined
list parameters). Refresh both with ``scripts/sync_api_v1_contract.py``; CI fails when
either is stale.

The client uses only the generated request builders (each endpoint's ``_get_kwargs``)
and reads every answer itself. The generated ``sync``/``sync_detailed`` response parsers
are not a supported surface: they assume JSON, so they can't read file bytes
(``delivery=inline``) or CSV, and they pick the first ``oneOf`` model that parses.
"""

from typing import Any

__all__ = ["ProblemError", "TERMINAL_STATUSES", "Tamarind", "paginate"]


def __getattr__(name: str) -> Any:
    # Loaded on first use: `import tamarind` shouldn't pay for the generated client.
    if name == "ProblemError":
        from tamarind._v1.errors import ProblemError

        return ProblemError
    if name in ("Tamarind", "TERMINAL_STATUSES", "paginate"):
        from tamarind._v1 import client

        return client.Tamarind.paginate if name == "paginate" else getattr(client, name)
    raise AttributeError(f"module 'tamarind._v1' has no attribute {name!r}")
