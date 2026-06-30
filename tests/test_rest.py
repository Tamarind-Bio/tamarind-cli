import json

import httpx
import pytest
import respx

from tamarind import catalog, rest
from tamarind.errors import AuthError, NotFoundError, RateLimitError, ValidationError
from tamarind.http import HTTPClient

BASE = "https://api.test/"
CAT = "https://catalog.test/"


def client(base=BASE):
    return HTTPClient(base, "test-key")


@respx.mock
def test_submit_job_body():
    route = respx.post(f"{BASE}submit-job").mock(return_value=httpx.Response(200, json={"ok": True}))
    rest.submit_job(client(), job_name="run1", job_type="boltz", settings={"sequence": "ABC"})
    body = json.loads(route.calls.last.request.content)
    assert body == {"jobName": "run1", "type": "boltz", "settings": {"sequence": "ABC"}}
    assert route.calls.last.request.headers["x-api-key"] == "test-key"


@respx.mock
def test_get_jobs_param_handling():
    route = respx.get(f"{BASE}jobs").mock(return_value=httpx.Response(200, json={"jobs": []}))
    rest.get_jobs(client(), limit=5, organization=True, include_subjobs=False)
    params = route.calls.last.request.url.params
    assert params["limit"] == "5"
    assert params["organization"] == "true"
    # None and False-as-absent params are dropped, not sent as "None"/"false"
    assert "jobName" not in params
    assert "includeSubjobs" not in params


@respx.mock
def test_validate_job_returns_body():
    respx.post(f"{BASE}validate-job").mock(
        return_value=httpx.Response(200, json={"valid": False, "error": "missing sequence"})
    )
    out = rest.validate_job(client(), job_name="x", job_type="boltz", settings={})
    assert out["valid"] is False
    assert "missing" in out["error"]


@respx.mock
def test_result_returns_presigned_string():
    respx.post(f"{BASE}result").mock(return_value=httpx.Response(200, text="https://s3/result.zip"))
    out = rest.get_result(client(), job_name="x")
    assert out == "https://s3/result.zip"


@respx.mock
def test_delete_job_uses_delete_verb():
    route = respx.delete(f"{BASE}delete-job").mock(return_value=httpx.Response(200, json={"message": "ok"}))
    rest.delete_job(client(), job_name="x")
    assert route.calls.last.request.method == "DELETE"
    assert json.loads(route.calls.last.request.content) == {"jobName": "x"}


@respx.mock
def test_delete_job_tolerates_string_response():
    # The endpoint can return a bare string, not JSON — must not raise.
    respx.delete(f"{BASE}delete-job").mock(return_value=httpx.Response(200, text="x deleted"))
    out = rest.delete_job(client(), job_name="x")
    assert out == "x deleted"


@respx.mock
@pytest.mark.parametrize(
    "status,exc",
    [(401, AuthError), (403, AuthError), (404, NotFoundError), (400, ValidationError), (429, RateLimitError)],
)
def test_error_mapping(status, exc):
    respx.get(f"{BASE}jobs").mock(return_value=httpx.Response(status, json={"error": "boom"}))
    with pytest.raises(exc):
        rest.get_jobs(client())


@respx.mock
@pytest.mark.parametrize(
    "message,exc",
    [
        ("Missing or incorrect API key", AuthError),       # bad key -> auth (3)
        ("Job 'x' not found", NotFoundError),               # -> not-found (4)
        ("file does not exist", NotFoundError),             # -> not-found (4)
        ("Unrecognized setting: foo", ValidationError),     # genuine -> validation (5)
    ],
)
def test_400_subtype_classification(message, exc):
    # The API overloads HTTP 400; the client classifies by message for stable exit codes.
    respx.get(f"{BASE}jobs").mock(return_value=httpx.Response(400, json={"error": message}))
    with pytest.raises(exc):
        rest.get_jobs(client())


def test_missing_key_raises_auth():
    c = HTTPClient(BASE, None)
    with pytest.raises(AuthError):
        rest.get_jobs(c)


@respx.mock
def test_delete_file_uses_delete():
    route = respx.delete(f"{BASE}delete-file").mock(
        return_value=httpx.Response(200, json={"message": "deleted"})
    )
    out = rest.delete_file(client(), file_path="x.txt")
    assert route.called
    assert out["message"] == "deleted"


@respx.mock
def test_delete_file_falls_back_to_get_on_405():
    # Older deployments may only accept GET; fall back when DELETE returns 405.
    respx.delete(f"{BASE}delete-file").mock(
        return_value=httpx.Response(405, json={"error": "Method not allowed"})
    )
    route = respx.get(f"{BASE}delete-file").mock(
        return_value=httpx.Response(200, json={"message": "deleted via get"})
    )
    out = rest.delete_file(client(), file_path="x.txt")
    assert route.called
    assert out["message"] == "deleted via get"


@respx.mock
def test_catalog_schema_path():
    route = respx.get(f"{CAT}catalog/tools/boltz/schema").mock(
        return_value=httpx.Response(200, json={"jobType": "boltz", "parameters": []})
    )
    out = catalog.get_schema(client(CAT), "boltz")
    assert route.called
    assert out["jobType"] == "boltz"


@respx.mock
def test_catalog_tools_filters():
    route = respx.get(f"{CAT}catalog/tools").mock(return_value=httpx.Response(200, json={"tools": []}))
    catalog.list_tools(client(CAT), modality="protein", function="structure-prediction", custom=True)
    params = route.calls.last.request.url.params
    assert params["modality"] == "protein"
    assert params["function"] == "structure-prediction"
    assert params["custom"] == "true"
