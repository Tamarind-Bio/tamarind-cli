"""Today's classic requests, answered by v1 where v1 gives the very same answer.

With v1 selected, every command the CLI already had keeps its classic code: the same
flags, the same output and the same exit codes. Only where some of its requests go
changes. :class:`ClassicOverV1` stands in for the classic :class:`~tamarind.http.HTTPClient`:

- a request :data:`ON_V1` names goes to the v1 operation behind it, and v1's answer is
  rebuilt into the exact value classic returns;
- every other request goes to the classic API, as it does without v1, because v1 can't
  give classic's answer to it (docs/architecture.md, "The v1 API", lists which and why);
- a request v1 refused before acting, where classic would answer on its own, is then
  sent to classic, so the refusal (or a request classic accepts and v1 doesn't, such as
  today's setting names) ends exactly as classic ends it. For a write that is only a
  400, 401, 404 or 422 (:data:`WRITE_FALLBACK`): a 409, 403 or 429 is v1's answer and is
  raised, so a write is never done twice and v1's limits are never stepped around. A
  read (``/result``) also falls back on 403 and 409 (a Stopped job's archive), never on
  429.

A v1 failure with no answer, a 5xx or a 409 ``idempotency_in_progress`` is not sent again
(a submit may have gone through): it is raised the way the classic client raises one, so
the commands' own "outcome may be ambiguous" handling applies unchanged.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from ...errors import APIError, TamarindError, ValidationError
from ...http import HTTPClient
from . import sdk

# What submit-job and submit-batch append for a low-priority job (classic's
# `lowPrioritySubmittedSuffix(true)`, src/lib/jobs/lowPriority.js).
LOW_PRIORITY_SUFFIX = (
    " at low priority (20% off, no completion guarantee, and a job not started within "
    "7 days stops with no charge)"
)


class ClassicAnswer(Exception):
    """v1 can't give classic's answer to this request: ask classic."""


# v1 refused before acting and classic would answer on its own: a malformed request or a
# setting v1 refuses (today's names), a key v1 doesn't take, something v1 can't find.
WRITE_FALLBACK = frozenset({400, 401, 404, 422})
# A read can't be done twice, so it also falls back on 403 and 409; never on 429.
READ_FALLBACK = WRITE_FALLBACK | {403, 409}


def _falls_back(exc: TamarindError, statuses: frozenset[int]) -> bool:
    return getattr(exc, "status", None) in statuses


def _classic_error(exc: TamarindError) -> TamarindError:
    """A v1 failure raised the way the classic client raises one.

    A 5xx becomes an :class:`APIError` with its status; a failure with no answer, or a
    409 ``idempotency_in_progress``, a plain :class:`TamarindError`, which is what the
    commands read as "the outcome may be ambiguous". Any other 4xx (a 409, 403, 429) is
    v1's own answer and keeps its exit code.
    """
    status = getattr(exc, "status", None)
    if getattr(exc, "code", None) == "idempotency_in_progress":
        return TamarindError(exc.message, detail=getattr(exc, "problem", None))
    if isinstance(status, int) and status >= 500:
        return APIError(exc.message, status_code=status, detail=getattr(exc, "problem", None))
    return exc


class ClassicOverV1:
    """The classic client's interface (``get_json``/``post_json``/``delete_json``),
    answering :data:`ON_V1`'s requests from v1."""

    def __init__(self, state: Any):
        cfg = state.config()
        self.base_url = cfg.api_base
        self.api_key = cfg.api_key
        self._state = state
        self._classic = HTTPClient(cfg.api_base, cfg.api_key)
        self._v1: Any = None
        # Requests a command keeps on classic (see keep_on_classic).
        self.on_classic: set[tuple[str, str]] = set()

    def close(self) -> None:
        self._classic.close()
        if self._v1 is not None:
            self._v1.__exit__(None, None, None)

    def __enter__(self) -> "ClassicOverV1":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def v1(self) -> Any:
        if self._v1 is None:
            self._v1 = sdk.make_client(self._state)
        return self._v1

    def get_json(
        self, path: str, *, params: dict[str, Any] | None = None, timeout: float | None = None
    ) -> Any:
        return self._serve(
            "GET", path, params, lambda: self._classic.get_json(path, params=params, timeout=timeout)
        )

    def post_json(self, path: str, *, json: Any | None = None) -> Any:
        return self._serve("POST", path, json, lambda: self._classic.post_json(path, json=json))

    def delete_json(
        self, path: str, *, params: dict[str, Any] | None = None, json: Any | None = None
    ) -> Any:
        payload = json if json is not None else params
        return self._serve(
            "DELETE", path, payload, lambda: self._classic.delete_json(path, params=params, json=json)
        )

    def _serve(self, method: str, path: str, payload: Any, classic: Callable[[], Any]) -> Any:
        key = (method, path.strip("/"))
        route = ON_V1.get(key)
        # No key: classic's client says so, in its words, before sending anything.
        if route is None or not self.api_key or key in self.on_classic:
            return classic()
        handler, fallback = route
        try:
            return handler(self, payload if isinstance(payload, dict) else {})
        except ClassicAnswer:
            return classic()
        except TamarindError as exc:
            if _falls_back(exc, fallback):
                return classic()
            raise _classic_error(exc) from exc

    # -- lookups -----------------------------------------------------------

    def own_item(self, name: Any) -> dict[str, Any]:
        """The caller's own job, batch or run named ``name`` (classic looks names up
        among the caller's own jobs). None found: classic answers it."""
        if not isinstance(name, str) or not name:
            raise ClassicAnswer
        page = sdk.plain(self.v1().jobs.list(name=name))
        items = page.get("items") if isinstance(page, dict) else None
        if not items:
            raise ClassicAnswer
        return dict(items[0])


