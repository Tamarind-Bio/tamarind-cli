"""Agent-facing CLI contract: structured failures and safe job completion."""

from __future__ import annotations

import json
import sys

import httpx
import pytest
import respx
from typer.testing import CliRunner

from tamarind.cli import main as main_module
from tamarind.cli.commands import jobs as jobs_commands
from tamarind.cli.main import app
from tamarind.errors import ExitCode, TamarindError, ValidationError


runner = CliRunner()
API = "https://api.test/"
CAT = "https://cat.test/"
ENV = {
    "TAMARIND_API_KEY": "k",
    "TAMARIND_API_BASE": API,
    "TAMARIND_CATALOG_BASE": CAT,
}


@respx.mock
@pytest.mark.parametrize(
    ("message", "expected_code", "expected_type"),
    [
        ("Weighted hours budget exceeded", ExitCode.BUDGET, "BudgetError"),
        ("This resource is forbidden by policy", ExitCode.ERROR, "APIError"),
    ],
)
def test_auth_status_preserves_non_auth_403_type(
    message, expected_code, expected_type, monkeypatch, capsys
):
    for key, value in ENV.items():
        monkeypatch.setenv(key, value)
    respx.get(f"{API}jobs").mock(
        return_value=httpx.Response(403, json={"error": message})
    )
    monkeypatch.setattr(sys, "argv", ["tamarind", "--json", "auth", "status"])

    with pytest.raises(SystemExit) as raised:
        main_module.run()

    captured = capsys.readouterr()
    assert raised.value.code == expected_code
    assert captured.out == ""
    assert json.loads(captured.err)["error"]["type"] == expected_type


@respx.mock
@pytest.mark.parametrize(
    ("message", "expected_code", "expected_type"),
    [
        ("Invalid API key", ExitCode.AUTH, "AuthError"),
        ("Weighted hours budget exceeded", ExitCode.BUDGET, "BudgetError"),
        ("This resource is forbidden by policy", ExitCode.ERROR, "APIError"),
    ],
)
def test_auth_login_never_saves_when_verification_fails(
    message, expected_code, expected_type, tmp_path, monkeypatch, capsys
):
    config_dir = tmp_path / "config"
    monkeypatch.setenv("TAMARIND_CONFIG_DIR", str(config_dir))
    monkeypatch.setenv("TAMARIND_API_BASE", API)
    respx.get(f"{API}jobs").mock(
        return_value=httpx.Response(403, json={"error": message})
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["tamarind", "--json", "auth", "login", "--api-key", "candidate"],
    )

    with pytest.raises(SystemExit) as raised:
        main_module.run()

    captured = capsys.readouterr()
    assert raised.value.code == expected_code
    assert captured.out == ""
    assert json.loads(captured.err)["error"]["type"] == expected_type
    assert not (config_dir / "config.json").exists()


def test_entrypoint_emits_json_error_with_stable_exit_code(tmp_path, monkeypatch, capsys):
    job = tmp_path / "job.yaml"
    job.write_text("type: esmfold\nsettings: {sequence: MKT}\n")
    monkeypatch.setattr(
        sys,
        "argv",
        ["tamarind", "--json", "validate", "boltz", "--input", str(job)],
    )

    with pytest.raises(SystemExit) as exc:
        main_module.run()

    captured = capsys.readouterr()
    payload = json.loads(captured.err)
    assert captured.out == ""
    assert exc.value.code == ExitCode.VALIDATION
    assert payload["error"]["type"] == "ValidationError"
    assert payload["error"]["exitCode"] == ExitCode.VALIDATION
    assert "boltz" in payload["error"]["message"]
    assert "esmfold" in payload["error"]["message"]


def test_entrypoint_keeps_human_error_format(tmp_path, monkeypatch, capsys):
    job = tmp_path / "job.yaml"
    job.write_text("type: esmfold\nsettings: {sequence: MKT}\n")
    monkeypatch.setattr(
        sys,
        "argv",
        ["tamarind", "--no-json", "validate", "boltz", "--input", str(job)],
    )

    with pytest.raises(SystemExit) as exc:
        main_module.run()

    captured = capsys.readouterr()
    assert exc.value.code == ExitCode.VALIDATION
    assert captured.err.startswith("error: Tool mismatch:")


