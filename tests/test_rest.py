import json

import httpx
import pytest
import respx

from tamarind import catalog, rest
from tamarind.errors import (
    APIError,
    AuthError,
    BudgetError,
    CustomToolBuildInProgressError,
    CustomToolBuildNotInProgressError,
    CustomToolExistsError,
    CustomToolNotFoundError,
    CustomToolNotDeployableError,
    CustomToolUploadError,
    CustomToolValidationError,
    NotFoundError,
    RateLimitError,
    StaleCustomToolError,
    TamarindError,
    ValidationError,
)
from tamarind.http import HTTPClient

BASE = "https://api.test/"
CAT = "https://catalog.test/"


def client(base=BASE):
    return HTTPClient(base, "test-key")


@respx.mock
def test_submit_job_body():
    route = respx.post(f"{BASE}submit-job").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )
    rest.submit_job(client(), job_name="run1", job_type="boltz", settings={"sequence": "ABC"})
    body = json.loads(route.calls.last.request.content)
    # jobSource="CLI" is stamped on every submission for usage tracking.
    assert body == {
        "jobName": "run1",
        "type": "boltz",
        "settings": {"sequence": "ABC"},
        "jobSource": "CLI",
    }
    assert route.calls.last.request.headers["x-api-key"] == "test-key"


@respx.mock
def test_submit_batch_body():
    route = respx.post(f"{BASE}submit-batch").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )
    rest.submit_batch(
        client(),
        batch_name="b1",
        job_type="boltz",
        settings=[{"sequence": "ABC"}],
        job_names=["b1-1"],
    )
    body = json.loads(route.calls.last.request.content)
    assert body["jobSource"] == "CLI"
    assert body["batchName"] == "b1" and body["jobNames"] == ["b1-1"]


@respx.mock
def test_submit_finetune_body():
    route = respx.post(f"{BASE}finetune").mock(return_value=httpx.Response(200, json={"ok": True}))
    rest.submit_finetune(client(), job_name="ft1", model="esm2", settings={"sequence": "ABC"})
    body = json.loads(route.calls.last.request.content)
    # Same envelope as /submit-job, except the tool name rides in `model`.
    assert body == {
        "jobName": "ft1",
        "model": "esm2",
        "settings": {"sequence": "ABC"},
        "jobSource": "CLI",
    }
    assert route.calls.last.request.headers["x-api-key"] == "test-key"


@respx.mock
def test_submit_finetune_batch_body():
    route = respx.post(f"{BASE}finetune-batch").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )
    rest.submit_finetune_batch(
        client(),
        batch_name="fb1",
        model="esm2",
        settings=[{"sequence": "ABC"}],
        job_names=["fb1-1"],
        max_runtime_seconds=600,
    )
    assert json.loads(route.calls.last.request.content) == {
        "batchName": "fb1",
        "model": "esm2",
        "settings": [{"sequence": "ABC"}],
        "jobSource": "CLI",
        "jobNames": ["fb1-1"],
        "maxRuntimeSeconds": 600,
    }


# ---------------------------------------------------------------------------
# The finetune routing table. Which tools are finetuning tools is knowable only
# server-side, so a submission sent to the wrong sibling route is resent ONCE to
# the right one with the tool-name key renamed. These tests are the table.
# ---------------------------------------------------------------------------

# Each entry submits through one of the four routes with an identical payload
# shape, so a resend's body can be compared field-for-field with the original.
SUBMISSIONS = {
    "submit-job": lambda c: rest.submit_job(
        c, job_name="j1", job_type="esm2", settings={"sequence": "ABC"}
    ),
    "submit-batch": lambda c: rest.submit_batch(
        c,
        batch_name="b1",
        job_type="esm2",
        settings=[{"sequence": "ABC"}],
        job_names=["b1-1"],
        max_runtime_seconds=900,
    ),
    "finetune": lambda c: rest.submit_finetune(
        c, job_name="j1", model="esm2", settings={"sequence": "ABC"}
    ),
    "finetune-batch": lambda c: rest.submit_finetune_batch(
        c,
        batch_name="b1",
        model="esm2",
        settings=[{"sequence": "ABC"}],
        job_names=["b1-1"],
        max_runtime_seconds=900,
    ),
}


