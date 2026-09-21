import io
import json

import pytest

from tamarind.cli.inputs import effective_job_name, effective_job_type, resolve_job_input
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


@pytest.mark.parametrize(
    "tool_key,document",
    [
        ("type", '{"type":"boltz","settings":{"sequence":"ABC"}}'),
        # The finetune commands name the tool "model". Without tool_key this is
        # not recognised as an envelope at all and the WHOLE document (model and
        # the nested settings object) silently becomes the job's settings.
        ("model", '{"model":"boltz","settings":{"sequence":"ABC"}}'),
        # jobName alone also marks an envelope, and then the tool is read from
        # whichever key carries it — including the other one.
        ("model", '{"jobName":"r","type":"boltz","settings":{"sequence":"ABC"}}'),
        ("type", '{"jobName":"r","model":"boltz","settings":{"sequence":"ABC"}}'),
    ],
)
def test_envelope_is_recognised_by_its_own_tool_key(tmp_path, tool_key, document):
    f = tmp_path / "job.json"
    f.write_text(document)
    job = resolve_job_input(str(f), [], tool_key=tool_key)
    assert job.job_type == "boltz"
    assert job.settings == {"sequence": "ABC"}


@pytest.mark.parametrize("tool_key,document", [
    ("type", {"type": "esmfold", "settings": {"sequence": "ABC"}}),
    ("model", {"model": "esmfold", "settings": {"sequence": "ABC"}}),
    # A disagreeing tool named under the OTHER key of an envelope must still be
    # rejected. It was read as None and silently discarded, so `finetune boltz` on
    # a file saying type: esmfold submitted boltz without a word.
    ("model", {"jobName": "r", "type": "esmfold", "settings": {"sequence": "ABC"}}),
    ("type", {"jobName": "r", "model": "esmfold", "settings": {"sequence": "ABC"}}),
    # A key PRESENT but null is absent, not "the tool". Reading it as the tool
    # returned None and never looked at the real name under the other key, so the
    # disagreement went unreported and the command-line tool was submitted.
    ("type", {"jobName": "r", "type": None, "model": "esmfold",
              "settings": {"sequence": "ABC"}}),
    ("model", {"jobName": "r", "model": None, "type": "esmfold",
               "settings": {"sequence": "ABC"}}),
])
def test_envelope_tool_key_must_agree_with_the_command(tmp_path, tool_key, document):
    f = tmp_path / "job.json"
    f.write_text(json.dumps(document))
    job = resolve_job_input(str(f), [], tool_key=tool_key)
    with pytest.raises(ValidationError, match="esmfold"):
        effective_job_type("boltz", job.job_type, tool_key=tool_key)


@pytest.mark.parametrize("tool_key", ["type", "model"])
@pytest.mark.parametrize("document", [
    {"type": "boltz", "model": "esmfold", "settings": {"sequence": "ABC"}},
    # A non-string can never BE a string tool name. Rendering it into the string
    # space to compare (repr(1) == "1") would hide a malformed value behind an
    # apparent agreement.
    {"type": 1, "model": "1", "settings": {"sequence": "ABC"}},
])
def test_an_envelope_naming_two_different_tools_is_refused(tmp_path, tool_key, document):
    f = tmp_path / "job.json"
    f.write_text(json.dumps(document))
    with pytest.raises(ValidationError, match="two different tools"):
        resolve_job_input(str(f), [], tool_key=tool_key)


@pytest.mark.parametrize("tool_key", ["type", "model"])
@pytest.mark.parametrize("document", [
    # Same tool, spelled differently. effective_job_type compares trimmed and
    # case-insensitively, so the conflict check must too or the two rules disagree
    # and a perfectly valid document is refused.
    {"type": "ESM2", "model": "esm2", "settings": {"sequence": "ABC"}},
    {"type": " esm2 ", "model": "esm2", "settings": {"sequence": "ABC"}},
])
def test_two_tool_keys_naming_the_same_tool_are_not_a_conflict(
    tmp_path, tool_key, document
):
    f = tmp_path / "job.json"
    f.write_text(json.dumps(document))

    job = resolve_job_input(str(f), [], tool_key=tool_key)

    assert effective_job_type("esm2", job.job_type, tool_key=tool_key) == "esm2"


@pytest.mark.parametrize("tool_key", ["type", "model"])
def test_a_settings_document_that_merely_contains_a_tool_key_is_not_an_envelope(
    tmp_path, tool_key
):
    """Raw settings that happen to carry the OTHER tool key beside their own
    `settings` must stay settings. custom-tools test allows user-defined schemas
    with exactly this shape, and submit/validate accept it today."""
    other = "model" if tool_key == "type" else "type"
    doc = {other: "esmfold2-fast", "settings": {"weights": "s3://bucket/model"}}
    f = tmp_path / "job.json"
    f.write_text(json.dumps(doc))

    job = resolve_job_input(str(f), [], tool_key=tool_key)

    assert job.job_type is None
    assert job.settings == doc


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
