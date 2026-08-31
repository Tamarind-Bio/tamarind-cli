from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Literal, TypeVar, cast

from attrs import define as _attrs_define

T = TypeVar("T", bound="PublicRecoveryAction")


@_attrs_define
class PublicRecoveryAction:
    """A safe, machine-readable action that can move a failed request forward.

    Attributes:
        authorization_url (str):
        expires_at (str):
        resume_token (str):
        type_ (Literal['authorize_github']):
    """

    authorization_url: str
    expires_at: str
    resume_token: str
    type_: Literal["authorize_github"]

    def to_dict(self) -> dict[str, Any]:
        authorization_url = self.authorization_url

        expires_at = self.expires_at

        resume_token = self.resume_token

        type_ = self.type_

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "authorizationUrl": authorization_url,
                "expiresAt": expires_at,
                "resumeToken": resume_token,
                "type": type_,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        authorization_url = d.pop("authorizationUrl")

        expires_at = d.pop("expiresAt")

        resume_token = d.pop("resumeToken")

        type_ = cast(Literal["authorize_github"], d.pop("type"))
        if type_ != "authorize_github":
            raise ValueError(f"type must match const 'authorize_github', got '{type_}'")

        public_recovery_action = cls(
            authorization_url=authorization_url,
            expires_at=expires_at,
            resume_token=resume_token,
            type_=type_,
        )

        return public_recovery_action
