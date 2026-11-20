from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from tamarind.errors import TamarindError
from tamarind.file_pages import collect_file_pages


def test_collects_empty_and_nonempty_pages():
    client = Mock()
    client.request = Mock()
    client.request.side_effect = [
        {"files": ["a.pdb"], "hasMore": True, "nextCursor": "a"},
        {"files": [], "hasMore": True, "nextCursor": "b"},
        {"files": ["b.pdb"], "hasMore": False, "nextCursor": None},
    ]
    client.request.side_effect = [SimpleNamespace(content=b"payload", json=lambda page=page: page) for page in client.request.side_effect]
    assert collect_file_pages(client, folder="job") == ["a.pdb", "b.pdb"]
    assert client.request.call_args.kwargs["params"] == {"limit": 100, "folder": "job", "cursor": "b"}


def test_array_response_is_rejected():
    client = Mock()
    client.request = Mock()
    client.request.return_value = SimpleNamespace(content=b"payload", json=lambda: ["legacy.pdb"])
    with pytest.raises(TamarindError):
        collect_file_pages(client)


@pytest.mark.parametrize("pages", [
    [{"files": [], "hasMore": True, "nextCursor": "a"}] * 2,
    [{"files": ["partial"], "hasMore": True, "nextCursor": "a"}, ["not-a-page"]],
    [{"files": [], "hasMore": False, "nextCursor": "a"}],
    [{"files": []}],
])
def test_invalid_pagination_never_returns_partial_results(pages):
    client = Mock()
    client.request = Mock()
    client.request.side_effect = [SimpleNamespace(content=b"payload", json=lambda page=page: page) for page in pages]
    with pytest.raises(TamarindError):
        collect_file_pages(client)


def test_budgets_and_page_failure_are_not_success():
    client = Mock()
    client.request = Mock()
    client.request.return_value = SimpleNamespace(content=b"payload", json=lambda: {"files": ["partial"], "hasMore": True, "nextCursor": "a"})
    with pytest.raises(TamarindError, match="page budget"):
        collect_file_pages(client, max_pages=1)
    with pytest.raises(TamarindError, match="response budget"):
        collect_file_pages(client, max_bytes=1)
    client.request.side_effect = [client.request.return_value, RuntimeError("network")]
    with pytest.raises(RuntimeError):
        collect_file_pages(client)


def test_collector_is_usable_inside_running_event_loop():
    import asyncio
    client = Mock()
    client.request.return_value = SimpleNamespace(content=b"payload", json=lambda: {"files": [], "hasMore": False, "nextCursor": None})
    async def caller():
        return collect_file_pages(client)
    assert asyncio.run(caller()) == []
    assert 'timeout' not in client.request.call_args.kwargs


def test_byte_budget_uses_received_payload():
    client = Mock()
    client.request.return_value = SimpleNamespace(content=b" " * 100, json=lambda: {"files": [], "hasMore": False, "nextCursor": None})
    with pytest.raises(TamarindError, match="response budget"):
        collect_file_pages(client, max_bytes=99)
