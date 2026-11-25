"""Top-level Tamarind Python SDK client."""

from __future__ import annotations

from typing import Any, Iterator

from tamarind._v1 import public as _v1_public
from tamarind.config import load_config
from tamarind.custom_tools.transport import GeneratedCustomToolsTransport
from tamarind.custom_tools.resources import CustomTools
from tamarind.http import DEFAULT_TIMEOUT, HTTPClient
from tamarind.pipelines.resources import Pipelines
from tamarind.pipelines.transport import GeneratedPipelinesTransport
from tamarind.resources import Files, Jobs, Tools


class Tamarind:
    """Configured Tamarind SDK session.

    It authenticates with an API key, or with a service account's ``client_id`` and
    ``client_secret``, traded for one-hour access tokens that the client renews itself
    (:mod:`tamarind.oauth`). Settings resolve as in :mod:`tamarind.config`.

    Whether its requests go to the v1 API is the server's answer for this key, asked
    once on the first request v1 can answer and cached for a few minutes. Every method
    behaves the same either way; ``docs/v1-mode.md`` lists the small differences.

    The v1-only parts (``me``, ``api_keys``, ``service_accounts``, ``organization``,
    ``usage``, ``models``, ``projects``, ``molecules``, ``assays``, and the methods marked
    "v1 only" on the other resources) take v1's arguments and return its answers; they
    raise ``V1NotEnabledError`` without sending anything when v1 isn't on for the key.
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        api_base: str | None = None,
        profile: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        _flag_cache: Any = None,
    ):
        config = load_config(
            api_key=api_key,
            client_id=client_id,
            client_secret=client_secret,
            api_base=api_base,
            profile=profile,
        )
        self._http = HTTPClient(
            config.api_base,
            config.api_key,
            timeout=timeout,
            flag_cache=_flag_cache,
            credentials=config.client_credentials(),
        )
        self.custom_tools = CustomTools(
            GeneratedCustomToolsTransport(self._http),
            upload_timeout=timeout,
        )
        self.pipelines = Pipelines(GeneratedPipelinesTransport(self._http))
        # Job / catalog / file surfaces, mirroring the `tamarind` CLI command groups.
        self.jobs = Jobs(self._http)
        self.tools = Tools(self._http)
        self.files = Files(self._http)
        # v1 only.
        v1_only = _v1_public.resources(self._http)
        self.me = v1_only["me"]
        self.api_keys = v1_only["api_keys"]
        self.service_accounts = v1_only["service_accounts"]
        self.organization = v1_only["organization"]
        self.usage = v1_only["usage"]
        self.models = v1_only["models"]
        self.projects = v1_only["projects"]
        self.molecules = v1_only["molecules"]
        self.assays = v1_only["assays"]

    @staticmethod
    def paginate(method: Any, *args: Any, **params: Any) -> Iterator[Any]:
        """Every item of a v1 list operation, page by page (v1 only):
        ``Tamarind.paginate(client.projects.list, limit=200)``."""
        return _v1_public.paginate(method, *args, **params)

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "Tamarind":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
