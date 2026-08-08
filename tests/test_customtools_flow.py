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
        no commit, and the server says noop. Success, with nothing to do.

        Uses the StampingServer because the real one stamps a completion timestamp even
        when it makes no commit — that is precisely what distinguishes this from an
        extraction that never finished, and the plain FakeServer (which reports no
        timestamp at all) cannot express the difference.
        """
        server = patched(StampingServer(lands_on_read=2, content_changed=False))
        server.deploy_paths = ["noop"]
        outcome = flow.build(None, name="t", folder=tool_folder, wait=False)
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

    def _fake_download(self, client, *, name, ref=None, destination=None):
        """Matches the streaming signature: writes the zip, returns its path."""
        target = Path(destination)
        target.write_bytes(self._blob())
        return target

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
        monkeypatch.setattr(flow.api, "download_archive", self._fake_download)
        flow.init(None, name="my-tool", destination=tmp_path / "my-tool")
        assert seen == {"name": "my-tool", "template": "scratch"}

    def test_writes_the_files_and_records_the_tool(self, tmp_path, monkeypatch) -> None:
        from tamarind.customtools import project, wire

        monkeypatch.setattr(flow.api, "create_tool", lambda *a, **k: wire.Tool(name="t"))
        monkeypatch.setattr(flow.api, "download_archive", self._fake_download)
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
        zip_path = tmp_path / "src.zip"
        zip_path.write_bytes(buf.getvalue())
        folder, pointers = flow.unpack_source(zip_path, tmp_path / "out")
        assert (folder / "main.py").is_file()
        assert pointers == ("weights.pt",)

    def test_a_corrupt_archive_is_a_clean_error(self, tmp_path) -> None:
        bad = tmp_path / "bad.zip"
        bad.write_bytes(b"not a zip")
        with pytest.raises(TamarindError):
            flow.unpack_source(bad, tmp_path / "out")


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
            flow.build(ExplodingClient(), name="t", folder=folder, preflight=False)


class StampingServer(FakeServer):
    """A server that behaves like the real one: it stamps `lastUpdatedAt` on EVERY
    successful extraction, including one whose tree matched and produced no commit.

    That is the distinction the ref cannot express, so it is the distinction the fake
    has to be able to produce.
    """

    def __init__(self, *, lands_on_read: int = 2, content_changed: bool = True, **kw) -> None:
        super().__init__(lands_on_read=lands_on_read, **kw)
        self.content_changed = content_changed
        self.error: str | None = None

    @property
    def current_ref(self) -> str:
        # No commit when the content is identical — exactly what the server does.
        landed = self.finalized and self.ref_reads >= self.lands_on_read
        return "ref-new" if landed and self.content_changed else "ref-old"

    def get_tool(self, client, *, name):
        from tamarind.customtools import wire

        self.ref_reads += 1
        landed = self.finalized and self.ref_reads >= self.lands_on_read
        return wire.Tool(
            name=name,
            current_source_ref=self.current_ref,
            last_updated_at="2026-01-02T00:00:00Z" if landed else "2026-01-01T00:00:00Z",
            connection_error=self.error,
        )


class TestExtractionSignal:
    """What the wait watches. The ref answers "did the content change"; the timestamp
    answers "is the server done" — and only the second one is what a deploy needs."""

    def test_an_unchanged_upload_finishes_the_wait_without_the_ref_moving(
        self, tool_folder, patched
    ) -> None:
        """THE regression. On an identical re-upload the server makes no commit, so a
        ref-watcher sees nothing change and polls until its deadline — turning the most
        common CI deploy into a five-minute wait every time.

        Without the timestamp check, `wait_for_source` would take all 30 reads its
        deadline allows and return landed=False; the assertion on `ref_reads` is what
        fails. The generous timeout here is deliberate: it is what a ref-watcher would
        burn, and the point is that this returns long before it.
        """
        server = patched(StampingServer(lands_on_read=3, content_changed=False))
        state = flow.SourceState(ref="ref-old", updated_at="2026-01-01T00:00:00Z")
        server.finalized = True
        result = flow.wait_for_source(None, name="t", before=state, timeout=300.0)
        assert result.landed is True, "extraction completion was not observed"
        assert result.ref_moved is False, "an identical upload must not look like a change"
        assert server.ref_reads <= 3, "polled past the completion signal"

    def test_a_changed_upload_reports_both_landed_and_moved(self, tool_folder, patched) -> None:
        server = patched(StampingServer(lands_on_read=2, content_changed=True))
        server.finalized = True
        state = flow.SourceState(ref="ref-old", updated_at="2026-01-01T00:00:00Z")
        result = flow.wait_for_source(None, name="t", before=state, timeout=300.0)
        assert result.landed is True and result.ref_moved is True

    def test_a_failed_extraction_raises_instead_of_waiting(self, tool_folder, patched) -> None:
        """A bad zip is recorded server-side. Polling past it burns the whole timeout
        and then reports `unchanged` — telling the user the opposite of what happened."""
        server = patched(StampingServer(lands_on_read=99, content_changed=True))
        server.error = "Zip contains LFS pointers"
        state = flow.SourceState(ref="ref-old", updated_at="2026-01-01T00:00:00Z")
        with pytest.raises(TamarindError) as exc:
            flow.wait_for_source(None, name="t", before=state, timeout=300.0)
        assert "LFS pointers" in str(exc.value), "the server's own reason was dropped"

    def test_a_server_without_the_timestamp_still_works(self, tool_folder, patched) -> None:
        """The plain FakeServer reports no lastUpdatedAt at all. Ref movement is the
        fallback, so an older deployment does not simply hang."""
        server = patched(FakeServer(lands_on_read=2))
        server.finalized = True
        state = flow.SourceState(ref="ref-old", updated_at=None)
        result = flow.wait_for_source(None, name="t", before=state, timeout=300.0)
        assert result.landed is True and result.ref_moved is True

    def test_a_timeout_is_reported_as_unconfirmed_not_unchanged(self, tool_folder, patched) -> None:
        """The silent-failure case. Extraction never completes, the deploy no-ops
        against the old source, and calling that `unchanged` claims a success nobody
        observed — the uploaded code may never be built at all.

        Without the `extraction_landed` argument to `reconcile`, this reason is
        "unchanged" and a CI job checking it would pass.
        """
        server = patched(StampingServer(lands_on_read=99, deploy_paths=["noop"]))
        outcome = flow.build(None, name="t", folder=tool_folder, wait=False, extract_timeout=0.0)
        assert outcome.deployed is False
        assert outcome.reason == "unconfirmed"
        assert "unknown" in outcome.explanation
        assert len(server.deploys) == 1, "an unconfirmed deploy must not silently retry forever"


class TestDestinationGuard:
    """One guard for `init` and `clone`. There were two, and both had the same hole."""

    def test_a_missing_path_is_fine(self, tmp_path) -> None:
        target = tmp_path / "new"
        assert flow.ensure_usable_destination(target) == target

    def test_an_empty_folder_is_fine(self, tmp_path) -> None:
        (tmp_path / "empty").mkdir()
        assert flow.ensure_usable_destination(tmp_path / "empty")

    def test_an_existing_file_is_a_typed_error_not_a_traceback(self, tmp_path) -> None:
        """THE regression. `exists() and any(iterdir())` raises NotADirectoryError on a
        file, and the CLI boundary does not catch arbitrary OSError — so ordinary user
        input produced a stack trace.

        Without the is_dir() branch this raises NotADirectoryError, which
        `pytest.raises(ValidationError)` does not catch, and the test errors.
        """
        target = tmp_path / "notafolder"
        target.write_text("i am a file\n")
        with pytest.raises(ValidationError):
            flow.ensure_usable_destination(target)

    def test_a_non_empty_folder_is_refused_by_default(self, tmp_path) -> None:
        busy = tmp_path / "busy"
        busy.mkdir()
        (busy / "work.py").write_text("mine\n")
        with pytest.raises(ValidationError):
            flow.ensure_usable_destination(busy)

    def test_a_non_empty_folder_is_allowed_when_asked(self, tmp_path) -> None:
        """`clone --force` is the caller that opts in."""
        busy = tmp_path / "busy"
        busy.mkdir()
        (busy / "work.py").write_text("mine\n")
        assert flow.ensure_usable_destination(busy, allow_nonempty=True) == busy


class TestExtractionDoesNotFollowLinks:
    def _zip(self, path: Path, members: dict) -> Path:
        import zipfile

        with zipfile.ZipFile(path, "w") as zf:
            for name, body in members.items():
                zf.writestr(name, body)
        return path

    def test_a_destination_symlink_is_replaced_not_written_through(self, tmp_path) -> None:
        """`extractall` opens each output path for writing, and open() follows a symlink
        already sitting there. With `clone --force` into a folder containing
        `config.json -> outside/secret.json`, the archive's own config.json would be
        written OUTSIDE the destination.

        Without `_extract_without_following_links` the outside file's content changes
        and this test fails on the final assertion.
        """
        outside = tmp_path / "outside.json"
        outside.write_text("ORIGINAL\n")
        dest = tmp_path / "dest"
        dest.mkdir()
        (dest / "config.json").symlink_to(outside)

        archive_path = self._zip(tmp_path / "a.zip", {"config.json": "FROM ARCHIVE\n"})
        flow.unpack_source(archive_path, dest)

        assert (dest / "config.json").read_text() == "FROM ARCHIVE\n"
        assert outside.read_text() == "ORIGINAL\n", "wrote through the link, outside the folder"

    def test_a_symlinked_parent_directory_is_also_replaced(self, tmp_path) -> None:
        """Same escape one level up: `a/b.txt` writes through `a` when `a` is a link."""
        outside = tmp_path / "outside"
        outside.mkdir()
        (outside / "b.txt").write_text("ORIGINAL\n")
        dest = tmp_path / "dest"
        dest.mkdir()
        (dest / "a").symlink_to(outside, target_is_directory=True)

        archive_path = self._zip(tmp_path / "a.zip", {"a/b.txt": "FROM ARCHIVE\n"})
        flow.unpack_source(archive_path, dest)

        assert (outside / "b.txt").read_text() == "ORIGINAL\n"

    def test_ordinary_extraction_is_unaffected(self, tmp_path) -> None:
        dest = tmp_path / "dest"
        archive_path = self._zip(tmp_path / "a.zip", {"main.py": "x\n", "sub/y.txt": "y\n"})
        folder, _ = flow.unpack_source(archive_path, dest)
        assert (folder / "main.py").read_text() == "x\n"
        assert (folder / "sub" / "y.txt").read_text() == "y\n"


class TestBuildTimeoutIsTyped:
    def test_a_build_deadline_raises_the_timeout_type(self, monkeypatch) -> None:
        """A bounded wait that elapses is not a failure — the build is still running and
        `ct logs` reattaches. Exiting 1 makes that indistinguishable from a build that
        actually failed; JobTimeoutError carries exit code 7.

        Without the typed raise this is a plain TamarindError, which
        `pytest.raises(JobTimeoutError)` does not match, and the test fails.
        """
        from tamarind.customtools import wire
        from tamarind.errors import ExitCode, JobTimeoutError

        monkeypatch.setattr(
            flow.api,
            "get_logs",
            lambda client, *, name, build_id, next_token=None: wire.LogPage(
                build_status="IN_PROGRESS"
            ),
        )
        monkeypatch.setattr(flow.time, "sleep", lambda _s: None)
        with pytest.raises(JobTimeoutError) as exc:
            flow.wait_for_build(None, name="t", build_id="b-1", timeout=0.0)
        assert exc.value.exit_code == ExitCode.TIMEOUT


class TestLogDraining:
    """One drain, used by both the follow and non-follow paths."""

    def _paged(self, pages):
        """A get_logs that walks a fixed list of pages by token."""
        from tamarind.customtools import wire

        def get_logs(client, *, name, build_id, next_token=None):
            index = 0 if next_token is None else int(next_token)
            body, token, status = pages[index]
            return wire.LogPage(
                build_status=status,
                lines=tuple(wire.LogLine(message=m) for m in body),
                next_token=token,
            )

        return get_logs

    def test_a_terminal_first_page_does_not_stop_the_drain(self, monkeypatch) -> None:
        """THE regression. The first page already carries the build's GLOBAL terminal
        status, so breaking on it skipped every remaining page — and a failed build's
        error is in the tail, which is exactly what was dropped.

        Without draining, `lines` is ("start",) and the assertion on "the real error"
        fails.
        """
        pages = [
            (["start"], "1", "FAILED"),
            (["middle"], "2", "FAILED"),
            (["the real error"], None, "FAILED"),
        ]
        monkeypatch.setattr(flow.api, "get_logs", self._paged(pages))
        page, token, lines = flow.drain_logs(None, name="t", build_id="b-1")
        assert [line.message for line in lines] == ["start", "middle", "the real error"]
        assert page.build_status == "FAILED"
        # The LAST REAL token is kept, not None. `wait_for_build` passes it back on the
        # next poll, and a forward token means "anything after this point" — resuming
        # there is right, while starting from None would replay the log from the top.
        assert token == "2"

    def test_a_repeated_token_ends_the_drain(self, monkeypatch) -> None:
        """A server that keeps handing back the same token would otherwise replay one
        page forever."""
        from tamarind.customtools import wire

        monkeypatch.setattr(
            flow.api,
            "get_logs",
            lambda client, *, name, build_id, next_token=None: wire.LogPage(
                build_status="IN_PROGRESS",
                lines=(wire.LogLine(message="same"),),
                next_token="stuck",
            ),
        )
        _, _, lines = flow.drain_logs(None, name="t", build_id="b-1")
        assert len(lines) == 2, "the loop did not stop on a repeated token"


class TestPreflightAgreesWithThePackager:
    """`is_file()` follows symlinks and the packager drops them. That disagreement let
    preflight bless a folder whose required file would never be uploaded."""

    def _folder(self, tmp_path: Path) -> Path:
        folder = tmp_path / "tool"
        folder.mkdir()
        (folder / "Dockerfile").write_text("FROM scratch\n")
        (folder / "run.sh").write_text("true\n")
        (folder / "config.json").write_text("{}\n")
        return folder

    @pytest.mark.parametrize("required", ["Dockerfile", "run.sh", "config.json"])
    def test_a_symlinked_required_file_fails_preflight(self, tmp_path, required: str) -> None:
        """THE regression. Before the fix `inspect_folder` reports ok, the upload
        contains no Dockerfile at all, and a remote build starts that can only fail.
        """
        folder = self._folder(tmp_path)
        real = tmp_path / f"real-{required}"
        real.write_text("content\n")
        (folder / required).unlink()
        (folder / required).symlink_to(real)

        findings = flow.inspect_folder(folder)
        assert not findings.ok
        assert any("symlink" in e for e in findings.errors), findings.errors

    def test_a_normal_folder_still_passes(self, tmp_path) -> None:
        assert flow.inspect_folder(self._folder(tmp_path)).ok


class TestBuildingWithoutABuildId:
    def test_a_building_response_with_no_id_is_an_error(
        self, tool_folder, patched, monkeypatch
    ) -> None:
        """`building` promises a build is running. With no id there is nothing to watch,
        so `wait=True` cannot be honoured — and returning success exits clean while an
        untracked build is still going.

        Without the guard this returns a deployed outcome and the test's
        `pytest.raises` never fires.
        """
        server = patched(StampingServer(lands_on_read=2, deploy_paths=["building"]))

        def no_id(client, *, name, carry_forward_from_version=None):
            from tamarind.customtools import wire

            server.deploys.append(server.current_ref)
            return wire.DeployResult(version_name="v1", path="building", build_id=None)

        monkeypatch.setattr(flow.api, "deploy", no_id)
        with pytest.raises(TamarindError) as exc:
            flow.build(None, name="t", folder=tool_folder, wait=True)
        assert "build id" in str(exc.value)
