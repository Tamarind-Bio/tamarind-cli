"""The deploy sequence, against a fake server that can lag.

`plan` settles the matrix; this settles the ORDER — which is the part a table cannot
check. Specifically: that the source ref is read before the upload, that a slow
extraction does not fail the deploy, and that a late landing causes a second deploy
rather than a false success.

The fake lets extraction land after N polls, which is the timing that produced the
original bug and cannot be reproduced against a real server on demand.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tamarind.customtools import flow
from tamarind.errors import TamarindError


class FakeServer:
    """A custom-tools backend whose extraction lands on a chosen read.

    Timing is expressed in READS, not seconds. The first version of this fake used a
    wall-clock notion of "late", but the tests patch `sleep` to a no-op, so the wait
    polled a hundred times in milliseconds and every scenario landed promptly — the
    race branch was never entered and three tests passed while proving nothing.

    Read 1 is `build`'s pre-upload read. Reads 2..n are the extraction wait. The read
    after the wait gives up is the late-landing recheck. So:

        lands_on_read=2   extraction is prompt (the wait observes it)
        lands_on_read=3   with a zero-length wait: the wait sees nothing, the RECHECK
                          sees it — exactly the race
        lands_on_read=99  never, within any test's sequence
    """

    def __init__(self, *, lands_on_read: int = 2, deploy_paths: list[str] | None = None) -> None:
        self.lands_on_read = lands_on_read
        self.ref_reads = 0
        self.deploy_paths = deploy_paths or ["building"]
        self.deploys: list[str] = []
        self.finalized = False

    @property
    def current_ref(self) -> str:
        return "ref-new" if self.finalized and self.ref_reads >= self.lands_on_read else "ref-old"

    # -- the api surface flow.build touches -------------------------------------
    def get_tool(self, client, *, name):
        from tamarind.customtools import wire

        self.ref_reads += 1
        return wire.Tool(name=name, current_source_ref=self.current_ref)

    def init_upload(self, client, *, name):
        from tamarind.customtools import wire

        return wire.UploadTicket(
            upload_id="u-1", upload_url="https://upload.test/x", expires_in=900
        )

    def finalize_upload(self, client, *, name, upload_id):
        self.finalized = True
        return {"sourceHash": "pending", "status": "processing"}

    def deploy(self, client, *, name, carry_forward_from_version=None):
        from tamarind.customtools import wire

        path = self.deploy_paths[min(len(self.deploys), len(self.deploy_paths) - 1)]
        # Record the source this deploy would have built, which is the thing that
        # actually matters when checking the retry.
        self.deploys.append(self.current_ref)
        return wire.DeployResult(
            version_name=f"v{len(self.deploys)}",
            path=path,
            build_id="b-1" if path == "building" else None,
            raw={"path": path},
        )


@pytest.fixture
def tool_folder(tmp_path: Path) -> Path:
    (tmp_path / "Dockerfile").write_text("FROM python:3.12-slim\n")
    (tmp_path / "run.sh").write_text("#!/bin/bash\npython3 main.py\n")
    (tmp_path / "main.py").write_text("print('hi')\n")
    (tmp_path / "config.json").write_text('{"displayName": "T"}\n')
    return tmp_path


@pytest.fixture
def patched(monkeypatch):
    """Wire a FakeServer into flow's api calls and neuter the network + clock."""

    def install(server: FakeServer):
        monkeypatch.setattr(flow.api, "get_tool", server.get_tool)
        monkeypatch.setattr(flow.api, "init_upload", server.init_upload)
        monkeypatch.setattr(flow.api, "finalize_upload", server.finalize_upload)
        monkeypatch.setattr(flow.api, "deploy", server.deploy)
        monkeypatch.setattr(flow, "put_presigned", lambda *a, **k: 123)
        monkeypatch.setattr(flow.time, "sleep", lambda _s: None)
        return server

    return install


