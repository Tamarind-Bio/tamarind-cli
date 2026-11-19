from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

T = TypeVar("T", bound="PublishPipelineTemplateRequest")


@_attrs_define
class PublishPipelineTemplateRequest:
    """
    Example:
        {'version': 'v1'}

    Attributes:
        version (str): The version handle to publish e.g. 'v1' (from a prior response's version).
    """

    version: str

    def to_dict(self) -> dict[str, Any]:
        version = self.version

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "version": version,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        version = d.pop("version")

        publish_pipeline_template_request = cls(
            version=version,
        )

        return publish_pipeline_template_request