@respx.mock
@pytest.mark.parametrize(
    "origin,origin_key,sibling,sibling_key,status,code",
    [
        # /submit-job and /submit-batch: only the explicit 400 problem code reroutes.
        ("submit-job", "type", "finetune", "model", 400, "use_finetune_endpoint"),
        ("submit-batch", "type", "finetune-batch", "model", 400, "use_finetune_endpoint"),
        # /finetune and /finetune-batch: the 400 problem code, OR an exact 404.
        ("finetune", "model", "submit-job", "type", 400, "not_a_finetune_tool"),
        ("finetune-batch", "model", "submit-batch", "type", 400, "not_a_finetune_tool"),
        # The 404 rows are why this ships safely before the server routes exist:
        # an older deployment has no /finetune* at all.
        ("finetune", "model", "submit-job", "type", 404, None),
        ("finetune-batch", "model", "submit-batch", "type", 404, None),
    ],
)
def test_misrouted_submission_is_resent_once_to_the_sibling_route(
    origin, origin_key, sibling, sibling_key, status, code
):
    refusal = {"error": "wrong route"}
    if code:
        refusal["code"] = code
    first = respx.post(f"{BASE}{origin}").mock(return_value=httpx.Response(status, json=refusal))
    second = respx.post(f"{BASE}{sibling}").mock(
        return_value=httpx.Response(200, json={"message": "queued"})
    )

    assert SUBMISSIONS[origin](client()) == {"message": "queued"}

    assert first.call_count == 1
    assert second.call_count == 1
    sent = json.loads(first.calls.last.request.content)
    resent = json.loads(second.calls.last.request.content)
    # Only the tool-name key is renamed; its value and every other field survive.
    assert sent.pop(origin_key) == resent.pop(sibling_key) == "esm2"
    assert origin_key not in resent and sibling_key not in sent
    assert resent == sent
    assert sent["jobSource"] == "CLI"
    assert second.calls.last.request.headers["x-api-key"] == "test-key"


@respx.mock
@pytest.mark.parametrize(
    "origin,sibling,status,body,exc",
    [
        # A 400 with any other problem code is a genuine caller error.
        ("submit-job", "finetune", 400, {"code": "invalid_settings", "error": "bad"}, ValidationError),
        ("finetune", "submit-job", 400, {"code": "model_required", "error": "model is required"}, ValidationError),
        # A 400 with no JSON body has no problem code to trust.
        ("submit-job", "finetune", 400, None, ValidationError),
        ("finetune", "submit-job", 400, None, ValidationError),
        # The code only counts on a 400: a 403 carrying it is still a refusal.
        ("submit-job", "finetune", 403, {"code": "use_finetune_endpoint", "error": "denied"}, APIError),
        ("finetune", "submit-job", 403, {"code": "not_a_finetune_tool", "error": "denied"}, APIError),
        # Only an EXACT 404 falls back, and only from the /finetune* rows.
        ("finetune", "submit-job", 405, {"error": "Method not allowed"}, APIError),
        ("submit-job", "finetune", 404, {"error": "Not Found"}, NotFoundError),
        ("submit-batch", "finetune-batch", 404, {"error": "Not Found"}, NotFoundError),
        # A 5xx may already have created the job; resending would submit twice.
        ("submit-job", "finetune", 500, {"error": "boom"}, APIError),
        ("submit-batch", "finetune-batch", 503, {"error": "boom"}, APIError),
        ("finetune", "submit-job", 500, {"error": "boom"}, APIError),
        ("finetune-batch", "submit-batch", 502, {"error": "boom"}, APIError),
    ],
)
def test_refusals_that_must_not_be_resent(origin, sibling, status, body, exc):
    refusal = (
        httpx.Response(status, json=body)
        if body is not None
        else httpx.Response(status, text="<html>upstream refused</html>")
    )
    first = respx.post(f"{BASE}{origin}").mock(return_value=refusal)
    second = respx.post(f"{BASE}{sibling}").mock(
        return_value=httpx.Response(200, json={"message": "must never be reached"})
    )

    with pytest.raises(exc):
        SUBMISSIONS[origin](client())

    assert first.call_count == 1
    assert not second.called


