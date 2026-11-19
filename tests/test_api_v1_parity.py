"""Parity: every operation in the v1 contract has its SDK method (DESIGN, "Parity").

Each operation's ``x-clients.sdk`` (``projects.notes.createEntry``) must resolve on a
``tamarind.v1.Tamarind`` client in snake_case (``projects.notes.create_entry``), and a
1:1 method must be built on that operation's generated module with the path
parameters in path order. Fails when the contract gains an operation the SDK lacks.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from sync_api_v1_contract import load_contract, operations  # noqa: E402

from tamarind.v1 import Tamarind  # noqa: E402
from tamarind.v1.client import BoundOperation  # noqa: E402

# Operations whose x-clients method is a documented helper rather than a 1:1 method.
HELPERS = {"uploadFile": "files.upload", "completeFileUpload": "files.upload"}


def _snake(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def _resolve(client: Any, dotted: str) -> Any:
    target = client
    for part in dotted.split("."):
        target = getattr(target, _snake(part), None)
        if target is None:
            return None
    return target


def _sdk_operations(client: Tamarind) -> dict[str, BoundOperation]:
    found = {}
    resources = [(name, value) for name, value in vars(client).items() if not name.startswith("_")]
    while resources:
        prefix, resource = resources.pop()
        for name in dir(resource):
            if name.startswith("_"):
                continue
            value = getattr(resource, name)
            if isinstance(value, BoundOperation):
                found[f"{prefix}.{name}"] = value
            elif hasattr(value, "_transport") and not callable(value):
                resources.append((f"{prefix}.{name}", value))
    return found


def test_every_operation_has_an_sdk_method() -> None:
    document = load_contract((ROOT / "openapi/api-v1.yaml").read_bytes())
    client = Tamarind("k", base_url="https://api.test")
    missing, wrong = [], []
    covered = set()
    for _method, path, operation in operations(document):
        operation_id = operation["operationId"]
        sdk = operation["x-clients"]["sdk"]
        method = _resolve(client, sdk)
        if method is None or not callable(method):
            missing.append(f"{operation_id} -> {sdk}")
            continue
        if operation_id in HELPERS:
            assert HELPERS[operation_id] == sdk
            continue
        if not isinstance(method, BoundOperation):
            wrong.append(f"{sdk} is not a 1:1 method")
            continue
        module = method.operation.endpoint.__name__.rsplit(".", 1)[-1]
        if module != _snake(operation_id):
            wrong.append(f"{sdk} calls {module}, not {_snake(operation_id)}")
        placeholders = tuple(_snake(name) for name in re.findall(r"{([^}]+)}", path))
        if method.operation.path != placeholders:
            wrong.append(f"{sdk} takes {method.operation.path}, path has {placeholders}")
        covered.add(".".join(_snake(part) for part in sdk.split(".")))
    assert not missing, "operations without an SDK method:\n" + "\n".join(missing)
    assert not wrong, "\n".join(wrong)
    extra = set(_sdk_operations(client)) - covered
    assert not extra, f"SDK methods with no contract operation: {sorted(extra)}"
    assert len(covered) == len(operations(document)) - len(HELPERS)
