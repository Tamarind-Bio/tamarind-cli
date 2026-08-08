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
from tamarind.errors import TamarindError, ValidationError


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
        patched(FakeServer(lands_on_read=2))
        seen: list[flow.BuildEvent] = []
        flow.build(None, name="t", folder=tool_folder, wait=False, on_event=seen.append)
        assert seen, "no events emitted"
        assert all(isinstance(e, flow.BuildEvent) for e in seen)
        assert {"package", "upload", "extract", "deploy"} <= {e.phase for e in seen}

    def test_a_silent_caller_is_supported(self, tool_folder, patched) -> None:
        """on_event=None must be a no-op, not a crash — that is the scripted path."""
        patched(FakeServer(lands_on_read=2))
        assert flow.build(None, name="t", folder=tool_folder, wait=False, on_event=None).deployed


class TestSecretsNeverUpload:
    def test_a_credential_in_the_folder_is_excluded_and_reported(
        self, tool_folder, patched
    ) -> None:
        """End-to-end through the real packaging path: the file must not be in the
        archive, and the user must be told why."""
        (tool_folder / ".env").write_text("API_KEY=secret\n")
        patched(FakeServer(lands_on_read=2))
        seen: list[flow.BuildEvent] = []
        flow.build(None, name="t", folder=tool_folder, wait=False, on_event=seen.append)
        warnings = [e.message for e in seen if e.kind == "warning"]
        assert any(".env" in w for w in warnings), "the dropped credential was not reported"
        assert any("ct config --env" in w for w in warnings), "no pointer to the right mechanism"


class TestInit:
    """The scaffold comes from the server, not from templates carried here."""

    def _blob(self) -> bytes:
        import io
        import zipfile

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("Dockerfile", "FROM python:3.12-slim\n")
            zf.writestr("run.sh", "#!/bin/bash\npython3 main.py\n")
            zf.writestr("config.json", '{"displayName": ""}\n')
        return buf.getvalue()

    def test_asks_the_server_to_seed_the_scaffold(self, tmp_path, monkeypatch) -> None:
        """`template="scratch"` matters: the server picks the Dockerfile's base image
        from the tool's packages, so local templates would be a fourth copy of that
        logic and would drift the first time a base image moved."""
        seen: dict = {}

        def create(client, *, name, display_name=None, description=None, template=None):
            seen.update(name=name, template=template)
            from tamarind.customtools import wire

            return wire.Tool(name=name)

        monkeypatch.setattr(flow.api, "create_tool", create)
        monkeypatch.setattr(flow.api, "download_archive", lambda *a, **k: self._blob())
        flow.init(None, name="my-tool", destination=tmp_path / "my-tool")
        assert seen == {"name": "my-tool", "template": "scratch"}

    def test_writes_the_files_and_records_the_tool(self, tmp_path, monkeypatch) -> None:
        from tamarind.customtools import project, wire

        monkeypatch.setattr(flow.api, "create_tool", lambda *a, **k: wire.Tool(name="t"))
        monkeypatch.setattr(flow.api, "download_archive", lambda *a, **k: self._blob())
        folder, _ = flow.init(None, name="t", destination=tmp_path / "t")
        assert (folder / "Dockerfile").is_file()
        assert (folder / "run.sh").is_file()
        # Without this, a later bare `deploy` would guess the tool from the folder name.
        assert project.read(folder).name == "t"

    def test_refuses_a_non_empty_folder(self, tmp_path, monkeypatch) -> None:
        """Scaffolding over someone's work would destroy it silently."""
        from tamarind.customtools import wire

        target = tmp_path / "busy"
        target.mkdir()
        (target / "main.py").write_text("mine\n")
        monkeypatch.setattr(flow.api, "create_tool", lambda *a, **k: wire.Tool(name="t"))
        with pytest.raises(ValidationError):
            flow.init(None, name="t", destination=target)