@respx.mock
@pytest.mark.parametrize(
    "origin,first_code,sibling,status,body,exc",
    [
        ("submit-job", "use_finetune_endpoint", "finetune", 400,
         {"code": "not_a_finetune_tool", "error": "second refusal"}, ValidationError),
        ("submit-batch", "use_finetune_endpoint", "finetune-batch", 400,
         {"code": "not_a_finetune_tool", "error": "second refusal"}, ValidationError),
        ("finetune", "not_a_finetune_tool", "submit-job", 400,
         {"code": "use_finetune_endpoint", "error": "second refusal"}, ValidationError),
        ("finetune-batch", "not_a_finetune_tool", "submit-batch", 400,
         {"code": "use_finetune_endpoint", "error": "second refusal"}, ValidationError),
        # A 404 on the resend is not a licence to bounce back either.
        ("finetune", "not_a_finetune_tool", "submit-job", 404,
         {"error": "second refusal"}, NotFoundError),
    ],
)
def test_a_resend_that_is_refused_again_is_returned_as_is(
    origin, first_code, sibling, status, body, exc
):
    # The origin would answer 200 on a SECOND visit, so an implementation that
    # ping-pongs succeeds here instead of raising — the assertion is real.
    first = respx.post(f"{BASE}{origin}").mock(
        side_effect=[
            httpx.Response(400, json={"code": first_code, "error": "first refusal"}),
            httpx.Response(200, json={"message": "a third request must never happen"}),
        ]
    )
    second = respx.post(f"{BASE}{sibling}").mock(return_value=httpx.Response(status, json=body))

    with pytest.raises(exc, match="second refusal"):
        SUBMISSIONS[origin](client())

    assert first.call_count == 1
    assert second.call_count == 1


@respx.mock
@pytest.mark.parametrize("origin,sibling", list(
    zip(
        ["submit-job", "submit-batch", "finetune", "finetune-batch"],
        ["finetune", "finetune-batch", "submit-job", "submit-batch"],
    )
))
@pytest.mark.parametrize("failure", [httpx.ConnectError("no route"), httpx.ReadTimeout("too slow")])
def test_transport_failures_are_never_resent(origin, sibling, failure):
    # No answer means the server may have received and acted on the request.
    first = respx.post(f"{BASE}{origin}").mock(side_effect=failure)
    second = respx.post(f"{BASE}{sibling}").mock(
        return_value=httpx.Response(200, json={"message": "must never be reached"})
    )

    with pytest.raises(TamarindError) as raised:
        SUBMISSIONS[origin](client())

    assert first.call_count == 1
    assert not second.called
    # The EXACT type matters, not just the base class: cli/commands/jobs.py's
    # _outcome_is_ambiguous keys on `type(exc) is TamarindError` to decide whether a
    # submit's outcome is unknown. A subclass here would silently stop the CLI
    # reporting outcomeMayBeAmbiguous on a network failure, and a bare
    # pytest.raises(TamarindError) would not notice, since everything subclasses it.
    assert type(raised.value) is TamarindError


@respx.mock
def test_a_route_with_no_routing_row_surfaces_the_servers_own_error():
    """A submission posted through _post_submission on a route the table does not
    cover must report what the server said, not crash looking the route up."""
    from tamarind import rest

    respx.post(f"{BASE}some-future-route").mock(
        return_value=httpx.Response(400, json={"error": "Unrecognized setting: foo"})
    )

    with pytest.raises(ValidationError, match="Unrecognized setting"):
        rest._post_submission(client(), "some-future-route", {"jobName": "j", "type": "t"})


