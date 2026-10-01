"""Tell Tamarind which channel and AI agent a request comes from.

Tamarind breaks usage down by channel (this package as a CLI vs as an SDK) and by the AI agent
driving it (Claude Code, Codex, Claude Science, ...). Every request carries two headers:

* ``X-Tamarind-Client-Channel``: ``cli`` when run as the ``tamarind`` command, ``sdk`` when
  imported as a library.
* ``X-Tamarind-Client-Agent``: the agent whose shell ran this process, detected from the
  environment variables agents set for the commands they run. Omitted when none is found.

Attribution only: the server never grants or refuses anything based on them. Set
``TAMARIND_AGENT`` to name the agent explicitly, or ``TAMARIND_AGENT=none`` to send none.
"""

from __future__ import annotations

import os
import re
from collections.abc import Mapping

CHANNEL_CLI = "cli"
CHANNEL_SDK = "sdk"

_channel = CHANNEL_SDK
_SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{0,39}$")


def set_channel(channel: str) -> None:
    """Called once by the ``tamarind`` entry point; library use stays ``sdk``."""
    global _channel
    _channel = channel


def detect_agent(env: Mapping[str, str] | None = None) -> str | None:
    """The agent whose shell is running this process, or None.

    Checked most specific first. What each agent sets was read from its own build on
    2026-09-30: Claude Science (0.1.x) exports ``OPERON_*`` for the commands it runs and is
    built on the Claude Agent SDK, so it is checked before ``CLAUDECODE``; Claude Code (2.1.x)
    sets ``CLAUDECODE=1`` and ``CLAUDE_CODE_ENTRYPOINT`` (``cli``, ``claude-vscode``, or
    ``sdk-py``/``sdk-ts`` for apps built on the Agent SDK); Codex (0.144) sets
    ``CODEX_THREAD_ID`` and, when sandboxed, ``CODEX_SANDBOX``; Gemini CLI sets ``GEMINI_CLI=1``.
    """
    env = os.environ if env is None else env
    explicit = (env.get("TAMARIND_AGENT") or "").strip().lower()
    if explicit:
        return explicit if explicit != "none" and _SLUG.match(explicit) else None
    if any(key.startswith("OPERON_") for key in env):
        return "claude-science"
    if env.get("CLAUDECODE") == "1" or env.get("CLAUDE_CODE_ENTRYPOINT"):
        entrypoint = env.get("CLAUDE_CODE_ENTRYPOINT") or ""
        return "claude-agent-sdk" if entrypoint.startswith("sdk-") else "claude-code"
    if env.get("CODEX_THREAD_ID") or env.get("CODEX_SANDBOX"):
        return "codex"
    if env.get("GEMINI_CLI") == "1":
        return "gemini-cli"
    return None


def client_headers(env: Mapping[str, str] | None = None) -> dict[str, str]:
    """The attribution headers for a request made now."""
    headers = {"X-Tamarind-Client-Channel": _channel}
    agent = detect_agent(env)
    if agent:
        headers["X-Tamarind-Client-Agent"] = agent
    return headers
