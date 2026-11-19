from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.job_stop_reason_kind import JobStopReasonKind

T = TypeVar("T", bound="JobStopReason")


@_attrs_define
class JobStopReason:
    """
    Attributes:
        code (str): With `kind` `error`: `tool_error`, `invalid_input`, `out_of_memory`, `timeout` (the tool's own time
            limit) or `platform_error` (our fault). With `limit`: `budget_exceeded`, `quota_exceeded`, `runtime_limit` (the
            maximum runtime set at submit) or, on a batch only, `queue_full` (too many of your jobs were waiting to run).
            With `canceled`: `canceled`. With `unknown`: `unknown`. New codes can be added.
        hint (None | str): What to try next, when we know, e.g. `Use a larger GPU or split the input`.
        kind (JobStopReasonKind): `error` (status `Failed`): it failed; read `code` and `message`. `canceled` (status
            `Stopped`): a user or an API call stopped it, so there is nothing to fix. `limit` (status `Stopped`): a budget,
            quota or runtime limit you or your organization set stopped it. `unknown` (status `Stopped`): it stopped and no
            reason was recorded, so we don't claim it failed.
        message (str): What happened, in words safe to show a user. The message recorded with the stop when there is one
            (a cancel's `reason`, for example), at most 500 characters; otherwise a fixed sentence for the `code`. A
            pipeline run's is always the fixed sentence.
        retryable (bool | None): Whether `rerunJob` with unchanged settings could help. Null when unknown.
    """

    code: str
    hint: None | str
    kind: JobStopReasonKind
    message: str
    retryable: bool | None
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        code = self.code

        hint: None | str
        hint = self.hint

        kind = self.kind.value

        message = self.message

        retryable: bool | None
        retryable = self.retryable

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "code": code,
                "hint": hint,
                "kind": kind,
                "message": message,
                "retryable": retryable,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        code = d.pop("code")

        def _parse_hint(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        hint = _parse_hint(d.pop("hint"))

        kind = JobStopReasonKind(d.pop("kind"))

        message = d.pop("message")

        def _parse_retryable(data: object) -> bool | None:
            if data is None:
                return data
            return cast(bool | None, data)

        retryable = _parse_retryable(d.pop("retryable"))

        job_stop_reason = cls(
            code=code,
            hint=hint,
            kind=kind,
            message=message,
            retryable=retryable,
        )

        job_stop_reason.additional_properties = d
        return job_stop_reason

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
