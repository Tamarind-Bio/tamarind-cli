"""Boundary parsing: the API's shape variance, resolved once.

These are table tests with no server, no fixtures and no clock — which is the whole
argument for having a boundary. Every case here previously had to be re-established
at each call site that read a payload.
"""

from __future__ import annotations

import dataclasses

import pytest

from tamarind.catalog import wire as catalog_wire
from tamarind.files import wire as files_wire
from tamarind.jobs import wire as jobs_wire


class TestParseJob:
    def test_reads_status_across_casings(self) -> None:
        assert jobs_wire.parse_job({"JobStatus": "Running"}).status == "Running"
        assert jobs_wire.parse_job({"status": "completed"}).status == "completed"
        assert jobs_wire.parse_job({"Status": "Stopped"}).status == "Stopped"

    def test_batch_parent_lifecycle_wins_over_per_job_status(self) -> None:
        """A parent can hold a nonterminal JobStatus while aggregation has finished —
        reading the wrong one is how a wait loop hangs on a completed batch."""
        parent = {"Type": "batch", "batchStatus": "Complete", "JobStatus": "Running"}
        assert jobs_wire.parse_job(parent).status == "Complete"
        assert jobs_wire.parse_job(parent).is_batch_parent is True

    def test_subjob_keeps_its_own_status_despite_parent_metadata(self) -> None:
        """The mirror case: a subjob carrying its parent's batchStatus must still
        report its own, or every subjob in a finished batch looks finished."""
        subjob = {
            "Type": "boltz",
            "JobName": "batch-1-subjob-1",
            "batchName": "batch-1",
            "batchStatus": "Complete",
            "JobStatus": "Running",
        }
        parsed = jobs_wire.parse_job(subjob)
        assert parsed.status == "Running"
        assert parsed.is_batch_parent is False

    def test_batch_name_without_job_name_is_a_parent(self) -> None:
        parsed = jobs_wire.parse_job({"batchName": "batch-1", "batchStatus": "Aggregating"})
        assert parsed.is_batch_parent is True
        assert parsed.name == "batch-1"

    @pytest.mark.parametrize("payload", [None, 7, "text", [], {"unrelated": 1}])
    def test_unknown_shapes_parse_to_blanks_rather_than_raising(self, payload: object) -> None:
        """Tolerant in, strict out. Refusing to parse would turn a new server field
        into a client-side outage; the caller gets nulls and the payload intact."""
        parsed = jobs_wire.parse_job(payload)
        assert parsed.name is None and parsed.status is None

    def test_raw_payload_is_preserved(self) -> None:
        """The CLI renders fields this type doesn't model, so nothing may be dropped."""
        payload = {"JobName": "x", "JobStatus": "Complete", "SomeFutureField": 42}
        assert jobs_wire.parse_job(payload).raw["SomeFutureField"] == 42

    def test_job_is_immutable(self) -> None:
        parsed = jobs_wire.parse_job({"JobName": "x"})
        with pytest.raises(dataclasses.FrozenInstanceError):
            parsed.name = "y"  # type: ignore[misc]


class TestFindJob:
    def test_list_envelope_prefers_the_named_job(self) -> None:
        resp = {"jobs": [{"JobName": "a"}, {"JobName": "b"}]}
        assert jobs_wire.find_job(resp, "b")["JobName"] == "b"

    def test_list_envelope_falls_back_to_first(self) -> None:
        resp = {"jobs": [{"JobName": "a"}, {"JobName": "b"}]}
        assert jobs_wire.find_job(resp, "zzz")["JobName"] == "a"

    def test_index_keyed_envelope(self) -> None:
        """What the API returns for a single-jobName query."""
        resp = {
            "0": {"JobName": "cli-e2e", "JobStatus": "In Queue"},
            "statuses": {"In Queue": 1},
        }
        assert jobs_wire.find_job(resp, "cli-e2e")["JobName"] == "cli-e2e"

    def test_bare_object(self) -> None:
        payload = {"JobName": "a", "JobStatus": "Running"}
        assert jobs_wire.find_job(payload, "a") == payload

    @pytest.mark.parametrize("resp", [None, [], "text", {"statuses": {"Complete": 0}}])
    def test_unrecognized_envelope_is_none(self, resp: object) -> None:
        assert jobs_wire.find_job(resp, "x") is None


