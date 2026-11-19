from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.model_status import ModelStatus

T = TypeVar("T", bound="Model")


@_attrs_define
class Model:
    """
    Attributes:
        base_model (None | str):
        created_at (datetime.datetime):
        display_name (None | str): The name the owner gave it, or null when it hasn't been renamed. The app shows `name`
            then.
        id (str): Send as `modelId` on `submitJob`, for a single job or a batch.
        inference_tool (None | str): The tool to send as `tool` to run this model. Null when it has none.
        is_default (bool):
        name (str):
        owner (str):
        parent_model_id (None | str):
        shared_with_organization (bool): Always true for now, as in the app, which shares every live model with its
            owner's organization.
        status (ModelStatus): `unknown` for any stored status other than these three: only call a model failed with
            evidence.
        tags (list[str]):
        tool (str): The finetuning tool that trained it, or `org/tool` for an organization's custom tool.
        version (int | None):
    """

    base_model: None | str
    created_at: datetime.datetime
    display_name: None | str
    id: str
    inference_tool: None | str
    is_default: bool
    name: str
    owner: str
    parent_model_id: None | str
    shared_with_organization: bool
    status: ModelStatus
    tags: list[str]
    tool: str
    version: int | None
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        base_model: None | str
        base_model = self.base_model

        created_at = self.created_at.isoformat()

        display_name: None | str
        display_name = self.display_name

        id = self.id

        inference_tool: None | str
        inference_tool = self.inference_tool

        is_default = self.is_default

        name = self.name

        owner = self.owner

        parent_model_id: None | str
        parent_model_id = self.parent_model_id

        shared_with_organization = self.shared_with_organization

        status = self.status.value

        tags = self.tags

        tool = self.tool

        version: int | None
        version = self.version

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "baseModel": base_model,
                "createdAt": created_at,
                "displayName": display_name,
                "id": id,
                "inferenceTool": inference_tool,
                "isDefault": is_default,
                "name": name,
                "owner": owner,
                "parentModelId": parent_model_id,
                "sharedWithOrganization": shared_with_organization,
                "status": status,
                "tags": tags,
                "tool": tool,
                "version": version,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_base_model(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        base_model = _parse_base_model(d.pop("baseModel"))

        created_at = isoparse(d.pop("createdAt"))

        def _parse_display_name(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        display_name = _parse_display_name(d.pop("displayName"))

        id = d.pop("id")

        def _parse_inference_tool(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        inference_tool = _parse_inference_tool(d.pop("inferenceTool"))

        is_default = d.pop("isDefault")

        name = d.pop("name")

        owner = d.pop("owner")

        def _parse_parent_model_id(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        parent_model_id = _parse_parent_model_id(d.pop("parentModelId"))

        shared_with_organization = d.pop("sharedWithOrganization")

        status = ModelStatus(d.pop("status"))

        tags = cast(list[str], d.pop("tags"))

        tool = d.pop("tool")

        def _parse_version(data: object) -> int | None:
            if data is None:
                return data
            return cast(int | None, data)

        version = _parse_version(d.pop("version"))

        model = cls(
            base_model=base_model,
            created_at=created_at,
            display_name=display_name,
            id=id,
            inference_tool=inference_tool,
            is_default=is_default,
            name=name,
            owner=owner,
            parent_model_id=parent_model_id,
            shared_with_organization=shared_with_organization,
            status=status,
            tags=tags,
            tool=tool,
            version=version,
        )

        model.additional_properties = d
        return model

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
