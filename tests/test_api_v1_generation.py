"""Smoke tests for the generated Tamarind API v1 client."""

from __future__ import annotations

from hashlib import sha256
import importlib
import inspect
import json
from pathlib import Path
import re
import sys

import httpx
import respx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from sync_api_v1_contract import load_contract, operations, project_contract  # noqa: E402

from tamarind.v1._generated import AuthenticatedClient  # noqa: E402
from tamarind.v1._generated.api.jobs import list_jobs, validate_job  # noqa: E402
from tamarind.v1._generated.models.job_page import JobPage  # noqa: E402
from tamarind.v1._generated.models.submit_job_request import SubmitJobRequest  # noqa: E402
from tamarind.v1._generated.models.problem import Problem  # noqa: E402

BASE = "https://api.test.tamarind.bio"


def _contract() -> dict:
    return load_contract((ROOT / "openapi/api-v1.yaml").read_bytes())


def _snake(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def test_vendored_contract_matches_its_lock() -> None:
    lock = json.loads((ROOT / "openapi/api-v1.lock.json").read_text())
    raw = (ROOT / "openapi/api-v1.yaml").read_bytes()
    assert sha256(raw).hexdigest() == lock["artifactSha256"]
    assert lock["sourcePath"] == "documentation/api-redesign/openapi-v1.yaml"


def test_every_operation_has_a_generated_endpoint() -> None:
    document = _contract()
    found = operations(document)
    assert len(found) >= 100
    for method, path, operation in found:
        tag = re.sub(r"[^a-z0-9]+", "_", operation["tags"][0].lower())
        module = importlib.import_module(
            f"tamarind.v1._generated.api.{tag}.{_snake(operation['operationId'])}"
        )
        kwargs = module._get_kwargs.__code__.co_varnames
        assert hasattr(module, "sync_detailed"), operation["operationId"]
        assert "tamarind_version" in kwargs, operation["operationId"]
        source = inspect.getsource(module._get_kwargs)
        assert f'"method": "{method}"' in source, operation["operationId"]
        assert path.split("{")[0].rstrip("/") in source, operation["operationId"]


def test_projection_changes_only_the_two_generator_workarounds() -> None:
    document = _contract()
    projected = project_contract(document)
    version = projected["components"]["parameters"]["TamarindVersion"]["schema"]
    assert "format" not in version
    assert projected["components"]["schemas"]["Batch"]["properties"]["source"]["title"] == "Channel"
    # Undo both workarounds and nothing else differs.
    version["format"] = document["components"]["parameters"]["TamarindVersion"]["schema"]["format"]
    projected["components"]["schemas"]["Batch"]["properties"]["source"].pop("title")
    assert projected == document
    assert project_contract(projected) == project_contract(document)


@respx.mock
def test_generated_client_parses_pages_and_problems() -> None:
    client = AuthenticatedClient(
        base_url=BASE, token="test-key", prefix="", auth_header_name="x-api-key"
    )
    route = respx.get(f"{BASE}/jobs").mock(
        return_value=httpx.Response(200, json={"items": [], "nextCursor": None})
    )
    page = list_jobs.sync(client=client, limit=10)
    assert isinstance(page, JobPage)
    assert page.items == [] and page.next_cursor is None
    sent = route.calls.last.request
    assert sent.headers["x-api-key"] == "test-key"
    assert sent.url.params["limit"] == "10"

    problem = {
        "type": "https://docs.tamarind.bio/errors/validation_failed",
        "title": "Unprocessable Content",
        "status": 422,
        "code": "validation_failed",
        "detail": "2 settings are invalid.",
        "requestId": "req_1",
        "errors": [
            {
                "code": "required",
                "severity": "error",
                "pointer": "/settings/sequence",
                "detail": "x",
            },
            {
                "code": "unknown_field",
                "severity": "error",
                "pointer": "/settings/foo",
                "detail": "y",
            },
        ],
    }
    respx.post(f"{BASE}/jobs/validate").mock(return_value=httpx.Response(422, json=problem))
    body = SubmitJobRequest.from_dict({"tool": "esmfold", "settings": {}})
    parsed = validate_job.sync(client=client, body=body)
    assert isinstance(parsed, Problem)
    assert parsed.code == "validation_failed" and parsed.status == 422
    assert len(parsed.errors) == 2
