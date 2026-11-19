from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="BoardNote")


@_attrs_define
class BoardNote:
    """One note in an entry's log. `editedAt` is there only once somebody has edited it.

    Attributes:
        author (None | str):
        author_actor_type (str):
        body (str):
        created_at (datetime.datetime | None):
        entry_id (None | str):
        id (str):
        version (float | int):
        edited_at (datetime.datetime | None | Unset):
    """

    author: None | str
    author_actor_type: str
    body: str
    created_at: datetime.datetime | None
    entry_id: None | str
    id: str
    version: float | int
    edited_at: datetime.datetime | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        author: None | str
        author = self.author

        author_actor_type = self.author_actor_type

        body = self.body

        created_at: None | str
        if isinstance(self.created_at, datetime.datetime):
            created_at = self.created_at.isoformat()
        else:
            created_at = self.created_at

        entry_id: None | str
        entry_id = self.entry_id

        id = self.id

        version: float | int
        version = self.version

        edited_at: None | str | Unset
        if isinstance(self.edited_at, Unset):
            edited_at = UNSET
        elif isinstance(self.edited_at, datetime.datetime):
            edited_at = self.edited_at.isoformat()
        else:
            edited_at = self.edited_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "author": author,
                "authorActorType": author_actor_type,
                "body": body,
                "createdAt": created_at,
                "entryId": entry_id,
                "id": id,
                "version": version,
            }
        )
        if edited_at is not UNSET:
            field_dict["editedAt"] = edited_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_author(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        author = _parse_author(d.pop("author"))

        author_actor_type = d.pop("authorActorType")

        body = d.pop("body")

        def _parse_created_at(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                created_at_type_0 = isoparse(data)

                return created_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        created_at = _parse_created_at(d.pop("createdAt"))

        def _parse_entry_id(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        entry_id = _parse_entry_id(d.pop("entryId"))

        id = d.pop("id")

        def _parse_version(data: object) -> float | int:
            return cast(float | int, data)

        version = _parse_version(d.pop("version"))

        def _parse_edited_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                edited_at_type_0 = isoparse(data)

                return edited_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        edited_at = _parse_edited_at(d.pop("editedAt", UNSET))

        board_note = cls(
            author=author,
            author_actor_type=author_actor_type,
            body=body,
            created_at=created_at,
            entry_id=entry_id,
            id=id,
            version=version,
            edited_at=edited_at,
        )

        board_note.additional_properties = d
        return board_note

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
