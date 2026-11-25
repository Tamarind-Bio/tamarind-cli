"""The Tamarind API v1 client: one method per operation, plus a few helpers.

Each method is named from its operation's ``x-clients.sdk`` in the contract, in
snake_case (``projects.notes.createEntry`` is ``client.projects.notes.create_entry``),
and is built on that operation's generated module in ``tamarind._v1._generated``.

- Path parameters are positional, in path order; a request body (a ``dict``, or a
  generated model) comes next or as ``body=``; query parameters are keyword
  arguments named as in the generated module (``batch_id=``, ``created_after=``).
- The answer is the decoded JSON as plain ``dict``/``list`` values, ``None`` for an
  empty answer, or ``bytes`` for file content. Fields and enum values the API adds
  later reach you unchanged; the generated models stay available for typed parsing
  (``Job.from_dict(answer)``).
- A failure raises :class:`~tamarind._v1.errors.ProblemError`.

Helpers (DESIGN decision 25): :meth:`Jobs.wait`, :meth:`Files.upload`,
:meth:`Tamarind.paginate`, and in every call an automatic ``Idempotency-Key`` and
retries on 429 and 5xx that honor ``Retry-After``.
"""

from __future__ import annotations

import base64
import inspect
import io
import os
import time
import types
from collections.abc import Callable, Iterator, Mapping
from pathlib import Path
from typing import IO, Any

import attrs
import httpx

from tamarind.errors import JobTimeoutError, TamarindError
from tamarind._v1._generated.api.api_keys import (
    create_api_key,
    get_api_key,
    list_api_keys,
    revoke_api_key,
    update_api_key,
)
from tamarind._v1._generated.api.assays import (
    cancel_assay,
    estimate_assay,
    get_assay,
    get_assay_results,
    list_assay_targets,
    list_assay_types,
    list_assays,
    submit_assay,
    validate_assay,
)
from tamarind._v1._generated.api.custom_tools import (
    build_custom_tool,
    cancel_custom_tool_build,
    create_custom_tool,
    create_custom_tool_upload,
    delete_custom_tool,
    get_custom_tool,
    list_custom_tool_build_logs,
    list_custom_tool_versions,
    list_custom_tools,
    publish_custom_tool,
    update_custom_tool,
    validate_custom_tool_config,
)
from tamarind._v1._generated.api.files import (
    complete_file_upload,
    delete_file,
    get_file,
    get_file_stats,
    list_files,
    upload_file,
)
from tamarind._v1._generated.api.identity import get_me
from tamarind._v1._generated.api.job_outputs import (
    get_job_file,
    get_job_logs,
    get_job_results,
    list_job_files,
)
from tamarind._v1._generated.api.jobs import (
    cancel_job,
    delete_job,
    estimate_job,
    get_job,
    list_jobs,
    rerun_job,
    search_jobs,
    submit_job,
    update_job,
    validate_job,
)
from tamarind._v1._generated.api.models import get_model, list_models
from tamarind._v1._generated.api.molecules import (
    commit_molecule_import,
    create_molecule_group,
    create_molecule_schema,
    delete_molecule,
    delete_molecule_import,
    get_molecule,
    get_molecule_group,
    get_molecule_import,
    get_molecule_schema,
    list_groups_for_molecule,
    list_molecule_groups,
    list_molecule_schemas,
    list_molecule_score_observations,
    list_molecules,
    remove_molecules_from_group,
    search_molecules,
    start_molecule_import,
    update_molecule_metadata,
    update_molecule_schema,
    upload_molecules,
)
from tamarind._v1._generated.api.organization import (
    get_organization,
    get_organization_contract,
    list_organization_members,
    list_sub_organizations,
)
from tamarind._v1._generated.api.pipelines import (
    cancel_pipeline_run,
    create_pipeline_template,
    delete_pipeline_template,
    duplicate_pipeline_template,
    estimate_pipeline,
    get_pipeline_run,
    get_pipeline_run_results,
    get_pipeline_schema,
    get_pipeline_template,
    list_node_run_molecules,
    list_pipeline_runs,
    list_pipeline_templates,
    publish_pipeline_template,
    submit_pipeline,
    validate_pipeline,
    validate_pipeline_template,
)
from tamarind._v1._generated.api.project_notes import (
    append_project_notes_note,
    create_project_notes_entry,
    delete_project_notes_entry,
    delete_project_notes_note,
    get_project_notes,
    get_project_notes_entry,
    update_project_notes,
    update_project_notes_entry,
    update_project_notes_note,
)
from tamarind._v1._generated.api.projects import (
    create_project,
    delete_project,
    get_project,
    leave_project,
    list_project_members,
    list_projects,
    update_project,
)
from tamarind._v1._generated.api.service_accounts import (
    create_service_account,
    delete_service_account,
    get_service_account,
    list_service_accounts,
)
from tamarind._v1._generated.api.tools import (
    get_tool,
    get_tool_facets,
    get_tool_schema,
    list_tools,
    recommend_tools,
)
from tamarind._v1._generated.api.usage import get_usage, refresh_usage
from tamarind._v1._generated.types import UNSET
from tamarind._v1._transport import (
    DEFAULT_BASE_URL,
    DEFAULT_MAX_RETRIES,
    DEFAULT_TIMEOUT,
    Transport,
    _hints,
    _members,
    decode,
)

