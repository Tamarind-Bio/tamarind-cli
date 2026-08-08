"""What reaches the upload — the security-relevant half of `deploy`.

The archive becomes a Docker image layer readable by anyone with source access, and a
credential in a layer survives being deleted from the folder. So these are not
tidiness assertions: each excluded pattern is a thing that would otherwise be
published.
"""

from __future__ import annotations

import pytest

from tamarind.customtools import archive, packaging
from tamarind.customtools.packaging import Disposition


class TestSecretsNeverReachTheArchive:
    @pytest.mark.parametrize(
        "path",
        [
            ".env",
            ".env.local",
            ".env.production",
            "server.pem",
            "private.key",
            "cert.p12",
            "cert.pfx",
            "id_rsa",
            "id_rsa.pub",
            "id_ed25519",
            ".netrc",
            ".npmrc",
            ".pypirc",
            ".git-credentials",
            "credentials",
            "credentials.json",
            "service-account-prod.json",
            "app/.env",
            "nested/deep/.env",
        ],
    )
    def test_credential_files_are_refused(self, path: str) -> None:
        assert packaging.classify(path).disposition is Disposition.SECRET

    @pytest.mark.parametrize(
        "path",
        [".ssh/id_rsa", ".aws/credentials", ".gcloud/token.json", "sub/.ssh/known_hosts"],
    )
    def test_credential_directories_are_refused_wholesale(self, path: str) -> None:
        """Excluding by filename alone misses everything inside `.ssh/`, whose contents
        are not individually recognizable."""
        assert packaging.classify(path).disposition is Disposition.SECRET

    def test_a_secret_is_reported_as_a_secret_not_as_noise(self) -> None:
        """The message matters as much as the exclusion. Someone whose `.env` silently
        vanished will work around the tool; someone told why will use env vars."""
        decision = packaging.classify(".env")
        assert decision.disposition is Disposition.SECRET
        assert ".env" in decision.reason

    def test_the_advice_names_the_mechanism_that_replaces_it(self) -> None:
        advice = packaging.env_var_advice((".env",))
        assert advice is not None
        assert "ct config --env" in advice
        assert "image layer" in advice

    def test_no_advice_when_nothing_was_dropped(self) -> None:
        assert packaging.env_var_advice(()) is None


class TestNoiseIsDropped:
    @pytest.mark.parametrize(
        "path",
        [
            ".git/config",
            ".git/objects/ab/cdef",
            "__pycache__/mod.cpython-312.pyc",
            "mod.pyc",
            ".venv/lib/python3.12/site-packages/x.py",
            "node_modules/pkg/index.js",
            ".DS_Store",
            "sub/.DS_Store",
            ".pytest_cache/v/cache",
            ".mypy_cache/3.12/x.json",
            ".ruff_cache/x",
            "pkg.egg-info",
            ".tamarind",
        ],
    )
    def test_build_detritus_and_vcs_internals(self, path: str) -> None:
        assert packaging.classify(path).disposition is Disposition.NOISE


class TestRealSourceSurvives:
    @pytest.mark.parametrize(
        "path",
        [
            "Dockerfile",
            "run.sh",
            "main.py",
            "config.json",
            "requirements.txt",
            "src/model.py",
            "data/example.pdb",
            "README.md",
            # Near-misses for the exclusion patterns — a filter that eats these is
            # worse than no filter, because the build fails confusingly.
            "environment.yml",
            "keys.py",
            "credentials_helper.py",
            "my.env.example",
            "docs/git/notes.md",
            "envs/prod.yaml",
        ],
    )
    def test_ordinary_files_are_included(self, path: str) -> None:
        assert packaging.classify(path).included is True


class TestWeightsAreIncludedButFlagged:
    @pytest.mark.parametrize(
        "path", ["model.pt", "weights.pth", "ckpt.ckpt", "m.safetensors", "w.h5", "m.onnx"]
    )
    def test_weight_files_are_recognized(self, path: str) -> None:
        assert packaging.is_weight_file(path) is True

    @pytest.mark.parametrize("path", ["model.pt", "sub/weights.safetensors"])
    def test_weights_are_still_uploaded(self, path: str) -> None:
        """Recognized so the user can be warned, NOT excluded — silently dropping a
        file someone deliberately added would be its own bug."""
        assert packaging.classify(path).included is True

    @pytest.mark.parametrize("path", ["main.py", "config.json", "notes.txt"])
    def test_ordinary_files_are_not_mistaken_for_weights(self, path: str) -> None:
        assert packaging.is_weight_file(path) is False


