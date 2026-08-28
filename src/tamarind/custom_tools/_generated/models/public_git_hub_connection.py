from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..models.public_git_hub_connection_status import PublicGitHubConnectionStatus

T = TypeVar("T", bound="PublicGitHubConnection")


@_attrs_define
class PublicGitHubConnection:
    """
    Attributes:
        auto_publish (bool):
        branch (None | str):
        commit (None | str):
        error (None | str):
        repo (None | str):
        status (PublicGitHubConnectionStatus):
    """

    auto_publish: bool
    branch: None | str
    commit: None | str
    error: None | str
    repo: None | str
    status: PublicGitHubConnectionStatus

    def to_dict(self) -> dict[str, Any]:
        auto_publish = self.auto_publish

        branch: None | str
        branch = self.branch

        commit: None | str
        commit = self.commit

        error: None | str
        error = self.error

        repo: None | str
        repo = self.repo

        status = self.status.value

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "autoPublish": auto_publish,
                "branch": branch,
                "commit": commit,
                "error": error,
                "repo": repo,
                "status": status,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        auto_publish = d.pop("autoPublish")

        def _parse_branch(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        branch = _parse_branch(d.pop("branch"))

        def _parse_commit(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        commit = _parse_commit(d.pop("commit"))

        def _parse_error(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        error = _parse_error(d.pop("error"))

        def _parse_repo(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        repo = _parse_repo(d.pop("repo"))

        status = PublicGitHubConnectionStatus(d.pop("status"))

        public_git_hub_connection = cls(
            auto_publish=auto_publish,
            branch=branch,
            commit=commit,
            error=error,
            repo=repo,
            status=status,
        )

        return public_git_hub_connection
