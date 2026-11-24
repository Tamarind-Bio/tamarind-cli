from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="GetPipelineRunResultsBodyType0")


@_attrs_define
class GetPipelineRunResultsBodyType0:
    """Optional; no body, `null` or `{}` is the whole run's zip.

    Attributes:
        node_run_id (None | str | Unset): Only this node run's outputs (the `id` of an entry in the run's `nodeRuns`).
            An id that isn't one of the run's node runs is 404.
    """

    node_run_id: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        node_run_id: None | str | Unset
        if isinstance(self.node_run_id, Unset):
            node_run_id = UNSET
        else:
            node_run_id = self.node_run_id

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if node_run_id is not UNSET:
            field_dict["nodeRunId"] = node_run_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_node_run_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        node_run_id = _parse_node_run_id(d.pop("nodeRunId", UNSET))

        get_pipeline_run_results_body_type_0 = cls(
            node_run_id=node_run_id,
        )

        return get_pipeline_run_results_body_type_0
