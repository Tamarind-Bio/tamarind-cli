# v1 mode

The CLI and the Python SDK (`tamarind.Tamarind`, `tamarind.rest`) call the v1 API for a
key when the server says to. Nothing changes on the client side: today's commands and
methods keep their names, flags, signatures, output layout and exit codes, and the
requests behind them go to v1. This page lists what runs on v1, what still runs on
classic, and where the output differs from classic.

## How v1 is chosen

The server decides, per user: the LaunchDarkly flag `cli-sdk-v1-api`, answered on v1
`GET /me` as `clients.useV1`. The client asks on the first request v1 can answer (never
for `--help`, `--version` or other offline commands) and keeps the answer for 5 minutes,
per key and environment. The CLI keeps it in `~/.tamarind/v1-flag.json` (or under
`TAMARIND_CONFIG_DIR`), mode 0600, which holds a hash of the key, never the key itself.
Anything but an explicit `true` means classic: no answer, a 401, a 404 (a caller outside
v1), the field false or missing. Once a client (or a CLI command) has its answer it keeps
it, so a long `wait` never changes API halfway; a flag change reaches the next command
within 5 minutes. `--help` lists the v1-only commands from the last answer kept, so a
flagged user's very first `--help`, before any command has asked, doesn't list them yet.

The v1 API is the one in the classic base's environment: `app.tamarind.bio` →
`api.tamarind.bio`, `staging.tamarind.bio` → `api-staging.tamarind.bio`. Any other
`--api-base` (a local server) has no v1 and stays classic. `TAMARIND_V1_API_BASE`
overrides the v1 base for tests; `TAMARIND_API=classic` turns v1 off.

Operations only v1 has (`tamarind projects`, `client.projects`, `client.jobs.get`...)
run only when v1 is on for the key; otherwise they say "uses the v1 API, which isn't
enabled for this account yet" (exit 2) and send nothing.

## What runs on v1

| Command | v1 operation |
|---|---|
| `auth status`, `auth login` (the key check) | listJobs (classic's check, one job) |
| `jobs`, `jobs --batch`, `status`, `wait`, `submit --wait` | listJobs, getJob |
| `jobs --organization`, and `--email M` on `jobs`, `jobs --batch`, `status`, `wait`, `results` | listJobs with `scope=org` (and `createdBy=M`), getJob; another member's batch is listed by its id |
| `validate`, the check `submit` makes first, `batch --prevalidate` | validateJob |
| `submit`, `batch` | submitJob |
| `cancel`, `cancel --batch` | cancelJob |
| `results` (download, `--show-url`, `--file`) | archiveJob (archivePipelineRun for a run), getJobFile |
| `results --pdbs-only` | archiveJob with `bestStructures` |
| `delete` | deleteJob |
| `logs` | getJobLogs |
| `files list`, `files stats` | listFiles |
| `files folders` | listFiles with `type=folder` |
| `files upload` | uploadFile |
| `files delete` | deleteFile (`PATH --folder F` deletes the folder, as classic does) |
| `custom-tools …` | the same operations at the v1 base; `custom-tools test` is submitJob pinned to the version; a build's upload session (v1 `id`) is read as classic's `uploadId` |

In the SDK, `Tamarind().jobs`, `.files`, `.custom_tools`, `.pipelines.get_run` and the
`tamarind.rest` functions follow the same table: the SDK and the CLI share one mapping
(`tamarind._v1.classic`). The SDK's `jobs.cancel(job_id=...)` (classic's cancel by row
`Id`) is cancelJob of `job_<Id>`, else of the batch `batch_<Id>`.

`scope=org` and `createdBy` call classic's own organization and member readers, so who
can see whose jobs, and which jobs, is classic's rule.

