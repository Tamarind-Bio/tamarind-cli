"""Typed, read-only Pipelines resources."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Generic, Mapping, TypeVar

from tamarind.errors import TamarindError
from tamarind.pipelines._generated.models.node_run_status import NodeRunStatus
from tamarind.pipelines._generated.models.run_status import RunStatus
from tamarind.pipelines._generated.models.source import Source
from tamarind.pipelines.transport import GeneratedPipelinesTransport

T = TypeVar("T")


@dataclass(frozen=True)
class Page(Generic[T]):
    items: tuple[T, ...]
    next_cursor: str | None = None


@dataclass(frozen=True)
class NodeRunMolecule:
    complex_id: str
    name: str
    molecule_type: str | None
    sequence: str | None
    scores: Mapping[str, Any]
    has_structure: bool


@dataclass(frozen=True)
class NodeRun:
    id: str
    node_id: str
    label: str
    node_type: str
    status: NodeRunStatus
    started_at: str | None
    completed_at: str | None
    output_count: int | None
    jobs_total: int
    jobs_complete: int
    output_group: str | None
    _run_id: str = field(repr=False, compare=False)
    _collection: "Pipelines" = field(repr=False, compare=False)

    def molecules(self, *, limit: int = 25, cursor: str | None = None) -> Page[NodeRunMolecule]:
        """Return one page of molecules produced by this exact node run."""
        return self._collection._node_run_molecules(
            self._run_id,
            self.id,
            limit=limit,
            cursor=cursor,
        )


@dataclass(frozen=True)
class PipelineRun:
    id: str
    template_id: str
    template_version: str | None
    name: str | None
    source: Source
    status: RunStatus
    started_at: str
    completed_at: str | None
    inputs: Mapping[str, Any]
    node_runs: tuple[NodeRun, ...]


class Pipelines:
    """Entry point for typed Pipeline run reads."""

    def __init__(self, transport: GeneratedPipelinesTransport):
        self._transport = transport

    def get_run(self, run_id: str) -> PipelineRun:
        if not isinstance(run_id, str) or not run_id:
            raise ValueError("run_id must be a non-empty string")
        wire = self._transport.get_run(run_id)
        try:
            actual_id = _string(wire, "id")
            node_runs = tuple(
                _node_run_from_wire(self, actual_id, item)
                for item in _object_list(wire, "nodeRuns")
            )
            return PipelineRun(
                id=actual_id,
                template_id=_string(wire, "templateId"),
                template_version=_optional_string(wire, "templateVersion"),
                name=_optional_string(wire, "name"),
                source=Source(_string(wire, "source")),
                status=RunStatus(_string(wire, "status")),
                started_at=_string(wire, "startedAt"),
                completed_at=_optional_string(wire, "completedAt"),
                inputs=_object(wire, "inputs"),
                node_runs=node_runs,
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise TamarindError("Pipelines response did not match the generated contract") from exc

    def _node_run_molecules(
        self,
        run_id: str,
        node_run_id: str,
        *,
        limit: int,
        cursor: str | None,
    ) -> Page[NodeRunMolecule]:
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
            raise ValueError("limit must be an integer from 1 to 100")
        if cursor is not None and not isinstance(cursor, str):
            raise ValueError("cursor must be a string or None")
        wire = self._transport.list_node_run_molecules(
            run_id,
            node_run_id,
            limit=limit,
            cursor=cursor,
        )
        try:
            items = tuple(_molecule_from_wire(item) for item in _object_list(wire, "molecules"))
            return Page(items=items, next_cursor=_optional_string(wire, "nextCursor"))
        except (KeyError, TypeError, ValueError) as exc:
            raise TamarindError("Pipelines response did not match the generated contract") from exc


def _node_run_from_wire(collection: Pipelines, run_id: str, wire: dict[str, Any]) -> NodeRun:
    return NodeRun(
        id=_string(wire, "id"),
        node_id=_string(wire, "nodeId"),
        label=_string(wire, "label"),
        node_type=_string(wire, "nodeType"),
        status=NodeRunStatus(_string(wire, "status")),
        started_at=_optional_string(wire, "startedAt"),
        completed_at=_optional_string(wire, "completedAt"),
        output_count=_optional_integer(wire, "outputCount"),
        jobs_total=_integer(wire, "jobsTotal"),
        jobs_complete=_integer(wire, "jobsComplete"),
        output_group=_optional_string(wire, "outputGroup"),
        _run_id=run_id,
        _collection=collection,
    )


def _molecule_from_wire(wire: dict[str, Any]) -> NodeRunMolecule:
    return NodeRunMolecule(
        complex_id=_string(wire, "complexId"),
        name=_string(wire, "name"),
        molecule_type=_optional_string(wire, "moleculeType"),
        sequence=_optional_string(wire, "sequence"),
        scores=_object(wire, "scores"),
        has_structure=_boolean(wire, "hasStructure"),
    )


def _string(wire: dict[str, Any], key: str) -> str:
    value = wire[key]
    if not isinstance(value, str):
        raise TypeError(f"{key} is not a string")
    return value


def _optional_string(wire: dict[str, Any], key: str) -> str | None:
    value = wire[key]
    if value is not None and not isinstance(value, str):
        raise TypeError(f"{key} is not a string or null")
    return value


def _integer(wire: dict[str, Any], key: str) -> int:
    value = wire[key]
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{key} is not an integer")
    return value


def _optional_integer(wire: dict[str, Any], key: str) -> int | None:
    value = wire[key]
    if value is not None and (isinstance(value, bool) or not isinstance(value, int)):
        raise TypeError(f"{key} is not an integer or null")
    return value


def _boolean(wire: dict[str, Any], key: str) -> bool:
    value = wire[key]
    if not isinstance(value, bool):
        raise TypeError(f"{key} is not a boolean")
    return value


def _object(wire: dict[str, Any], key: str) -> dict[str, Any]:
    value = wire[key]
    if not isinstance(value, dict):
        raise TypeError(f"{key} is not an object")
    return value


def _object_list(wire: dict[str, Any], key: str) -> list[dict[str, Any]]:
    value = wire[key]
    if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
        raise TypeError(f"{key} is not an array of objects")
    return value
