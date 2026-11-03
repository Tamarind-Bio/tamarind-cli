import asyncio
from types import SimpleNamespace
from unittest.mock import Mock, AsyncMock

import pytest

from tamarind.errors import TamarindError
from tamarind.file_pages import collect_file_pages


def test_collects_empty_and_nonempty_pages():
    client = Mock()
    client.request_async = AsyncMock()
    client.request_async.side_effect = [
        {"files": ["a.pdb"], "hasMore": True, "nextCursor": "a"},
        {"files": [], "hasMore": True, "nextCursor": "b"},
        {"files": ["b.pdb"], "hasMore": False, "nextCursor": None},
    ]
    client.request_async.side_effect = [SimpleNamespace(json=lambda page=page: page) for page in client.request_async.side_effect]
    assert collect_file_pages(client, folder="job") == ["a.pdb", "b.pdb"]
    assert client.request_async.call_args.kwargs["params"] == {"limit": 100, "folder": "job", "cursor": "b"}


def test_array_response_is_rejected():
    client = Mock()
    client.request_async = AsyncMock()
    client.request_async.return_value = SimpleNamespace(json=lambda: ["legacy.pdb"])
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
    client.request_async = AsyncMock()
    client.request_async.side_effect = [SimpleNamespace(json=lambda page=page: page) for page in pages]
    with pytest.raises(TamarindError):
        collect_file_pages(client)


def test_budgets_and_page_failure_are_not_success():
    client = Mock()
    client.request_async = AsyncMock()
    client.request_async.return_value = SimpleNamespace(json=lambda: {"files": ["partial"], "hasMore": True, "nextCursor": "a"})
    with pytest.raises(TamarindError, match="page budget"):
        collect_file_pages(client, max_pages=1)
    with pytest.raises(TamarindError, match="response budget"):
        collect_file_pages(client, max_bytes=1)
    client.request_async.side_effect = [client.request_async.return_value, RuntimeError("network")]
    with pytest.raises(RuntimeError):
        collect_file_pages(client)


def test_inflight_collection_is_cancelled_at_wall_clock_deadline():
    cancelled = []
    async def slow(*args, **kwargs):
        try:
            await asyncio.sleep(10)
        finally:
            cancelled.append(True)
    client = Mock(request_async=AsyncMock(side_effect=slow))
    with pytest.raises(TamarindError, match="deadline"):
        collect_file_pages(client, timeout=0.01)
    assert cancelled == [True]
