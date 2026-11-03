import io
import json

import pytest

from tamarind.cli.inputs import effective_job_name, resolve_job_input
from tamarind.errors import ExitCode, ValidationError


def test_bare_settings(tmp_path):
    f = tmp_path / "job.yaml"
    f.write_text("inputFormat: sequence\nsequence: ABCDE\nnumSamples: 5\n")
    job = resolve_job_input(str(f), [])
    assert job.settings == {"inputFormat": "sequence", "sequence": "ABCDE", "numSamples": 5}
    assert job.job_type is None and job.job_name is None


def test_envelope(tmp_path):
    f = tmp_path / "job.json"
    f.write_text('{"jobName":"run1","type":"boltz","settings":{"sequence":"ABC"}}')
    job = resolve_job_input(str(f), [])
    assert job.job_type == "boltz"
    assert job.job_name == "run1"
    assert job.settings == {"sequence": "ABC"}


def test_set_overrides_and_coercion(tmp_path):
    f = tmp_path / "job.yaml"
    f.write_text("sequence: ABC\n")
    job = resolve_job_input(str(f), ["numSamples=5", "useMSA=true", "seed=abc"])
    assert job.settings["numSamples"] == 5
    assert job.settings["useMSA"] is True
    assert job.settings["seed"] == "abc"
    assert job.settings["sequence"] == "ABC"


def test_set_without_file():
    job = resolve_job_input(None, ["inputFormat=sequence", "sequence=MK"])
    assert job.settings == {"inputFormat": "sequence", "sequence": "MK"}


def test_at_reference(tmp_path):
    f = tmp_path / "job.yaml"
    f.write_text("sequence: ABC\n")
    job = resolve_job_input(f"@yaml://{f}", [])
    assert job.settings == {"sequence": "ABC"}


def test_stdin(monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("sequence: XYZ\n"))
    job = resolve_job_input("-", [])
    assert job.settings == {"sequence": "XYZ"}


def test_bad_set():
    with pytest.raises(ValidationError) as exc:
        resolve_job_input(None, ["noequalshere"])
    assert exc.value.exit_code == ExitCode.VALIDATION


def test_missing_file():
    # A bad --input path is an input/validation error (exit 5), not a generic one.
    with pytest.raises(ValidationError) as exc:
        resolve_job_input("/no/such/file.yaml", [])
    assert exc.value.exit_code == ExitCode.VALIDATION


def test_malformed_document(tmp_path):
    f = tmp_path / "bad.yaml"
    f.write_text("{:::not yaml::")
    with pytest.raises(ValidationError):
        resolve_job_input(str(f), [])


def test_non_mapping_document(tmp_path):
    f = tmp_path / "list.json"
    f.write_text("[1, 2, 3]")
    with pytest.raises(ValidationError):
        resolve_job_input(str(f), [])


@pytest.mark.parametrize("settings", [None, False, 0, 1, "", "text", [], [["key", "value"]]])
@pytest.mark.parametrize("source", ["file", "stdin"])
def test_envelope_requires_mapping_settings(tmp_path, monkeypatch, settings, source):
    document = json.dumps({"type": "fold-local", "settings": settings})
    if source == "stdin":
        monkeypatch.setattr("sys.stdin", io.StringIO(document))
        input_source = "-"
    else:
        path = tmp_path / "input.json"
        path.write_text(document)
        input_source = str(path)
    with pytest.raises(ValidationError, match="Job settings must be a mapping"):
        resolve_job_input(input_source, ["sequence=AAA"])


def test_explicit_name_precedence_and_absence():
    assert effective_job_name(None, None) is None
    assert effective_job_name(None, "file-name") == "file-name"
    assert effective_job_name("cli-name", "file-name") == "cli-name"
    assert effective_job_name("cli-name", False) == "cli-name"
    with pytest.raises(ValidationError):
        effective_job_name("", "file-name")


def test_low_priority_in_an_envelope_is_a_request_field(tmp_path):
    path = tmp_path / "job.json"
    path.write_text(json.dumps({"jobName": "j", "type": "boltz", "lowPriority": True, "settings": {"sequence": "A"}}))
    job = resolve_job_input(str(path), None)
    assert job.low_priority is True
    assert job.settings == {"sequence": "A"}


def test_low_priority_among_the_settings_is_moved_out(tmp_path):
    # Left there the server would ignore it, and the job would bill full price.
    path = tmp_path / "job.json"
    path.write_text(json.dumps({"sequence": "A", "lowPriority": True}))
    job = resolve_job_input(str(path), None)
    assert job.low_priority is True
    assert job.settings == {"sequence": "A"}


def test_low_priority_defaults_off():
    assert resolve_job_input(None, ["sequence=A"]).low_priority is False


def test_low_priority_that_is_not_a_boolean_is_refused(tmp_path):
    path = tmp_path / "job.json"
    path.write_text(json.dumps({"sequence": "A", "lowPriority": "yes"}))
    with pytest.raises(ValidationError):
        resolve_job_input(str(path), None)


@pytest.mark.parametrize(
    "doc",
    [
        {"sequence": "A", "lowPriority": None},
        {"jobName": "j", "lowPriority": None, "settings": {"sequence": "A"}},
    ],
)
def test_low_priority_that_is_null_is_refused(tmp_path, doc):
    # An unfilled template must not quietly become a full-price job.
    path = tmp_path / "job.json"
    path.write_text(json.dumps(doc))
    with pytest.raises(ValidationError):
        resolve_job_input(str(path), None)


def test_low_priority_alone_marks_an_envelope(tmp_path):
    path = tmp_path / "job.json"
    path.write_text(json.dumps({"lowPriority": True, "settings": {"sequence": "A"}}))
    job = resolve_job_input(str(path), None)
    assert job.low_priority is True
    assert job.settings == {"sequence": "A"}


def test_low_priority_stays_a_setting_where_the_command_does_not_support_it(tmp_path):
    path = tmp_path / "job.json"
    path.write_text(json.dumps({"sequence": "A", "lowPriority": True}))
    job = resolve_job_input(str(path), ["other=1"], supports_low_priority=False)
    assert job.low_priority is False
    assert job.settings == {"sequence": "A", "lowPriority": True, "other": 1}

    job = resolve_job_input(None, ["lowPriority=true"], supports_low_priority=False)
    assert job.low_priority is False
    assert job.settings == {"lowPriority": True}


def test_low_priority_alone_is_no_envelope_where_the_command_does_not_support_it(tmp_path):
    path = tmp_path / "job.json"
    doc = {"lowPriority": True, "settings": {"sequence": "A"}}
    path.write_text(json.dumps(doc))
    job = resolve_job_input(str(path), None, supports_low_priority=False)
    assert job.low_priority is False
    assert job.settings == doc