TERMINAL_STATUSES = frozenset({"Complete", "Stopped", "Failed"})
INLINE_UPLOAD_LIMIT = 3 * 1024 * 1024
SIGNED_UPLOAD_LIMIT = 5_000_000_000


class Operation:
    """Binds one generated endpoint module to a resource as a method."""

    def __init__(
        self,
        endpoint: types.ModuleType,
        *path: str,
        check: Callable[[httpx.Response, Any], None] | None = None,
        repeat_safe: bool = False,
    ):
        self.endpoint = endpoint
        self.path = path
        self.check = check
        # The contract makes this operation repeatable: a POST that only reads, or one its
        # description calls safe to repeat, idempotent or polled (the cancels, the two
        # archive builds, usage refresh, key revoke, molecule delete and group removal). It is retried after an
        # ambiguous failure like a GET.
        self.repeat_safe = repeat_safe
        self.__doc__ = _doc(endpoint)

    def __set_name__(self, owner: type, name: str) -> None:
        self.name = name

    def __get__(self, resource: Any, owner: type | None = None) -> Any:
        if resource is None:
            return self
        return BoundOperation(self, resource._transport)


def _doc(endpoint: types.ModuleType) -> str:
    """The generated summary, description and Args, without its Raises/Returns."""
    text = inspect.cleandoc(endpoint.sync_detailed.__doc__ or "")
    kept = []
    for line in text.splitlines():
        if line.strip() in {"Raises:", "Returns:"}:
            break
        kept.append(line)
    return "\n".join(kept).rstrip() + (
        "\n\nextra_headers (dict): headers to add to this one request, such as"
        " ``{'Accept': 'text/csv'}``."
        "\n\nReturns the decoded JSON answer (bytes for file content, None when empty)."
        "\nRaises tamarind._v1.ProblemError for an error answer."
    )


