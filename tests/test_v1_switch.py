"""The v1 switch: the server's answer on GET /me, the v1 base, and the caches."""

from __future__ import annotations

import json
import os
import stat

import httpx
import pytest
import respx

from tamarind._v1 import switch
from tamarind.errors import AuthError
from tamarind.http import HTTPClient

V1 = "https://api.tamarind.bio"


@pytest.fixture
def real_probe(monkeypatch):
    """Undo conftest's stub: these tests send the probe itself (to respx)."""
    monkeypatch.setattr(switch, "probe", _PROBE)


_PROBE = switch.probe


@pytest.mark.parametrize(
    "base, v1",
    [
        ("https://app.tamarind.bio/api", V1),
        ("https://app.tamarind.bio/api/", V1),
        ("https://mcp.tamarind.bio", V1),
        ("https://staging.tamarind.bio/api/", "https://api-staging.tamarind.bio"),
        ("https://mcp-staging.tamarind.bio", "https://api-staging.tamarind.bio"),
        ("http://localhost:3000/api", None),
        ("https://api.test/", None),
        ("not a url", None),
        (None, None),
    ],
)
def test_the_v1_base_is_the_classic_bases_environment(monkeypatch, base, v1):
    monkeypatch.delenv("TAMARIND_V1_API_BASE", raising=False)
    assert switch.v1_base_for(base) == v1


def test_the_override_points_any_base_elsewhere(monkeypatch):
    monkeypatch.setenv("TAMARIND_V1_API_BASE", "https://v1.test/")
    assert switch.v1_base_for("http://localhost:3000/api") == "https://v1.test"


@pytest.mark.parametrize(
    "answer, expected",
    [
        (httpx.Response(200, json={"user": {}, "clients": {"useV1": True}}), True),
        (httpx.Response(200, json={"user": {}, "clients": {"useV1": False}}), False),
        (httpx.Response(200, json={"user": {}, "clients": {"useV1": "true"}}), False),
        (httpx.Response(200, json={"user": {}, "clients": None}), False),
        (httpx.Response(200, json={"user": {}}), False),  # a backend not yet deployed
        (httpx.Response(200, json=["clients"]), False),
        (httpx.Response(200, text="<html>"), False),
        (httpx.Response(401, json={"code": "invalid_api_key"}), False),
        (httpx.Response(404, json={"code": "not_found"}), False),  # outside api-v1
        (httpx.Response(302, headers={"location": "https://elsewhere.test/me"}), False),
        (httpx.Response(503), False),
        (httpx.ConnectError("no DNS"), False),
        (httpx.ReadTimeout("slow"), False),
    ],
)
@respx.mock
def test_only_an_explicit_true_means_v1(real_probe, answer, expected):
    route = respx.get(f"{V1}/me")
    route.side_effect = answer if isinstance(answer, Exception) else None
    if not isinstance(answer, Exception):
        route.mock(return_value=answer)
    assert switch.probe(V1, "key") is expected
    request = route.calls[0].request
    assert request.headers["x-api-key"] == "key"
    assert route.call_count == 1  # no retries


def test_asked_once_per_key_and_base_then_cached(monkeypatch):
    asked: list[tuple[str, str]] = []
    monkeypatch.setattr(switch, "probe", lambda base, key, **k: (asked.append((base, key)), key == "on")[1])
    assert switch.Switch("on", V1).on() and switch.Switch("on", V1).on()
    assert not switch.Switch("off", V1).on()
    assert switch.Switch("on", "https://api-staging.tamarind.bio").on()
    assert asked == [(V1, "on"), (V1, "off"), ("https://api-staging.tamarind.bio", "on")]


def test_no_key_no_base_or_the_escape_hatch_never_ask(monkeypatch):
    monkeypatch.setattr(switch, "probe", lambda *a, **k: pytest.fail("asked"))
    assert not switch.Switch(None, V1).on()
    assert not switch.Switch("k", None).on()
    monkeypatch.setenv("TAMARIND_API", "classic")
    assert not switch.Switch("k", V1).on()


