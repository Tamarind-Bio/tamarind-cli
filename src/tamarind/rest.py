"""Deprecated: the job/file REST surface, now split by resource.

This module mixed two resources — jobs and workspace files — behind one flat
namespace. They now live in :mod:`tamarind.jobs` and :mod:`tamarind.files`, each
split into `api` / `plan` / `flow` like every other resource in the package.

Every name below still works and still calls the same code. Prefer the new homes:

    from tamarind import rest                  ->  from tamarind.jobs import api as jobs_api
    rest.submit_job(client, ...)                   jobs_api.submit_job(client, ...)

    rest.get_files(client, ...)                ->  from tamarind.files import api as files_api
                                                   files_api.get_files(client, ...)

Scheduled for removal one minor version after 0.1.x. Importing this module emits a
DeprecationWarning, which is hidden by default — run with ``-W default`` to see it.
"""

from __future__ import annotations

import warnings

from .files.api import delete_file, get_files, get_folders, upload_file_url
from .jobs.api import (
    cancel_batch,
    cancel_job,
    delete_job,
    get_jobs,
    get_result,
    submit_batch,
    submit_job,
    validate_job,
)

warnings.warn(
    "tamarind.rest is deprecated; use tamarind.jobs and tamarind.files "
    "(see the module docstring for the mapping).",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = [
    "cancel_batch",
    "cancel_job",
    "delete_file",
    "delete_job",
    "get_files",
    "get_folders",
    "get_jobs",
    "get_result",
    "submit_batch",
    "submit_job",
    "upload_file_url",
    "validate_job",
]
