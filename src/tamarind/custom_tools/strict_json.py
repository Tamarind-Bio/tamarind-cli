"""Strict JSON for config.json: no NaN/Infinity, no duplicate members.

Shared by the archive validator and the finetune compiler so that a sync of the finetune block
can never launder a malformed config.json past the validation that runs after it.
"""

from __future__ import annotations

import json
from typing import NoReturn


def _reject_json_constant(value: str) -> NoReturn:
    raise ValueError(f"non-standard JSON constant {value!r}")


def _object_without_duplicate_members(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for name, member in pairs:
        if name in value:
            raise ValueError(f"duplicate JSON object member {name!r}")
        value[name] = member
    return value


def load_strict_json(raw: str) -> object:
    return json.loads(
        raw,
        parse_constant=_reject_json_constant,
        object_pairs_hook=_object_without_duplicate_members,
    )