class BoundOperation:
    def __init__(self, operation: Operation, transport: Transport):
        self.operation = operation
        self._transport = transport
        self.__doc__ = operation.__doc__
        self.__name__ = operation.name

    @property
    def takes_body(self) -> bool:
        return "body" in _hints(self.operation.endpoint._get_kwargs)

    @property
    def pageable(self) -> bool:
        """``cursor`` is a query parameter and the answer is a page of ``items``."""
        return "cursor" in _hints(self.operation.endpoint._get_kwargs) and self._pages_items

    @property
    def _pages_items(self) -> bool:
        answer = _hints(self.operation.endpoint._parse_response).get("return")
        return any(
            attrs.has(member) and "items" in attrs.fields_dict(member)
            for member in _members(answer)
            if isinstance(member, type)
        )

    @property
    def body_pageable(self) -> bool:
        """``cursor`` is a field of this operation's request body."""
        hint = _hints(self.operation.endpoint._get_kwargs).get("body")
        return self._pages_items and any(
            attrs.has(member) and "cursor" in attrs.fields_dict(member)
            for member in _members(hint)
            if isinstance(member, type)
        )

    def __call__(
        self,
        *args: Any,
        body: Any = UNSET,
        extra_headers: Mapping[str, str] | None = None,
        **params: Any,
    ) -> Any:
        response = self.raw(*args, body=body, extra_headers=extra_headers, **params)
        answer = decode(response)
        if self.operation.check is not None:
            self.operation.check(response, answer)
        return answer

    def raw(
        self,
        *args: Any,
        body: Any = UNSET,
        extra_headers: Mapping[str, str] | None = None,
        **params: Any,
    ) -> httpx.Response:
        """Send the same request and return the ``httpx.Response`` itself, for its headers
        (``X-Next-Cursor`` on a CSV usage page, ``X-RateLimit-*``, ``Location``)."""
        path = self.operation.path
        positional_body = self.takes_body and body is UNSET
        if len(args) > len(path) + (1 if positional_body else 0):
            raise TypeError(f"{self.__name__}() takes the path parameters {list(path)}")
        if len(args) == len(path) + 1:
            body = args[-1]
            args = args[:-1]
        if len(args) < len(path):
            missing = ", ".join(path[len(args) :])
            raise TypeError(f"{self.__name__}() is missing {missing}")
        overlap = set(path) & set(params)
        if overlap:
            raise TypeError(f"{self.__name__}() got {', '.join(sorted(overlap))} twice")
        return self._transport.call(
            self.operation.endpoint,
            body=body,
            extra_headers=extra_headers,
            repeat_safe=self.operation.repeat_safe,
            **dict(zip(path, args)),
            **params,
        )


def _secret_shown(response: httpx.Response, answer: Any) -> None:
    """A replayed ``createApiKey`` has no secret: the key exists but can't be used."""
    if response.headers.get("idempotent-replayed") == "true" and not (
        isinstance(answer, dict) and answer.get("secret")
    ):
        key_id = answer.get("id") if isinstance(answer, dict) else None
        raise TamarindError(
            f"Key {key_id} was made by an earlier attempt with this Idempotency-Key, and its "
            "secret can't be shown again. Revoke it (api_keys.revoke) and create another.",
            detail=answer,
        )


class _Resource:
    def __init__(self, transport: Transport):
        self._transport = transport


class Me(_Resource):
    get = Operation(get_me)


class ApiKeys(_Resource):
    list = Operation(list_api_keys)
    create = Operation(create_api_key, check=_secret_shown)
    get = Operation(get_api_key, "key_id")
    update = Operation(update_api_key, "key_id")
    revoke = Operation(revoke_api_key, "key_id", repeat_safe=True)


class ServiceAccounts(_Resource):
    list = Operation(list_service_accounts)
    create = Operation(create_service_account)
    get = Operation(get_service_account, "service_account_id")
    delete = Operation(delete_service_account, "service_account_id")


class Organization(_Resource):
    get = Operation(get_organization)
    get_contract = Operation(get_organization_contract)
    list_members = Operation(list_organization_members)
    list_sub_organizations = Operation(list_sub_organizations)


class Usage(_Resource):
    get = Operation(get_usage)
    refresh = Operation(refresh_usage, repeat_safe=True)


class Tools(_Resource):
    list = Operation(list_tools)
    facets = Operation(get_tool_facets)
    recommend = Operation(recommend_tools, repeat_safe=True)
    get = Operation(get_tool, "tool")
    schema = Operation(get_tool_schema, "tool")


