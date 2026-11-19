from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.custom_tool_build_result_action import CustomToolBuildResultAction

if TYPE_CHECKING:
    from ..models.custom_tool_version import CustomToolVersion


T = TypeVar("T", bound="CustomToolBuildResult")


@_attrs_define
class CustomToolBuildResult:
    """
    Attributes:
        action (CustomToolBuildResultAction): What happened: `build` started a new image build, `reuse_image` created a
            version from the current image, and `unchanged` returned the version already associated with this source.
        version (CustomToolVersion):
    """

    action: CustomToolBuildResultAction
    version: CustomToolVersion
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        action = self.action.value

        version = self.version.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "action": action,
                "version": version,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.custom_tool_version import CustomToolVersion

        d = dict(src_dict)
        action = CustomToolBuildResultAction(d.pop("action"))

        version = CustomToolVersion.from_dict(d.pop("version"))

        custom_tool_build_result = cls(
            action=action,
            version=version,
        )

        custom_tool_build_result.additional_properties = d
        return custom_tool_build_result

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
