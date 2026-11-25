"""OAuth client credentials: the token is fetched, shared, renewed and rate limited, and
neither the secret nor a token is ever shown."""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import stat
import threading
import time

import httpx
import pytest
import respx
from typer.testing import CliRunner

from tamarind import Tamarind, config, oauth
from tamarind._v1 import switch
from tamarind._v1.client import Tamarind as V1Client
from tamarind.cli.main import app
from tamarind.errors import AuthError, ExitCode, RateLimitError, TamarindError, UsageError
from tamarind.http import HTTPClient

API = "https://app.tamarind.bio/api/"
TOKEN_URL = API + "oauth/token"
V1 = "https://api.tamarind.bio"
CLIENT_ID = "svc_123"
SECRET = "cs_super-secret-value"
_PROBE = switch.probe
runner = CliRunner()


class Clock:
    def __init__(self, now: float = 1000.0):
        self.now = now

    def __call__(self) -> float:
        return self.now


def granted(token: str, expires_in: object = 3600) -> httpx.Response:
    return httpx.Response(
        200, json={"access_token": token, "token_type": "Bearer", "expires_in": expires_in}
    )


def make(clock: Clock | None = None, sleeps: list[float] | None = None) -> oauth.ClientCredentials:
    return oauth.ClientCredentials(
        CLIENT_ID,
        SECRET,
        token_url=TOKEN_URL,
        sleep=(sleeps.append if sleeps is not None else lambda _s: None),
        clock=clock or Clock(),
    )