@respx.mock
@pytest.mark.parametrize("path", ["submit-job", "/submit-job"])
def test_the_routing_table_matches_a_leading_slash_too(path):
    """HTTPClient.send resolves the URL with path.lstrip("/"), so "/submit-job" and
    "submit-job" are the SAME endpoint. The routing table must agree, or a caller
    writing the leading slash silently loses its reroute with no error at all."""
    from tamarind import rest

    origin = respx.post(f"{BASE}submit-job").mock(
        return_value=httpx.Response(400, json={"code": "use_finetune_endpoint", "error": "x"})
    )
    resent = respx.post(f"{BASE}finetune").mock(
        return_value=httpx.Response(200, json={"message": "ok"})
    )

    rest._post_submission(client(), path, {"jobName": "j", "type": "plm-finetune"})

    assert origin.call_count == 1
    assert resent.call_count == 1
    assert json.loads(resent.calls.last.request.content)["model"] == "plm-finetune"


@respx.mock
def test_validate_job_not_tagged():
    # Validation never creates a job, so it carries no jobSource.
    route = respx.post(f"{BASE}validate-job").mock(
        return_value=httpx.Response(200, json={"valid": True})
    )
    rest.validate_job(client(), job_name="x", job_type="boltz", settings={})
    assert "jobSource" not in json.loads(route.calls.last.request.content)


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
def test_http_client_omits_absent_optional_headers():
    route = respx.get(f"{BASE}headers").mock(return_value=httpx.Response(200, json={}))

    client().request(
        "GET",
        "headers",
        headers={"X-Required": "present", "X-Optional": None},
    )

    headers = route.calls.last.request.headers
    assert headers["X-Required"] == "present"
    assert "X-Optional" not in headers


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
    route = respx.delete(f"{BASE}delete-job").mock(
        return_value=httpx.Response(200, json={"message": "ok"})
    )
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
    [
        (401, AuthError),
        (403, APIError),
        (404, NotFoundError),
        (400, ValidationError),
        (429, RateLimitError),
    ],
)
def test_error_mapping(status, exc):
    respx.get(f"{BASE}jobs").mock(return_value=httpx.Response(status, json={"error": "boom"}))
    with pytest.raises(exc):
        rest.get_jobs(client())


@respx.mock
def test_422_preserves_structured_validation_problem() -> None:
    problem = {
        "code": "validation_error",
        "message": "Request validation failed",
        "errors": [{"field": "name", "message": "invalid"}],
    }
    respx.get(f"{BASE}custom-tools").mock(return_value=httpx.Response(422, json=problem))

    with pytest.raises(ValidationError) as raised:
        client().get_json("custom-tools")

    assert raised.value.detail == problem


@respx.mock
def test_422_uses_problem_title_when_detail_is_absent() -> None:
    problem = {
        "type": "about:blank",
        "title": "Request validation failed",
        "status": 422,
        "detail": None,
    }
    respx.get(f"{BASE}custom-tools").mock(return_value=httpx.Response(422, json=problem))

    with pytest.raises(ValidationError, match="Request validation failed") as raised:
        client().get_json("custom-tools")

    assert raised.value.detail == problem


@respx.mock
@pytest.mark.parametrize(
    "code,exc",
    [
        ("custom_tool_not_found", CustomToolNotFoundError),
        ("custom_tool_version_not_found", CustomToolNotFoundError),
        ("custom_tool_name_taken", CustomToolExistsError),
        ("custom_tool_not_deployable", CustomToolNotDeployableError),
        ("invalid_custom_tool_config", CustomToolValidationError),
        ("invalid_custom_tool_source", CustomToolValidationError),
        ("custom_tool_generation_mismatch", StaleCustomToolError),
        ("custom_tool_source_changed", StaleCustomToolError),
        ("custom_tool_source_digest_mismatch", CustomToolUploadError),
        ("custom_tool_upload_not_found", CustomToolUploadError),
        ("custom_tool_build_in_progress", CustomToolBuildInProgressError),
        ("custom_tool_build_not_cancellable", CustomToolBuildNotInProgressError),
    ],
)
def test_custom_tool_problem_codes_have_stable_error_types(code, exc) -> None:
    problem = {
        "type": f"https://app.tamarind.bio/errors/{code}",
        "title": "Custom Tool request failed",
        "status": 409,
        "code": code,
        "detail": "actionable detail",
        "errors": [{"field": "config.json", "message": "specific diagnosis"}],
    }
    respx.get(f"{BASE}custom-tools/example").mock(return_value=httpx.Response(409, json=problem))

    with pytest.raises(exc, match="actionable detail") as raised:
        client().get_json("custom-tools/example")

    assert raised.value.detail == problem


