"""config.json validation.

The rules mirror the server's. What is worth testing is the JUDGEMENT: which
findings are fatal, which are warnings, and — most of all — which mistakes the
server accepts and then ignores, since those are the ones that cost a rebuild to
discover.
"""

from __future__ import annotations

import pytest

from tamarind.customtools import manifest


def _errors(config: object) -> list[str]:
    return list(manifest.check(config).errors)


def _warnings(config: object) -> list[str]:
    return list(manifest.check(config).warnings)


class TestShape:
    def test_an_empty_object_is_valid(self) -> None:
        """Every field is optional; the server fills defaults. A check that demanded
        fields would reject configs that deploy fine today."""
        assert manifest.check({}).ok

    @pytest.mark.parametrize("config", [None, [], "text", 7])
    def test_a_non_object_is_fatal(self, config: object) -> None:
        assert not manifest.check(config).ok

    def test_never_raises_on_hostile_input(self) -> None:
        """Findings are the return value; a malformed config must not become an
        exception with a stack trace where a message belongs."""
        assert not manifest.check({"inputs": [None, 5, {"name": None}]}).ok


class TestMisplacedFlags:
    """The category that matters most: accepted, then silently ignored."""

    @pytest.mark.parametrize("flag", ["usesMsa", "designBatching", "designsPerBatch"])
    def test_a_top_level_input_flag_warns_but_does_not_fail(self, flag: str) -> None:
        """The server reads none of these at the top level. It deploys happily and the
        feature is simply absent — so this must be reported, and must NOT block the
        deploy, because the config is genuinely valid."""
        findings = manifest.check({flag: True})
        assert findings.ok
        assert any(flag in w for w in findings.warnings)

    def test_the_warning_shows_where_the_flag_belongs(self) -> None:
        """A warning that only says "wrong" makes the author guess. Naming the shape
        is the difference between a fix and a support question."""
        warning = next(w for w in _warnings({"usesMsa": True}) if "usesMsa" in w)
        assert '"type": "sequence"' in warning

    def test_the_same_flag_on_an_input_is_correct_and_silent(self) -> None:
        findings = manifest.check(
            {"inputs": [{"name": "seq", "type": "sequence", "usesMsa": True}]}
        )
        assert findings.ok and not findings.warnings


class TestUsesMsa:
    def test_reports_which_input_is_aligned(self) -> None:
        facts = manifest.check(
            {"inputs": [{"name": "target", "type": "sequence", "usesMsa": True}]}
        ).facts
        assert facts["usesMsa"] is True
        assert facts["msaInput"] == "target"

    def test_absent_means_false(self) -> None:
        assert manifest.check({"inputs": [{"name": "a", "type": "text"}]}).facts["usesMsa"] is False

    def test_only_a_sequence_input_may_carry_it(self) -> None:
        """The value is sent to the aligner as a protein query, so a text or number
        field would put arbitrary content in front of it."""
        assert any(
            "sequence" in e
            for e in _errors({"inputs": [{"name": "a", "type": "text", "usesMsa": True}]})
        )

    def test_two_flags_are_rejected(self) -> None:
        """The MSA stage aligns a single field. Silently honouring one of two is worse
        than refusing both."""
        assert _errors(
            {
                "inputs": [
                    {"name": "a", "type": "sequence", "usesMsa": True},
                    {"name": "b", "type": "sequence", "usesMsa": True},
                ]
            }
        )

    def test_a_string_false_is_rejected_rather_than_believed(self) -> None:
        """`"false"` is truthy in Python and this value becomes the attribute the
        worker reads back. Without the bool check the tool would run MSA on a config
        that plainly says not to."""
        errors = _errors({"inputs": [{"name": "a", "type": "sequence", "usesMsa": "false"}]})
        assert any("boolean" in e for e in errors)

    def test_an_explicit_false_is_fine_anywhere(self) -> None:
        assert manifest.check({"inputs": [{"name": "a", "type": "text", "usesMsa": False}]}).ok