class Jobs(_Resource):
    """Jobs, batches and pipeline runs (``job_``, ``batch_`` and ``run_`` ids)."""

    list = Operation(list_jobs)
    submit = Operation(submit_job)
    estimate = Operation(estimate_job, repeat_safe=True)
    search = Operation(search_jobs, repeat_safe=True)
    validate = Operation(validate_job, repeat_safe=True)
    get = Operation(get_job, "job_id")
    update = Operation(update_job, "job_id")
    delete = Operation(delete_job, "job_id")
    cancel = Operation(cancel_job, "job_id", repeat_safe=True)
    rerun = Operation(rerun_job, "job_id")
    results = Operation(get_job_results, "job_id", repeat_safe=True)
    list_files = Operation(list_job_files, "job_id")
    get_file = Operation(get_job_file, "job_id")
    logs = Operation(get_job_logs, "job_id")

    def wait(
        self,
        job_id: str,
        *,
        timeout: float | None = None,
        poll_interval: float | None = None,
        on_update: Callable[[dict[str, Any]], None] | None = None,
    ) -> dict[str, Any]:
        """Poll a job, batch or run until it is ``Complete``, ``Stopped`` or ``Failed``.

        Returns the final item; check its ``status`` (and ``stopReason``). Between
        polls it waits ``poll_interval`` seconds, or else the item's own
        ``pollAfterSeconds``. ``on_update`` sees every item read. Raises
        :class:`~tamarind.errors.JobTimeoutError` once ``timeout`` seconds have passed
        without a finished item; the job itself keeps running. ``timeout`` bounds the
        waiting between polls: no poll starts after it, and a poll already sent is an
        ordinary request, bounded by the client's own ``timeout``.
        """
        deadline = None if timeout is None else time.monotonic() + timeout
        while True:
            item = self.get(job_id)
            if on_update is not None:
                on_update(item)
            if item.get("status") in TERMINAL_STATUSES:
                return item
            if poll_interval is not None:
                delay = float(poll_interval)
            else:
                delay = float(item.get("pollAfterSeconds") or 15)
            if deadline is not None:
                delay = min(delay, max(0.0, deadline - time.monotonic()))
            self._transport._sleep(delay)
            # Checked before the next read, so no request starts after the deadline.
            if deadline is not None and time.monotonic() >= deadline:
                raise JobTimeoutError(
                    f"{job_id} was still {item.get('status')} when {timeout:g}s passed",
                    detail=item,
                )


class Files(_Resource):
    """Your workspace files.

    ``get``/``jobs.get_file`` answer ``delivery="url"`` (the default) with a short-lived
    link to fetch without your key, and ``delivery="inline"`` with the bytes (up to
    4 MiB). ``delivery="redirect"`` is for clients that follow redirects and needs
    ``Authorization: Bearer``; with this client's ``x-api-key`` it is 422
    ``redirect_needs_bearer``, and the link it would redirect to is the one ``url`` gives.
    """

    list = Operation(list_files)
    delete = Operation(delete_file)
    get = Operation(get_file)
    stats = Operation(get_file_stats)

    def sign_upload(
        self, path: str, *, content_type: str | None = None, size_bytes: int = 0
    ) -> dict[str, Any]:
        """Ask for one signed PUT link to ``path`` (uploadFile without the content) and
        return v1's answer, ``{"file", "upload"}``. Nothing is stored until the bytes are
        PUT to ``upload["url"]`` with ``upload["headers"]``. ``size_bytes`` is echoed back
        in ``file`` and isn't part of the signature; ``content_type`` is, when sent."""
        request: dict[str, Any] = {"path": path, "sizeBytes": size_bytes}
        if content_type is not None:
            request["contentType"] = content_type
        return dict(decode(self._transport.call(upload_file, body=request)))

    def upload(
        self,
        source: str | os.PathLike[str] | bytes | IO[bytes],
        path: str | None = None,
        *,
        content_type: str | None = None,
        multipart: bool = False,
    ) -> dict[str, Any]:
        """Upload one file in a single call and return its file entry.

        ``source`` is a local file path, the bytes themselves, or a seekable binary
        file. ``path`` is where it goes in your workspace; it defaults to the local
        file's name. Up to 3 MiB goes inline (``contentBase64``), up to 5 GB through
        one signed PUT, and anything larger in signed parts finished by
        ``completeFileUpload``; ``multipart=True`` uses parts for a smaller file too. The bytes go straight to storage, never
        with your API key.
        """
        content = _Content.open(source)
        try:
            if path is None:
                if content.name is None:
                    raise TypeError("upload() needs path= when source is not a local file")
                path = content.name
            request: dict[str, Any] = {"path": path}
            if content_type is not None:
                request["contentType"] = content_type
            use_multipart = multipart or content.size > SIGNED_UPLOAD_LIMIT
            if not use_multipart and content.size <= INLINE_UPLOAD_LIMIT:
                request["contentBase64"] = base64.b64encode(content.read(0, content.size)).decode()
                return dict(decode(self._transport.call(upload_file, body=request))["file"])
            request["sizeBytes"] = content.size
            if use_multipart:
                request["multipart"] = True
            answer = decode(self._transport.call(upload_file, body=request))
            upload = answer["upload"]
            if not use_multipart:
                self._transport.put_signed(
                    upload["url"],
                    lambda: content.stream(0, content.size),
                    {**upload.get("headers", {}), "Content-Length": str(content.size)},
                )
                return dict(answer["file"])
            part_size = int(upload["partSizeBytes"])
            numbers = [int(part["partNumber"]) for part in upload["parts"]]
            if part_size <= 0 or sorted(numbers) != list(range(1, len(numbers) + 1)):
                raise TamarindError("The upload session's parts don't number 1 to N.")
            if (len(numbers) - 1) * part_size >= max(content.size, 1) or (
                len(numbers) * part_size < content.size
            ):
                raise TamarindError("The upload session's parts don't cover the file.")
            for part in upload["parts"]:
                self._transport.require_secure(part.get("url"))
            parts = []
            for part in upload["parts"]:
                number = int(part["partNumber"])
                start = (number - 1) * part_size
                length = min(part_size, content.size - start)
                response = self._transport.put_signed(
                    part["url"],
                    lambda start=start, length=length: content.stream(start, length),
                    {"Content-Length": str(length)},
                )
                etag = response.headers.get("etag")
                if not etag:
                    raise TamarindError(f"storage returned no ETag for part {number}")
                parts.append({"partNumber": number, "etag": etag})
            # The contract makes completion repeatable: a repeat after a lost answer
            # returns the stored file.
            completed = self._transport.call(
                complete_file_upload,
                body={"uploadId": upload["id"], "parts": parts},
                repeat_safe=True,
            )
            return dict(decode(completed))
        finally:
            content.close()