@respx.mock
@pytest.mark.parametrize(
    "body,exc",
    [
        ({"error": "Missing or incorrect API key"}, AuthError),  # bad key -> auth (3)
        ({"error": "Job 'x' not found"}, NotFoundError),  # -> not-found (4)
        ({"error": "file does not exist"}, NotFoundError),  # -> not-found (4)
        ({"error": "Unrecognized setting: foo"}, ValidationError),  # genuine -> validation (5)
        # The finetune routes' real messages, classified by problem code rather
        # than wording. Both of the first two quote the caller's own tool name
        # back, so a tool named "no such thing" would otherwise read as a missing
        # resource and get exit code 4 instead of 5.
        (
            {
                "code": "not_a_finetune_tool",
                "error": '"no such thing" is not a finetuning tool. Submit it with POST /submit-job.',
            },
            ValidationError,
        ),
        (
            {
                "code": "use_finetune_endpoint",
                "error": '"not found here" is a finetuning tool. Submit it with POST /finetune.',
            },
            ValidationError,
        ),
        ({"code": "model_required", "error": "model is required"}, ValidationError),
        (
            {
                "code": "type_model_mismatch",
                "error": '"type" ("a") does not match "model" ("b"). Send only "model" to POST /finetune.',
            },
            ValidationError,
        ),
    ],
)
def test_400_subtype_classification(body, exc):
    # The API overloads HTTP 400; the client classifies by problem code when the
    # server sends one, and by message otherwise, for stable exit codes.
    respx.get(f"{BASE}jobs").mock(return_value=httpx.Response(400, json=body))
    with pytest.raises(exc) as raised:
        rest.get_jobs(client())
    assert raised.value.detail == body


@respx.mock
@pytest.mark.parametrize(
    "message,exc",
    [
        ("Invalid API key", AuthError),
        ("Weighted hours budget exceeded", BudgetError),
        ("Weighted-hours quota exhausted", BudgetError),
        ("Organization spend limit reached", BudgetError),
        ("Monthly usage cap exceeded", BudgetError),
        ("Insufficient credits", BudgetError),
        ("This resource is forbidden by policy", APIError),
    ],
)
def test_403_subtype_classification(message, exc):
    respx.get(f"{BASE}jobs").mock(return_value=httpx.Response(403, json={"error": message}))
    with pytest.raises(exc):
        rest.get_jobs(client())


@respx.mock
@pytest.mark.parametrize(
    "message",
    [
        "Budget administration is forbidden by policy",
        "Quota settings are not accessible",
        "Credit report access is forbidden",
        "The organization is accredited but this resource is forbidden",
    ],
)
def test_403_resource_words_without_exhaustion_are_not_budget_errors(message):
    respx.get(f"{BASE}jobs").mock(return_value=httpx.Response(403, json={"error": message}))
    with pytest.raises(APIError):
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
    route = respx.get(f"{CAT}catalog/tools").mock(
        return_value=httpx.Response(200, json={"tools": []})
    )
    catalog.list_tools(
        client(CAT), modality="protein", function="structure-prediction", custom=True
    )
    params = route.calls.last.request.url.params
    assert params["modality"] == "protein"
    assert params["function"] == "structure-prediction"
    assert params["custom"] == "true"
