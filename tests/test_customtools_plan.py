"""Custom-tool decisions, as tables. No server, no clock, no fixtures.

These exist before the network code that uses them, which is the point: the deploy
matrix is the part that is expensive to get wrong and cheap to settle here. Every real
build costs five minutes, so nothing that can be decided on paper should be discovered
against staging.
"""

from __future__ import annotations

import pytest

from tamarind.customtools import plan, wire


def _result(
    path: str | None, *, version: str = "v3", build: str | None = "b-1"
) -> wire.DeployResult:
    return wire.DeployResult(version_name=version, path=path, build_id=build, raw={"path": path})


class TestBuildTerminality:
    """A build that is watched with the wrong terminal set does not error — it hangs."""

    @pytest.mark.parametrize(
        "status", ["SUCCEEDED", "FAILED", "STOPPED", "FAULT", "TIMED_OUT", "CLIENT_ERROR"]
    )
    def test_all_six_terminal_states(self, status: str) -> None:
        assert plan.is_terminal_build(status) is True

    @pytest.mark.parametrize("status", ["IN_PROGRESS", "QUEUED", None, "", "unknown"])
    def test_non_terminal_states(self, status: str | None) -> None:
        assert plan.is_terminal_build(status) is False

    def test_the_two_easily_forgotten_states_are_terminal(self) -> None:
        """FAULT and CLIENT_ERROR are the ones a hand-written set omits, and omitting
        either means polling a build that will never change again."""
        assert plan.is_terminal_build("FAULT")
        assert plan.is_terminal_build("CLIENT_ERROR")

    @pytest.mark.parametrize("status", ["succeeded", "Succeeded", "SUCCEEDED"])
    def test_success_is_case_insensitive(self, status: str) -> None:
        assert plan.build_succeeded(status) is True

    @pytest.mark.parametrize("status", ["FAILED", "STOPPED", "FAULT", None, "Complete"])
    def test_non_success(self, status: str | None) -> None:
        assert plan.build_succeeded(status) is False

    def test_a_version_status_is_not_a_build_status(self) -> None:
        """The vocabularies overlap on "Stopped" and mean different things. "Complete"
        is a VERSION state and must never read as a successful build."""
        assert plan.build_succeeded(wire.COMPLETE_VERSION_STATUS) is False


class TestNeedsLateLandingRecheck:
    """Exactly one corner is ambiguous, and only it should cost an extra read."""

    def test_the_ambiguous_corner(self) -> None:
        assert plan.needs_late_landing_recheck(ref_moved=False, path="noop") is True

    @pytest.mark.parametrize(
        ("ref_moved", "path"),
        [
            (True, "noop"),  # our upload landed; noop means someone beat us to it
            (False, "building"),  # something is building, so the upload plainly landed
            (True, "building"),
            (False, "saved"),
            (True, "saved"),
        ],
    )
    def test_every_other_combination_is_already_decided(self, ref_moved: bool, path: str) -> None:
        assert plan.needs_late_landing_recheck(ref_moved=ref_moved, path=path) is False