# -- the requests v1 answers ---------------------------------------------------


def submit_job(client: ClassicOverV1, body: dict[str, Any]) -> str:
    """POST /submit-job → submitJob; classic answers ``<name> submitted to queue.``"""
    name, settings = body.get("jobName"), body.get("settings")
    if not isinstance(name, str) or not isinstance(body.get("type"), str) or not isinstance(settings, dict):
        raise ClassicAnswer  # classic's own wording for a malformed request
    request: dict[str, Any] = {"kind": "job", "tool": body["type"], "name": name, "settings": settings}
    low_priority = body.get("lowPriority") is True
    if low_priority:
        request["lowPriority"] = True
    try:
        client.v1().jobs.submit(body=request)
    except TamarindError as exc:
        if getattr(exc, "code", None) == "job_name_conflict":
            # v1's 409 for a name you already use; classic answers it as a 400 in these words.
            raise ValidationError(f"jobName {name} already exists, please choose a different name") from exc
        raise
    return f"{name} submitted to queue{LOW_PRIORITY_SUFFIX if low_priority else ''}."


def result(client: ClassicOverV1, body: dict[str, Any]) -> str:
    """POST /result → archiveJob (or getJobFile for ``fileName``); classic answers the
    signed link. v1's archive is the stored ``result-<folder>.zip`` classic serves, so
    the bytes are the same.

    Classic keeps: another member's job (``jobEmail``), ``pdbsOnly`` (classic's best
    structures; v1's archive selection isn't built yet), a pipeline run, one file of a
    batch (classic finds it among the batch's jobs), and an archive v1 is still
    preparing (classic builds it in its own way).
    """
    if body.get("jobEmail") is not None or body.get("pdbsOnly"):
        raise ClassicAnswer
    item = client.own_item(body.get("jobName"))
    if item.get("kind") not in ("job", "batch"):
        raise ClassicAnswer
    file_name = body.get("fileName")
    if file_name is not None:
        if not isinstance(file_name, str) or not file_name or item.get("kind") != "job":
            raise ClassicAnswer
        link = sdk.plain(client.v1().jobs.get_file(item["id"], path=file_name, delivery="url"))
        url = link.get("url") if isinstance(link, dict) else None
    else:
        answer = sdk.plain(client.v1().jobs.archive(item["id"], body={}))
        url = answer.get("downloadUrl") if isinstance(answer, dict) else None
    if not isinstance(url, str) or not url.startswith("https://"):
        raise ClassicAnswer
    return url


def delete_job(client: ClassicOverV1, body: dict[str, Any]) -> str:
    """DELETE /delete-job → deleteJob; classic answers ``<name> deleted``."""
    name = body.get("jobName")
    item = client.own_item(name)
    if item.get("kind") not in ("job", "batch"):
        raise ClassicAnswer
    client.v1().jobs.delete(item["id"])
    return f"{name} deleted"


def delete_file(client: ClassicOverV1, params: dict[str, Any]) -> dict[str, str]:
    """DELETE /delete-file → deleteFile; classic answers ``{message}``."""
    path, folder = params.get("filePath"), params.get("folder")
    if path and folder:
        raise ClassicAnswer  # v1 takes exactly one; classic decides as it does today
    if folder:
        client.v1().files.delete(folder=folder)
        return {"message": "Folder deleted successfully"}
    if not path:
        raise ClassicAnswer
    client.v1().files.delete(path=path)
    return {"message": "File deleted successfully"}


Handler = Callable[[ClassicOverV1, dict[str, Any]], Any]
# Each request v1 answers: its handler, and the v1 statuses that send it to classic.
ON_V1: dict[tuple[str, str], tuple[Handler, frozenset[int]]] = {
    ("POST", "submit-job"): (submit_job, WRITE_FALLBACK),
    ("POST", "result"): (result, READ_FALLBACK),
    ("DELETE", "delete-job"): (delete_job, WRITE_FALLBACK),
    ("DELETE", "delete-file"): (delete_file, WRITE_FALLBACK),
}


def keep_on_classic(client: Any, method: str, path: str) -> None:
    """Send this request to classic for the rest of ``client``'s life (nothing to do on
    the classic client itself). ``results --show-url`` prints classic's link: v1 signs
    a different (global-endpoint) one."""
    if isinstance(client, ClassicOverV1):
        client.on_classic.add((method, path))


# -- outside the classic client ---------------------------------------------------


def upload(state: Any, path: Path, remote: str) -> dict[str, Any] | None:
    """``files upload`` on v1 (uploadFile, the PUTs, completeFileUpload); the answer
    classic's upload gives. None when v1 refuses the upload: classic uploads it then."""
    if not state.config().api_key:
        return None
    try:
        with sdk.make_client(state) as client:
            client.files.upload(path, path=remote)
    except TamarindError as exc:
        if _falls_back(exc, WRITE_FALLBACK):
            return None
        raise _classic_error(exc) from exc
    return {"ok": True, "filename": remote, "bytes": path.stat().st_size}


def key_works(state: Any, api_key: str) -> bool | None:
    """Whether v1 accepts ``api_key`` (getMe): None when v1 can't say, so classic decides."""
    if not api_key.strip():
        return None
    try:
        with sdk.make_client(state, api_key=api_key) as client:
            client.me.get()
    except TamarindError as exc:
        # 401 is v1 refusing the key itself; anything else, classic's check decides.
        return False if getattr(exc, "status", None) == 401 else None
    return True
