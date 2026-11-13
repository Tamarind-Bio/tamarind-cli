"""Channel and agent attribution headers (tamarind.attribution)."""

import pytest

from tamarind import attribution
from tamarind.http import HTTPClient


@pytest.fixture(autouse=True)
def _sdk_channel():
    attribution.set_channel(attribution.CHANNEL_SDK)
    yield
    attribution.set_channel(attribution.CHANNEL_SDK)


@pytest.mark.parametrize(
    "env, agent",
    [
        ({}, None),
        ({"CLAUDECODE": "1", "CLAUDE_CODE_ENTRYPOINT": "cli"}, "claude-code"),
        ({"CLAUDECODE": "1", "CLAUDE_CODE_ENTRYPOINT": "claude-vscode"}, "claude-code"),
        ({"CLAUDECODE": "1", "CLAUDE_CODE_ENTRYPOINT": "sdk-py"}, "claude-agent-sdk"),
        # Claude Science runs on the Agent SDK, so its own marker must win.
        ({"OPERON_ARTIFACTS_ROOTS": "/x", "CLAUDECODE": "1", "CLAUDE_CODE_ENTRYPOINT": "sdk-ts"}, "claude-science"),
        ({"CODEX_THREAD_ID": "019a"}, "codex"),
        ({"CODEX_SANDBOX": "seatbelt"}, "codex"),
        ({"GEMINI_CLI": "1"}, "gemini-cli"),
        ({"TAMARIND_AGENT": "Cursor", "CLAUDECODE": "1"}, "cursor"),
        ({"TAMARIND_AGENT": "none", "CLAUDECODE": "1"}, None),
        ({"TAMARIND_AGENT": "not a slug!"}, None),
    ],
)
def test_detect_agent(env, agent):
    assert attribution.detect_agent(env) == agent


def test_headers_default_to_the_sdk_channel_and_omit_an_undetected_agent():
    assert attribution.client_headers({}) == {"X-Tamarind-Client-Channel": "sdk"}


def test_the_cli_entry_point_switches_the_channel():
    attribution.set_channel(attribution.CHANNEL_CLI)
    assert attribution.client_headers({"CODEX_THREAD_ID": "x"}) == {
        "X-Tamarind-Client-Channel": "cli",
        "X-Tamarind-Client-Agent": "codex",
    }


def test_http_client_sends_the_headers(monkeypatch):
    monkeypatch.setenv("CLAUDECODE", "1")
    monkeypatch.setenv("CLAUDE_CODE_ENTRYPOINT", "cli")
    for key in [k for k in __import__("os").environ if k.startswith("OPERON_")]:
        monkeypatch.delenv(key)
    monkeypatch.delenv("TAMARIND_AGENT", raising=False)
    with HTTPClient("https://app.tamarind.bio/api/", "k") as client:
        assert client._headers["X-Tamarind-Client-Channel"] == "sdk"
        assert client._headers["X-Tamarind-Client-Agent"] == "claude-code"
        assert client._headers["User-Agent"].startswith("tamarind-cli/")
