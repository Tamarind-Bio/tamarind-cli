"""`example_settings` must return an example the API will actually accept.

The catalog builds `exampleJob.settings` from every parameter's `example`, including ones
gated behind a `conditionals` controller it does not also set — so the raw blob is rejected
by /submit-job. These cover the pruning that makes it submittable, against the real boltz
shape that first surfaced it (the /api-docs/sdk quickstart submitted this verbatim and 400'd
with `boltz field "ligands" can only be set when addLigands equals true`).
"""

from tamarind import catalog


def _schema(parameters, settings):
    return {"parameters": parameters, "exampleJob": {"settings": settings}}


def test_drops_field_whose_controller_is_absent():
    schema = _schema(
        [
            {"name": "sequence"},
            {"name": "addLigands", "default": False},
            {
                "name": "ligands",
                "conditionals": [
                    {"checkType": "equals", "otherSettingName": "addLigands", "otherSettingValue": True}
                ],
            },
        ],
        {"sequence": "MKT", "ligands": ["SAH"]},
    )
    assert catalog.example_settings(schema) == {"sequence": "MKT"}


def test_keeps_field_whose_gate_a_default_satisfies():
    # useMSA defaults to true, so msaDatabase is legitimately active even though the
    # example never mentions useMSA. The server validates post-autofill settings too.
    schema = _schema(
        [
            {"name": "useMSA", "default": True},
            {
                "name": "msaDatabase",
                "conditionals": [
                    {"checkType": "equals", "otherSettingName": "useMSA", "otherSettingValue": True}
                ],
            },
        ],
        {"msaDatabase": "uniref"},
    )
    assert catalog.example_settings(schema) == {"msaDatabase": "uniref"}


def test_prunes_transitively_to_a_fixed_point():
    # boltz's real chain: version -> predictAffinity -> binderChain. Dropping predictAffinity
    # must also drop binderChain, which a single pass would leave behind.
    schema = _schema(
        [
            {"name": "version", "default": "2.1.0"},
            {
                "name": "predictAffinity",
                "conditionals": [
                    {"checkType": "equals", "otherSettingName": "version", "otherSettingValue": "2.2.1"}
                ],
            },
            {
                "name": "binderChain",
                "conditionals": [
                    {"checkType": "equals", "otherSettingName": "predictAffinity", "otherSettingValue": True}
                ],
            },
        ],
        {"predictAffinity": True, "binderChain": "C"},
    )
    assert catalog.example_settings(schema) == {}


def test_supports_the_other_check_types_the_catalog_uses():
    # not-equals and notEmpty both appear in live schemas (proteinmpnn/rfdiffusion
    # verifyTopK, boltzgen scaffoldSubType).
    schema = _schema(
        [
            {"name": "verify", "default": ""},
            {
                "name": "verifyTopK",
                "conditionals": [
                    {"checkType": "notEmpty", "otherSettingName": "verify"},
                    {"checkType": "not-equals", "otherSettingName": "verify", "otherSettingValue": "none"},
                ],
            },
        ],
        {"verifyTopK": 5},
    )
    assert catalog.example_settings(schema) == {}

    schema["exampleJob"]["settings"] = {"verify": "alphafold", "verifyTopK": 5}
    assert catalog.example_settings(schema) == {"verify": "alphafold", "verifyTopK": 5}


def test_unknown_check_type_is_not_a_reason_to_prune():
    # Matches the JS `default:` branch: an unrecognized checkType is skipped, so we keep the
    # field and let the server decide rather than silently dropping a valid one.
    schema = _schema(
        [{"name": "x", "conditionals": [{"checkType": "someNewThing", "otherSettingName": "y"}]}, {"name": "y"}],
        {"x": 1, "y": 2},
    )
    assert catalog.example_settings(schema) == {"x": 1, "y": 2}


def test_ungated_and_empty_examples_pass_through():
    assert catalog.example_settings({"parameters": [{"name": "a"}], "exampleJob": {"settings": {"a": 1}}}) == {"a": 1}
    assert catalog.example_settings({}) == {}
