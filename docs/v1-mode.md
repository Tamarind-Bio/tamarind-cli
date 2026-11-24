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
| `jobs`, `status`, `wait`, `submit --wait` | listJobs, getJob |
| `jobs --batch B`, `jobs --include-subjobs` | listJobs with `batchName=B`, or `includeSubjobs` |
| `jobs --organization`, `status`, `wait` and `results NAME --organization`, and `--email M` on `jobs`, `status`, `wait`, `results` | listJobs with `scope=org` (and `createdBy=M`; an organization's name with `allMatches`), getJob |
| `validate`, the check `submit` makes first, `batch --prevalidate` | validateJob |
| `submit`, `batch` | submitJob |
| `cancel`, `cancel --batch` | cancelJob |
| `results` (download, `--show-url`, `--file`) | archiveJob (archivePipelineRun for a run), getJobFile |
| `results --pdbs-only` | archiveJob with `bestStructures` |
| `delete` | deleteJob (a run's `run_` id when only a pipeline run has the name) |
| `logs` | getJobLogs (a job's or a batch's) |
| `files list`, `files stats` | listFiles |
| `files folders` | listFiles with `type=folder` |
| `files upload` | uploadFile |
| `files delete` | deleteFile (`PATH --folder F` deletes the folder, as classic does) |
| `custom-tools …` | the same operations at the v1 base; `custom-tools test` is submitJob pinned to the version; a build's upload session (v1 `id`) is read as classic's `uploadId` |
| `tools`, `modalities`, `functions` | listTools with `view=agent`, getToolFacets with `view=agent` |
| `tools --custom` | listTools with `custom=true` |
| `schema`, `schema --example` | getToolSchema, getTool |

In the SDK, `Tamarind().jobs`, `.files`, `.custom_tools`, `.tools`, `.pipelines.get_run`,
`tamarind.catalog` and the `tamarind.rest` functions follow the same table: the SDK and
the CLI share one mapping (`tamarind._v1.classic`, and `tamarind._v1.catalog` for the
catalog). The SDK's `jobs.cancel(job_id=...)` (classic's cancel by row
`Id`) is cancelJob of `job_<Id>`, else of the batch `batch_<Id>`.

`scope=org` and `createdBy` call classic's own organization and member readers, so who
can see whose jobs, and which jobs, is classic's rule. So do `batchName`, `includeSubjobs`
and `allMatches`: they are classic's batch read, its `includeSubjobs` list and its
organization lookup of a name (every member's match, so the CLI still refuses a name
several members share).

A pipeline run's file or best structures (`results RUN --file PATH`, `--pdbs-only`) and its
`logs` get classic's answer without asking either API: classic reads a run's jobs row,
whose status is `Wrapper`, so it says "Job RUN is not complete. Status: Wrapper" (exit 5),
"File output.log not found" for `--file output.log` (exit 4), and for `logs` "Job 'RUN'
not found or you don't have access to it" (exit 4).

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

- in the SDK, `include_subjobs` with `organization` and `job_name`: classic's organization
  name read then admits a batch's own jobs, and v1's `allMatches` doesn't take
  `includeSubjobs`. (A name read of your own jobs or one member's never reads
  `includeSubjobs`, so there it is left out and the read goes to v1. With `batch` both are
  sent: classic's batch read, which v1's `batchName` is, decides.)

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

**jobs --batch right after batch:** v1 makes a batch's jobs after it answers the submit,
so until they exist the list is empty, and it stays empty for a batch cancelled before they
were made. Classic writes them before it answers, so it lists them at once. A name that
isn't one of your batches (or the member's, with `--email`) is classic's "Jobs in batch B
not found" (exit 4).

**cancel --batch:** the counts come from v1's batch counts just before the cancel. Right
after `batch`, v1 may not have created the batch's jobs yet. It then says "Cancelled 1
job" (the batch itself) where classic says "Cancelled 3 jobs".

**results --show-url:** the URL is v1's presigned URL: a different S3 host form and
different query parameters, for the same file.

