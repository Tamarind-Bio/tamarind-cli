"""Generated-contract adapter for the Pipelines SDK."""

from __future__ import annotations

from typing import Any, NamedTuple, cast

from tamarind.errors import TamarindError
from tamarind.http import HTTPClient
from tamarind.pipelines._generated.client import Client as GeneratedClient

from ._generated.api.pipelines_public import get_run, list_node_run_molecules


class _Operation(NamedTuple):
    endpoint: Any
    success_status: int


_GET_RUN = _Operation(get_run, 200)
_LIST_NODE_RUN_MOLECULES = _Operation(list_node_run_molecules, 200)


class GeneratedPipelinesTransport:
    """Use generated URL/response semantics through Tamarind's shared HTTP boundary."""

    def __init__(self, client: HTTPClient):
        self._client = client
        self._parser = GeneratedClient(base_url=client.base_url)

    def _sync(self, operation: _Operation, kwargs: dict[str, Any]) -> dict[str, Any]:
        values = dict(kwargs)
        values["path"] = values.pop("url")
        response = self._client.request(**values)
        if response.status_code != operation.success_status:
            raise TamarindError("Pipelines response did not match the generated contract")
        try:
            raw = response.json()
            parsed = operation.endpoint._parse_response(client=self._parser, response=response)
            if parsed is None or not hasattr(parsed, "to_dict"):
                raise TypeError("missing generated response model")
            parsed.to_dict()
            if not isinstance(raw, dict):
                raise TypeError("response is not an object")
            return cast(dict[str, Any], raw)
        except (AttributeError, KeyError, TypeError, ValueError) as exc:
            raise TamarindError("Pipelines response did not match the generated contract") from exc

    def get_run(self, run_id: str) -> dict[str, Any]:
        return self._sync(_GET_RUN, get_run._get_kwargs(run_id=run_id))

    def list_node_run_molecules(
        self,
        run_id: str,
        node_run_id: str,
        *,
        limit: int = 25,
        cursor: str | None = None,
    ) -> dict[str, Any]:
        return self._sync(
            _LIST_NODE_RUN_MOLECULES,
            list_node_run_molecules._get_kwargs(
                run_id=run_id,
                node_run_id=node_run_id,
                limit=limit,
                cursor=cursor,
            ),
        )
