from unittest.mock import Mock

import pytest

from tamarind.errors import TamarindError
from tamarind.file_pages import collect_file_pages


def test_collects_empty_and_nonempty_pages():
    client = Mock()
    client.get_json.side_effect = [
        {"files": ["a.pdb"], "hasMore": True, "nextCursor": "a"},
        {"files": [], "hasMore": True, "nextCursor": "b"},
        {"files": ["b.pdb"], "hasMore": False, "nextCursor": None},
    ]
    assert collect_file_pages(client, folder="job") == ["a.pdb", "b.pdb"]
    assert client.get_json.call_args.kwargs["params"] == {"version": "2", "limit": 100, "folder": "job", "cursor": "b"}


def test_old_server_array_is_accepted_once():
    client = Mock()
    client.get_json.return_value = ["legacy.pdb"]
    assert collect_file_pages(client) == ["legacy.pdb"]
    assert client.get_json.call_count == 1


@pytest.mark.parametrize("pages", [
    [{"files": [], "hasMore": True, "nextCursor": "a"}] * 2,
    [{"files": ["partial"], "hasMore": True, "nextCursor": "a"}, ["not-a-page"]],
    [{"files": [], "hasMore": False, "nextCursor": "a"}],
    [{"files": []}],
])
def test_invalid_pagination_never_returns_partial_results(pages):
    client = Mock()
    client.get_json.side_effect = pages
    with pytest.raises(TamarindError):
        collect_file_pages(client)


def test_budgets_and_page_failure_are_not_success():
    client = Mock()
    client.get_json.return_value = {"files": ["partial"], "hasMore": True, "nextCursor": "a"}
    with pytest.raises(TamarindError, match="page budget"):
        collect_file_pages(client, max_pages=1)
    with pytest.raises(TamarindError, match="response budget"):
        collect_file_pages(client, max_bytes=1)
    client.get_json.side_effect = [client.get_json.return_value, RuntimeError("network")]
    with pytest.raises(RuntimeError):
        collect_file_pages(client)
