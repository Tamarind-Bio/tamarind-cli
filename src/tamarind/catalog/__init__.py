"""Tool discovery.

Layers as elsewhere — `api` for the ``/catalog/*`` routes, `plan` for the pure schema
helpers. The public surface is re-exported, so ``from tamarind import catalog`` works
exactly as it did when this was a single module.
"""

from __future__ import annotations

from .api import CATALOG_PREFIX, get_schema, list_functions, list_modalities, list_tools
from .plan import example_settings, required_param_names

__all__ = [
    "CATALOG_PREFIX",
    "example_settings",
    "get_schema",
    "list_functions",
    "list_modalities",
    "list_tools",
    "required_param_names",
]