class TestBatching:
    def test_only_a_number_input_may_batch(self) -> None:
        assert _errors(
            {
                "inputs": [
                    {"name": "n", "type": "text", "designBatching": True, "designsPerBatch": 10}
                ]
            }
        )

    def test_batching_needs_a_positive_designs_per_batch(self) -> None:
        assert _errors({"inputs": [{"name": "n", "type": "number", "designBatching": True}]})

    def test_an_integer_valued_float_is_accepted(self) -> None:
        """JSON has no int/float distinction, so 100.0 is how a valid config can
        legitimately arrive."""
        assert manifest.check(
            {
                "inputs": [
                    {
                        "name": "n",
                        "type": "number",
                        "designBatching": True,
                        "designsPerBatch": 100.0,
                    }
                ]
            }
        ).ok

    def test_true_is_not_a_count(self) -> None:
        """bool subclasses int, so `designsPerBatch: true` would pass a naive
        isinstance check and then split every run into batches of one."""
        assert _errors(
            {
                "inputs": [
                    {
                        "name": "n",
                        "type": "number",
                        "designBatching": True,
                        "designsPerBatch": True,
                    }
                ]
            }
        )

    def test_two_batching_inputs_are_rejected(self) -> None:
        assert _errors(
            {
                "inputs": [
                    {"name": "a", "type": "number", "designBatching": True, "designsPerBatch": 5},
                    {"name": "b", "type": "number", "designBatching": True, "designsPerBatch": 5},
                ]
            }
        )


class TestResources:
    @pytest.mark.parametrize("gpu", ["A100", "None", "T4"])
    def test_accepts_the_real_skus(self, gpu: str) -> None:
        assert manifest.check({"gpuType": gpu}).ok

    def test_accepts_the_legacy_alias(self) -> None:
        """A10g upgrades transparently server-side; rejecting it here would fail a
        config that deploys fine."""
        assert manifest.check({"gpuType": "A10g"}).ok

    def test_rejects_an_unknown_sku_and_lists_the_real_ones(self) -> None:
        errors = _errors({"gpuType": "H100"})
        assert errors and "A100" in errors[0]

    def test_rejects_a_memory_size_that_is_not_offered(self) -> None:
        assert _errors({"memory": "16Gi"})

    def test_cpu_above_the_cap_is_fatal_but_below_the_floor_is_only_a_warning(self) -> None:
        """Asymmetric because the server is: it rejects the high side and silently
        clamps the low one. Treating both as errors would fail a deployable config."""
        assert _errors({"cpu": 99})
        assert not _errors({"cpu": 0})
        assert _warnings({"cpu": 0})

    def test_home_disk_out_of_range_is_a_warning_not_an_error(self) -> None:
        """Clamped at both ends, never rejected."""
        assert not _errors({"homeDiskGi": 500})
        assert _warnings({"homeDiskGi": 500})


class TestMisc:
    @pytest.mark.parametrize("value", ["5:0:0", "0:59:59", ""])
    def test_accepts_valid_est_times(self, value: str) -> None:
        assert manifest.check({"estTime": value}).ok

    @pytest.mark.parametrize("value", ["5:0", "5:60:0", "1:0:99", "an hour"])
    def test_rejects_malformed_est_times(self, value: str) -> None:
        assert _errors({"estTime": value})

    def test_requires_a_scheme_on_the_paper_url(self) -> None:
        assert _errors({"paperUrl": "biorxiv.org/x"})
        assert manifest.check({"paperUrl": "https://biorxiv.org/x"}).ok

    def test_env_vars_must_be_strings(self) -> None:
        assert _errors({"envVars": {"K": 1}})
        assert manifest.check({"envVars": {"K": "1"}}).ok

    @pytest.mark.parametrize("value", [30, 90000, "3600", True])
    def test_rejects_out_of_range_runtimes(self, value: object) -> None:
        assert _errors({"maxRuntimeSeconds": value})

    def test_accepts_an_integer_valued_float_runtime(self) -> None:
        assert manifest.check({"maxRuntimeSeconds": 3600.0}).ok

    def test_duplicate_input_names_are_rejected(self) -> None:
        """The run form keys inputs by name, so the second silently shadows the first."""
        assert _errors({"inputs": [{"name": "a", "type": "text"}, {"name": "a", "type": "text"}]})

    def test_an_unknown_input_type_is_not_rejected(self) -> None:
        """Deliberately silent. The server accepts types this client has never heard
        of, so a hardcoded enum here would reject valid configs the day one is added."""
        assert manifest.check({"inputs": [{"name": "a", "type": "something-new"}]}).ok

    def test_unknown_top_level_keys_pass_through(self) -> None:
        assert manifest.check({"someFutureField": {"nested": True}}).ok


