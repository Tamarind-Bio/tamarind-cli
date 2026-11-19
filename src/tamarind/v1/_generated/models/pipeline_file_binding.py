from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

T = TypeVar("T", bound="PipelineFileBinding")


@_attrs_define
class PipelineFileBinding:
    """
    Attributes:
        file (str): A file path (relative to your user folder).
    """

    file: str

    def to_dict(self) -> dict[str, Any]:
        file = self.file

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "file": file,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        file = d.pop("file")

        pipeline_file_binding = cls(
            file=file,
        )

        return pipeline_file_binding
