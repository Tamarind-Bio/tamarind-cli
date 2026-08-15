"""Top-level Tamarind Python SDK client."""

from __future__ import annotations

from tamarind.config import load_config
from tamarind.custom_tools.generated import GeneratedCustomToolsTransport
from tamarind.custom_tools.resources import CustomTools
from tamarind.http import DEFAULT_TIMEOUT, HTTPClient


class Tamarind:
    """Configured Tamarind SDK session."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        api_base: str | None = None,
        profile: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        config = load_config(api_key=api_key, api_base=api_base, profile=profile)
        self._http = HTTPClient(config.api_base, config.api_key, timeout=timeout)
        self.custom_tools = CustomTools(
            GeneratedCustomToolsTransport(self._http),
            upload_timeout=timeout,
        )

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "Tamarind":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
