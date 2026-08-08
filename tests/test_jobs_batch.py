"""Batch submission at a pinned version.

The route answers 200 even when items failed, so the interesting behaviour is all
in the reconciliation: what a caller is told ran, and what it is told did not.
No server and no clock — `summarize_batch` is a function of one payload.
"""

from __future__ import annotations

import pytest

from tamarind import jobs
from tamarind.errors import ValidationError
from tamarind.jobs import plan, wire


def _response(items: list[dict], **counts: int) -> dict:
    body: dict = {"results": items}
    body.update(counts)
    return body


class TestParsing:
    def test_reads_the_per_item_outcome(self) -> None:
        parsed = wire.parse_batch_submission(
            _response(
                [{"JobName": "a", "Type": "org/tool", "ok": True, "Id": "1"}],
                submitted=1,
                failed=0,
            )
        )
        assert parsed.submitted == 1 and parsed.failed == 0
        assert parsed.items[0].job_name == "a"
        assert parsed.items[0].ok is True
        assert parsed.items[0].job_id == "1"

    @pytest.mark.parametrize("payload", [None, "nope", [], 7, {}])
    def test_an_unreadable_payload_never_raises(self, payload: object) -> None:
        """Tolerant in: a shape we don't recognize yields empty, not an exception."""
        assert wire.parse_batch_submission(payload).items == ()

    def test_an_unreadable_item_is_not_counted_as_submitted(self) -> None:
        """`ok` defaults False. An item we cannot read is one we cannot claim ran."""
        parsed = wire.parse_batch_submission(_response(["garbage", None]))
        assert len(parsed.items) == 2
        assert not any(i.ok for i in parsed.items)

    def test_a_missing_ok_flag_is_not_success(self) -> None:
        """Only an explicit `ok: true` counts — a truthy-looking absence must not."""
        parsed = wire.parse_batch_submission(_response([{"JobName": "a"}]))
        assert parsed.items[0].ok is False


class TestSummarize:
    def test_every_item_ok_is_submitted(self) -> None:
        summary = plan.summarize_batch(
            wire.parse_batch_submission(
                _response([{"JobName": "a", "ok": True}, {"JobName": "b", "ok": True}])
            )
        )
        assert summary.outcome is plan.BatchOutcome.SUBMITTED
        assert summary.ok is True
        assert summary.submitted == ("a", "b")

    def test_a_mix_is_partial_and_not_ok(self) -> None:
        summary = plan.summarize_batch(
            wire.parse_batch_submission(
                _response(
                    [
                        {"JobName": "a", "ok": True},
                        {"JobName": "b", "ok": False, "error": "duplicate name"},
                    ]
                )
            )
        )
        assert summary.outcome is plan.BatchOutcome.PARTIAL
        assert summary.ok is False
        assert summary.submitted == ("a",)
        assert summary.failures == (("b", "duplicate name"),)

    def test_nothing_dispatched_is_failed(self) -> None:
        summary = plan.summarize_batch(
            wire.parse_batch_submission(_response([{"JobName": "a", "ok": False}]))
        )
        assert summary.outcome is plan.BatchOutcome.FAILED
        assert summary.failures == (("a", "no reason given"),)

    def test_the_items_beat_the_servers_counts(self) -> None:
        """The load-bearing one.

        A response claiming `submitted: 2, failed: 0` while an item says `ok: false`
        must NOT report success. Believing the header here is precisely how a batch
        failure becomes invisible: the caller sees "2 submitted", never retries, and
        the work silently never ran. Without this the outcome would be SUBMITTED.
        """
        summary = plan.summarize_batch(
            wire.parse_batch_submission(
                _response(
                    [{"JobName": "a", "ok": True}, {"JobName": "b", "ok": False}],
                    submitted=2,
                    failed=0,
                )
            )
        )
        assert summary.outcome is plan.BatchOutcome.PARTIAL
        assert summary.counts_disagreed is True

    def test_agreeing_counts_are_not_flagged(self) -> None:
        summary = plan.summarize_batch(
            wire.parse_batch_submission(
                _response([{"JobName": "a", "ok": True}], submitted=1, failed=0)
            )
        )
        assert summary.counts_disagreed is False

    def test_counts_only_is_believed_when_there_are_no_items(self) -> None:
        """Honest rather than clever: something ran, and we cannot say what."""
        summary = plan.summarize_batch(wire.parse_batch_submission({"submitted": 3, "failed": 0}))
        assert summary.outcome is plan.BatchOutcome.SUBMITTED
        assert summary.submitted == ()

    def test_an_empty_response_is_failure_not_success(self) -> None:
        summary = plan.summarize_batch(wire.parse_batch_submission({}))
        assert summary.outcome is plan.BatchOutcome.FAILED

    def test_a_failed_item_without_a_name_still_reports(self) -> None:
        summary = plan.summarize_batch(
            wire.parse_batch_submission(_response([{"ok": False, "error": "bad name"}]))
        )
        assert summary.failures == (("<unnamed>", "bad name"),)


