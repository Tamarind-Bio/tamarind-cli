from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.diagnostic import Diagnostic
    from ..models.problem_errors_item_type_1 import ProblemErrorsItemType1


T = TypeVar("T", bound="Problem")


@_attrs_define
class Problem:
    """An RFC 9457 problem document. Every error response in this API has this shape. A few codes add a top-level field of
    their own (RFC 9457 "extension members"); each is listed below with the code that sends it. Ignore any field you
    don't know.

        Attributes:
            code (str): Stable and machine-readable. Switch on this. New codes can be added at any time. Each has a docs
                page at `https://docs.tamarind.bio/errors/<code>`.

                Any operation: `authentication_required`, `invalid_api_key`, `agent_trial_expired`,
                `organization_read_disabled`, `organization_access_unavailable`, `account_not_ready`, `forbidden`,
                `not_found`, `method_not_allowed`, `unsupported_version`, `validation_failed`, `invalid_cursor`,
                `payload_too_large`, `rate_limited`, `service_unavailable`, `lane_at_capacity`, `internal_error`.
                An error with no more specific code names only the HTTP status: `bad_request`, `conflict`,
                `precondition_failed`, `unprocessable`, `upstream_error`.

                Jobs, tools and outputs: `tool_not_found`, `tool_not_available`, `tool_lifetime_changed`,
                `job_name_conflict`, `job_already_finished`, `job_still_starting`, `jobs_dependency_unavailable`,
                `redirect_needs_bearer`, `archive_failed`, `idempotency_key_reused`, `idempotency_in_progress`,
                `budget_exceeded`, `quota_exceeded`, `queue_full`, `upstream_unavailable`, `design_count_too_large`,
                `unclaimed_agent_credential_route`, `submission_plan_mismatch`, `organization_compute_disabled`,
                `organization_export_disabled` (website#7805, not merged yet), `job_not_finished`, `inputs_still_ingesting`,
                `inputs_not_ingested`, `nothing_to_rerun`,
                `rerun_incomplete`.
                Files: `folder_too_large`, `folder_changed`.
                Projects and notes: `project_name_taken`, `project_not_empty`, `project_move_required`,
                `project_partially_emptied`, `members_changed`, `members_not_removed`, `member_key_outdated`,
                `version_conflict`, `write_contended`.
                Keys, service accounts and organization: `session_required`, `org_admin_required`, `mfa_required`,
                `api_key_not_changeable`, `api_key_limit`, `service_account_exists`.
                Assays: `wetlab_access_required`, `targets_unavailable`, `results_unavailable`, `quote_rejected`,
                `lab_unavailable`, `not_cancellable`, `approval_in_progress`, `approval_under_review`,
                `order_changed`, `cancel_unconfirmed`, `duplicate_order`, `assays_blocked`, `assays_in_flight`,
                `idempotency_order_unavailable`, `order_incomplete`, `provider_error`, `outcome_unknown`.
                Pipelines: `node_run_molecule_response_too_large`, `organization_compute_disabled`,
                `organization_export_disabled` (website#7805, not merged yet), `molecule_group_view_only`,
                `molecules_import_ingestion_failed`, `molecules_import_ingestion_timeout`,
                `pg_pool_exhausted`, `pg_query_timeout`, and the pipelines service's own `pipeline_*` codes, which
                pass through unchanged.
                Molecules: their own `molecule_*` and `molecules_*` codes, plus `job_not_found` and
                `job_access_unavailable`.
                Custom tools: their own `custom_tool_*` codes, plus `invalid_custom_tool_config`,
                `invalid_custom_tool_source`, `tool_access_denied` and `upstream_failed`.
                A retired operation will answer 410 `endpoint_moved`.
            request_id (str): Quote this to support. Also in the `X-Request-Id` header.
            status (int): The HTTP status code.
            title (str): A short summary of the HTTP status, such as `Resource not found` or `Conflict`. Don't switch on it;
                switch on `code`.
            type_ (str): `https://docs.tamarind.bio/errors/<code>`, the docs page for this `code`.
            current_version (int | None | Unset): On a project notes `version_conflict`, the version the record is at now;
                send it as `version` on the retry. Null when the record couldn't be read again or the conflict isn't about one
                record.
            detail (str | Unset): What went wrong this time, in words safe to show a user.
            errors (list[Diagnostic | ProblemErrorsItemType1] | Unset): Every individual problem. Validation failures always
                carry it, one entry per problem, each a `Diagnostic`. The Molecules operations and
                `node_run_molecule_response_too_large` can send entries of their own shape (for example `{importId}` or
                `{message}`).
            existing_id (str | Unset): On `job_name_conflict`, the id of your job or batch that already has this name
                (`job_...` or `batch_...`, the id `getJob` reads), so you can fetch it instead of submitting again. Absent when
                none of your jobs or batches you can see has the name, or it couldn't be read; the 409 is the same either way.
            retryable (bool | Unset): Whether sending the same request again could succeed. Absent when unknown.
    """

    code: str
    request_id: str
    status: int
    title: str
    type_: str
    current_version: int | None | Unset = UNSET
    detail: str | Unset = UNSET
    errors: list[Diagnostic | ProblemErrorsItemType1] | Unset = UNSET
    existing_id: str | Unset = UNSET
    retryable: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.diagnostic import Diagnostic

        code = self.code

        request_id = self.request_id

        status = self.status

        title = self.title

        type_ = self.type_

        current_version: int | None | Unset
        if isinstance(self.current_version, Unset):
            current_version = UNSET
        else:
            current_version = self.current_version

        detail = self.detail

        errors: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.errors, Unset):
            errors = []
            for errors_item_data in self.errors:
                errors_item: dict[str, Any]
                if isinstance(errors_item_data, Diagnostic):
                    errors_item = errors_item_data.to_dict()
                else:
                    errors_item = errors_item_data.to_dict()

                errors.append(errors_item)

        existing_id = self.existing_id

        retryable = self.retryable

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "code": code,
                "requestId": request_id,
                "status": status,
                "title": title,
                "type": type_,
            }
        )
        if current_version is not UNSET:
            field_dict["currentVersion"] = current_version
        if detail is not UNSET:
            field_dict["detail"] = detail
        if errors is not UNSET:
            field_dict["errors"] = errors
        if existing_id is not UNSET:
            field_dict["existingId"] = existing_id
        if retryable is not UNSET:
            field_dict["retryable"] = retryable

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.diagnostic import Diagnostic
        from ..models.problem_errors_item_type_1 import ProblemErrorsItemType1

        d = dict(src_dict)
        code = d.pop("code")

        request_id = d.pop("requestId")

        status = d.pop("status")

        title = d.pop("title")

        type_ = d.pop("type")

        def _parse_current_version(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        current_version = _parse_current_version(d.pop("currentVersion", UNSET))

        detail = d.pop("detail", UNSET)

        _errors = d.pop("errors", UNSET)
        errors: list[Diagnostic | ProblemErrorsItemType1] | Unset = UNSET
        if _errors is not UNSET:
            errors = []
            for errors_item_data in _errors:

                def _parse_errors_item(data: object) -> Diagnostic | ProblemErrorsItemType1:
                    try:
                        if not isinstance(data, dict):
                            raise TypeError()
                        errors_item_type_0 = Diagnostic.from_dict(data)

                        return errors_item_type_0
                    except (TypeError, ValueError, AttributeError, KeyError):
                        pass
                    if not isinstance(data, dict):
                        raise TypeError()
                    errors_item_type_1 = ProblemErrorsItemType1.from_dict(data)

                    return errors_item_type_1

                errors_item = _parse_errors_item(errors_item_data)

                errors.append(errors_item)

        existing_id = d.pop("existingId", UNSET)

        retryable = d.pop("retryable", UNSET)

        problem = cls(
            code=code,
            request_id=request_id,
            status=status,
            title=title,
            type_=type_,
            current_version=current_version,
            detail=detail,
            errors=errors,
            existing_id=existing_id,
            retryable=retryable,
        )

        problem.additional_properties = d
        return problem

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