**logs:** no `s3Path`. For a log longer than 256 KB, `totalLines` and the byte offsets are
null, because v1 pages back with a cursor rather than byte offsets. A log v1 has nothing
of is classic's "No log file found for job 'X'." (with its `hint`); that includes a
0-byte `output.log`, which classic reads as an empty log.

**results RUN** (the whole run, no `--file` or `--pdbs-only`): v1's archivePipelineRun,
the run's results. Classic refuses it, as it refuses every `/result` of a run ("Job RUN
is not complete. Status: Wrapper").

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
and `job_email`, with `include_subjobs` and with `batch` (v1 itself refuses `search` and
`kind="pipeline"` with these), but not with `job_name`. A filtered batch that matches
nothing is an empty page, not classic's "Jobs in batch B not found".

**The catalog** (`tamarind._v1.catalog`). `tools`, `modalities`, `functions` and `schema`
(in the SDK `tamarind.catalog` and `Tamarind().tools`) are answered from v1 and rebuilt
in the catalog's layout. The list is every page of listTools in the agent view
(`view=agent`, the tools the MCP's getAvailableTools lists), with the catalog's own
filters, sort, facet lists, unrecognized-filter note and hints applied; `tools --custom`
is listTools with `custom=true`; `modalities` and `functions` are getToolFacets in the
agent view; `schema` is getToolSchema with getTool. Turning `TOOL_SET_ON_V1` off (it is
on) sends the list, the custom list and the facets back to the catalog. Diffed on staging
for one account, every tool, against the staging MCP's catalog:
- `tools`: 479 tools where the catalog lists 480. v1 leaves out `abgpt`, which this
  account's organization policy refuses (the catalog lists it and its submit refuses it).
  For the rest: the same envelope, filters, order, hints and fields.
- `modalities` and `functions`: the same values, labels and descriptions. `toolCount` is
  one lower for the two modalities and two functions that count `abgpt`.
- `tools --custom`: the same 51 tools and fields, listed by name, where the catalog lists
  them in the order they were deployed. A tool that trains models is `trainable`, as
  before; v1 doesn't say whether it also runs the models it trains, so `servesModels` is
  left out.
- `schema`: the same envelope, display name, description, categories, tags, hint and
  output types. `outputs` is v1's output contract (with the catalog's `byTaskNote`), the
  catalog's for 446 of 455 tools. Pending a tools fix, 9 differ in `produces`:
  `autodock-vina`, `diffdock`, `gnina`, `matcha`, `smina` and `surfdock` add `sdf`;
  `flowdock` drops `sdf`; `fastsolv` and `unimol2` list none. `exampleJobNote` is the
  catalog's text for the example.
- `schema` parameters are v1's JSON Schema rebuilt as the catalog's list: `name`, `type`,
  `displayName`, `descr`, `default`, `required`, `options`, `lowerBound`/`upperBound` and
  `example`. Left out, with no v1 form: `constraints`, `constraintsText`, `conditionals`,
  `tasks` and the catalog's other UI keys (`showWithRequired`, `extension`, `list`,
  `optionsDescr`, `requiredWhen`...). `descr` is v1's description, which also states the
  constraints (the catalog's text for 42% of settings). `required` is v1's, with what a
  branch requires; a required setting with a default isn't required on v1, which fills it
  in (87% the same). The names are v1's: about 150 settings are named differently from the
  catalog's, and with v1 on, submits take v1's names.
- `schema --example` (`Tamarind().tools.example`) is v1's `example`, built for one task
  branch: the same settings as before for 389 of 426 tools.
- A tool hidden from the assistant (`Hide: agent`: `odesign-antibody`, `protein-scoring`,
  `virtual-screening`) has a schema on v1, where the catalog refuses it.

**Job rows, three more** (from review, not yet changed): a v1 `Failed` job shows `Failed`
where classic says `Stopped`; `stopReason` is kept only for a low-priority job; a pipeline
step's job has no `Batch`.