def basic(request: httpx.Request) -> str:
    scheme, _, encoded = request.headers["authorization"].partition(" ")
    assert scheme == "Basic"
    return base64.b64decode(encoded).decode()


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setenv("TAMARIND_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setenv("TAMARIND_API_BASE", API)
    for name in ("TAMARIND_API_KEY", "TAMARIND_PROFILE", "TAMARIND_V1_API_BASE", "TAMARIND_API"):
        monkeypatch.delenv(name, raising=False)
    return tmp_path / "config"


# -- fetching and sending ------------------------------------------------------------


@respx.mock
def test_a_token_is_fetched_with_basic_auth_and_sent_as_the_key():
    token_route = respx.post(TOKEN_URL).mock(return_value=granted("tok_1"))
    jobs = respx.get(f"{API}jobs").mock(return_value=httpx.Response(200, json={"jobs": []}))
    with HTTPClient(API, None, credentials=make()) as client:
        client.request("GET", "jobs")
    asked = token_route.calls[0].request
    assert basic(asked) == f"{CLIENT_ID}:{SECRET}"
    assert asked.content == b"grant_type=client_credentials"
    assert asked.headers["content-type"] == "application/x-www-form-urlencoded"
    sent = jobs.calls[0].request
    assert sent.headers["x-api-key"] == "tok_1"
    assert "authorization" not in sent.headers


@respx.mock
def test_one_token_serves_every_request_and_client_in_the_process(env):
    token_route = respx.post(TOKEN_URL).mock(return_value=granted("tok_1"))
    respx.get(f"{API}jobs").mock(return_value=httpx.Response(200, json={"jobs": []}))
    first = config.load_config(client_id=CLIENT_ID, client_secret=SECRET).client_credentials()
    second = config.load_config(client_id=CLIENT_ID, client_secret=SECRET).client_credentials()
    assert first is second
    for _ in range(2):
        with HTTPClient(API, None, credentials=first) as client:
            client.request("GET", "jobs")
            client.request("GET", "jobs")
    with Tamarind(client_id=CLIENT_ID, client_secret=SECRET) as sdk:
        assert sdk._http.credentials is first
    assert token_route.call_count == 1


def test_threads_that_need_a_token_at_once_share_one_fetch():
    calls: list[float] = []

    def slow(request: httpx.Request) -> httpx.Response:
        calls.append(time.monotonic())
        time.sleep(0.05)
        return granted("tok_1")

    credentials = oauth.ClientCredentials(CLIENT_ID, SECRET, token_url=TOKEN_URL)
    seen: list[str] = []
    with respx.mock:
        respx.post(TOKEN_URL).mock(side_effect=slow)
        threads = [threading.Thread(target=lambda: seen.append(credentials.token())) for _ in range(8)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
    assert len(calls) == 1 and seen == ["tok_1"] * 8


@respx.mock
def test_the_token_is_renewed_a_minute_before_it_runs_out():
    clock = Clock()
    token_route = respx.post(TOKEN_URL).mock(side_effect=[granted("tok_1"), granted("tok_2")])
    credentials = make(clock)
    assert credentials.token() == "tok_1"
    clock.now += 3600 - 61
    assert credentials.token() == "tok_1" and token_route.call_count == 1
    clock.now += 2
    assert credentials.token() == "tok_2" and token_route.call_count == 2


@respx.mock
@pytest.mark.parametrize("expires_in", [None, "3600", 0, -5, True])
def test_an_answer_without_a_usable_lifetime_is_renewed_within_five_minutes(expires_in):
    clock = Clock()
    respx.post(TOKEN_URL).mock(side_effect=[granted("tok_1", expires_in), granted("tok_2")])
    credentials = make(clock)
    assert credentials.token() == "tok_1"
    clock.now += 300 - 59
    assert credentials.token() == "tok_2"


# -- a refused token ------------------------------------------------------------------


@respx.mock
def test_a_401_renews_the_token_once_and_sends_again():
    token_route = respx.post(TOKEN_URL).mock(side_effect=[granted("tok_1"), granted("tok_2")])
    jobs = respx.post(f"{API}submit-job").mock(
        side_effect=[httpx.Response(401, json={"error": "Unauthorized"}), httpx.Response(200, json={"ok": True})]
    )
    with HTTPClient(API, None, credentials=make()) as client:
        assert client.request("POST", "submit-job", json={"jobName": "j"}).json() == {"ok": True}
    assert [c.request.headers["x-api-key"] for c in jobs.calls] == ["tok_1", "tok_2"]
    assert [json.loads(c.request.content) for c in jobs.calls] == [{"jobName": "j"}] * 2
    assert token_route.call_count == 2


@respx.mock
def test_a_second_401_stands_and_401s_never_renew_more_than_once_a_minute():
    clock = Clock()
    token_route = respx.post(TOKEN_URL).mock(side_effect=[granted("tok_1"), granted("tok_2"), granted("tok_3")])
    jobs = respx.get(f"{API}jobs").mock(return_value=httpx.Response(401, json={"error": "Unauthorized"}))
    with HTTPClient(API, None, credentials=make(clock)) as client:
        with pytest.raises(AuthError):
            client.request("GET", "jobs")
        assert jobs.call_count == 2 and token_route.call_count == 2
        # Within the minute: the refusal stands, nothing more is asked for.
        clock.now += 30
        with pytest.raises(AuthError):
            client.request("GET", "jobs")
        assert jobs.call_count == 3 and token_route.call_count == 2
        clock.now += 31
        with pytest.raises(AuthError):
            client.request("GET", "jobs")
        assert jobs.call_count == 5 and token_route.call_count == 3


def test_a_token_another_request_already_replaced_is_not_fetched_again():
    clock = Clock()
    with respx.mock:
        token_route = respx.post(TOKEN_URL).mock(side_effect=[granted("tok_1"), granted("tok_2")])
        credentials = make(clock)
        assert credentials.token() == "tok_1"
        clock.now += 120
        assert credentials.renew("tok_1") == "tok_2"
        assert credentials.renew("tok_1") == "tok_2"  # a second request refused with tok_1
        assert token_route.call_count == 2


@respx.mock
def test_the_async_request_renews_once_too():
    respx.post(TOKEN_URL).mock(side_effect=[granted("tok_1"), granted("tok_2")])
    route = respx.get(f"{API}jobs").mock(
        side_effect=[httpx.Response(401, json={"error": "Unauthorized"}), httpx.Response(200, json={"jobs": []})]
    )
    with HTTPClient(API, None, credentials=make()) as client:
        response = asyncio.run(client.request_async("GET", "jobs"))
    assert response.status_code == 200
    assert [c.request.headers["x-api-key"] for c in route.calls] == ["tok_1", "tok_2"]


# -- the token endpoint's refusals ------------------------------------------------------


@respx.mock
def test_a_short_retry_after_is_slept_through():
    sleeps: list[float] = []
    respx.post(TOKEN_URL).mock(
        side_effect=[httpx.Response(429, headers={"retry-after": "7"}, json={"error": "slow_down"}), granted("tok_1")]
    )
    assert make(sleeps=sleeps).token() == "tok_1"
    assert sleeps == [7.0]


@respx.mock
def test_a_long_retry_after_is_raised_and_nothing_is_asked_before_it_ends():
    clock = Clock()
    sleeps: list[float] = []
    token_route = respx.post(TOKEN_URL).mock(
        side_effect=[httpx.Response(429, headers={"retry-after": "600"}, json={"error": "slow_down"}), granted("tok_1")]
    )
    credentials = make(clock, sleeps)
    with pytest.raises(RateLimitError, match="600 s") as raised:
        credentials.token()
    assert raised.value.exit_code == ExitCode.RATE_LIMIT
    assert raised.value.detail == {"error": "slow_down", "retryAfter": 600}
    assert sleeps == [] and token_route.call_count == 1
    clock.now += 599
    with pytest.raises(RateLimitError, match="1 s"):
        credentials.token()
    assert token_route.call_count == 1
    clock.now += 2
    assert credentials.token() == "tok_1" and token_route.call_count == 2


@respx.mock
def test_unavailable_and_server_errors_are_retried():
    sleeps: list[float] = []
    respx.post(TOKEN_URL).mock(
        side_effect=[
            httpx.Response(503, headers={"retry-after": "30"}, json={"error": "temporarily_unavailable"}),
            httpx.Response(500, json={"error": "server_error"}),
            httpx.ConnectError("refused"),
            granted("tok_1"),
        ]
    )
    assert make(sleeps=sleeps).token() == "tok_1"
    assert sleeps[0] == 30.0 and len(sleeps) == 3


@respx.mock
@pytest.mark.parametrize(
    "answer, match",
    [
        (httpx.Response(401, json={"error": "invalid_client", "error_description": "Client authentication failed."}), "refused this client ID and secret"),
        (httpx.Response(404, json={"error": "not_found"}), "aren't enabled for this account"),
        (httpx.Response(400, json={"error": "unsupported_grant_type", "error_description": "Only client_credentials is supported."}), "Only client_credentials"),
    ],
)
def test_refusals_are_auth_errors(answer, match):
    token_route = respx.post(TOKEN_URL).mock(return_value=answer)
    with pytest.raises(AuthError, match=match) as raised:
        make().token()
    assert raised.value.exit_code == ExitCode.AUTH
    assert token_route.call_count == 1  # never retried


def test_the_secret_only_goes_over_https():
    with pytest.raises(UsageError, match="HTTPS"):
        oauth.ClientCredentials(CLIENT_ID, SECRET, token_url="http://app.tamarind.bio/api/oauth/token")
    oauth.ClientCredentials(CLIENT_ID, SECRET, token_url="http://localhost:3000/api/oauth/token")


@respx.mock
def test_redirects_are_not_followed_with_the_secret():
    respx.post(TOKEN_URL).mock(return_value=httpx.Response(307, headers={"location": "https://elsewhere.test/token"}))
    elsewhere = respx.post("https://elsewhere.test/token").mock(return_value=granted("tok_1"))
    with pytest.raises(TamarindError):
        make().token()
    assert elsewhere.call_count == 0


# -- secrets never shown ----------------------------------------------------------------


@respx.mock
@pytest.mark.parametrize(
    "answer",
    [
        httpx.Response(401, json={"error": "invalid_client"}),
        httpx.Response(200, json={"accessToken": "tok_leaked_shape", "expires_in": 3600}),
        httpx.Response(200, text="tok_leaked_shape"),
        httpx.ConnectError("refused"),
        httpx.Response(500, text="tok_leaked_shape"),
    ],
)
def test_neither_the_secret_nor_a_token_reaches_an_error_or_a_log(caplog, answer):
    caplog.set_level(logging.DEBUG)
    route = respx.post(TOKEN_URL)
    if isinstance(answer, Exception):
        route.side_effect = answer
    else:
        route.mock(return_value=answer)
    credentials = make()
    with pytest.raises(TamarindError) as raised:
        credentials.token()
    pair = base64.b64encode(f"{CLIENT_ID}:{SECRET}".encode()).decode()
    shown = " ".join(
        [str(raised.value), repr(raised.value.detail), caplog.text, repr(credentials), repr(raised.value.__cause__)]
    )
    for secret in (SECRET, pair, "tok_leaked_shape"):
        assert secret not in shown
    # Never chained to an httpx error, which carries the request and its Basic header.
    assert raised.value.__cause__ is None
    assert raised.value.__context__ is None or raised.value.__suppress_context__


@respx.mock
def test_a_working_token_never_reaches_the_logs(caplog):
    caplog.set_level(logging.DEBUG)
    respx.post(TOKEN_URL).mock(return_value=granted("tok_live_123"))
    respx.get(f"{API}jobs").mock(return_value=httpx.Response(401, json={"error": "Unauthorized"}))
    credentials = make()
    with HTTPClient(API, None, credentials=credentials) as client:
        with pytest.raises(AuthError) as raised:
            client.request("GET", "jobs")
    assert "tok_live_123" not in caplog.text + str(raised.value) + repr(raised.value.detail)
    assert SECRET not in caplog.text + repr(credentials)


def test_the_config_never_shows_the_secret(env):
    shown = repr(config.load_config(client_id=CLIENT_ID, client_secret=SECRET))
    assert CLIENT_ID in shown and SECRET not in shown


# -- API keys -----------------------------------------------------------------------------


@respx.mock
def test_a_key_user_never_asks_for_a_token(env):
    token_route = respx.post(TOKEN_URL).mock(return_value=granted("tok_1"))
    jobs = respx.get(f"{API}jobs").mock(return_value=httpx.Response(200, json={"jobs": []}))
    cfg = config.load_config(api_key="sk_key")
    assert cfg.client_credentials() is None
    with HTTPClient(API, cfg.api_key, credentials=cfg.client_credentials()) as client:
        client.request("GET", "jobs")
    with Tamarind(api_key="sk_key") as sdk:
        assert sdk._http.credentials is None and sdk._http.api_key == "sk_key"
    assert jobs.calls[0].request.headers["x-api-key"] == "sk_key"
    assert token_route.call_count == 0


@respx.mock
def test_a_key_users_401_is_not_retried():
    route = respx.get(f"{API}jobs").mock(return_value=httpx.Response(401, json={"error": "Unauthorized"}))
    with HTTPClient(API, "sk_key") as client:
        with pytest.raises(AuthError):
            client.request("GET", "jobs")
    assert route.call_count == 1


def test_an_api_key_and_client_credentials_together_are_refused():
    with pytest.raises(ValueError):
        HTTPClient(API, "sk_key", credentials=make())


def test_a_key_users_flag_cache_key_is_unchanged():
    assert switch.Switch("sk_key", V1)._key() == switch.cache_key(V1, "sk_key")


# -- the v1 flag cache and the v1 API ----------------------------------------------------


def test_the_flag_cache_is_keyed_on_the_client_id_and_survives_renewals(tmp_path, monkeypatch):
    asked: list[object] = []
    monkeypatch.setattr(switch, "probe", lambda base, credential, **k: (asked.append(credential), True)[1])
    clock = Clock()
    with respx.mock:
        respx.post(TOKEN_URL).mock(side_effect=[granted("tok_1"), granted("tok_2")])
        credentials = make(clock)
        credentials.token()
        first = switch.Switch(None, V1, switch.FileFlagCache(tmp_path), credentials=credentials)
        assert first.on() and len(asked) == 1
        clock.now += 3600
        assert credentials.token() == "tok_2"
    monkeypatch.setattr(switch, "_PROCESS_CACHE", switch.MemoryFlagCache())  # a new command
    again = switch.Switch(None, V1, switch.FileFlagCache(tmp_path), credentials=credentials)
    assert again.on() and len(asked) == 1
    other_secret = oauth.ClientCredentials(CLIENT_ID, "another-secret", token_url=TOKEN_URL)
    assert switch.Switch(None, V1, credentials=other_secret)._key() == first._key()
    assert first._key() == switch.cache_key(V1, f"oauth-client\n{CLIENT_ID}")
    stored = (tmp_path / switch.CACHE_FILE).read_text()
    for secret in ("tok_1", "tok_2", SECRET, CLIENT_ID):
        assert secret not in stored


@respx.mock
def test_the_v1_question_is_asked_with_the_token_and_renews_once(monkeypatch):
    monkeypatch.setattr(switch, "probe", _PROBE)
    respx.post(TOKEN_URL).mock(side_effect=[granted("tok_1"), granted("tok_2")])
    me = respx.get(f"{V1}/me").mock(
        side_effect=[httpx.Response(401, json={"code": "invalid_api_key"}), httpx.Response(200, json={"clients": {"useV1": True}})]
    )
    assert switch.probe(V1, make()) is True
    assert [c.request.headers["x-api-key"] for c in me.calls] == ["tok_1", "tok_2"]


@respx.mock
def test_the_v1_client_sends_the_token_and_renews_once():
    token_route = respx.post(TOKEN_URL).mock(side_effect=[granted("tok_1"), granted("tok_2")])
    me = respx.get(f"{V1}/me").mock(
        side_effect=[
            httpx.Response(401, json={"type": "about:blank", "status": 401, "code": "invalid_api_key"}),
            httpx.Response(429, headers={"retry-after": "0"}, json={"type": "about:blank", "status": 429, "code": "rate_limited"}),
            httpx.Response(200, json={"user": {}}),
        ]
    )
    with V1Client(base_url=V1, credentials=make()) as client:
        client.me.get()
    assert [c.request.headers["x-api-key"] for c in me.calls] == ["tok_1", "tok_2", "tok_2"]
    assert all("authorization" not in c.request.headers for c in me.calls)
    assert token_route.call_count == 2


@respx.mock
def test_the_v1_client_ignores_an_api_key_in_the_environment_when_given_credentials(monkeypatch):
    monkeypatch.setenv("TAMARIND_API_KEY", "sk_env")
    respx.post(TOKEN_URL).mock(return_value=granted("tok_1"))
    me = respx.get(f"{V1}/me").mock(return_value=httpx.Response(200, json={"user": {}}))
    with V1Client(base_url=V1, credentials=make()) as client:
        client.me.get()
    assert me.calls[0].request.headers["x-api-key"] == "tok_1"


# -- which credential is used -------------------------------------------------------------


def test_client_credentials_in_the_environment_beat_a_profile_key(env, monkeypatch):
    config.save_profile("default", api_key="sk_profile")
    monkeypatch.setenv("TAMARIND_CLIENT_ID", CLIENT_ID)
    monkeypatch.setenv("TAMARIND_CLIENT_SECRET", SECRET)
    cfg = config.load_config()
    assert cfg.api_key is None and cfg.client_id == CLIENT_ID


def test_an_explicit_key_beats_client_credentials_in_the_environment(env, monkeypatch):
    monkeypatch.setenv("TAMARIND_CLIENT_ID", CLIENT_ID)
    monkeypatch.setenv("TAMARIND_CLIENT_SECRET", SECRET)
    cfg = config.load_config(api_key="sk_flag")
    assert cfg.api_key == "sk_flag" and cfg.client_id is None and cfg.client_credentials() is None


def test_explicit_client_credentials_beat_a_key_in_the_environment(env, monkeypatch):
    monkeypatch.setenv("TAMARIND_API_KEY", "sk_env")
    cfg = config.load_config(client_id=CLIENT_ID, client_secret=SECRET)
    assert cfg.api_key is None and cfg.client_id == CLIENT_ID


def test_at_the_same_level_the_key_wins(env, monkeypatch):
    monkeypatch.setenv("TAMARIND_API_KEY", "sk_env")
    monkeypatch.setenv("TAMARIND_CLIENT_ID", CLIENT_ID)
    monkeypatch.setenv("TAMARIND_CLIENT_SECRET", SECRET)
    assert config.load_config().api_key == "sk_env"
    config.save_profile("default", api_key="sk_profile", client_id=CLIENT_ID, client_secret=SECRET)
    for name in ("TAMARIND_API_KEY", "TAMARIND_CLIENT_ID", "TAMARIND_CLIENT_SECRET"):
        monkeypatch.delenv(name)
    assert config.load_config().api_key == "sk_profile"


def test_a_pair_split_across_levels_counts_at_its_more_specific_half(env, monkeypatch):
    config.save_profile("default", api_key="sk_profile", client_secret=SECRET)
    monkeypatch.setenv("TAMARIND_CLIENT_ID", CLIENT_ID)
    cfg = config.load_config()
    assert cfg.api_key is None and (cfg.client_id, cfg.client_secret) == (CLIENT_ID, SECRET)


@pytest.mark.parametrize(
    "variables, match",
    [({"TAMARIND_CLIENT_ID": CLIENT_ID}, "needs its client secret"), ({"TAMARIND_CLIENT_SECRET": SECRET}, "needs its client ID")],
)
def test_half_a_pair_is_an_error_even_beside_a_key(env, monkeypatch, variables, match):
    monkeypatch.setenv("TAMARIND_API_KEY", "sk_env")
    for name, value in variables.items():
        monkeypatch.setenv(name, value)
    cfg = config.load_config()
    with pytest.raises(UsageError, match=match) as raised:
        cfg.client_credentials()
    assert SECRET not in str(raised.value)
    with pytest.raises(UsageError):
        Tamarind()


# -- the CLI ------------------------------------------------------------------------------


@respx.mock
def test_cli_flags_use_client_credentials_over_a_key_in_the_environment(env, monkeypatch):
    monkeypatch.setenv("TAMARIND_API_KEY", "sk_env")
    respx.post(TOKEN_URL).mock(return_value=granted("tok_1"))
    jobs = respx.get(f"{API}jobs").mock(return_value=httpx.Response(200, json={"jobs": []}))
    res = runner.invoke(
        app, ["--json", "--client-id", CLIENT_ID, "--client-secret", SECRET, "auth", "status"]
    )
    assert res.exit_code == 0, res.output
    assert json.loads(res.stdout) == {
        "profile": "default",
        "hasKey": False,
        "hasClientCredentials": True,
        "clientId": CLIENT_ID,
        "verified": True,
    }
    assert jobs.calls[0].request.headers["x-api-key"] == "tok_1"
    assert SECRET not in res.output and "tok_1" not in res.output


@respx.mock
def test_cli_login_stores_the_pair_and_replaces_a_stored_key(env):
    config.save_profile("default", api_key="sk_profile")
    respx.post(TOKEN_URL).mock(return_value=granted("tok_1"))
    respx.get(f"{API}jobs").mock(return_value=httpx.Response(200, json={"jobs": []}))
    res = runner.invoke(app, ["--json", "auth", "login", "--client-id", CLIENT_ID, "--client-secret", SECRET])
    assert res.exit_code == 0, res.output
    assert json.loads(res.stdout) == {"ok": True, "profile": "default", "clientId": CLIENT_ID, "verified": True}
    assert SECRET not in res.output and "tok_1" not in res.output
    path = env / "config.json"
    stored = json.loads(path.read_text())["profiles"]["default"]
    assert stored == {"client_id": CLIENT_ID, "client_secret": SECRET}
    assert stat.S_IMODE(path.stat().st_mode) == 0o600

    human = runner.invoke(app, ["--no-json", "auth", "status"])
    assert human.exit_code == 0 and f"client id:    {CLIENT_ID} (verified)" in human.stdout

    res = runner.invoke(app, ["--json", "auth", "login", "--api-key", "sk_new", "--no-verify"])
    assert res.exit_code == 0, res.output
    assert json.loads(path.read_text())["profiles"]["default"] == {"api_key": "sk_new"}

    config.save_profile("default", client_id=CLIENT_ID, client_secret=SECRET, forget=("api_key",))
    res = runner.invoke(app, ["--no-json", "auth", "logout"])
    assert res.exit_code == 0 and "client credentials" in res.stdout
    assert json.loads(path.read_text())["profiles"]["default"] == {"api_key": ""}


@respx.mock
def test_cli_login_keeps_the_token_endpoints_reason_and_saves_nothing(env):
    respx.post(TOKEN_URL).mock(return_value=httpx.Response(404, json={"error": "not_found"}))
    res = runner.invoke(app, ["--json", "auth", "login", "--client-id", CLIENT_ID, "--client-secret", SECRET])
    assert res.exception is not None and res.exception.exit_code == ExitCode.AUTH
    assert "aren't enabled" in str(res.exception) and "Not saved" in str(res.exception)
    assert SECRET not in str(res.exception)
    assert not (env / "config.json").exists()


def test_cli_login_refuses_a_key_and_a_client_together(env):
    res = runner.invoke(app, ["--json", "auth", "login", "--api-key", "k", "--client-id", CLIENT_ID])
    assert isinstance(res.exception, UsageError)
    res = runner.invoke(app, ["--json", "auth", "login", "--client-secret", SECRET])
    assert isinstance(res.exception, UsageError) and SECRET not in str(res.exception)


@respx.mock
def test_cli_login_prompts_for_the_secret_without_echoing_it(env):
    respx.post(TOKEN_URL).mock(return_value=granted("tok_1"))
    respx.get(f"{API}jobs").mock(return_value=httpx.Response(200, json={"jobs": []}))
    res = runner.invoke(app, ["--no-json", "auth", "login", "--client-id", CLIENT_ID], input=SECRET + "\n")
    assert res.exit_code == 0, res.output
    assert SECRET not in res.output
    assert json.loads((env / "config.json").read_text())["profiles"]["default"]["client_secret"] == SECRET


# -- network errors keep their type, not the request ------------------------------------


def _request_of(error: BaseException | None) -> httpx.Request | None:
    try:
        return error.request if isinstance(error, httpx.HTTPError) else None
    except RuntimeError:  # httpx: "The .request property has not been set."
        return None


@respx.mock
@pytest.mark.parametrize("asynchronous", [False, True])
def test_a_network_error_is_chained_without_the_token(asynchronous):
    respx.post(TOKEN_URL).mock(return_value=granted("tok_live_123"))
    respx.get(f"{API}jobs").mock(side_effect=httpx.ConnectError("refused"))
    with HTTPClient(API, None, credentials=make()) as client:
        with pytest.raises(TamarindError) as raised:
            if asynchronous:
                asyncio.run(client.request_async("GET", "jobs"))
            else:
                client.request("GET", "jobs")
    # The type is kept (outcome_unclear and the build-timeout check read it) ...
    assert isinstance(raised.value.__cause__, httpx.ConnectError)
    # ... and the request, with the token in x-api-key, is not.
    assert _request_of(raised.value.__cause__) is None
    assert _request_of(raised.value.__context__) is None


@respx.mock
def test_a_v1_network_error_is_chained_without_the_token():
    respx.post(TOKEN_URL).mock(return_value=granted("tok_live_123"))
    respx.get(f"{V1}/me").mock(side_effect=httpx.ConnectError("refused"))
    with V1Client(base_url=V1, credentials=make(), max_retries=0) as client:
        with pytest.raises(TamarindError) as raised:
            client.me.get()
    assert isinstance(raised.value.__cause__, httpx.ConnectError)
    assert _request_of(raised.value.__cause__) is None
