"""Custom-tool decisions. Pure — no network, no clock, no filesystem.

The interesting one is :func:`reconcile`. Deploying is not a single call: the archive
is uploaded, the server extracts it in the background, and the deploy that follows
builds at whatever the repository currently points to. Those can race, and the naive
handling of that race silently ships nothing.

Everything here is a function of values the caller already holds, so the whole matrix
is a table test with no server and no clock.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from . import wire

# ---------------------------------------------------------------- build status ----


def is_terminal_build(status: str | None) -> bool:
    """Whether a build has stopped changing.

    Compared case-insensitively and against ALL six terminal states. Watching only the
    obvious two leaves a poll loop running forever when a build FAULTs or is rejected
    as a CLIENT_ERROR.
    """
    return bool(status) and status.upper() in wire.TERMINAL_BUILD_STATUSES


def build_succeeded(status: str | None) -> bool:
    return bool(status) and status.upper() == wire.SUCCESSFUL_BUILD_STATUS


# ------------------------------------------------------------------ reconcile ----

# Why each outcome exists, keyed by `reason`. Kept as data so the CLI and a script can
# explain a result without either restating the matrix.
REASONS: Mapping[str, str] = {
    "built": "a new image is building",
    "saved": "source changed; the existing image was reused",
    "unchanged": "nothing to do — the source is identical to what is already deployed",
    "already-deployed": "this exact source was already deployed by another run",
    "unconfirmed": (
        "the server did not confirm it finished unpacking the upload, so whether your "
        "source is deployed is unknown — check `ct status` before assuming it shipped"
    ),
}


@dataclass(frozen=True)
class ConfirmedVersion:
    """A version we KNOW was built from the caller's own source.

    Evidence, not a name. `publish` promoting the wrong version is the worst outcome
    the deploy sequence can produce, and it happened twice: once because an unconfirmed
    extraction still reported `deployed: true`, and once because a deployed response
    with no version name silently skipped the publish and exited zero.

    Both were gates I had to remember to write. Making the automatic publish path
    require this instead means the bad state cannot be constructed: there is exactly
    one producer, :meth:`DeployOutcome.confirmed_version`, and it returns None in
    every case where publishing would be wrong.
    """

    name: str


@dataclass(frozen=True)
class DeployOutcome:
    """The result of a deploy, with `deployed` decided in exactly one place.

    Callers must not re-derive "did anything happen" from `path`: that inference is
    what the reconcile step exists to make, and two callers making it separately is
    how they come to disagree.
    """

    path: str | None = None
    version_name: str | None = None
    build_id: str | None = None
    deployed: bool = False
    reason: str = "unchanged"
    # Whether we ever OBSERVED our own upload in the repository. False means this
    # deploy may have run against the previous source, whatever the server reported.
    #
    # Separate from `deployed` because the two answer different questions and only one
    # of them can be trusted here: `deployed` says the server acted, `confirmed` says
    # it acted on OUR source. Rechecking the ref at more and more points kept missing
    # a window (before the build wait, then during it); carrying the doubt forward
    # instead means the caller decides, once, whether that doubt matters.
    confirmed: bool = True
    raw: Mapping[str, Any] = field(default_factory=dict)

    @property
    def publishable(self) -> bool:
        """Whether promoting this version org-wide is a safe thing to do.

        Publishing is the one irreversible step, and publishing a version built from
        source nobody asked to ship is the worst outcome this whole sequence exists to
        prevent. An unconfirmed deploy is therefore never publishable — the caller can
        still check `ct status` and publish deliberately.
        """
        return self.deployed and self.confirmed

    def confirmed_version(self) -> ConfirmedVersion | None:
        """The version this deploy may safely publish, or None.

        THE only producer of :class:`ConfirmedVersion`. None covers every case where
        an automatic publish would be wrong — nothing deployed, the extraction was
        never confirmed so the build may have used the previous source, or the server
        named no version to promote.
        """
        if not self.publishable or not self.version_name:
            return None
        return ConfirmedVersion(name=self.version_name)

    @property
    def explanation(self) -> str:
        return REASONS.get(self.reason, self.reason)


def needs_late_landing_recheck(*, ref_moved: bool, path: str | None = None) -> bool:
    """Whether this deploy might have run against the PREVIOUS source.

    The question is only ever "did we watch our own content land before deploying".
    If we did not, the deploy read whatever the repository held at that moment, and
    what the server then reported says nothing about which source it read.

    ``path`` is accepted and deliberately unused. Keying on `noop` — the first version
    of this — looked right because the ambiguity is most obvious there, but it silently
    excluded the worse case: when the PREVIOUS head itself needed building, an
    unconfirmed deploy returns `building` or `saved` for the OLD tree. That reports
    `deployed: true`, and `deploy --publish` will then publish a version built from
    source the caller never asked to ship, while their actual upload sits undeployed.
    A recheck that skips exactly the paths capable of publishing the wrong thing is
    worse than no recheck at all.

    The cost of widening it is one extra read on a deploy whose content was genuinely
    identical, which is cheap and produces no redeploy.
    """
    return not ref_moved


def reconcile(
    *, ref_moved: bool, result: wire.DeployResult, extraction_landed: bool = True
) -> DeployOutcome:
    """Turn what the server said, plus what we observed, into one answer.

    ``ref_moved`` is advisory: it is allowed to be False for a perfectly good deploy,
    because an identical re-upload produces no new commit (the server skips a commit
    whose tree matches HEAD).

    ``extraction_landed`` is what makes the no-op branch trustworthy. "The source is
    identical to what is deployed" and "we never saw the server finish unpacking" both
    produce a no-op with a still ref, and only the first is good news. Reporting the
    second as `unchanged` claims the deploy was a success when the uploaded source may
    never have been built at all — so an unconfirmed extraction gets its own reason and
    tells the caller to go and look.

    The late-landing race is not an outcome here. `flow.build` detects it with
    :func:`needs_late_landing_recheck` and DEPLOYS AGAIN, so by the time this runs the
    ref is confirmed moved and the retry's result lands on the ordinary paths. Modelling
    the race as a reportable outcome would add a state the shell can never produce.
    """
    path = result.path
    common = {
        "path": path,
        "version_name": result.version_name,
        "build_id": result.build_id,
        "raw": result.raw,
    }

    if path == "building":
        return DeployOutcome(**common, deployed=True, reason="built", confirmed=extraction_landed)
    if path == "saved":
        return DeployOutcome(**common, deployed=True, reason="saved", confirmed=extraction_landed)
    if path == "noop":
        if ref_moved:
            # Our upload landed, yet the server found an existing version at that exact
            # source. Someone deployed the same content first; the state is correct.
            return DeployOutcome(**common, deployed=False, reason="already-deployed")
        if not extraction_landed:
            return DeployOutcome(**common, deployed=False, reason="unconfirmed")
        return DeployOutcome(**common, deployed=False, reason="unchanged")

    # An unrecognized path. Report it rather than guessing — a server that invents a
    # fourth outcome should surface, not be silently mapped onto one of the three.
    return DeployOutcome(**common, deployed=False, reason=f"unknown-path:{path}")


# -------------------------------------------------------------------- versions ----


def select_publishable(versions: tuple[wire.Version, ...]) -> wire.Version | None:
    """The newest version that actually built, or None.

    The list arrives newest-first. A failed build leaves its version *Stopped*, not
    FAILED, so selecting on "not failed" would happily publish a build that never
    produced an image.
    """
    for version in versions:
        if version.is_complete:
            return version
    return None


def find_version(versions: tuple[wire.Version, ...], name: str) -> wire.Version | None:
    for version in versions:
        if version.name == name:
            return version
    return None


def cancellable_build_id(versions: tuple[wire.Version, ...]) -> str | None:
    """The build id of the newest version still in flight, or None.

    Cancelling something already terminal should be an error rather than a silent
    no-op, so this deliberately answers None instead of falling back to the latest.
    """
    for version in versions:
        if version.is_in_flight and version.build_id:
            return version.build_id
    return None
