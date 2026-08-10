import io

import pytest

from tamarind.cli.inputs import resolve_job_input
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
