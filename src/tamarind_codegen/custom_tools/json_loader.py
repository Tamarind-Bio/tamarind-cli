"""Strict JSON loading for generated-contract entry points."""

from __future__ import annotations

import json
import math
from decimal import Decimal
from typing import Any, NoReturn


def _reject_constant(value: str) -> NoReturn:
    raise ValueError(f"non-standard JSON constant {value!r}")


def _object_without_duplicate_members(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object member {key!r}")
        result[key] = value
    return result


def _finite_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed):
        raise ValueError(f"JSON number is outside the finite float range: {value!r}")
    if Decimal.from_float(parsed) != Decimal(value):
        raise ValueError(f"JSON number cannot be represented exactly as a float: {value!r}")
    return parsed


def load_json_document(raw: str | bytes) -> Any:
    """Parse standards-compliant JSON without silently discarding duplicate members."""
    return json.loads(
        raw,
        parse_float=_finite_float,
        parse_constant=_reject_constant,
        object_pairs_hook=_object_without_duplicate_members,
    )
