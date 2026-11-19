from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.assay_setting_required_when import AssaySettingRequiredWhen


T = TypeVar("T", bound="AssaySetting")


@_attrs_define
class AssaySetting:
    """One setting an assay type takes.

    Attributes:
        description (str):
        name (str):
        required (bool):
        type_ (str): The kind of value, such as `string` or `number`. `dropdown` means one of `options`.
        default (Any | Unset): The value used when this is omitted. Present only when there is one.
        list_ (bool | Unset): Present and true when the setting takes an array of `type`.
        options (list[Any] | Unset): The values allowed. Present when `type` is `dropdown`.
        required_when (AssaySettingRequiredWhen | Unset): When this setting becomes required: another setting's name,
            and the values of it that require this one. Present only when that applies.
    """

    description: str
    name: str
    required: bool
    type_: str
    default: Any | Unset = UNSET
    list_: bool | Unset = UNSET
    options: list[Any] | Unset = UNSET
    required_when: AssaySettingRequiredWhen | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        description = self.description

        name = self.name

        required = self.required

        type_ = self.type_

        default = self.default

        list_ = self.list_

        options: list[Any] | Unset = UNSET
        if not isinstance(self.options, Unset):
            options = self.options

        required_when: dict[str, Any] | Unset = UNSET
        if not isinstance(self.required_when, Unset):
            required_when = self.required_when.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "description": description,
                "name": name,
                "required": required,
                "type": type_,
            }
        )
        if default is not UNSET:
            field_dict["default"] = default
        if list_ is not UNSET:
            field_dict["list"] = list_
        if options is not UNSET:
            field_dict["options"] = options
        if required_when is not UNSET:
            field_dict["requiredWhen"] = required_when

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.assay_setting_required_when import AssaySettingRequiredWhen

        d = dict(src_dict)
        description = d.pop("description")

        name = d.pop("name")

        required = d.pop("required")

        type_ = d.pop("type")

        default = d.pop("default", UNSET)

        list_ = d.pop("list", UNSET)

        options = cast(list[Any], d.pop("options", UNSET))

        _required_when = d.pop("requiredWhen", UNSET)
        required_when: AssaySettingRequiredWhen | Unset
        if isinstance(_required_when, Unset):
            required_when = UNSET
        else:
            required_when = AssaySettingRequiredWhen.from_dict(_required_when)

        assay_setting = cls(
            description=description,
            name=name,
            required=required,
            type_=type_,
            default=default,
            list_=list_,
            options=options,
            required_when=required_when,
        )

        assay_setting.additional_properties = d
        return assay_setting

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