class Models(_Resource):
    list = Operation(list_models)
    get = Operation(get_model, "model_id")


class ProjectNotes(_Resource):
    get = Operation(get_project_notes, "project_id")
    update = Operation(update_project_notes, "project_id")
    create_entry = Operation(create_project_notes_entry, "project_id")
    get_entry = Operation(get_project_notes_entry, "project_id", "entry_id")
    update_entry = Operation(update_project_notes_entry, "project_id", "entry_id")
    delete_entry = Operation(delete_project_notes_entry, "project_id", "entry_id")
    append_note = Operation(append_project_notes_note, "project_id", "entry_id")
    update_note = Operation(update_project_notes_note, "project_id", "entry_id", "note_id")
    delete_note = Operation(delete_project_notes_note, "project_id", "entry_id", "note_id")


class Projects(_Resource):
    list = Operation(list_projects)
    create = Operation(create_project)
    get = Operation(get_project, "project_id")
    update = Operation(update_project, "project_id")
    delete = Operation(delete_project, "project_id")
    list_members = Operation(list_project_members, "project_id")
    leave = Operation(leave_project, "project_id")

    def __init__(self, transport: Transport):
        super().__init__(transport)
        self.notes = ProjectNotes(transport)


class Pipelines(_Resource):
    estimate = Operation(estimate_pipeline, repeat_safe=True)
    list_runs = Operation(list_pipeline_runs)
    submit = Operation(submit_pipeline)
    get_run = Operation(get_pipeline_run, "run_id")
    run_results = Operation(get_pipeline_run_results, "run_id", repeat_safe=True)
    cancel_run = Operation(cancel_pipeline_run, "run_id", repeat_safe=True)
    list_node_run_molecules = Operation(list_node_run_molecules, "run_id", "node_run_id")
    schema = Operation(get_pipeline_schema)
    list_templates = Operation(list_pipeline_templates)
    create_template = Operation(create_pipeline_template)
    get_template = Operation(get_pipeline_template, "template_id")
    delete_template = Operation(delete_pipeline_template, "template_id")
    duplicate_template = Operation(duplicate_pipeline_template, "template_id")
    publish_template = Operation(publish_pipeline_template, "template_id")
    validate_template = Operation(validate_pipeline_template, "template_id", repeat_safe=True)
    validate = Operation(validate_pipeline, repeat_safe=True)


