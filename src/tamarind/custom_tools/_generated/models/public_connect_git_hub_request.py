from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="PublicConnectGitHubRequest")


@_attrs_define
class PublicConnectGitHubRequest:
    """
    Attributes:
        repo (str): GitHub repository in `owner/repo` form.
        authorization_token (None | str | Unset): Opaque token returned by a prior `github_authorization_required`
            response.
        auto_publish (bool | Unset):  Default: False.
        branch (str | Unset):  Default: 'main'.
    """

    repo: str
    authorization_token: None | str | Unset = UNSET
    auto_publish: bool | Unset = False
    branch: str | Unset = "main"

    def to_dict(self) -> dict[str, Any]:
        repo = self.repo

        authorization_token: None | str | Unset
        if isinstance(self.authorization_token, Unset):
            authorization_token = UNSET
        else:
            authorization_token = self.authorization_token

        auto_publish = self.auto_publish

        branch = self.branch

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "repo": repo,
            }
        )
        if authorization_token is not UNSET:
            field_dict["authorizationToken"] = authorization_token
        if auto_publish is not UNSET:
            field_dict["autoPublish"] = auto_publish
        if branch is not UNSET:
            field_dict["branch"] = branch

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        repo = d.pop("repo")

        def _parse_authorization_token(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        authorization_token = _parse_authorization_token(d.pop("authorizationToken", UNSET))

        auto_publish = d.pop("autoPublish", UNSET)

        branch = d.pop("branch", UNSET)

        public_connect_git_hub_request = cls(
            repo=repo,
            authorization_token=authorization_token,
            auto_publish=auto_publish,
            branch=branch,
        )

        return public_connect_git_hub_request