class TestPathHandling:
    @pytest.mark.parametrize("path", ["app\\.env", "app\\sub\\.env"])
    def test_windows_separators(self, path: str) -> None:
        """CI runs on windows-latest, so a POSIX-only split would classify nothing."""
        assert packaging.classify(path).disposition is Disposition.SECRET

    @pytest.mark.parametrize("path", ["./main.py", "././src/model.py"])
    def test_leading_dot_segments_do_not_confuse_the_split(self, path: str) -> None:
        assert packaging.classify(path).included is True

    @pytest.mark.parametrize("path", ["", ".", "./"])
    def test_empty_paths_are_dropped_rather_than_crashing(self, path: str) -> None:
        assert packaging.classify(path).included is False


class TestSymlinks:
    """Links are never followed, and the reason is security rather than tidiness."""

    def test_a_symlink_to_a_secret_is_not_uploaded(self, tmp_path) -> None:
        """THE escape. Every exclusion in `packaging` works on the PATHNAME, and a
        link's name says nothing about its target: `config.txt -> id_rsa` classifies as
        an ordinary file, `is_file()` follows the link, and `ZipFile.write` then stores
        the KEY's bytes under that innocuous name.

        Without the symlink check this asserts False — `config.txt` appears in
        `included`, and the archive would carry the private key past every filter the
        module exists to enforce.
        """
        secret = tmp_path / "id_rsa"
        secret.write_text("-----BEGIN OPENSSH PRIVATE KEY-----\n")
        folder = tmp_path / "tool"
        folder.mkdir()
        (folder / "Dockerfile").write_text("FROM scratch\n")
        (folder / "config.txt").symlink_to(secret)

        spec = archive.plan_archive(folder)
        names = {p.name for p in spec.included}
        assert "config.txt" not in names, "a symlink was followed into the archive"
        assert "config.txt" in spec.links, "the skipped link was not reported"

    def test_a_symlink_to_an_ordinary_file_is_also_skipped(self, tmp_path) -> None:
        """Not just secrets. Resolving links to decide would still let a link to an
        unnamed-but-sensitive file through, so the rule is the simple one: never
        follow. Reporting it is what keeps that from being a silent omission."""
        target = tmp_path / "shared.py"
        target.write_text("x = 1\n")
        folder = tmp_path / "tool"
        folder.mkdir()
        (folder / "Dockerfile").write_text("FROM scratch\n")
        (folder / "lib.py").symlink_to(target)

        spec = archive.plan_archive(folder)
        assert "lib.py" not in {p.name for p in spec.included}
        assert spec.links == ("lib.py",)

    def test_a_symlinked_directory_is_not_descended_into(self, tmp_path) -> None:
        """The same escape one level up: linking a directory would sweep in everything
        under it, none of which the walk ever names."""
        outside = tmp_path / "outside"
        outside.mkdir()
        (outside / "creds.json").write_text("{}\n")
        folder = tmp_path / "tool"
        folder.mkdir()
        (folder / "Dockerfile").write_text("FROM scratch\n")
        (folder / "data").symlink_to(outside, target_is_directory=True)

        spec = archive.plan_archive(folder)
        assert not any("creds" in p.name for p in spec.included)

    def test_ordinary_files_are_unaffected(self, tmp_path) -> None:
        folder = tmp_path / "tool"
        folder.mkdir()
        (folder / "Dockerfile").write_text("FROM scratch\n")
        (folder / "main.py").write_text("print('hi')\n")
        spec = archive.plan_archive(folder)
        assert {p.name for p in spec.included} == {"Dockerfile", "main.py"}
        assert spec.links == ()


class TestSecretMatchingIsCaseInsensitive:
    """These patterns are a security control, so a capital letter must not defeat them.

    `fnmatch.fnmatch` normalizes case only on case-insensitive filesystems — on Linux,
    where CI runs, it does not. Without the fix every name below classifies as INCLUDE
    and lands in the image layer.
    """

    @pytest.mark.parametrize(
        "name",
        ["server.PEM", "PRIVATE.KEY", "ID_RSA", ".AWS/credentials", "Secrets.YAML", ".ENV"],
    )
    def test_uppercase_credentials_are_still_excluded(self, name: str) -> None:
        assert packaging.classify(name).disposition is Disposition.SECRET

    @pytest.mark.parametrize("name", ["Main.py", "README.md", "Environment.yml"])
    def test_ordinary_uppercase_files_are_untouched(self, name: str) -> None:
        """The insensitivity must not start swallowing legitimate files."""
        assert packaging.classify(name).disposition is Disposition.INCLUDE