class TestParseFile:
    def test_bare_string_entry(self) -> None:
        assert files_wire.parse_file("a.pdb").name == "a.pdb"

    @pytest.mark.parametrize("key", ["name", "filename", "key"])
    def test_object_entry_under_any_name_key(self, key: str) -> None:
        assert files_wire.parse_file({key: "b.cif"}).name == "b.cif"

    def test_metadata_is_typed_when_present(self) -> None:
        parsed = files_wire.parse_file({"name": "c.pdb", "size": 12, "lastModified": "2026-01-01"})
        assert (parsed.size, parsed.last_modified) == (12, "2026-01-01")

    def test_non_string_entry_degrades_to_its_string_form(self) -> None:
        """Preserved from the pre-boundary behaviour: a listing is a read, and a
        surprising entry should not fail it."""
        assert files_wire.parse_file(123).name == "123"


class TestParseSchema:
    def test_required_names_and_example_settings(self) -> None:
        schema = {
            "parameters": [
                {"name": "sequence", "required": True},
                {"name": "seed", "required": False},
                {"name": "temperature"},
            ],
            "exampleJob": {"settings": {"sequence": "MKT"}},
        }
        parsed = catalog_wire.parse_schema(schema)
        assert parsed.required_names == ("sequence",)
        assert parsed.example_settings == {"sequence": "MKT"}

    @pytest.mark.parametrize("schema", [{}, None, {"parameters": "not-a-list"}])
    def test_missing_or_malformed_sections_parse_empty(self, schema: object) -> None:
        parsed = catalog_wire.parse_schema(schema)
        assert parsed.required_names == () and parsed.example_settings == {}


class TestDelegationIsRealNotParallel:
    """The public helpers must BE the parser, not a copy kept in step by hand.

    Asserting the two agree on some inputs does not show that — a hand-maintained
    copy agrees too, right up until someone edits one side. So these patch the
    parser and check the helper's answer moves with it. A helper carrying its own
    logic is unaffected by the patch and fails here, which is the whole point.
    """

    def test_job_status_and_name_come_from_the_parser(self, monkeypatch) -> None:
        from tamarind.jobs import plan

        sentinel = jobs_wire.Job(name="SENTINEL-NAME", status="SENTINEL-STATUS")
        monkeypatch.setattr(jobs_wire, "parse_job", lambda payload: sentinel)
        # Real payloads whose real answers are "Running"/"x" — a helper with its own
        # copy of the casing rules would return those and fail.
        assert plan.job_status({"JobStatus": "Running"}) == "SENTINEL-STATUS"
        assert plan.job_name({"JobName": "x"}) == "SENTINEL-NAME"

    def test_extract_single_comes_from_the_parser(self, monkeypatch) -> None:
        from tamarind.jobs import plan

        monkeypatch.setattr(jobs_wire, "find_job", lambda resp, name: {"SENTINEL": True})
        assert plan.extract_single({"jobs": [{"JobName": "a"}]}, "a") == {"SENTINEL": True}

    def test_file_name_comes_from_the_parser(self, monkeypatch) -> None:
        from tamarind.files import plan

        monkeypatch.setattr(
            files_wire, "parse_file", lambda e: files_wire.FileEntry(name="SENTINEL")
        )
        assert plan.file_name({"key": "z.pdb"}) == "SENTINEL"

    def test_catalog_helpers_come_from_the_parser(self, monkeypatch) -> None:
        from tamarind.catalog import plan

        monkeypatch.setattr(
            catalog_wire,
            "parse_schema",
            lambda s: catalog_wire.ToolSchema(
                parameters=(catalog_wire.Parameter(name="SENTINEL", required=True),),
                example_settings={"sentinel": 1},
            ),
        )
        real = {
            "parameters": [{"name": "sequence", "required": True}],
            "exampleJob": {"settings": {"s": 1}},
        }
        assert plan.required_param_names(real) == ["SENTINEL"]
        assert plan.example_settings(real) == {"sentinel": 1}


class TestHelpersStillBehaveCorrectly:
    """Unpatched behaviour, so the delegation tests above can't pass a broken parser."""

    def test_job_status_reads_batch_parent_lifecycle(self) -> None:
        from tamarind.jobs import plan

        assert plan.job_status({"Type": "batch", "batchStatus": "Complete"}) == "Complete"

    def test_file_name_reads_any_key(self) -> None:
        from tamarind.files import plan

        assert plan.file_name({"key": "z.pdb"}) == "z.pdb"

    def test_catalog_helpers_read_a_real_schema(self) -> None:
        from tamarind.catalog import plan

        schema = {
            "parameters": [{"name": "s", "required": True}],
            "exampleJob": {"settings": {"s": 1}},
        }
        assert plan.required_param_names(schema) == ["s"]
        assert plan.example_settings(schema) == {"s": 1}