class TestReconcileMatrix:
    """The whole matrix, exhaustively. A gap here is a silently wrong deploy."""

    @pytest.mark.parametrize("ref_moved", [True, False])
    def test_building_is_a_deploy_regardless_of_what_we_observed(self, ref_moved: bool) -> None:
        """`ref_moved` is advisory. If the server is building, the upload landed —
        our failure to observe the move only means the poll was slow."""
        out = plan.reconcile(ref_moved=ref_moved, result=_result("building"))
        assert out.deployed is True
        assert out.reason == "built"
        assert out.build_id == "b-1"

    @pytest.mark.parametrize("ref_moved", [True, False])
    def test_saved_is_a_deploy_regardless_of_what_we_observed(self, ref_moved: bool) -> None:
        out = plan.reconcile(ref_moved=ref_moved, result=_result("saved", build=None))
        assert out.deployed is True
        assert out.reason == "saved"

    def test_noop_without_an_observed_move_is_a_genuine_no_op(self) -> None:
        """The common CI case: redeploying an unchanged folder. An identical upload
        produces no new commit, so the ref legitimately never moves — treating that as
        failure would turn every unchanged re-deploy into an error."""
        out = plan.reconcile(ref_moved=False, result=_result("noop", build=None))
        assert out.deployed is False
        assert out.reason == "unchanged"

    def test_noop_after_an_observed_move_means_someone_else_got_there_first(self) -> None:
        """Our upload landed, yet the server found an existing version at that source.
        Nothing for us to do, but it is NOT the same as 'nothing changed'."""
        out = plan.reconcile(ref_moved=True, result=_result("noop", build=None))
        assert out.deployed is False
        assert out.reason == "already-deployed"

    def test_the_race_is_detected_here_and_resolved_by_the_shell(self) -> None:
        """The race is NOT an outcome of this function.

        `needs_late_landing_recheck` flags the ambiguous corner and `flow.build` responds
        by deploying again, so by the time reconcile runs the ref is confirmed moved and
        the retry lands on an ordinary path. Modelling "raced" as a reportable outcome
        would create a state the shell can never produce — and a test asserting it would
        pass forever while proving nothing.
        """
        assert plan.needs_late_landing_recheck(ref_moved=False, path="noop") is True
        # What the retry then reconciles to, the ref now confirmed moved:
        after_retry = plan.reconcile(ref_moved=True, result=_result("building"))
        assert after_retry.deployed is True and after_retry.reason == "built"

    @pytest.mark.parametrize("path", [None, "", "rebuilding", "unknown"])
    def test_an_unrecognized_path_is_reported_not_guessed(self, path: str | None) -> None:
        """A server that invents a fourth outcome should surface, not be silently
        mapped onto one of the three we know."""
        out = plan.reconcile(ref_moved=True, result=_result(path))
        assert out.deployed is False
        assert out.reason.startswith("unknown-path:")

    def test_every_outcome_carries_the_version_name(self) -> None:
        """The publish step needs it, so no branch may drop it."""
        for path in ("building", "saved", "noop", "bogus"):
            assert plan.reconcile(ref_moved=True, result=_result(path)).version_name == "v3"

    def test_every_reason_has_an_explanation(self) -> None:
        """`reason` is machine-readable and `explanation` is what a human sees; a
        reason with no entry would render as a bare slug."""
        for path in ("building", "saved", "noop"):
            for moved in (True, False):
                out = plan.reconcile(ref_moved=moved, result=_result(path))
                assert out.reason in plan.REASONS
                assert out.explanation != out.reason


class TestSelectPublishable:
    def _v(self, name: str, status: str) -> wire.Version:
        return wire.Version(name=name, status=status)

    def test_picks_the_newest_complete_version(self) -> None:
        versions = (self._v("v3", "Running"), self._v("v2", "Complete"), self._v("v1", "Complete"))
        assert plan.select_publishable(versions).name == "v2"

    def test_skips_a_failed_build(self) -> None:
        """A failed build leaves its version *Stopped*, not FAILED. Selecting on
        'not failed' would publish a version that never produced an image."""
        versions = (self._v("v3", "Stopped"), self._v("v2", "Complete"))
        assert plan.select_publishable(versions).name == "v2"

    @pytest.mark.parametrize(
        "versions",
        [
            (),
            (wire.Version(name="v1", status="Stopped"),),
            (wire.Version(name="v1", status="Running"),),
        ],
    )
    def test_none_when_nothing_has_built(self, versions: tuple) -> None:
        assert plan.select_publishable(versions) is None


class TestCancellableBuild:
    def test_finds_the_in_flight_build(self) -> None:
        versions = (
            wire.Version(name="v2", status="Running", build_id="b-2"),
            wire.Version(name="v1", status="Complete", build_id="b-1"),
        )
        assert plan.cancellable_build_id(versions) == "b-2"

    @pytest.mark.parametrize("status", ["Queued", "Claimed", "Running"])
    def test_every_in_flight_state_counts(self, status: str) -> None:
        assert (
            plan.cancellable_build_id((wire.Version(name="v1", status=status, build_id="b"),))
            == "b"
        )

    def test_none_when_everything_is_terminal(self) -> None:
        """Cancelling a finished build should raise, not silently target the latest —
        so this answers None rather than falling back."""
        versions = (
            wire.Version(name="v2", status="Complete", build_id="b-2"),
            wire.Version(name="v1", status="Stopped", build_id="b-1"),
        )
        assert plan.cancellable_build_id(versions) is None
