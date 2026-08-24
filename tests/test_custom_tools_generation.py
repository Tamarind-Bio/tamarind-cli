from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_vendored_contract_is_the_dedicated_backend_artifact() -> None:
    document = json.loads((ROOT / "openapi/public-v1.json").read_text())
    assert document["paths"]
    assert all(path.startswith("/custom-tools") for path in document["paths"])
    assert not any(
        parameter.get("name") == "If-Match"
        for path, item in document["paths"].items()
        if "/generations/{generation}/" in path
        for operation in item.values()
        if isinstance(operation, dict)
        for parameter in operation.get("parameters", [])
    )


def test_generated_client_contains_sync_async_endpoints_and_attrs_models() -> None:
    from tamarind.custom_tools._generated.api.custom_tools import get_custom_tool_version
    from tamarind.custom_tools._generated.models.public_version import PublicVersion

    assert callable(get_custom_tool_version.sync)
    assert callable(get_custom_tool_version.asyncio)
    assert callable(PublicVersion.from_dict)
    assert callable(PublicVersion.to_dict)


def test_generator_is_exactly_pinned() -> None:
    pyproject = (ROOT / "pyproject.toml").read_text()
    lock = json.loads((ROOT / "openapi/public-v1.lock.json").read_text())
    assert '"openapi-python-client==0.28.4"' in pyproject
    assert lock["generator"] == "openapi-python-client==0.28.4"