class Molecules(_Resource):
    list = Operation(list_molecules)
    list_groups = Operation(list_molecule_groups)
    create_group = Operation(create_molecule_group)
    get_group = Operation(get_molecule_group, "group_id")
    remove_from_group = Operation(remove_molecules_from_group, "group_id", repeat_safe=True)
    list_score_observations = Operation(
        list_molecule_score_observations, "group_id", repeat_safe=True
    )
    start_import = Operation(start_molecule_import)
    get_import = Operation(get_molecule_import, "import_id")
    delete_import = Operation(delete_molecule_import, "import_id")
    commit_import = Operation(commit_molecule_import, "import_id")
    list_schemas = Operation(list_molecule_schemas)
    create_schema = Operation(create_molecule_schema)
    get_schema = Operation(get_molecule_schema, "schema_id")
    update_schema = Operation(update_molecule_schema, "schema_id")
    search = Operation(search_molecules, repeat_safe=True)
    upload = Operation(upload_molecules)
    get = Operation(get_molecule, "molecule_id")
    delete = Operation(delete_molecule, "molecule_id", repeat_safe=True)
    list_groups_for = Operation(list_groups_for_molecule, "molecule_id")
    update_metadata = Operation(update_molecule_metadata, "molecule_id")


class CustomTools(_Resource):
    list = Operation(list_custom_tools)
    create = Operation(create_custom_tool)
    validate_config = Operation(validate_custom_tool_config, repeat_safe=True)
    delete = Operation(delete_custom_tool, "name")
    get = Operation(get_custom_tool, "name")
    update = Operation(update_custom_tool, "name")
    build = Operation(build_custom_tool, "name")
    build_logs = Operation(list_custom_tool_build_logs, "name")
    cancel_build = Operation(cancel_custom_tool_build, "name")
    publish = Operation(publish_custom_tool, "name")
    create_upload = Operation(create_custom_tool_upload, "name")
    list_versions = Operation(list_custom_tool_versions, "name")


class Assays(_Resource):
    list_targets = Operation(list_assay_targets)
    list_types = Operation(list_assay_types)
    list = Operation(list_assays)
    submit = Operation(submit_assay)
    # Not repeat-safe: an estimate sends the sequences to the lab, which files a quote.
    estimate = Operation(estimate_assay)
    validate = Operation(validate_assay, repeat_safe=True)
    get = Operation(get_assay, "assay_id")
    cancel = Operation(cancel_assay, "assay_id", repeat_safe=True)
    results = Operation(get_assay_results, "assay_id")


