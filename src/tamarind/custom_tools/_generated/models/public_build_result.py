from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define

from ..models.public_build_result_action import PublicBuildResultAction

if TYPE_CHECKING:
    from ..models.public_version import PublicVersion


T = TypeVar("T", bound="PublicBuildResult")


@_attrs_define
class PublicBuildResult:
    """
    Attributes:
        action (PublicBuildResultAction): What happened: `build` started a new image build, `reuse_image` created a
            version from the current image, and `unchanged` returned the version already associated with this source.
        version (PublicVersion):
    """

    action: PublicBuildResultAction
    version: PublicVersion

    def to_dict(self) -> dict[str, Any]:
        action = self.action.value

        version = self.version.to_dict()

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "action": action,
                "version": version,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.public_version import PublicVersion

        d = dict(src_dict)
        action = PublicBuildResultAction(d.pop("action"))

        version = PublicVersion.from_dict(d.pop("version"))

        public_build_result = cls(
            action=action,
            version=version,
        )

        return public_build_result