def test_a_client_keeps_its_answer_and_new_clients_see_a_change_after_the_cache(monkeypatch):
    clock = [1000.0]
    monkeypatch.setattr(switch.time, "monotonic", lambda: clock[0])
    answers = iter([True, False])
    asked: list[str] = []
    monkeypatch.setattr(switch, "probe", lambda base, key, **k: (asked.append(key), next(answers))[1])
    one = switch.Switch("k", V1)
    assert one.on()
    clock[0] += switch.CACHE_SECONDS - 1
    assert switch.Switch("k", V1).on() and asked == ["k"]  # a new client: the cache
    clock[0] += 2
    assert one.on() and asked == ["k"]  # a long wait keeps its API
    assert not switch.Switch("k", V1).on() and asked == ["k", "k"]  # a new client asks again


def test_an_unusable_cache_still_asks_once_per_client(tmp_path, monkeypatch):
    blocker = tmp_path / "file"
    blocker.write_text("")
    asked: list[str] = []
    monkeypatch.setattr(switch, "probe", lambda base, key, **k: (asked.append(key), True)[1])
    one = switch.Switch("k", V1, switch.FileFlagCache(blocker))
    assert one.on() and one.on() and one.on()
    assert asked == ["k"]


def test_the_file_cache_is_private_and_never_holds_the_key(tmp_path):
    cache = switch.FileFlagCache(tmp_path)
    key = switch.cache_key(V1, "secret-key-value")
    cache.set(key, True)
    text = cache.path.read_text()
    assert "secret-key-value" not in text and json.loads(text)[key]["useV1"] is True
    if os.name == "posix":
        assert stat.S_IMODE(cache.path.stat().st_mode) == 0o600
    assert switch.FileFlagCache(tmp_path).get(key) is True
    assert not list(tmp_path.glob(".v1-flag.json.*"))  # no temporary file left behind


def test_the_file_cache_keeps_old_answers_only_for_help(tmp_path, monkeypatch):
    cache = switch.FileFlagCache(tmp_path)
    cache.set("a", True)
    now = os.path.getmtime(cache.path)
    monkeypatch.setattr(switch.time, "time", lambda: now + switch.CACHE_SECONDS + 5)
    assert cache.get("a") is None
    assert cache.get("a", max_age=switch.KEEP_SECONDS) is True
    monkeypatch.setattr(switch.time, "time", lambda: now + switch.KEEP_SECONDS + 5)
    cache.set("b", False)  # writing drops what is past keeping
    assert set(json.loads(cache.path.read_text())) == {"b"}


@pytest.mark.parametrize("content", ["", "not json", "[1]", '{"k": "x"}', '{"k": {"useV1": "yes", "at": 1}}'])
def test_a_bad_cache_file_means_asking_again(tmp_path, content):
    (tmp_path / switch.CACHE_FILE).write_text(content)
    assert switch.FileFlagCache(tmp_path).get("k") is None


def test_an_unwritable_cache_is_ignored(tmp_path):
    blocker = tmp_path / "file"
    blocker.write_text("")
    cache = switch.FileFlagCache(blocker)  # its "directory" is a file
    cache.set("k", True)
    assert cache.get("k") is None


# -- HTTPClient --------------------------------------------------------------------


def test_a_request_v1_has_no_form_for_never_asks(monkeypatch):
    monkeypatch.setattr(switch, "probe", lambda *a, **k: pytest.fail("asked"))
    monkeypatch.setattr(HTTPClient, "_classic_json", lambda self, method, path, **k: {"path": path})
    with HTTPClient("https://mcp.tamarind.bio", "k") as client:
        assert client.get_json("catalog/tools") == {"path": "catalog/tools"}
        assert client.get_json("getPresignedUploadUrl") == {"path": "getPresignedUploadUrl"}


def test_without_a_key_classic_says_so_before_asking(monkeypatch):
    monkeypatch.setattr(switch, "probe", lambda *a, **k: pytest.fail("asked"))
    with HTTPClient("https://app.tamarind.bio/api", None) as client:
        with pytest.raises(AuthError, match="No API key configured"):
            client.get_json("jobs")
        with pytest.raises(AuthError, match="No API key configured"):
            client.v1()


def test_a_flag_cache_is_shared_through_its_file(tmp_path, monkeypatch):
    asked: list[str] = []
    monkeypatch.setattr(switch, "probe", lambda base, key, **k: (asked.append(key), True)[1])
    for _ in range(3):  # three CLI commands
        assert HTTPClient("https://app.tamarind.bio/api", "k", flag_cache=switch.FileFlagCache(tmp_path)).uses_v1()
    assert asked == ["k"]
    fresh = HTTPClient("https://app.tamarind.bio/api", "k", flag_cache=switch.FileFlagCache(tmp_path))
    assert fresh.cached_uses_v1() is True