class Tamarind:
    """A Tamarind API v1 client.

    ``api_key`` defaults to ``TAMARIND_API_KEY`` and ``base_url`` to
    ``https://api.tamarind.bio``; :class:`tamarind.http.HTTPClient` passes the v1 base of
    its own environment (``tamarind._v1.switch``). ``credentials``, a service account's
    :class:`tamarind.oauth.ClientCredentials`, is used in place of a key. ``version`` pins the
    ``Tamarind-Version`` header (``YYYY-MM-DD``); without it the API answers with its
    first version. ``max_retries`` bounds retries of a failed request.
    """

    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        version: str | None = None,
        http_client: httpx.Client | None = None,
        credentials: Any = None,
    ):
        if credentials is not None:
            api_key = None
        else:
            api_key = api_key or os.environ.get("TAMARIND_API_KEY") or None
        self._transport = Transport(
            api_key=api_key,
            credentials=credentials,
            base_url=base_url or DEFAULT_BASE_URL,
            timeout=timeout,
            max_retries=max_retries,
            version=version,
            http_client=http_client,
        )
        self.base_url = self._transport.base_url
        self.me = Me(self._transport)
        self.api_keys = ApiKeys(self._transport)
        self.service_accounts = ServiceAccounts(self._transport)
        self.organization = Organization(self._transport)
        self.usage = Usage(self._transport)
        self.tools = Tools(self._transport)
        self.jobs = Jobs(self._transport)
        self.files = Files(self._transport)
        self.models = Models(self._transport)
        self.projects = Projects(self._transport)
        self.pipelines = Pipelines(self._transport)
        self.molecules = Molecules(self._transport)
        self.custom_tools = CustomTools(self._transport)
        self.assays = Assays(self._transport)

    @staticmethod
    def paginate(method: Any, *args: Any, **params: Any) -> Iterator[Any]:
        """Yield every item of a list operation, following ``nextCursor`` page by page.

        ``client.paginate(client.jobs.list, status="Running", limit=200)``. Takes the
        same arguments as ``method``; ``limit`` sets the page size.
        """
        if not isinstance(method, BoundOperation) or not (method.pageable or method.body_pageable):
            raise TypeError("paginate() takes a list operation such as client.jobs.list")
        if method.pageable:
            cursor = params.pop("cursor", None)
            while True:
                page = _json_page(method(*args, cursor=cursor, **params))
                yield from page.get("items") or []
                cursor = page.get("nextCursor")
                if not cursor:
                    return
                _pause_if_waiting(method, page)
        # The cursor is a body field (molecules.search, molecules.list_score_observations).
        path = len(method.operation.path)
        body = args[path] if len(args) > path else params.pop("body", None)
        request = dict(getattr(body, "to_dict", lambda: body)() or {})
        while True:
            page = _json_page(method(*args[:path], body=request, **params))
            yield from page.get("items") or []
            cursor = page.get("nextCursor")
            if not cursor:
                return
            _pause_if_waiting(method, page)
            request = {**request, "cursor": cursor}

    def close(self) -> None:
        self._transport.close()

    def __enter__(self) -> "Tamarind":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


def _pause_if_waiting(method: BoundOperation, page: dict[str, Any]) -> None:
    """A page still being prepared (``waiting``) says how long to wait for the next one."""
    if page.get("waiting") and isinstance(page.get("retryAfterMs"), (int, float)):
        method._transport._sleep(page["retryAfterMs"] / 1000)


def _json_page(page: Any) -> dict[str, Any]:
    if not isinstance(page, dict):
        raise TypeError(
            "paginate() reads JSON pages; for a CSV page call the method's .raw() and "
            "pass its X-Next-Cursor header as cursor="
        )
    return page


class _Content:
    """Random access to an upload's bytes, whatever the source."""

    def __init__(
        self, handle: IO[bytes], size: int, name: str | None, *, owned: bool, base: int = 0
    ):
        self._handle = handle
        self.size = size
        self.name = name
        self._owned = owned
        # A caller's file is read from where it was positioned when upload() was called.
        self._base = base

    @classmethod
    def open(cls, source: str | os.PathLike[str] | bytes | IO[bytes]) -> "_Content":
        if isinstance(source, (bytes, bytearray, memoryview)):
            data = bytes(source)
            return cls(io.BytesIO(data), len(data), None, owned=True)
        if isinstance(source, (str, os.PathLike)):
            local = Path(source)
            return cls(local.open("rb"), local.stat().st_size, local.name, owned=True)
        if hasattr(source, "read") and hasattr(source, "seek"):
            start = source.tell()
            size = source.seek(0, io.SEEK_END) - start
            source.seek(start)
            return cls(source, size, None, owned=False, base=start)
        raise TypeError("upload() takes a local path, bytes, or a seekable binary file")

    def read(self, start: int, length: int) -> bytes:
        self._handle.seek(self._base + start)
        return self._handle.read(length)

    def stream(self, start: int, length: int, chunk: int = 1024 * 1024) -> Iterator[bytes]:
        self._handle.seek(self._base + start)
        left = length
        while left > 0:
            data = self._handle.read(min(chunk, left))
            if not data:
                break
            left -= len(data)
            yield data

    def close(self) -> None:
        if self._owned:
            self._handle.close()