def test_entrypoint_emits_json_for_usage_errors(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["tamarind", "--json", "submit"])

    with pytest.raises(SystemExit) as exc:
        main_module.run()

    captured = capsys.readouterr()
    payload = json.loads(captured.err)
    assert captured.out == ""
    assert exc.value.code == ExitCode.USAGE
    assert payload["error"]["type"] == "MissingParameter"
    assert payload["error"]["exitCode"] == ExitCode.USAGE
    assert "TOOL" in payload["error"]["message"]


def test_dangling_global_value_option_keeps_precise_json_usage_error(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["tamarind", "--json", "--profile"])

    with pytest.raises(SystemExit) as exc:
        main_module.run()

    captured = capsys.readouterr()
    payload = json.loads(captured.err)
    assert exc.value.code == ExitCode.USAGE
    assert captured.out == ""
    assert payload["error"]["type"] == "BadOptionUsage"
    assert "--profile" in payload["error"]["message"]
    assert "Missing command" not in payload["error"]["message"]


@pytest.mark.parametrize("argv", [["tamarind"], ["tamarind", "--json", "files"]])
def test_json_no_command_is_clean_and_machine_readable(argv, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", argv)

    with pytest.raises(SystemExit) as exc:
        main_module.run()

    captured = capsys.readouterr()
    assert exc.value.code == ExitCode.USAGE
    assert captured.out == ""
    payload = json.loads(captured.err)
    assert payload["error"]["type"] == "UsageError"
    assert payload["error"]["message"]


@respx.mock
def test_entrypoint_preserves_command_level_exit_code(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["tamarind", "--json", "validate", "boltz"])
    for key, value in ENV.items():
        monkeypatch.setenv(key, value)
    respx.post(f"{API}validate-job").mock(
        return_value=httpx.Response(200, json={"valid": False, "error": "missing sequence"})
    )

    with pytest.raises(SystemExit) as exc:
        main_module.run()

    captured = capsys.readouterr()
    assert exc.value.code == ExitCode.VALIDATION
    assert captured.err == ""
    assert json.loads(captured.out)["valid"] is False


def test_entrypoint_preserves_human_abort_behavior(monkeypatch, capsys):
    def aborting_app(**kwargs):
        raise main_module.Abort()

    monkeypatch.setattr(sys, "argv", ["tamarind", "--no-json", "delete", "job-1"])
    monkeypatch.setattr(main_module, "app", aborting_app)

    with pytest.raises(SystemExit) as exc:
        main_module.run()

    captured = capsys.readouterr()
    assert exc.value.code == ExitCode.ERROR
    assert captured.err == "Aborted!\n"


@respx.mock
def test_ambiguous_auto_named_submit_surfaces_recovery_name(monkeypatch, capsys):
    for key, value in ENV.items():
        monkeypatch.setenv(key, value)
    respx.post(f"{API}validate-job").mock(
        return_value=httpx.Response(200, json={"valid": True})
    )
    request = httpx.Request("POST", f"{API}submit-job")
    respx.post(f"{API}submit-job").mock(
        side_effect=httpx.ReadTimeout("response lost", request=request)
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["tamarind", "--json", "submit", "boltz", "--set", "sequence=MKT"],
    )

    with pytest.raises(SystemExit) as exc:
        main_module.run()

    payload = json.loads(capsys.readouterr().err)
    detail = payload["error"]["detail"]
    assert exc.value.code == ExitCode.ERROR
    assert detail["jobName"].startswith("boltz-")
    assert detail["outcomeMayBeAmbiguous"] is True
    assert detail["submitted"] is None
    assert detail["jobName"] in detail["recoveryCommand"]
    assert "before retrying" in payload["error"]["message"]


@pytest.mark.parametrize("status", ["Failed", "Stopped", "Cancelled", "Error"])
def test_wait_returns_final_payload_but_exits_nonzero(status, monkeypatch):
    monkeypatch.setattr(
        jobs_commands.jobs_helpers,
        "wait_for_job",
        lambda *args, **kwargs: {"JobName": "job-1", "JobStatus": status},
    )

    result = runner.invoke(app, ["--json", "wait", "job-1"], env=ENV)

    assert result.exit_code == ExitCode.JOB_FAILED
    assert json.loads(result.stdout)["JobStatus"] == status


def test_wait_failed_batch_parent_exits_nonzero(monkeypatch):
    monkeypatch.setattr(
        jobs_commands.jobs_helpers,
        "wait_for_job",
        lambda *args, **kwargs: {
            "batchName": "batch-1",
            "batchStatus": "AggregationFailed",
        },
    )

    result = runner.invoke(app, ["--json", "wait", "batch-1"], env=ENV)

    assert result.exit_code == ExitCode.JOB_FAILED
    assert json.loads(result.stdout)["batchStatus"] == "AggregationFailed"


@respx.mock
def test_submit_wait_forwards_timeout_and_failed_job_exits_nonzero(monkeypatch):
    respx.post(f"{API}validate-job").mock(return_value=httpx.Response(200, json={"valid": True}))
    respx.post(f"{API}submit-job").mock(return_value=httpx.Response(200, json={"message": "queued"}))
    observed = {}

    def fake_wait(*args, **kwargs):
        observed.update(kwargs)
        return {"JobName": "job-1", "JobStatus": "Failed"}

    monkeypatch.setattr(jobs_commands.jobs_helpers, "wait_for_job", fake_wait)
    result = runner.invoke(
        app,
        [
            "--json",
            "submit",
            "boltz",
            "--name",
            "job-1",
            "--set",
            "sequence=MKT",
            "--wait",
            "--timeout",
            "12.5",
        ],
        env=ENV,
    )

    assert result.exit_code == ExitCode.JOB_FAILED
    assert observed["timeout"] == 12.5
    assert json.loads(result.stdout)["final"]["JobStatus"] == "Failed"


@respx.mock
@pytest.mark.parametrize(
    "timing_args",
    [
        ["--poll-interval", "-1"],
        ["--poll-interval", "nan"],
        ["--poll-interval", "inf"],
        ["--timeout", "-1"],
        ["--timeout", "nan"],
        ["--timeout", "inf"],
    ],
)
def test_submit_wait_rejects_invalid_timing_before_any_remote_request(timing_args):
    validation = respx.post(f"{API}validate-job").mock(
        return_value=httpx.Response(200, json={"valid": True})
    )
    submit = respx.post(f"{API}submit-job").mock(
        return_value=httpx.Response(200, json={"message": "must not submit"})
    )

    result = runner.invoke(
        app,
        [
            "--json",
            "submit",
            "boltz",
            "--name",
            "job-invalid-wait",
            "--set",
            "sequence=MKT",
            "--wait",
            *timing_args,
        ],
        env=ENV,
    )

    assert isinstance(result.exception, ValidationError)
    assert not validation.called
    assert not submit.called


@respx.mock
def test_submit_wait_redacts_result_url_from_final_job(monkeypatch):
    secret = "https://storage.test/result.zip?signature=do-not-leak"
    respx.post(f"{API}validate-job").mock(
        return_value=httpx.Response(200, json={"valid": True})
    )
    respx.post(f"{API}submit-job").mock(
        return_value=httpx.Response(200, json={"message": "queued"})
    )
    monkeypatch.setattr(
        jobs_commands.jobs_helpers,
        "wait_for_job",
        lambda *args, **kwargs: {
            "JobName": "job-1",
            "JobStatus": "Complete",
            "resultUrl": secret,
        },
    )

    result = runner.invoke(
        app,
        [
            "--json",
            "submit",
            "boltz",
            "--name",
            "job-1",
            "--set",
            "sequence=MKT",
            "--wait",
        ],
        env=ENV,
    )

    assert result.exit_code == 0, result.stdout
    assert "do-not-leak" not in result.stdout
    assert json.loads(result.stdout)["final"]["redactedFields"] == ["resultUrl"]


@respx.mock
def test_submit_wait_download_accepts_wrapped_url_and_sanitizes_job_name(
    tmp_path, monkeypatch
):
    respx.post(f"{API}validate-job").mock(
        return_value=httpx.Response(200, json={"valid": True})
    )
    respx.post(f"{API}submit-job").mock(
        return_value=httpx.Response(200, json={"message": "queued"})
    )
    presigned = "https://storage.test/result.zip?signature=secret"
    respx.post(f"{API}result").mock(
        return_value=httpx.Response(200, json={"downloadUrl": presigned})
    )
    respx.get(presigned).mock(return_value=httpx.Response(200, content=b"zip-bytes"))
    monkeypatch.setattr(
        jobs_commands.jobs_helpers,
        "wait_for_job",
        lambda *args, **kwargs: {"JobName": "../job-1", "JobStatus": "Complete"},
    )

    result = runner.invoke(
        app,
        [
            "--json",
            "submit",
            "boltz",
            "--name",
            "../job-1",
            "--set",
            "sequence=MKT",
            "--wait",
            "--download",
            str(tmp_path),
        ],
        env=ENV,
    )

    assert result.exit_code == 0, result.stdout
    assert (tmp_path / "job-1.zip").read_bytes() == b"zip-bytes"
    assert not (tmp_path.parent / "job-1.zip").exists()
    assert "url" not in json.loads(result.stdout)


@respx.mock
def test_results_wait_failure_never_requests_presigned_url(monkeypatch):
    route = respx.post(f"{API}result").mock(
        return_value=httpx.Response(200, json={"downloadUrl": "https://secret.test/result"})
    )
    observed = {}

    def fake_wait(*args, **kwargs):
        observed.update(kwargs)
        return {"JobName": "job-1", "JobStatus": "Stopped"}

    monkeypatch.setattr(jobs_commands.jobs_helpers, "wait_for_job", fake_wait)
    result = runner.invoke(
        app,
        [
            "--json",
            "results",
            "job-1",
            "--show-url",
            "--wait",
            "--timeout",
            "9",
        ],
        env=ENV,
    )

    assert result.exit_code == ExitCode.JOB_FAILED
    assert observed["timeout"] == 9
    assert json.loads(result.stdout)["final"]["JobStatus"] == "Stopped"
    assert not route.called


@respx.mock
def test_downloaded_results_json_omits_presigned_url(tmp_path):
    presigned = "https://storage.test/result.zip?signature=secret"
    respx.post(f"{API}result").mock(return_value=httpx.Response(200, json=presigned))
    respx.get(presigned).mock(return_value=httpx.Response(200, content=b"zip-bytes"))

    result = runner.invoke(
        app,
        ["--json", "results", "job-1", "--download", str(tmp_path)],
        env=ENV,
    )

    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    assert "url" not in payload
    assert payload["download"]["bytes"] == len(b"zip-bytes")
    assert (tmp_path / "job-1.zip").read_bytes() == b"zip-bytes"


@respx.mock
def test_results_requires_explicit_download_or_show_url():
    route = respx.post(f"{API}result").mock(
        return_value=httpx.Response(
            200,
            json="https://storage.test/result.zip?signature=do-not-leak",
        )
    )

    result = runner.invoke(app, ["--json", "results", "job-1"], env=ENV)

    assert result.exit_code == ExitCode.USAGE
    assert "do-not-leak" not in result.stdout
    assert not route.called


@respx.mock
def test_results_show_url_is_an_explicit_escape_hatch():
    presigned = "https://storage.test/result.zip?signature=explicit"
    respx.post(f"{API}result").mock(
        return_value=httpx.Response(200, json=presigned)
    )

    result = runner.invoke(
        app,
        ["--json", "results", "job-1", "--show-url"],
        env=ENV,
    )

    assert result.exit_code == 0, result.stdout
    assert json.loads(result.stdout)["url"] == presigned


@respx.mock
def test_validation_rewrites_legacy_upload_endpoint_guidance():
    respx.post(f"{API}validate-job").mock(
        return_value=httpx.Response(
            200,
            json={
                "valid": False,
                "error": (
                    'File "missing.pdb" has not been uploaded. Please upload '
                    "your file using the /upload endpoint."
                ),
                "missing_fields": [],
            },
        )
    )

    result = runner.invoke(
        app,
        [
            "--json",
            "validate",
            "aggrescan3d",
            "--name",
            "missing-file",
            "--set",
            "pdbFile=missing.pdb",
        ],
        env=ENV,
    )

    assert result.exit_code == ExitCode.VALIDATION
    assert "/upload endpoint" not in result.stdout
    assert "tamarind --json files upload PATH" in result.stdout


@respx.mock
def test_validation_guidance_rewrite_does_not_mutate_user_settings_text():
    user_text = "A literal uploadFile() token in user-controlled text"
    respx.post(f"{API}validate-job").mock(
        return_value=httpx.Response(
            200,
            json={"valid": True, "normalized": {"note": user_text}},
        )
    )

    result = runner.invoke(
        app,
        [
            "--json",
            "validate",
            "custom-tool",
            "--name",
            "literal-text",
            "--set",
            f"note={user_text}",
        ],
        env=ENV,
    )

    assert result.exit_code == 0, result.stdout
    assert json.loads(result.stdout)["normalized"]["note"] == user_text


@respx.mock
@pytest.mark.parametrize("token", ["validateJob", "submitJob", "uploadFile()"])
def test_validation_error_preserves_echoed_user_tokens(token):
    message = f"Unknown setting value: {token}"
    respx.post(f"{API}validate-job").mock(
        return_value=httpx.Response(200, json={"valid": False, "error": message})
    )

    result = runner.invoke(
        app,
        ["--json", "validate", "custom-tool", "--set", "sequence=MKT"],
        env=ENV,
    )

    assert result.exit_code == ExitCode.VALIDATION
    assert json.loads(result.stdout)["error"] == message


@respx.mock
def test_status_and_job_lists_redact_presigned_result_urls():
    secret = "https://storage.test/result.zip?signature=do-not-leak"
    respx.get(f"{API}jobs").mock(
        side_effect=[
            httpx.Response(
                200,
                json={
                    "JobName": "job-1",
                    "JobStatus": "Complete",
                    "resultUrl": secret,
                },
            ),
            httpx.Response(
                200,
                json={
                    "jobs": [
                        {
                            "JobName": "job-1",
                            "JobStatus": "Complete",
                            "resultUrl": secret,
                        }
                    ]
                },
            ),
        ]
    )

    status = runner.invoke(app, ["--json", "status", "job-1"], env=ENV)
    listing = runner.invoke(app, ["--json", "jobs"], env=ENV)

    assert status.exit_code == listing.exit_code == 0
    for text in (status.stdout, listing.stdout):
        assert "do-not-leak" not in text
        assert "resultUrl" in json.loads(text).get(
            "redactedFields",
            json.loads(text).get("jobs", [{}])[0].get("redactedFields", []),
        )


@pytest.mark.parametrize(
    "secret",
    [
        "https://storage.test/object?X-Amz-Signature=do-not-leak",
        "https://storage.googleapis.test/object?X-Goog-Signature=do-not-leak",
        "https://account.blob.core.windows.net/object?sv=2024-01-01&sig=do-not-leak",
    ],
)
def test_sanitizer_redacts_signed_urls_by_value_and_preserves_ordinary_urls(secret):
    ordinary = "https://docs.tamarind.bio/results"
    payload = {
        "artifactLink": secret,
        "nested": {"futureField": secret, "docs": ordinary},
        "items": [secret, ordinary],
    }

    sanitized = jobs_commands._sanitize_job_output(payload)
    rendered = json.dumps(sanitized)

    assert "do-not-leak" not in rendered
    assert sanitized["redactedFields"] == ["artifactLink"]
    assert sanitized["nested"]["futureField"] == "<redacted credential URL>"
    assert sanitized["nested"]["docs"] == ordinary
    assert sanitized["items"] == ["<redacted credential URL>", ordinary]
    assert jobs_commands._sanitize_job_output(secret) == "<redacted credential URL>"


def test_sanitizer_does_not_overwrite_existing_redaction_metadata():
    payload = {
        "resultUrl": "https://storage.test/result",
        "redactedFields": {"upstream": True},
    }

    sanitized = jobs_commands._sanitize_job_output(payload)

    assert sanitized["redactedFields"] == {"upstream": True}
    assert sanitized["tamarindRedactedFields"] == ["resultUrl"]


@respx.mock
def test_results_accepts_wrapped_download_url(tmp_path):
    presigned = "https://storage.test/result.zip?signature=secret"
    respx.post(f"{API}result").mock(
        return_value=httpx.Response(200, json={"downloadUrl": presigned})
    )
    respx.get(presigned).mock(return_value=httpx.Response(200, content=b"zip-bytes"))

    result = runner.invoke(
        app,
        ["--json", "results", "job-1", "--download", str(tmp_path)],
        env=ENV,
    )

    assert result.exit_code == 0, result.stdout
    assert json.loads(result.stdout)["download"]["bytes"] == len(b"zip-bytes")


@respx.mock
def test_results_rejects_missing_download_url_cleanly(tmp_path):
    respx.post(f"{API}result").mock(
        return_value=httpx.Response(200, json={"message": "not ready"})
    )

    result = runner.invoke(
        app,
        ["--json", "results", "job-1", "--download", str(tmp_path)],
        env=ENV,
    )

    assert result.exit_code != 0
    assert isinstance(result.exception, TamarindError)
    assert "download URL" in result.exception.message


@respx.mock
def test_download_http_failure_is_typed_sanitized_and_preserves_destination(tmp_path):
    presigned = "https://storage.test/result.zip?signature=do-not-leak"
    destination = tmp_path / "job-1.zip"
    destination.write_bytes(b"old-result")
    respx.post(f"{API}result").mock(return_value=httpx.Response(200, json=presigned))
    respx.get(presigned).mock(return_value=httpx.Response(503, text="unavailable"))

    result = runner.invoke(
        app,
        ["--json", "results", "job-1", "--download", str(tmp_path)],
        env=ENV,
    )

    assert result.exit_code != 0
    assert isinstance(result.exception, TamarindError)
    assert "do-not-leak" not in result.exception.message
    assert "do-not-leak" not in str(result.exception.detail)
    assert destination.read_bytes() == b"old-result"
    assert not list(tmp_path.glob("*.part"))


class _FailingStream(httpx.SyncByteStream):
    def __iter__(self):
        yield b"partial-download"
        raise httpx.ReadError(
            "stream interrupted",
            request=httpx.Request(
                "GET", "https://storage.test/result.zip?signature=do-not-leak"
            ),
        )


class _InterruptedStream(httpx.SyncByteStream):
    def __iter__(self):
        yield b"partial-download"
        raise KeyboardInterrupt


class _BrokenProtocolStream(httpx.SyncByteStream):
    def __iter__(self):
        yield b"partial-download"
        raise httpx.StreamError("stream was consumed incorrectly")


@respx.mock
def test_midstream_download_failure_removes_partial_and_preserves_destination(tmp_path):
    presigned = "https://storage.test/result.zip?signature=do-not-leak"
    destination = tmp_path / "job-1.zip"
    destination.write_bytes(b"old-result")
    respx.post(f"{API}result").mock(return_value=httpx.Response(200, json=presigned))
    respx.get(presigned).mock(return_value=httpx.Response(200, stream=_FailingStream()))

    result = runner.invoke(
        app,
        ["--json", "results", "job-1", "--download", str(tmp_path)],
        env=ENV,
    )

    assert result.exit_code != 0
    assert isinstance(result.exception, TamarindError)
    assert "do-not-leak" not in result.exception.message
    assert "do-not-leak" not in str(result.exception.detail)
    assert destination.read_bytes() == b"old-result"
    assert [path.name for path in tmp_path.iterdir()] == ["job-1.zip"]


@respx.mock
def test_stream_protocol_failure_is_typed_and_removes_partial(tmp_path):
    presigned = "https://storage.test/result.zip?signature=do-not-leak"
    destination = tmp_path / "job-1.zip"
    respx.get(presigned).mock(
        return_value=httpx.Response(200, stream=_BrokenProtocolStream())
    )

    with pytest.raises(TamarindError) as raised:
        jobs_commands._download(presigned, destination)

    assert "do-not-leak" not in raised.value.message
    assert raised.value.detail == {"type": "StreamError"}
    assert not destination.exists()
    assert list(tmp_path.iterdir()) == []


@respx.mock
def test_interrupted_download_removes_partial_file(tmp_path):
    presigned = "https://storage.test/result.zip?signature=do-not-leak"
    destination = tmp_path / "job-1.zip"
    respx.get(presigned).mock(
        return_value=httpx.Response(200, stream=_InterruptedStream())
    )

    with pytest.raises(KeyboardInterrupt):
        jobs_commands._download(presigned, destination)

    assert not destination.exists()
    assert list(tmp_path.iterdir()) == []


@respx.mock
def test_batch_validates_every_item_before_single_submit(tmp_path):
    batch = tmp_path / "batch.yaml"
    batch.write_text("- {sequence: MKT}\n- {sequence: MKV}\n")
    validation = respx.post(f"{API}validate-job").mock(
        return_value=httpx.Response(200, json={"valid": True})
    )
    submit = respx.post(f"{API}submit-batch").mock(
        return_value=httpx.Response(200, json={"message": "queued"})
    )

    result = runner.invoke(
        app,
        [
            "--json",
            "batch",
            "boltz",
            "--name",
            "batch-1",
            "--input",
            str(batch),
            "--prevalidate",
        ],
        env=ENV,
    )

    assert result.exit_code == 0, result.stdout
    assert validation.call_count == 2
    assert submit.call_count == 1
    names = [json.loads(call.request.content)["jobName"] for call in validation.calls]
    assert names == ["batch-1-1", "batch-1-2"]


@respx.mock
def test_batch_invalid_item_prevents_submit(tmp_path):
    batch = tmp_path / "batch.yaml"
    batch.write_text("- {sequence: MKT}\n- {sequence: BAD}\n")
    respx.post(f"{API}validate-job").mock(
        side_effect=[
            httpx.Response(200, json={"valid": True}),
            httpx.Response(200, json={"valid": False, "error": "bad sequence"}),
        ]
    )
    submit = respx.post(f"{API}submit-batch").mock(
        return_value=httpx.Response(200, json={"message": "should not happen"})
    )

    result = runner.invoke(
        app,
        [
            "batch",
            "boltz",
            "--name",
            "batch-1",
            "--input",
            str(batch),
            "--prevalidate",
        ],
        env=ENV,
    )

    assert result.exit_code != 0
    assert isinstance(result.exception, ValidationError)
    assert result.exception.detail["index"] == 1
    assert not submit.called


@respx.mock
def test_batch_does_not_prevalidate_without_explicit_flag(tmp_path):
    batch = tmp_path / "batch.yaml"
    batch.write_text("- {sequence: MKT}\n- {sequence: MKV}\n")
    validation = respx.post(f"{API}validate-job").mock(
        return_value=httpx.Response(200, json={"valid": True})
    )
    submit = respx.post(f"{API}submit-batch").mock(
        return_value=httpx.Response(200, json={"message": "queued"})
    )

    result = runner.invoke(
        app,
        ["--json", "batch", "boltz", "--name", "batch-1", "--input", str(batch)],
        env=ENV,
    )

    assert result.exit_code == 0, result.stdout
    assert not validation.called
    assert submit.call_count == 1


@pytest.mark.parametrize(
    ("document", "message"),
    [
        ("[]\n", "may not be empty"),
        ("- {sequence: MKT}\n- not-an-object\n", "item 2 must be an object"),
        (
            "settings: [{sequence: MKT}, {sequence: MKV}]\njobNames: [only-one]\n",
            "one name per settings item",
        ),
        (
            "settings: [{sequence: MKT}, {sequence: MKV}]\njobNames: [ok, 3]\n",
            "non-empty string",
        ),
        (
            "settings: [{sequence: MKT}, {sequence: MKV}]\njobNames: [same, same]\n",
            "must be unique",
        ),
        (
            "settings: [{sequence: MKT}, {sequence: MKV}]\njobNames: [' a', b]\n",
            "jobNames may not have",
        ),
    ],
)
@respx.mock
def test_batch_rejects_local_input_invariants_before_network(tmp_path, document, message):
    batch = tmp_path / "batch.yaml"
    batch.write_text(document)
    submit = respx.post(f"{API}submit-batch").mock(
        return_value=httpx.Response(200, json={"message": "should not happen"})
    )

    result = runner.invoke(
        app,
        ["batch", "boltz", "--name", "batch-1", "--input", str(batch)],
        env=ENV,
    )

    assert result.exit_code != 0
    assert isinstance(result.exception, ValidationError)
    assert message in result.exception.message
    assert not submit.called


@pytest.mark.parametrize(
    ("extra_args", "document", "message"),
    [
        ([], "batchName: ' batch-1'\nsettings: [{sequence: MKT}]\n", "Batch name may not have"),
        (["--max-runtime", "0"], "- {sequence: MKT}\n", "greater than zero"),
    ],
)
@respx.mock
def test_batch_rejects_invalid_batch_options_before_network(
    tmp_path, extra_args, document, message
):
    batch = tmp_path / "batch.yaml"
    batch.write_text(document)
    submit = respx.post(f"{API}submit-batch").mock(
        return_value=httpx.Response(200, json={"message": "should not happen"})
    )

    result = runner.invoke(
        app,
        ["batch", "boltz", "--input", str(batch), *extra_args],
        env=ENV,
    )

    assert result.exit_code != 0
    assert isinstance(result.exception, ValidationError)
    assert message in result.exception.message
    assert not submit.called
