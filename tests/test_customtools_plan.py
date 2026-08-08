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
    """The question is only "did we watch our own content land before deploying"."""

    @pytest.mark.parametrize("path", ["noop", "building", "saved", None, "something-new"])
    def test_an_unwatched_landing_is_rechecked_whatever_the_server_said(self, path) -> None:
        """THE regression, and the sharpest one in this PR.

        The first version keyed on `noop`, which looked right because the ambiguity is
        most visible there. But when the PREVIOUS head itself needed building, a deploy
        that raced extraction comes back `building` for the OLD tree — and that path
        reports `deployed: true`, so `deploy --publish` publishes a version built from
        source the caller never asked to ship, while their upload sits undeployed.

        Keying on `noop` skipped exactly the paths capable of publishing the wrong
        thing. Restore `and path == "noop"` and every case here except the first fails.
        """
        assert plan.needs_late_landing_recheck(ref_moved=False, path=path) is True

    @pytest.mark.parametrize("path", ["noop", "building", "saved"])
    def test_a_watched_landing_needs_no_recheck(self, path: str) -> None:
        """A moved ref already proves our content was in the repository when the deploy
        ran, so there is nothing later to discover."""
        assert plan.needs_late_landing_recheck(ref_moved=True, path=path) is False

    def test_the_path_argument_is_not_load_bearing(self) -> None:
        """Kept only so existing callers keep working; the decision must not read it."""
        assert plan.needs_late_landing_recheck(ref_moved=False) is True


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


class TestUnconfirmedExtraction:
    """A no-op means two different things, and only one of them is good news."""

    def test_a_confirmed_no_op_is_unchanged(self) -> None:
        out = plan.reconcile(
            ref_moved=False, result=_result("noop", build=None), extraction_landed=True
        )
        assert out.reason == "unchanged"
        assert out.deployed is False

    def test_an_unconfirmed_no_op_is_not_called_unchanged(self) -> None:
        """The silent-failure case. If the server never confirmed it unpacked the
        upload, a no-op may mean the deploy built the PREVIOUS source and the new code
        was never built at all. `unchanged` asserts a success nobody observed.

        Without the `extraction_landed` branch this returns "unchanged", and a CI job
        branching on it reports a clean deploy for source that never shipped.
        """
        out = plan.reconcile(
            ref_moved=False, result=_result("noop", build=None), extraction_landed=False
        )
        assert out.reason == "unconfirmed"
        assert out.deployed is False
        assert "unknown" in out.explanation, "the reason must say what the caller should do"

    def test_confirmation_is_irrelevant_once_the_ref_moved(self) -> None:
        """A moved ref already proves the upload landed, so the extra flag must not
        override the more specific answer."""
        for landed in (True, False):
            out = plan.reconcile(
                ref_moved=True, result=_result("noop", build=None), extraction_landed=landed
            )
            assert out.reason == "already-deployed"

    def test_a_real_deploy_is_never_downgraded(self) -> None:
        """`building` and `saved` are positive statements from the server; an
        unconfirmed extraction does not make them less true."""
        for path in ("building", "saved"):
            out = plan.reconcile(ref_moved=False, result=_result(path), extraction_landed=False)
            assert out.deployed is True

    def test_the_default_keeps_existing_callers_honest(self) -> None:
        """Defaulting to True means an old caller reads exactly as before rather than
        every no-op suddenly becoming `unconfirmed`."""
        assert plan.reconcile(ref_moved=False, result=_result("noop", build=None)).reason == (
            "unchanged"
        )
