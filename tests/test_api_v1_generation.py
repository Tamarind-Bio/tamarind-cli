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

from sync_api_v1_contract import load_contract, operations  # noqa: E402

from tamarind._v1._generated import AuthenticatedClient  # noqa: E402
from tamarind._v1._generated.api.jobs import list_jobs, validate_job  # noqa: E402
from tamarind._v1._generated.models.job_page import JobPage  # noqa: E402
from tamarind._v1._generated.models.submit_job_request import SubmitJobRequest  # noqa: E402
from tamarind._v1._generated.models.problem import Problem  # noqa: E402

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
            f"tamarind._v1._generated.api.{tag}.{_snake(operation['operationId'])}"
        )
        kwargs = module._get_kwargs.__code__.co_varnames
        assert hasattr(module, "sync_detailed"), operation["operationId"]
        assert "tamarind_version" in kwargs, operation["operationId"]
        source = inspect.getsource(module._get_kwargs)
        assert f'"method": "{method}"' in source, operation["operationId"]
        assert path.split("{")[0].rstrip("/") in source, operation["operationId"]


def test_the_contract_generates_without_workarounds() -> None:
    # Both generator blockers are fixed in the contract itself (website#7081 7c3fe34):
    # the version header is a plain string and every channel field shares one enum.
    document = _contract()
    version = document["components"]["parameters"]["TamarindVersion"]["schema"]
    assert version == {**version, "type": "string"} and "format" not in version
    source = document["components"]["schemas"]["Batch"]["properties"]["source"]
    assert source["$ref"] == "#/components/schemas/SubmissionChannel"
    from tamarind._v1._generated.models.batch import Batch
    from tamarind._v1._generated.models.submission_channel import SubmissionChannel

    assert "source" in Batch.__annotations__ and SubmissionChannel("cli").value == "cli"


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


def test_comma_joined_query_parameters_match_the_contract() -> None:
    from tamarind._v1._contract import COMMA_JOINED_QUERY

    assert COMMA_JOINED_QUERY["list_jobs"] == {"status"}
    assert COMMA_JOINED_QUERY["list_files"] == {"extension"}
    # Default form-style arrays repeat the key, so they are not listed.
    assert "list_molecules" not in COMMA_JOINED_QUERY