There is no fallback to classic. When v1 refuses a request, the CLI shows v1's error with
today's exit codes (401 → 3, 404 → 4, 400/422 → 5, 429 → 6, budget or quota → 8, anything
else → 1). The error is a `ProblemError` (with v1's problem document) that is also the
classic class for its status (`AuthError`, `NotFoundError`, `ValidationError`,
`RateLimitError`, `BudgetError`, `APIError` with `status_code`), so existing `except`
clauses still match. On the requests v1 serves at the same path (custom tools, pipeline
runs) the error is the class classic gives the same answer (`CustomToolExistsError`...),
also a `ProblemError`; a refusal v1 codes as about the key or budget is the auth or
budget error. A 5xx or no answer is "outcome unclear", as in classic mode, so
`submit` and `batch` print their recovery command instead of retrying.

## What still runs on classic

These have no v1 form yet, so they stay on classic even with v1 on:

- the catalog: `tools`, `schema`, `modalities`, `functions`, and in the SDK
  `tamarind.catalog` and `Tamarind().tools.list/schema/modalities/functions/example`.
  Pending: once website#7796 and #7807 land (catalog visibility and fields), they move to
  v1, with v1's schema mapped back to today's parameter list;
- `status`, `wait` and `results NAME --organization` without `--email`: an
  organization-wide lookup by name. Classic answers every member's job of that name, and
  the CLI refuses a name several members share; v1's organization lookup answers only the
  newest match, so it would pick one silently. (`wait` keeps the owner its first poll
  finds, so its later polls, and the `results` download, go to v1.)
- `jobs --batch B --organization`: classic lists every member's batch named B; v1 can't
  combine a batch with `scope=org`, and its name lookup finds only the newest batch;
- `jobs --include-subjobs` (v1 lists one batch's jobs, never mixed into the list);
- `logs` of a batch or a pipeline run (v1 reads one job's log);
- `results RUN --file PATH`, one file of a pipeline run (v1's file read takes a job or a batch);
- `results RUN --pdbs-only` (a run's archive has no `bestStructures`);
- `delete NAME` when only a pipeline run has that name (v1 deletes jobs and batches);
- in the SDK, `rest.upload_file_url` (classic's presigned upload URL; v1 uploads are
  sessions, and `files upload` already uses them).

## Differences from classic mode

Found by running each command on staging in both modes and diffing the output.

**Job rows** (`jobs`, `status`, `wait`, `submit --wait`):
- No `StorageFolder` or `TamarindSchemaVersion`. List rows also have no `Settings`; v1
  lists don't carry settings, and `status` of one job does.
- A batch's `status` has no `redactedFields`.
- Lists leave out the internal `batch-aggregate` jobs. A page of `--limit N` therefore
  holds other jobs, and a `--status` filter (applied to that page) can count differently.
- `jobs --batch` lists the batch's jobs in v1's order, which can differ from classic's.
- `status` of an unknown job gives the same message and exit code, without classic's
  problem detail.
- `--organization` and `--email` lists show a job that was dispatched again once, as its
  current attempt; classic lists each attempt. Their rows carry `User`, as classic's do.
  A member whose jobs you can't see gives classic's message and exit code (3), where v1
  itself answers 403.

**validate:**
- An invalid report has no `missing_fields`. Classic lists the schema of each missing
  required setting there; v1 names the field in `errors`.
- v1 refuses the 99 old setting names that classic still accepts. Its 422 names the
  current setting to use.

**cancel --batch:** the counts come from v1's batch counts just before the cancel. Right
after `batch`, v1 may not have created the batch's jobs yet. It then says "Cancelled 1
job" (the batch itself) where classic says "Cancelled 3 jobs".

**results --show-url:** the URL is v1's presigned URL: a different S3 host form and
different query parameters, for the same file.

**logs:** no `s3Path`. For a log longer than 256 KB, `totalLines` and the byte offsets are
null, because v1 pages back with a cursor rather than byte offsets.

**files list:** the same files. After the five newest, the rest are sorted by name ignoring
case, by code point, where classic uses JavaScript's `localeCompare`. Names that differ
only in punctuation can swap places (`1IEP.pdb` and `1iep_imatinib_pose.pdb`).

**results --pdbs-only:**
- For a batch with no stored `-pdbs.zip`, classic builds the zip and sends it as its
  answer, which today's CLI can't read as a link, so the command fails in classic mode;
  v1 builds it and the CLI downloads it. Without `--wait` the CLI waits up to 10 minutes
  for v1's build (v1's own deadline is 8).
- For a batch that hasn't finished, classic zips the jobs complete so far; v1 says the
  batch isn't complete (exit 5).

**SDK `jobs.cancel(job_id=...)`** of a pipeline run's row: classic answers 400 ("stopped
through the pipeline run API"); v1 answers not found (exit 4).

**results --wait of a batch:** v1 can call a batch Complete before its archive is built.
Under `--wait` the CLI asks again after v1's `retryAfterSeconds` until the archive is ready
or `--timeout` passes (exit 7). Without `--wait` it says the archive is still being
prepared.

**custom-tools test** (and the SDK's `CustomTool.test`): v1 has no test marker, so the
run doesn't appear in the website's Test history.

**files delete of a missing file or folder** (also `PATH --folder F`, which deletes the
folder): v1 answers 404 (exit 4); classic answers "File deleted successfully" or "Folder
deleted successfully".

**SDK pipeline runs:** `pipelines.get_run` takes classic's bare run id (sent to v1 as
`run_<id>`) and answers with it; the run, its node runs and a node run's `molecules()`
are read in classic's shape (v1's molecule `id` is classic's `complex_id`, the same
value). Checked live on staging: the typed objects are equal. v1's added
`failureReason` isn't on the typed objects.

**SDK `files.list`:** like classic, it reads only `folder` and `include_folders` (classic's
`pages/api/files.js` ignores `include_all`, `include_metadata` and the paging options).
With `include_folders`, folders are listed as `path/` ahead of the newest files, as
classic dates them "now".

**SDK `rest.upload_file_url`** (classic's `POST /getPresignedUploadUrl`): v1's uploadFile
without content, which signs the same object in the same account bucket. The answer is
`{uploadUrl, key}`: v1 has no `headUrl` or `bucket`. `Content-Type` is always sent and so
always signed, as classic signs it. A path v1 won't take (a leading `/`, `..`, `//`) is
its 422; a path it won't store at is 422 `invalid_option`, where classic answers 403.

**SDK `jobs.list` filters:** `kind`, `status`, `tool` and `search` are v1's. With v1 off,
passing one raises "isn't enabled for this account yet". They combine with `organization`
and `job_email` (v1 itself refuses `search` and `kind="pipeline"` with an organization's
list), but not with `include_subjobs`, `job_name`, or `organization` with `batch`.

**Job rows, three more** (from review, not yet changed): a v1 `Failed` job shows `Failed`
where classic says `Stopped`; `stopReason` is kept only for a low-priority job; a pipeline
step's job has no `Batch`.