class TestApplyConfig:
    """Pushing config.json in place — the input-schema iteration loop."""

    def test_sends_the_folder_config(self, tool_folder, monkeypatch) -> None:
        sent: dict = {}
        monkeypatch.setattr(
            flow.api,
            "save_config",
            lambda client, *, name, config_json, target_version=None: sent.update(
                name=name, body=config_json, version=target_version
            ),
        )
        flow.apply_config(None, name="t", folder=tool_folder)
        assert sent["name"] == "t"
        assert "displayName" in sent["body"]
        assert sent["version"] is None

    def test_amends_a_named_version(self, tool_folder, monkeypatch) -> None:
        """The capability nothing else reaches: a version's inputs are snapshotted at
        build time, so this is the only way to correct a schema on one that exists."""
        sent: dict = {}
        monkeypatch.setattr(
            flow.api,
            "save_config",
            lambda client, *, name, config_json, target_version=None: sent.update(
                version=target_version
            ),
        )
        flow.apply_config(None, name="t", folder=tool_folder, target_version="v2")
        assert sent["version"] == "v2"

    def test_invalid_json_is_refused_before_the_request(self, tool_folder, monkeypatch) -> None:
        """A round trip proves nothing the local parser cannot, and the local message
        can name the position."""
        (tool_folder / "config.json").write_text("{not json")
        called = False

        def save(*a, **k):
            nonlocal called
            called = True

        monkeypatch.setattr(flow.api, "save_config", save)
        with pytest.raises(ValidationError):
            flow.apply_config(None, name="t", folder=tool_folder)
        assert called is False, "a malformed config must not reach the server"

    def test_a_missing_config_is_a_clean_error(self, tmp_path, monkeypatch) -> None:
        with pytest.raises(ValidationError):
            flow.apply_config(None, name="t", folder=tmp_path)


class TestUnpackSource:
    def test_reports_lfs_pointers_rather_than_letting_the_build_fail(self, tmp_path) -> None:
        """Archives serve LFS files as pointers, so a cloned tool with large assets is
        not immediately redeployable — better said than discovered at build time."""
        import io
        import zipfile

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("main.py", "print('hi')\n")
            zf.writestr(
                "weights.pt",
                "version https://git-lfs.github.com/spec/v1\noid sha256:abc\nsize 1\n",
            )
        folder, pointers = flow.unpack_source(buf.getvalue(), tmp_path / "out")
        assert (folder / "main.py").is_file()
        assert pointers == ("weights.pt",)

    def test_a_corrupt_archive_is_a_clean_error(self, tmp_path) -> None:
        with pytest.raises(TamarindError):
            flow.unpack_source(b"not a zip", tmp_path / "out")


class TestManifestPreflight:
    """`deploy` refuses a config the server would reject, before uploading anything."""

    def _folder(self, tmp_path, config: str):
        (tmp_path / "Dockerfile").write_text("FROM scratch\n")
        (tmp_path / "run.sh").write_text("echo hi\n")
        (tmp_path / "config.json").write_text(config)
        return tmp_path

    def test_a_fatal_config_stops_the_deploy_before_any_request(self, tmp_path) -> None:
        """The whole point of the pre-flight: no upload, no build, no waiting to be
        told about a typo. Without it this deploys and fails minutes later."""
        folder = self._folder(tmp_path, '{"cpu": 99}')

        class ExplodingClient:
            def __getattr__(self, item):
                raise AssertionError(f"deploy touched the network ({item}) despite a fatal config")

        with pytest.raises(ValidationError) as exc:
            flow.build(ExplodingClient(), name="t", folder=folder)
        assert "cpu" in str(exc.value)

    def test_a_warning_does_not_stop_the_deploy(self, tmp_path) -> None:
        """A misplaced flag is valid to the server, so refusing would block a deploy
        that works. It has to be reported and then allowed through."""
        folder = self._folder(tmp_path, '{"usesMsa": true}')
        assert flow.inspect_manifest(folder).warnings

        class ExplodingClient:
            def __getattr__(self, item):
                raise RuntimeError("reached the network")

        # Getting as far as the network is the assertion: a warning must not raise
        # ValidationError the way a fatal finding does.
        with pytest.raises(RuntimeError):
            flow.build(ExplodingClient(), name="t", folder=folder)

    def test_invalid_json_is_fatal(self, tmp_path) -> None:
        folder = self._folder(tmp_path, "{not json")
        with pytest.raises(ValidationError):
            flow.inspect_manifest(folder)

    def test_a_missing_config_is_not_an_error_here(self, tmp_path) -> None:
        """`deploy` is also how someone FIXES a broken tool. The server decides
        whether a config is required; refusing locally would stand in the way."""
        assert flow.inspect_manifest(tmp_path).ok

    def test_the_preflight_can_be_turned_off(self, tmp_path) -> None:
        """An escape hatch for the day these rules go stale against a newer server."""
        folder = self._folder(tmp_path, '{"cpu": 99}')

        class ExplodingClient:
            def __getattr__(self, item):
                raise RuntimeError("reached the network")

        # Reaching the network means the manifest check was skipped, which is the
        # behaviour under test — the RuntimeError proves it got past the gate.
        with pytest.raises(RuntimeError):
            flow.build(ExplodingClient(), name="t", folder=folder, check_manifest=False)