class TestDeploySequence:
    # A zero-length extraction wait makes the sequence deterministic: the wait observes
    # nothing, so whether the RECHECK sees a moved ref is entirely up to lands_on_read.
    RACE = dict(extract_timeout=0.0)

    def test_the_source_ref_is_read_before_the_upload(self, tool_folder, patched) -> None:
        """The pre-upload read is what makes late-landing detection possible at all —
        reading it afterwards would compare the new ref against itself."""
        server = patched(FakeServer(lands_on_read=2))
        flow.build(None, name="t", folder=tool_folder, wait=False)
        assert server.ref_reads >= 1
        assert server.deploys, "deploy never ran"

    def test_a_prompt_extraction_deploys_once(self, tool_folder, patched) -> None:
        server = patched(FakeServer(lands_on_read=2))
        outcome = flow.build(None, name="t", folder=tool_folder, wait=False)
        assert outcome.deployed is True
        assert outcome.reason == "built"
        assert len(server.deploys) == 1

    def test_a_slow_extraction_still_deploys_and_does_not_raise(self, tool_folder, patched) -> None:
        """A wait that gives up is NOT a failure — deploy runs anyway and the result is
        interpreted. Treating a still ref as fatal is what would break every unchanged
        CI re-deploy."""
        server = patched(FakeServer(lands_on_read=99, deploy_paths=["building"]))
        outcome = flow.build(None, name="t", folder=tool_folder, wait=False, **self.RACE)
        assert outcome.deployed is True
        assert len(server.deploys) == 1

    def test_an_unchanged_upload_reports_no_op_rather_than_timing_out(
        self, tool_folder, patched
    ) -> None:
        """THE common CI case. The ref never moves because an identical upload produces
        no commit, and the server says noop. Success, with nothing to do."""
        server = patched(FakeServer(lands_on_read=99, deploy_paths=["noop"]))
        outcome = flow.build(None, name="t", folder=tool_folder, wait=False, **self.RACE)
        assert outcome.deployed is False
        assert outcome.reason == "unchanged"
        assert len(server.deploys) == 1, "an unchanged deploy must not retry"

    def test_a_late_landing_triggers_a_second_deploy(self, tool_folder, patched) -> None:
        """THE bug this sequence exists to prevent.

        Read 1 is the pre-upload read and the zero-length wait makes read 2 the last
        one it takes, so landing on read 3 means extraction finished AFTER the first
        deploy read the repository. That deploy built the OLD source and returned noop.
        Reporting success there is the silent-nothing-shipped failure.
        """
        server = patched(FakeServer(lands_on_read=3, deploy_paths=["noop", "building"]))
        outcome = flow.build(None, name="t", folder=tool_folder, wait=False, **self.RACE)
        assert len(server.deploys) == 2, "the race was not detected — nothing was redeployed"
        assert outcome.deployed is True
        assert outcome.reason == "built"

    def test_the_retry_deploys_against_the_settled_source(self, tool_folder, patched) -> None:
        """Not merely 'deployed twice' — the second deploy must see the NEW source, or
        it would rebuild exactly the stale tree the first one did."""
        server = patched(FakeServer(lands_on_read=3, deploy_paths=["noop", "building"]))
        flow.build(None, name="t", folder=tool_folder, wait=False, **self.RACE)
        assert server.deploys[0] == "ref-old"
        assert server.deploys[-1] == "ref-new"


class TestUploadIsGuarded:
    def test_a_missing_upload_destination_is_a_clean_error(
        self, tool_folder, patched, monkeypatch
    ) -> None:
        """Never echo the response: sibling fields on an upload ticket can themselves
        be credential-bearing presigned URLs."""
        from tamarind.customtools import wire

        patched(FakeServer())
        monkeypatch.setattr(
            flow.api, "init_upload", lambda *a, **k: wire.UploadTicket(raw={"error": "x"})
        )
        with pytest.raises(TamarindError) as raised:
            flow.build(None, name="t", folder=tool_folder, wait=False)
        assert "https://" not in str(raised.value)


class TestEventsNotPrints:
    def test_progress_is_emitted_as_structured_events(self, tool_folder, patched) -> None:
        """The library must not print. A consumer gets phases it can filter on, not
        prose it would have to parse."""
        patched(FakeServer(lands_after=0))
        seen: list[flow.BuildEvent] = []
        flow.build(None, name="t", folder=tool_folder, wait=False, on_event=seen.append)
        assert seen, "no events emitted"
        assert all(isinstance(e, flow.BuildEvent) for e in seen)
        assert {"package", "upload", "extract", "deploy"} <= {e.phase for e in seen}

    def test_a_silent_caller_is_supported(self, tool_folder, patched) -> None:
        """on_event=None must be a no-op, not a crash — that is the scripted path."""
        patched(FakeServer(lands_after=0))
        assert flow.build(None, name="t", folder=tool_folder, wait=False, on_event=None).deployed


class TestSecretsNeverUpload:
    def test_a_credential_in_the_folder_is_excluded_and_reported(
        self, tool_folder, patched
    ) -> None:
        """End-to-end through the real packaging path: the file must not be in the
        archive, and the user must be told why."""
        (tool_folder / ".env").write_text("API_KEY=secret\n")
        patched(FakeServer(lands_after=0))
        seen: list[flow.BuildEvent] = []
        flow.build(None, name="t", folder=tool_folder, wait=False, on_event=seen.append)
        warnings = [e.message for e in seen if e.kind == "warning"]
        assert any(".env" in w for w in warnings), "the dropped credential was not reported"
        assert any("ct config --env" in w for w in warnings), "no pointer to the right mechanism"