class TestSizeLimit:
    def test_accepts_the_maximum(self) -> None:
        plan.validate_batch_size(plan.MAX_BATCH_ITEMS)

    def test_rejects_one_over_with_a_message_naming_the_limit(self) -> None:
        with pytest.raises(ValidationError) as exc:
            plan.validate_batch_size(plan.MAX_BATCH_ITEMS + 1)
        assert str(plan.MAX_BATCH_ITEMS) in str(exc.value)

    def test_rejects_empty(self) -> None:
        with pytest.raises(ValidationError):
            plan.validate_batch_size(0)

    def test_the_cap_matches_the_server(self) -> None:
        """Mirrors ORCHESTRATED_BATCH_MAX in the backend. If the server raises its
        cap, this is the line that has to move with it."""
        assert plan.MAX_BATCH_ITEMS == 500


class TestRequestShape:
    """`submit_batch_pinned` builds the request; these pin the parts that carry
    meaning rather than the whole body."""

    def test_stamps_the_channel_on_every_item(self) -> None:
        sent: dict = {}

        class FakeClient:
            def post_json(self, path, json):  # noqa: A002 - matches HTTPClient
                sent["path"] = path
                sent["json"] = json
                return {}

        jobs.submit_batch_pinned(
            FakeClient(),
            jobs=[{"jobName": "a", "type": "org/t"}, {"jobName": "b", "type": "org/t"}],
            tool_ref="org/t:v1",
        )
        assert sent["path"] == "v2/jobs/batch"
        assert all(i["jobSource"] == jobs.JOB_SOURCE for i in sent["json"]["jobs"])
        assert all(i["toolRef"] == "org/t:v1" for i in sent["json"]["jobs"])

    def test_an_explicit_per_item_toolref_wins(self) -> None:
        """A caller pinning items individually is not overridden by the default."""
        sent: dict = {}

        class FakeClient:
            def post_json(self, path, json):  # noqa: A002
                sent["json"] = json
                return {}

        jobs.submit_batch_pinned(
            FakeClient(),
            jobs=[{"jobName": "a", "toolRef": "org/t:v9"}],
            tool_ref="org/t:v1",
        )
        assert sent["json"]["jobs"][0]["toolRef"] == "org/t:v9"

    def test_does_not_mutate_the_callers_dicts(self) -> None:
        original = {"jobName": "a"}

        class FakeClient:
            def post_json(self, path, json):  # noqa: A002
                return {}

        jobs.submit_batch_pinned(FakeClient(), jobs=[original], tool_ref="org/t:v1")
        assert original == {"jobName": "a"}

    def test_never_sets_batch(self) -> None:
        """`batch` anchors children to a parent row that this path never creates;
        setting it would point the worker's aggregator at a row that isn't there."""
        sent: dict = {}

        class FakeClient:
            def post_json(self, path, json):  # noqa: A002
                sent["json"] = json
                return {}

        jobs.submit_batch_pinned(FakeClient(), jobs=[{"jobName": "a"}], tool_ref="org/t:v1")
        assert "batch" not in sent["json"]["jobs"][0]
