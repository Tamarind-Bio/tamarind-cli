"""Which tool a folder belongs to.

The failure this prevents is quiet and expensive: `tamarind deploy` with no arguments
targeting a *different* tool than the one you meant, because the folder happened to be
named something else.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tamarind.customtools import project
from tamarind.errors import TamarindError


class TestReadWrite:
    def test_round_trips(self, tmp_path: Path) -> None:
        project.write(tmp_path, name="my-esmfold")
        found = project.read(tmp_path)
        assert found is not None and found.name == "my-esmfold"

    def test_absent_file_is_none_not_an_error(self, tmp_path: Path) -> None:
        """A folder with no project file is the normal starting state."""
        assert project.read(tmp_path) is None

    def test_the_file_holds_no_credentials(self, tmp_path: Path) -> None:
        """It is safe to commit, so it must never accumulate anything secret."""
        project.write(tmp_path, name="t")
        data = json.loads((tmp_path / project.PROJECT_FILENAME).read_text())
        assert set(data) == {"name"}

    @pytest.mark.parametrize(
        "content", ["not json at all", "[]", "{}", '{"name": ""}', '{"name": 7}']
    )
    def test_a_malformed_file_raises_rather_than_falling_back(
        self, tmp_path: Path, content: str
    ) -> None:
        """Falling back to the folder name here would deploy to a DIFFERENT tool than
        the one recorded — the exact failure this file exists to prevent. Better to
        stop and say so."""
        (tmp_path / project.PROJECT_FILENAME).write_text(content)
        with pytest.raises(TamarindError):
            project.read(tmp_path)


class TestResolveName:
    def test_explicit_name_wins(self, tmp_path: Path) -> None:
        project.write(tmp_path, name="recorded")
        assert project.resolve_name(tmp_path, "explicit") == "explicit"

    def test_project_file_beats_the_folder_name(self, tmp_path: Path) -> None:
        """The whole point: a renamed or differently-checked-out folder still deploys
        to the tool it belongs to."""
        project.write(tmp_path, name="my-esmfold")
        assert project.resolve_name(tmp_path, None) == "my-esmfold"
        assert tmp_path.name != "my-esmfold"

    def test_folder_name_is_the_last_resort(self, tmp_path: Path) -> None:
        """Which is what makes the very first `deploy --create` work before any project
        file exists."""
        assert project.resolve_name(tmp_path, None) == tmp_path.resolve().name

    def test_the_marker_is_excluded_from_uploads(self) -> None:
        """It is ours, not the server's — shipping it into the image would be noise."""
        from tamarind.customtools import packaging

        assert packaging.classify(project.PROJECT_FILENAME).included is False