class TestOutputs:
    def test_two_primary_csvs_are_rejected(self) -> None:
        assert _errors(
            {
                "producedOutputs": [
                    {"type": "csv", "primary": True, "path": "a.csv"},
                    {"type": "csv", "primary": True, "path": "b.csv"},
                ]
            }
        )

    def test_the_primary_csv_needs_a_path_when_there_are_several(self) -> None:
        """Without one the declaration matches every .csv in a child."""
        assert _errors(
            {
                "producedOutputs": [
                    {"type": "csv", "primary": True},
                    {"type": "csv", "path": "b.csv"},
                ]
            }
        )

    def test_a_single_primary_csv_needs_no_path(self) -> None:
        assert manifest.check({"producedOutputs": [{"type": "csv", "primary": True}]}).ok


class TestEnvAssignments:
    def test_parses_pairs(self) -> None:
        assert manifest.parse_env_assignments(["A=1", "B=two"]) == {"A": "1", "B": "two"}

    def test_splits_on_the_first_equals_only(self) -> None:
        """Base64 values and connection strings contain '='. Splitting on every one
        would truncate a credential, and the resulting failure looks like a bad key
        rather than a mangled value."""
        assert manifest.parse_env_assignments(["TOKEN=aGVsbG8=="]) == {"TOKEN": "aGVsbG8=="}

    def test_an_empty_value_is_allowed(self) -> None:
        """`KEY=` is how you blank a variable."""
        assert manifest.parse_env_assignments(["KEY="]) == {"KEY": ""}

    @pytest.mark.parametrize("bad", ["NOEQUALS", "=value", "HAS SPACE=1", "a-b=1"])
    def test_rejects_what_is_not_an_assignment(self, bad: str) -> None:
        from tamarind.errors import ValidationError

        with pytest.raises(ValidationError):
            manifest.parse_env_assignments([bad])

    def test_later_wins_on_a_repeated_key(self) -> None:
        assert manifest.parse_env_assignments(["A=1", "A=2"]) == {"A": "2"}


class TestEnvVarsAreNotACredentialSink:
    """config.json is uploaded verbatim and becomes an image layer, so a value written
    here is exposed permanently — and the filename filters cannot help, because this is
    a file the tool genuinely needs holding a field the server genuinely reads."""

    def test_populated_env_values_are_rejected(self) -> None:
        """Without this check the manifest validates happily and the archive carries the
        literal key into every built image."""
        errors = _errors({"envVars": {"OPENAI_API_KEY": "sk-live-abc"}})
        assert errors
        assert "OPENAI_API_KEY" in errors[0]

    def test_the_message_names_the_safe_alternative(self) -> None:
        """Refusing without saying where to put it is how someone works around the
        check instead of using the mechanism that exists."""
        assert "ct config --env" in _errors({"envVars": {"K": "v"}})[0]

    def test_the_key_names_alone_are_fine(self) -> None:
        """Declaring which variables a tool expects is useful and exposes nothing."""
        assert manifest.check({"envVars": {"OPENAI_API_KEY": "", "MODEL": ""}}).ok

    def test_absent_env_vars_are_fine(self) -> None:
        assert manifest.check({}).ok

    def test_the_shape_check_still_runs_first(self) -> None:
        assert _errors({"envVars": {"K": 1}})
